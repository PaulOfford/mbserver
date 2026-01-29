import re
from socket import socket, AF_INET, SOCK_STREAM
import queue
import logging
import json
import time
import select

from .general_functions import add_progress_m
from .message_q import b2c_q_p0, b2c_q_p1, c2b_q, UnifiedMessage, MessageType, MessageVerb, MessageParameter
from .config import SETTINGS

role = SETTINGS.role
js8call_addr = SETTINGS.server
debug = SETTINGS.debug

logger = logging.getLogger(__name__)


class Js8CallApi:

    my_station = ''
    my_grid = ''

    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connect(self):
        logger.info('Connecting to JS8Call at ' + ':'.join(map(str, js8call_addr)))
        try:
            api = self.sock.connect(js8call_addr)
            logger.info('Connected to JS8Call')
            return api

        except ConnectionRefusedError:
            logger.error('Connection to JS8Call has been refused.')
            logger.error('Check that:')
            logger.error('* JS8Call is running')
            logger.error(
                '* JS8Call settings check boxes Enable TCP Server API and'
                'Accept TCP Requests are checked'
            )
            logger.error(
                '* The API server port number in JS8Call matches the setting in this script'
                ' - default is 2442'
            )
            logger.error('* There are no firewall rules preventing the connection')
            exit(1)

    def listen(self):
        # the following block of code provides a socket recv with a 0.5-second timeout
        messages = []
        self.sock.setblocking(False)
        ready = select.select([self.sock], [], [], 0.5)
        if ready[0]:
            content = self.sock.recv(65500)
            logger.debug('rx - ' + str(content))

            if content:
                # remove the terminator
                content = content.replace(bytes('♢', 'utf8'), bytes('', 'utf8'))
                content = content.replace(bytes("  '}", 'utf8'), bytes("'}", 'utf8'))
                # we have to tidy the content in case there are multiple responses in a single socket recv
                content = content.replace(bytes('}\n{', 'utf8'), bytes('},{', 'utf8'))
                content = bytes('[', 'utf8') + content
                content += bytes(']', 'utf8')
                content = content.replace(bytes('}\n]', 'utf8'), bytes('}]', 'utf8'))
                try:
                    messages = json.loads(content)
                except ValueError:
                    pass
            else:
                logger.info('ctrl: Connection to JS8Call has closed')
                # ToDo: signal connection loss to backend, which should then add a QSO box entry

        return messages  # we return a list of messages, typically with a length of one

    @staticmethod
    def to_message(typ, value='', params=None):
        if params is None:
            params = {}
        return json.dumps({'type': typ, 'value': value, 'params': params})

    def send(self, *args, **kwargs):
        params = kwargs.get('params', {})
        if '_ID' not in params:
            params['_ID'] = '{}'.format(int(time.time() * 1000))
            kwargs['params'] = params
        message = self.to_message(*args, **kwargs)

        message = message.replace('\n\n', '\n \n')  # this seems to help with the JS8Call message window format

        if len(args) > 1 and debug:
            logger.debug('MB message not sent as we are in debug mode')
            # this avoids hamlib errors in JS8Call if the radio isn't connected
        else:
            mb_msg = (message + '\n').encode()
            logger.debug('tx - ' + str(mb_msg))
            self.sock.send(mb_msg)   # newline suffix is required

    def close(self):
        self.sock.close()


