# In a YouTube video, Julian OH8STN proposed extending JS8Call to support microblogging; the creation
# blog posts which can be retrieved using JS8Call - see https://youtu.be/szZlPL2h534

# This program is an attempt to extend JS8Call, using its API, to serve microblogs in the way Julian
# suggests.  This program should run on the computer of the amateur radio operator serving the microblogs.
# See https://youtu.be/Nxg5_hiKlqc for an explanation.

# This "server" supports the following requests:
#  * MB.LST - list all posts available
#  * MB.LST >n - list all posts with an id greater than n
#  * MB.LST yyyy-mm-dd - list all posts dated yyyy-mm-dd
#  * MB.LST >yyyy-mm-dd - list all posts created after yyyy-mm-dd
#  * MB.GET n - get the post with the id n

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

# make sure you open port 2442 prior to opening JS8 application
# ubuntu command: sudo ufw allow 2442

server = ('127.0.0.1', 2442)    # in JS8Call go to File -> Settings -> Reporting in API section check:
                                # Enable TCP Server API
                                # Accept TCP Requests
posts_dir = 'C:\\Development\\microblog\\posts\\'  # location of the microblog posts
lst_limit = 5
replace_nl = False  # if True, \n characters in a post will be replaced with a space character

# when debugging this code, JS8Call must be running but a radio isn't needed
debug = False  # set to True to tests with simulated messages set in debug_json
debug_request = 'MB.LST'
# debug_request = 'MB.LST >22'
# debug_request = 'MB.LST 2023-01-13'
# debug_request = 'MB.LST >2023-01-06'
# debug_request = 'MB.GET 24'
# debug_request = 'MB.GET 9999'
# debug_request = 'MB.GET 2023-01-13'


def logmsg(msg_text):
    now = datetime.now(timezone.utc)
    date_time = now.strftime("%Y-%m-%d %H:%M:%SZ -")
    print(date_time, msg_text)

def from_message(content):
    try:
        return json.loads(content)
    except ValueError:
        return {}

def to_message(typ, value='', params=None):
    if params is None:
        params = {}
    return json.dumps({'type': typ, 'value': value, 'params': params})


