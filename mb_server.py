# In a YouTube video, Julian OH8STN proposed extending JS8Call to support microblogging; the creation
# blog posts which can be retrieved using JS8Call - see https://youtu.be/szZlPL2h534

# This program is an attempt to extend JS8Call, using its API, to serve microblogs in the way Julian
# suggests.  This program should run on the computer of the amateur radio operator serving the microblogs.
# See https://youtu.be/Nxg5_hiKlqc for an explanation.

# Documentation can is available at https://github.com/PaulOfford/mbserver and in the README.md file
# accompanying this file.

# USE OF THIS PROGRAM
# This is proof of concept program code and is freely available for experimentation.  You can change and
# reuse any portion of the program code without restriction.  The author(s) accept no responsibility for
# damage to equipment, corruption of data or consequential loss caused by this program code or any variant
# of it.  The author(s) accept no responsibility for violation of any radio or amateur radio regulations
# resulting from the use of the program code.

from datetime import datetime, timezone
from socket import socket, AF_INET, SOCK_STREAM

import re
import json
import time
import glob
import select

# Configuration Parameters ############################################################################

# make sure you open port 2442 prior to opening JS8 application
# ubuntu command: sudo ufw allow 2442
# in JS8Call go to File -> Settings -> Reporting in API section check:
# Enable TCP Server API
# Accept TCP Requests

server = ('127.0.0.1', 2442)
capabilities = 'LEG'
announce = True
mb_announcement_timer = 300
languages = 'EN-GB'

posts_dir = 'C:\\Development\\microblog\\posts\\'  # location of the microblog posts
lst_limit = 5
replace_nl = False  # if True, \n characters in a post will be replaced with a space character

# when debugging this code, JS8Call must be running but a radio isn't needed
debug = False  # set to True to tests with simulated messages set in debug_json
# debug_request = 'NOT AN MB REQUEST'
# debug_request = 'MB.L'
# debug_request = 'MB.E'
debug_request = 'MB.L >22'
# debug_request = 'MB.E >22'
# debug_request = 'MB.L > 22'
# debug_request = 'MB.L 2023-01-13'
# debug_request = 'MB.E 2023-01-13'
# debug_request = 'MB.E FRED'
# debug_request = 'MB.L >2023-01-06'
# debug_request = 'MB.E >2023-01-06'
# debug_request = 'MB.L > 2023-01-06'
# debug_request = 'MB.G 24'
# debug_request = 'MB.G 9999'
# debug_request = 'MB.G 2023-01-13'

#######################################################################################################


def logmsg(msg_text):
    now = datetime.now(timezone.utc)
    date_time = now.strftime("%Y-%m-%d %H:%M:%SZ -")
    print(date_time, msg_text)


class Js8CallApi:

    connected = False
    my_station = ''
    my_grid = ''

    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)

    def connect(self):
        logmsg('Connecting to JS8Call at ' + ':'.join(map(str, server)))
        try:
            api = self.sock.connect(server)
            self.connected = True
            logmsg('Connected to JS8Call')
            return api

        except ConnectionRefusedError:
            logmsg('Connection to JS8Call has been refused.')
            logmsg('Check that:')
            logmsg('* JS8Call is running')
            logmsg('* JS8Call settings check boxes Enable TCP Server API and Accept TCP Requests are checked')
            logmsg('* The API server port number in JS8Call matches the setting in this script - default is 2442')
            logmsg('* There are no firewall rules preventing the connection')
            exit(1)

    def set_my_grid(self, grid):
        self.my_grid = grid
        return

    def set_my_station(self, station_id):
        self.my_station = station_id
        return

    def listen(self):
        # the following block of code provides a socket recv with a 10-second timeout
        # we need this so that we call the @MB announcement code periodically
        self.sock.setblocking(0)
        ready = select.select([self.sock], [], [], 10)
        if ready[0]:
            content = self.sock.recv(65500)
        else:
            content = 'Check if announcement needed'

        if not content:
            message = {}
            self.connected = False
        else:
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
            logmsg('tx: ' + self.my_station + ': ' + args[1])  # console trace of messages sent

        message = message.replace('\n\n', '\n \n')  # this seems to help with the JS8Call message window format

        if args[1] and debug:
            logmsg('MB message not sent as we are in debug mode')
            # this avoids hamlib errors in JS8Call if the radio isn't connected
        else:
            self.sock.send((message + '\n').encode())   # newline suffix is required

    def close(self):
        self.sock.close()