class Js8CallDriver:

    status = None
    request = None
    rx_ind_timeout: float = 0.0
    flash_duration = 0.5

    tx_block_timeout: float = 0.0

    is_connected = False

    def __init__(self):
        self.js8call_api = Js8CallApi()
        self.js8call_api.connect()
        self.is_connected = True

    def set_radio_frequency(self, freq: int):
        logger.debug('call: RIG.SET_FREQ')
        kwargs = {'params': {'DIAL': freq}}
        self.js8call_api.send('RIG.SET_FREQ', **kwargs)
        pass

    def process_mb_msg(self, m: UnifiedMessage):
        req_msg = f"{m.get_param(MessageParameter.DESTINATION)} {m.get_param(MessageParameter.MB_MSG)}"
        # self.tx_block_timeout = time.time() + 15  # Block further sends
        self.js8call_api.send('TX.SEND_MESSAGE', req_msg)

    def process_control(self, m: UnifiedMessage):
        if m.get_verb() == MessageVerb.SHUTDOWN:
            self.is_connected = False
            return
        elif m.get_verb() == MessageVerb.SET_FREQ:
            self.set_radio_frequency(m.get_param(MessageParameter.FREQUENCY))
        elif m.get_verb() == MessageVerb.GET_FREQ:
            self.js8call_api.send('RIG.GET_FREQ', '')
        elif m.get_verb() == MessageVerb.GET_OFFSET:
            self.js8call_api.send('RIG.GET_FREQ', '')
        elif m.get_verb() == MessageVerb.GET_CALLSIGN:
            self.js8call_api.send('STATION.GET_CALLSIGN', '')

    def process_comms_tx(self, m: UnifiedMessage):
        if m.get_typ() == MessageType.MB_MSG:
            self.process_mb_msg(m)

        elif m.get_typ() == MessageType.CONTROL:
            self.process_control(m)

        else:
            logger.error(f"Invalid message received from backend, typ = {m.get_typ()}")

    def process_tx_q(self, timeout: float = 0.05):
        """Process outbound messages from the backend.

        Uses a short blocking wait (reduces CPU) and then drains any burst.
        """
        # if time.time() < self.tx_block_timeout:
        #     return

        try:
            comms_tx: UnifiedMessage = b2c_q_p0.get(timeout=timeout)
            logger.debug(f"Received from BACKEND: {comms_tx.get_params()}")
            self.process_comms_tx(comms_tx)
            add_progress_m(comms_tx)
            b2c_q_p0.task_done()
        except queue.Empty:
            try:
                comms_tx: UnifiedMessage = b2c_q_p1.get(timeout=timeout)
                logger.debug(f"Received from BACKEND: {comms_tx.get_params()}")
                self.process_comms_tx(comms_tx)
                add_progress_m(comms_tx)
                b2c_q_p1.task_done()
            except queue.Empty:
                return
        return

    @staticmethod
    def signal_frontend(verb: MessageVerb):
        # These are the signa verbs we can send to the FRONTEND:
        #   FLASH_RX_START, FLASH_RX_STOP, FLASH_TX_START, FLASH_TX_STOP, SCAN_OFF
        m = UnifiedMessage.create(
            priority=0,
            target="FRONTEND",
            typ="SIGNAL",
            verb=verb
        )
        c2b_q.put(m)

    @staticmethod
    def signal_backend(verb: MessageVerb, param):
        # These are the signal verbs we can send to the FRONTEND:
        #   NOTE_FREQ, NOTE_OFFSET, NOTE_CALLSIGN
        m = UnifiedMessage.create(
            priority=0,
            target="BACKEND",
            typ="SIGNAL",
            verb=verb,
            params=param
        )
        c2b_q.put(m)

    @staticmethod
    def inform_backend(source: str, frequency: int, destination: str, mb_message: str):
        # This is where we send an inbound microblog message to the backend
        m = UnifiedMessage.create(
            priority=1,
            target="BACKEND",
            typ="MB_MSG",
            verb="INFORM",
            params={
                "source": source,
                "destination": destination,
                "mb_msg": mb_message,
                "frequency": frequency
            }
        )
        c2b_q.put(m)
        add_progress_m(m)

    @staticmethod
    def announce_to_backend(source: str, frequency: int, destination: str, mb_message: str):
        # This is where we send an inbound microblog message to the backend
        m = UnifiedMessage.create(
            priority=1,
            target="BACKEND",
            typ="MB_MSG",
            verb="ANNOUNCE",
            params={
                "source": source,
                "destination": destination,
                "mb_msg": mb_message,
                "frequency": frequency
            }
        )
        c2b_q.put(m)
        add_progress_m(m)

    def run_comms(self):

        if self.is_connected:
            logger.debug('Send STATION.GET_CALLSIGN')
            self.js8call_api.send('STATION.GET_CALLSIGN', '')

            logger.debug('Send RIG.GET_FREQ')
            self.js8call_api.send('RIG.GET_FREQ', '')

        try:
            while self.is_connected:
                # process messages from the backend
                self.process_tx_q()

                # process messages from Js8Call
                messages = self.js8call_api.listen()

                if 0 < self.rx_ind_timeout < time.time():
                    if role == 'mbserver':
                        self.signal_backend(MessageVerb.FLASH_RX_STOP, None)
                    else:
                        self.signal_frontend(MessageVerb.FLASH_RX_STOP)
                    self.rx_ind_timeout = 0

                for message in messages:
                    js8call_msg_type = message.get('type', '')
                    value = message.get('value', '')
                    params = message.get('params', {})

                    if role == 'mbserver':
                        self.signal_backend(MessageVerb.FLASH_RX_START, None)
                    else:
                        self.signal_frontend(MessageVerb.FLASH_RX_START)
                    self.rx_ind_timeout = time.time() + self.flash_duration

                    if not js8call_msg_type:
                        continue

                    elif js8call_msg_type == 'RIG.PTT':
                        if value == 'on':
                            fe_verb = MessageVerb.FLASH_TX_START
                            ptt_state = True
                        else:
                            fe_verb = MessageVerb.FLASH_TX_STOP
                            ptt_state = False

                        if role == 'mbserver':
                            self.signal_backend(MessageVerb.NOTE_PTT, ptt_state)
                        else:
                            self.signal_frontend(fe_verb)

                    elif js8call_msg_type == 'STATION.CALLSIGN':
                        self.signal_backend(MessageVerb.NOTE_CALLSIGN, {'callsign': value})

                    elif js8call_msg_type == 'RIG.FREQ' or js8call_msg_type == 'STATION.STATUS':
                        dial = int(params['DIAL'])
                        offset = int(params['OFFSET'])

                        self.signal_backend(MessageVerb.NOTE_FREQ, {'frequency': dial})
                        logger.debug('q_put: NOTE_FREQ - ' + str(dial))

                        self.signal_backend(MessageVerb.NOTE_OFFSET, {'offset': offset})
                        logger.debug('q_put: NOTE_OFFSET - ' + str(offset))

                    elif js8call_msg_type == 'RX.DIRECTED':
                        # We need to extract the source and destination
                        msg_elements = re.findall(r"^\S+: +\S+ +([\S\s]+)", value)
                        mb_message = msg_elements[0]

                        if str(params['TO']) == "@MB":
                            self.announce_to_backend(
                                str(params['FROM']),
                                int(params['DIAL']),
                                str(params['TO']),
                                mb_message
                            )

                        else:
                            self.inform_backend(
                                str(params['FROM']),
                                int(params['DIAL']),
                                str(params['TO']),
                                mb_message
                            )

                        logger.debug('q_put: INFORM - ' + mb_message)

        finally:
            self.js8call_api.close()