class MbServer(object):
    first = True
    connected = False
    my_station = ''

    def __init__(self):
        logmsg('Connecting to JS8Call at ' + ':'.join(map(str, server)))
        self.sock = socket(AF_INET, SOCK_STREAM)
        try:
            self.sock.connect(server)
        except ConnectionRefusedError:
            logmsg('Connection to JS8Call has been refused.')
            print('Check that:')
            print('* JS8Call is running')
            print('* JS8Call settings check boxes Enable TCP Server API and Accept TCP Requests are checked')
            print('* The API server port number in JS8Call matches the setting in this script - default is 2442')
            print('* There are no firewall rules preventing the connection')
            exit(1)
        self.connected = True
        logmsg('Connected to JS8Call')

    def validate_criteria(self, criteria):
        # default values
        date = ''
        post_id = 0
        rc = 101
        msg = 'LOGIC ERROR'

        if criteria[0:1] == '>':
            operator = 'gt'
            criteria = criteria.replace('>', '')
        elif criteria[0:1] == '♢':
            operator = 'gt'
            criteria = criteria.replace('♢', '')
        else:
            operator = 'eq'

        if criteria:
            try:
                post_id = int(criteria)
                rc = 0
                msg = 'OK'
            except ValueError:
                try:
                    time.strptime(criteria, '%Y-%m-%d')
                    date = criteria
                    rc = 0
                    msg = 'OK'
                except ValueError:
                    rc = 102
                    msg = 'PARAMETER NOT INTEGER OR DATE'
        else:
            rc = 0
            msg = 'OK'

        return {'rc': rc, 'msg': msg, 'operator': operator, 'post_id': post_id, 'date': date}

    def parse_request(self, request):
        rc = -1  # default not a microblog command
        msg = ''
        cmd = ''
        op = ''
        post_id = 0
        date = ''

        request_parts = re.split('[ ]+', request)
        caller_callsign = request_parts[0].replace(':', '')
        if request_parts[2] in ['MB.GET', 'MB.LST']:
            cmd = request_parts[2][3:]
            logmsg('rx: ' + request)  # console trace of messages received
            if debug:
                logmsg(request_parts)
            if len(request_parts) > 3:
                # check Post ID and Date criteria
                validation_result = self.validate_criteria(request_parts[3])
                rc = validation_result['rc']
                msg = validation_result['msg']
                op = validation_result['operator']
                post_id = validation_result['post_id']
                date = validation_result['date']
            else:
                # there is no Post ID or Date criterion
                rc = 0
                op = 'gt'  # this will be greater than zero and so all posts

        return {'rc': rc, 'msg': msg, 'caller': caller_callsign,
                'cmd': cmd, 'operator': op, 'post_id': post_id, 'date': date}

    def mb_lst_by_id(self, op, post_id):
        if op == 'eq':
            file_list = glob.glob(posts_dir + '*' + str(post_id) + '*.txt')
        else:
            file_list = glob.glob(posts_dir + '*.txt')
        list_text = ''
        found_post = False
        lst_count = 0
        for filename in file_list:
            post = filename.replace(posts_dir, '')
            post = post.replace('.txt', '')
            temp = post.split(' ', 1)
            this_post_id = int(temp[0])
            if (op == 'gt' and this_post_id > post_id) or (op == 'eq' and this_post_id == post_id):
                found_post = True
                list_text += post + '\n'
                lst_count += 1
                if lst_count >= lst_limit:
                    break;
        if found_post:
            return list_text
        else:
            return 'NO POSTS FOUND' + '\n'

    def mb_lst_by_date(self, op, date):
        if op == 'eq':
            file_list = glob.glob(posts_dir + '*' + date + '*.txt')
        else:
            file_list = glob.glob(posts_dir + '*.txt')
        list_text = ''
        found_post = False
        lst_count = 0
        for filename in file_list:
            post = filename.replace(posts_dir, '')
            post = post.replace('.txt', '')
            temp = post.split(' ', 3)
            this_date = temp[2]
            if (op == 'gt' and this_date > date) or (op == 'eq' and this_date == date):
                found_post = True
                list_text += post + '\n'
                lst_count += 1
                if lst_count >= lst_limit:
                    break;

        if found_post:
            return list_text
        else:
            return 'NO POSTS FOUND' + '\n'

    def process_mb_lst(self, request):
        # validate the post id
        header = request['caller'] + ' '  # call id of requestor

        header += 'MICROBLOG POSTS\n'
        if request['post_id'] > 0:
            blog_list = self.mb_lst_by_id(request['operator'], request['post_id'])
        else:
            blog_list = self.mb_lst_by_date(request['operator'], request['date'])
        return header + blog_list + '#END#'

    def getmbpost(self, filename):
        f = open(filename)
        post = f.read()
        return post

    def process_mb_get(self, request):
        # validate the post id
        header = request['caller'] + ' MICROBLOG'  # call id of requestor
        trailer = ''

        filename = ''
        mb_message = ''
        post_id = request['post_id']
        if post_id > 0:
            header += ' #' + str(post_id)
            found_post = False
            file_list = glob.glob(posts_dir + '*' + str(post_id) + '*.txt')
            for filename in file_list:
                post = filename.replace(posts_dir, '')
                temp = post.split(' ', 1)
                this_post_id = int(temp[0])
                if this_post_id == post_id:
                    found_post = True
                    break
            if found_post:
                mb_message += self.getmbpost(filename)
                header += '\n'
                trailer = '#END#'
            else:
                header += ' '
                mb_message = 'NOT FOUND'

        else:
            header += ' '
            mb_message = 'GET BY DATE UNSUPPORTED'

        mb_message = mb_message.replace('\r\n', '\n')

        if replace_nl:
            mb_message = mb_message.replace('\n', ' ')  # temp code until NL fixed

        return header + mb_message + trailer

    def send(self, *args, **kwargs):
        params = kwargs.get('params', {})
        if '_ID' not in params:
            params['_ID'] = '{}'.format(int(time.time() * 1000))
            kwargs['params'] = params
        message = to_message(*args, **kwargs)

        logmsg('tx: ' + self.my_station + ': ' + args[1])  # console trace of messages sent

        message = message.replace('\n\n', '\n \n')  # this seems to help with the JS8Call message window format
        self.sock.send((message + '\n').encode())   # newline suffix is required

    def process(self, message):
        typ = message.get('type', '')
        value = message.get('value', '')

        if not typ:
            return

        elif typ == 'STATION.CALLSIGN':
            if debug:
                logmsg('api rsp: ' + value)
            self.my_station = value
            pass

        elif typ == 'RX.DIRECTED':  # we are only interested in messages directed to us
            if value:
                request = self.parse_request(value)
                if request['rc'] < 0:
                    return

                elif request['rc'] == 0:
                    if request['cmd'] == 'LST':
                        self.send('TX.SEND_MESSAGE', self.process_mb_lst(request))
                    elif request['cmd'] == 'GET':
                        self.send('TX.SEND_MESSAGE', self.process_mb_get(request))

                else:
                    mb_message = request['caller'] + ' MICROBLOG ' + request['msg']
                    self.send('TX.SEND_MESSAGE', mb_message)

    def run_server(self):
        # this debug code block gets your station call sign and so avoids hard coding it into the debug messages
        if debug:
            message = '{"type": "STATION.GET_CALLSIGN"}'
            self.sock.send((message + '\n').encode())  # remember to send the newline at the end :)
            logmsg('api call: ' + message)
            if self.connected:
                content = self.sock.recv(65500)
                if content:
                    try:
                        message = json.loads(content)
                    except ValueError:
                        message = {}

                    if message:
                        self.process(message)

        # this debug code block processes simulated incoming commands
        if debug:
            debug_json = '{"type":"RX.DIRECTED","value":"CALL3R: %s %s"}' % (self.my_station, debug_request)
            message = json.loads(debug_json)
            self.process(message)
            exit(0)

        try:
            while self.connected:
                content = self.sock.recv(65500)
                if not content:
                    break

                try:
                    message = json.loads(content)
                except ValueError:
                    message = {}

                if not message:
                    continue

                self.process(message)

        finally:
            self.sock.close()

    def close(self):
        self.connected = False


def main():
    s = MbServer()
    s.run_server()


if __name__ == '__main__':
    main()