class Request:
    # the following is a list of valid commands and
    # their corresponding command processors in the MbServer class
    cmd_list = {
        'M.LST': 'process_mb_lst',
        'M.L': 'process_mb_lst',
        'M.EXT': 'process_mb_ext',
        'M.E': 'process_mb_ext',
        'M.GET': 'process_mb_get',
        'M.G': 'process_mb_get',
        'MB.LST': 'process_mb_lst',
        'MB.L': 'process_mb_lst',
        'MB.EXT': 'process_mb_ext',
        'MB.E': 'process_mb_ext',
        'MB.GET': 'process_mb_get',
        'MB.G': 'process_mb_get',
    }

    caller = ''
    rc = -1  # default not a microblog command
    msg = ''
    cmd = ''
    op = ''
    post_id = 0
    date = ''
    processor = ''

    def validate_criteria(self, criteria):
        if criteria[0:1] == '>':
            self.op = 'gt'
            criteria = criteria.replace('>', '')
            criteria = criteria.replace(' ', '')  # eliminate any spaces
        elif criteria[0:1] == '♢':
            self.op = 'gt'
            criteria = criteria.replace('♢', '')
        else:
            self.op = 'eq'

        if criteria:
            try:
                self.post_id = int(criteria)
                self.rc = 0
                self.msg = 'OK'
            except ValueError:
                try:
                    time.strptime(criteria, '%Y-%m-%d')
                    self.date = criteria
                    self.rc = 0
                    self.msg = 'OK'
                except ValueError:
                    self.rc = 102
                    self.msg = 'PARAMETER NOT INTEGER OR DATE'
        else:
            self.rc = 0
            self.msg = 'OK'

        return self.rc

    def parse(self, request):
        request_parts = re.split(' +', request)
        self.caller = request_parts[0].replace(':', '')
        if len(request_parts) >= 2:
            # check if the command is in the cmd_list and if it is retrieve the processor function name
            if request_parts[2] in self.cmd_list:
                self.cmd = request_parts[2]
                self.processor = self.cmd_list[self.cmd]  # set the processor function name for this cmd
                logmsg('rx: ' + request)  # console trace of messages received
                if debug:
                    logmsg(request_parts)
                if len(request_parts) > 2:
                    # check Post ID and Date criteria
                    self.validate_criteria(request_parts[3])
                else:
                    # there is no Post ID or Date criterion
                    self.rc = 0
                    self.op = 'gt'  # this will be greater than zero and so all posts

        return self.rc


class CmdProcessors:
    @staticmethod
    def get_post_meta(filename, include_date):
        post = filename.replace(posts_dir, '')
        post = post.replace('.txt', '')
        temp = post.split(' ', 4)
        post_id = int(temp[0])
        date = temp[2]
        text = temp[4]

        list_text = str(post_id)
        if include_date:
            list_text += ' - ' + date
        list_text += ' - ' + text
        list_text += '\n'

        return {'post_id': post_id, 'date': date, 'list_text': list_text}

    def mb_lst_by_id(self, request, include_date):
        if request.op == 'eq':
            file_list = sorted(glob.glob(posts_dir + '*' + str(request.post_id) + '*.txt'))
        else:
            file_list = sorted(glob.glob(posts_dir + '*.txt'))
        list_text = ''
        found_post = False
        lst_count = 0
        for filename in file_list:
            post = self.get_post_meta(filename, include_date)
            if (request.op == 'gt' and post['post_id'] > request.post_id)\
                    or (request.op == 'eq' and post['post_id'] == request.post_id):
                found_post = True
                list_text += post['list_text']
                lst_count += 1
                if lst_count >= lst_limit:
                    break
        if found_post:
            return list_text
        else:
            return 'NO POSTS FOUND' + '\n'

    def mb_lst_by_date(self, request, include_date):
        if request.op == 'eq':
            file_list = sorted(glob.glob(posts_dir + '*' + request.date + '*.txt'))
        else:
            file_list = sorted(glob.glob(posts_dir + '*.txt'))
        list_text = ''
        found_post = False
        lst_count = 0

        for filename in file_list:
            post = self.get_post_meta(filename, include_date)
            if (request.op == 'gt' and post['date'] > request.date)\
                    or (request.op == 'eq' and post['date'] == request.date):
                found_post = True
                list_text += post['list_text']
                lst_count += 1
                if lst_count >= lst_limit:
                    break

        if found_post:
            return list_text
        else:
            return 'NO POSTS FOUND' + '\n'

    def process_mb_ext(self, request):
        header = '%s +%s\n' % (request.caller, request.cmd)

        if request.post_id > 0:
            blog_list = self.mb_lst_by_id(request, include_date=True)
        else:
            blog_list = self.mb_lst_by_date(request, include_date=True)
        return header + blog_list

    def process_mb_lst(self, request):
        header = '%s +%s\n' % (request.caller, request.cmd)

        if request.post_id > 0:
            blog_list = self.mb_lst_by_id(request, include_date=False)
        else:
            blog_list = self.mb_lst_by_date(request, include_date=False)
        return header + blog_list

    @staticmethod
    def getmbpost(filename):
        f = open(filename)
        post = f.read()
        return post

    def process_mb_get(self, request):
        header = '%s +%s' % (request.caller, request.cmd)

        filename = ''
        mb_message = ''
        if request.post_id > 0:
            header += ' ' + str(request.post_id)
            found_post = False
            file_list = sorted(glob.glob(posts_dir + '*' + str(request.post_id) + '*.txt'))
            for filename in file_list:
                post = filename.replace(posts_dir, '')
                temp = post.split(' ', 1)
                this_post_id = int(temp[0])
                if this_post_id == request.post_id:
                    found_post = True
                    break
            if found_post:
                mb_message += self.getmbpost(filename)
                header += '\n'
            else:
                header += ' '
                mb_message = 'NOT FOUND'

        else:
            header += ' '
            mb_message = 'BY DATE UNSUPPORTED'

        mb_message = mb_message.replace('\r\n', '\n')

        if replace_nl:
            mb_message = mb_message.replace('\n', ' ')  # temp code until NL fixed

        return header + mb_message


