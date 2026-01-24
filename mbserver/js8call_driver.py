import json
import select
import time

from socket import socket, AF_INET, SOCK_STREAM
from .logging import *


class Js8CallApi:

    connected = False
    my_station = ''

    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connect(self):
        logmsg(1, 'info: Connecting to JS8Call at ' + ':'.join(map(str, server)))
        try:
            api = self.sock.connect(server)
            self.connected = True
            logmsg(1, 'info: Connected to JS8Call')
            return api

        except ConnectionRefusedError:
            logmsg(1, 'err: Connection to JS8Call has been refused.')
            logmsg(1, 'info: Check that:')
            logmsg(1, 'info: * JS8Call is running')
            logmsg(1, 'info: * JS8Call settings check boxes Enable TCP Server API and Accept TCP Requests are checked')
            logmsg(1, 'info: * The API server port number in JS8Call matches the setting in this script'
                      ' - default is 2442')
            logmsg(1, 'info: * There are no firewall rules preventing the connection')
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
            logmsg(4, 'recv: ' + str(content))
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
        content = '{"params":{"CMD":" ","DIAL":14078000,"EXTRA":"","FREQ":14079060,"FROM":"2E0FGO","GRID":" JO01","OFFSET":1060,"SNR":-7,"SPEED":0,"TDRIFT":0.5,"TEXT":"2E0FGO: @MB  Q \xe2\x99\xa2 ","TO":"@MB","UTC":1695826287443,"_ID":-1},"type":"RX.DIRECTED","value":"2E0FGO: @MB  Q \xe2\x99\xa2 "}'

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

        if args[1]:  # if no args must be an api call that doesn't send a message
            # under normal circumstances, we don't want to fill the log with post content
            # only log the message content if running at log level 2 or above
            if current_log_level >= 2:
                log_line = args[1]
            else:
                temp = args[1].split('\n', 1)
                log_line = temp[0]
            logmsg(current_log_level, 'TX -> ' + self.my_station + ': ' + log_line)  # console trace of messages sent

        message = message.replace('\n\n', '\n \n')  # this seems to help with the JS8Call message window format
        logmsg(2, 'send: ' + message)

        if args[1] and debug:
            logmsg(3, 'info: MB message not sent as we are in debug mode')
            # this avoids hamlib errors in JS8Call if the radio isn't connected
        else:
            self.sock.send((message + '\n').encode())   # newline suffix is required

    def close(self):
        self.sock.close()
