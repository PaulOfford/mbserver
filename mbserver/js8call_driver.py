import json
import select
import time

from socket import socket, AF_INET, SOCK_STREAM
from logging import getLogger

from .config import SETTINGS

server = SETTINGS.server

logger = getLogger(__name__)


class Js8CallApi:

    connected = False
    my_station = ''

    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connect(self):
        logger.info('Connecting to JS8Call at ' + ':'.join(map(str, server)))
        try:
            api = self.sock.connect(server)
            self.connected = True
            logger.info('Connected to JS8Call')
            return api

        except ConnectionRefusedError:
            logger.error('Connection to JS8Call has been refused.')
            logger.error('Check that:')
            logger.error('* JS8Call is running')
            logger.error('* JS8Call settings check boxes Enable TCP Server API and Accept TCP Requests are checked')
            logger.error('* The API server port number in JS8Call matches the setting in this script'
                         ' - default is 2442')
            logger.info('* There are no firewall rules preventing the connection')
            exit(1)

    def set_my_station(self, station_id: str):
        self.my_station = station_id

    def listen(self):
        messages = []
        # the following block of code provides a socket recv with a 10-second timeout
        # we need this so that we call the @MB announcement code periodically
        self.sock.setblocking(False)
        ready = select.select([self.sock], [], [], 10)
        if ready[0]:
            content = self.sock.recv(65500)
            logger.debug('RX <- : ' + str(content))
        else:
            content = 'Check if announcement needed'

        if not content:
            messages = []
            self.connected = False
        else:
            json_docs = content.splitlines()
            for json_doc in json_docs:
                try:
                    message = json.loads(json_doc)
                except ValueError:
                    # The message looks corrupt.  Let's stop here.
                    return messages
                messages.append(message)

        return messages

    @staticmethod
    def listen_mock():
        content = '{"params":{"CMD":" ","DIAL":14078000,"EXTRA":"","FREQ":14079060,"FROM":"2E0FGO","GRID":" JO01",' \
                  '"OFFSET":1060,"SNR":-7,"SPEED":0,"TDRIFT":0.5,"TEXT":"2E0FGO: @MB  Q \xe2\x99\xa2 ",' \
                  '"TO":"@MB","UTC":1695826287443,"_ID":-1},"type":"RX.DIRECTED",' \
                  '"value":"2E0FGO: @MB  Q \xe2\x99\xa2 "}'

        time.sleep(1)

        try:
            message = json.loads(content)
        except ValueError:
            message = {}

        return message

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
        logger.debug('TX -> ' + message)

        self.sock.send((message + '\n').encode())  # newline suffix is required

    def close(self):
        self.sock.close()