class MbAnnouncement:

    latest_post_id = 0
    latest_post_date = '2000-01-01'
    next_announcement = 0

    def latest_post_meta(self):
        file_list = sorted(glob.glob(posts_dir + '*.txt'))
        latest_listing = file_list[len(file_list) - 1]
        latest_post_values = latest_listing.split(' ', 4)
        string_post_id = latest_post_values[0].replace(posts_dir, '')
        self.latest_post_id = int(string_post_id)
        self.latest_post_date = latest_post_values[2]
        return

    def send_mb_announcement(self, js8call_api):
        # get the current epoch
        epoch = time.time()
        if epoch > self.next_announcement:
            self.latest_post_meta()  # update with the latest post info
            message = '@MB {mgl} {capable} {pid} {pdate} {langs}'.format(
                                                                  mgl=js8call_api.my_grid,
                                                                  capable=capabilities,
                                                                  pid=self.latest_post_id,
                                                                  pdate=self.latest_post_date,
                                                                  langs=languages
                                                                )
            js8call_api.send('TX.SEND_MESSAGE', message)
            # update the next announcement epoch
            self.next_announcement = epoch + mb_announcement_timer

        return


class MbServer:

    first = True
    connected = False

    @staticmethod
    def process(js8call_api: Js8CallApi, message):
        typ = message.get('type', '')
        value = message.get('value', '')

        if not typ:
            return

        elif typ == 'STATION.GRID':
            if debug:
                logmsg('api rsp: ' + value)
            js8call_api.set_my_grid(value)
            pass

        elif typ == 'STATION.CALLSIGN':
            if debug:
                logmsg('api rsp: ' + value)
            js8call_api.set_my_station(value)
            pass

        elif typ == 'RX.DIRECTED':  # we are only interested in messages directed to us
            if value:
                request = Request()
                if request.parse(value) < 0:
                    return  # the received string isn't for us

                elif request.rc == 0:
                    procs = CmdProcessors()
                    mb_message = getattr(CmdProcessors, request.processor)(procs, request)
                    js8call_api.send('TX.SEND_MESSAGE', mb_message)

                else:
                    mb_message = '%s %s %s' % (request.caller, request.cmd, request.msg)
                    js8call_api.send('TX.SEND_MESSAGE', mb_message)

    def run_server(self):

        js8call_api = Js8CallApi()
        js8call_api.connect()

        js8call_api.send('STATION.GET_GRID', '')
        logmsg('api call: STATION.GET_GRID')
        if js8call_api.connected:
            message = js8call_api.listen()
            if message:
                self.process(js8call_api, message)
            else:
                logmsg('Unable to get My Grid.')
                logmsg('Check in File -> Settings -> General -> '
                       'Station -> Station Details -> My Maidenhead Grid Locator')

            js8call_api.send('STATION.GET_CALLSIGN', '')
            logmsg('api call: STATION.GET_CALLSIGN')
            if js8call_api.connected:
                message = js8call_api.listen()
                if message:
                    self.process(js8call_api, message)
                else:
                    logmsg('Unable to get My Callsign.')
                    logmsg('Check in File -> Settings -> General -> Station -> Station Details -> My Callsign')

        mb_announcement = MbAnnouncement()

        # this debug code block processes simulated incoming commands

        try:
            while js8call_api.connected:
                if announce:
                    mb_announcement.send_mb_announcement(js8call_api)

                if debug:
                    # simulate a received message
                    debug_json = '{"type":"RX.DIRECTED","value":"CALL3R: %s %s"}' % (js8call_api.my_station, debug_request)
                    message = json.loads(debug_json)
                else:
                    message = js8call_api.listen()

                if not message:
                    continue

                self.process(js8call_api, message)

                if debug:
                    break  # we only run one cycle when debugging

        finally:
            js8call_api.close()


def main():
    s = MbServer()
    s.run_server()


if __name__ == '__main__':
    main()
