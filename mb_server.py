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

import json
import select
import os

from socket import socket, AF_INET, SOCK_STREAM
from server_api import *
from server_cli import *
from logging import *
from server_settings import lst_limit
from _version import __version__


def is_valid_post_file(file_spec: str):
    result = [()]  # default value

    post_file_patterns = [
        {'exp': "^([0-9]+) - (\\d{4}-\\d{2}-\\d{2}) - ([\\S\\s]+) *.txt", 'type': 'post_file'},
    ]

    pos = len(posts_dir)

    file_name = file_spec[pos:]

    for entry in post_file_patterns:
        # try to match the request
        result = re.findall(entry['exp'], file_name)
        if len(result) > 0:
            break

    return result


class Js8CallApi:

    connected = False
    my_station = ''
    my_blog = ''
    my_grid = ''

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

    def set_my_grid(self, grid):
        self.my_grid = grid
        return

    def set_my_station(self, station_id: str):
        self.my_station = station_id

    def set_my_blog(self, blog: str):
        self.my_blog = blog

    def listen(self):
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
            message = {}
            self.connected = False
        else:
            try:
                message = json.loads(content)
            except ValueError:
                message = {}

        return message

    def listen_mock(self):
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
            logmsg(current_log_level, 'omsg: ' + self.my_station + ': ' + log_line)  # console trace of messages sent

        message = message.replace('\n\n', '\n \n')  # this seems to help with the JS8Call message window format
        logmsg(2, 'send: ' + message)

        if args[1] and debug:
            logmsg(3, 'info: MB message not sent as we are in debug mode')
            # this avoids hamlib errors in JS8Call if the radio isn't connected
        else:
            self.sock.send((message + '\n').encode())   # newline suffix is required

    def close(self):
        self.sock.close()


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

        file_list = sorted(glob.glob(posts_dir + '*.txt'))
        list_text = ''
        found_post = False
        lst_count = 0
        for post_id in request.post_list:
            for filename in file_list:
                if not is_valid_post_file(filename):
                    continue

                post = self.get_post_meta(filename, include_date)
                if (request.op == 'gt' and post['post_id'] > post_id)\
                        or (request.op == 'eq' and post['post_id'] == post_id):
                    found_post = True
                    list_text += post['list_text']
                    lst_count += 1
                    if request.op == 'eq' or lst_count >= lst_limit:
                        break
        if found_post:
            return list_text
        else:
            return 'NO POSTS FOUND' + '\n'

    def mb_lst_by_date(self, request, include_date):

        file_list = sorted(glob.glob(posts_dir + '*.txt'))
        list_text = ''
        found_post = False
        lst_count = 0

        for date in request.date_list:
            for filename in file_list:
                if not is_valid_post_file(filename):
                    continue

                post = self.get_post_meta(filename, include_date)
                if (request.op == 'gt' and post['date'] > date)\
                        or (request.op == 'eq' and post['date'] == date):
                    found_post = True
                    list_text += post['list_text']
                    lst_count += 1
                    if lst_count >= lst_limit:
                        break

        if found_post:
            return list_text
        else:
            return 'NO POSTS FOUND' + '\n'

    def process_mb_ext(self, request: ApiRequest):
        success = '+'

        if request.by == 'id':
            blog_list = self.mb_lst_by_id(request, include_date=True)
        elif request.by == 'date':
            blog_list = self.mb_lst_by_date(request, include_date=True)
        else:
            blog_list = 'Unexpected error in process_mb_ext - check the api_informat entries'

        header = '{caller} {success}{req_string}\n'.format(
            caller=request.caller,
            success=success,
            req_string=request.original_req_string
        )

        return header + blog_list

    def process_mb_lst(self, request: ApiRequest):
        success = '+'

        if request.by == 'id':
            blog_list = self.mb_lst_by_id(request, include_date=False)
        elif request.by == 'date':
            blog_list = self.mb_lst_by_date(request, include_date=False)
        else:
            blog_list = 'Unexpected error in process_mb_lst - check the api_informat entries'

        header = '{caller} {success}{req_string}\n'.format(
            caller=request.caller,
            success=success,
            req_string=request.original_req_string
        )

        return header + blog_list

    @staticmethod
    def getmbpost(filename):
        f = open(filename)
        post = f.read()
        f.close()
        return post

    def process_mb_get(self, request: ApiRequest) -> str:
        filename = ''
        mb_message = ''
        success = '-'  # assume failure

        if len(request.post_list) > 0:
            found_post = False
            file_list = sorted(glob.glob(posts_dir + '*' + str(request.post_list[0]) + '*.txt'))
            for filename in file_list:
                post = filename.replace(posts_dir, '')
                temp = post.split(' ', 1)
                this_post_id = int(temp[0])
                if this_post_id == request.post_list[0]:
                    found_post = True
                    break
            if found_post:
                mb_message += '\n' + self.getmbpost(filename)
                success = '+'  # change success to good
            else:
                mb_message = ' NOT FOUND'

        else:
            mb_message = ' BY DATE UNSUPPORTED'

        header = '{caller} {success}{req_string}'.format(
            caller=request.caller,
            success=success,
            req_string=request.original_req_string,
        )

        mb_message = mb_message.replace('\r\n', '\n')

        if replace_nl:
            mb_message = mb_message.replace('\n', ' ')  # temp code until NL fixed

        return header + mb_message

    def process_wx_get(self, req: ApiRequest) -> str:
        req.post_list.append(0)
        return self.process_mb_get(req)

class MbAnnouncement:

    latest_post_id = 0
    latest_post_date = '2000-01-01'
    next_announcement = 0

    def latest_post_meta(self):
        dir_informat = r"^.*[\\\\|/](\d+) - (\d\d\d\d-\d\d-\d\d) - (.+\.txt)"

        file_list = sorted(glob.glob(posts_dir + '*.txt'), reverse=True)
        for entry in file_list:
            post_details = (re.findall(dir_informat, entry))
            if len(post_details) > 0:
                self.latest_post_id = int(post_details[0][0])
                self.latest_post_date = post_details[0][1]
                return

        logmsg(1, 'There are no posts in the posts_dir - shutting down the Microblog Server')
        exit(0)  # we haven't found any posts -> we need to exit

    def send_mb_announcement(self, js8call_api: Js8CallApi):
        # get the current epoch
        epoch = time.time()
        if epoch > self.next_announcement:
            self.latest_post_meta()  # update with the latest post info
            message = f"@MB {js8call_api.my_blog} {self.latest_post_id} {self.latest_post_date}"
            js8call_api.send('TX.SEND_MESSAGE', message)
            # update the next announcement epoch
            self.next_announcement = epoch + (mb_announcement_timer * 60)


class MbServer:

    request = None

    def process(self, mb_req) -> [str, None]:
        mb_rsp = ''

        value = mb_req.get('value', '')
        # tidy up the message string
        value = value.replace(' ' + msg_terminator, '')  # remove the message terminator
        value = value.replace(msg_terminator, '')  # remove the message terminator
        value = value.strip()
        value = value.replace('  ', ' ')  # remove double spaces

        if value:
            # split into origin, destination and command
            value_parts = re.findall(r"\s*(\S+):\s+(\S+)\s*([\S\s]+)", value)
            if len(value_parts) == 0:
                return None  # not for us
            if len(value_parts[0]) < 3:
                return None  # not for us

            cli = CliCmd(value_parts[0][2])
            if cli.is_cli:
                api_req_string = cli.api_cmd
            else:
                api_req_string = value_parts[0][2]

            self.request = ApiRequest(value_parts[0][0], value_parts[0][2])

            if self.request.parse(api_req_string) < 0:
                pass  # the received string isn't for us - do nothing

            elif self.request.rc == 0:
                # looks good - go for it
                procs = CmdProcessors()
                mb_rsp = getattr(CmdProcessors, self.request.proc)(procs, self.request)

            else:
                # must be an error
                mb_rsp = '{caller} {success}{cmd} {error_msg}'.format(
                    caller=self.request.caller,
                    success='-',
                    cmd=self.request.cmd,
                    error_msg=self.request.msg
                )

        if len(mb_rsp) > 0:
            return mb_rsp.upper()
        else:
            return None

    def run_server(self, this_blog: [None, str]):
        # check the posts directory looks OK
        if not os.path.exists(posts_dir):
            logmsg(1, "err: Can't find the posts directory")
            logmsg(1, 'info: Check that the posts_dir value in server_settings.py is correct')
            exit(1)

        js8call_api = Js8CallApi()
        js8call_api.connect()

        js8call_api.send('STATION.GET_GRID', '')
        logmsg(2, 'call: STATION.GET_GRID')
        if js8call_api.connected:
            message = js8call_api.listen()
            if message:
                typ = message.get('type', '')
                value = message.get('value', '')
                if typ == 'STATION.GRID':
                    logmsg(3, 'resp: ' + value)
                    js8call_api.set_my_grid(value)
            else:
                logmsg(1, 'Unable to get My Grid.')
                logmsg(1, 'Check in File -> Settings -> General -> '
                       'Station -> Station Details -> My Maidenhead Grid Locator')

            js8call_api.send('STATION.GET_CALLSIGN', '')
            logmsg(2, 'call: STATION.GET_CALLSIGN')
            if js8call_api.connected:
                message = js8call_api.listen()
                if message:
                    typ = message.get('type', '')
                    value = message.get('value', '')
                    if typ == 'STATION.CALLSIGN':
                        logmsg(3, 'resp: ' + value)
                        js8call_api.set_my_station(value)
                        if this_blog:
                            js8call_api.set_my_blog(this_blog)
                        else:
                            js8call_api.set_my_blog(value)  # this is a temp measure until we fully implement blog names
                else:
                    logmsg(1, 'Unable to get My Callsign.')
                    logmsg(1, 'Check in File -> Settings -> General -> Station -> Station Details -> My Callsign')

        mb_announcement = MbAnnouncement()

        # this debug code block processes simulated incoming commands

        try:
            while js8call_api.connected:
                if announce:
                    mb_announcement.send_mb_announcement(js8call_api)

                message = js8call_api.listen()
                # message = js8call_api.listen_mock()

                if not message:
                    continue

                typ = message.get('type', '')
                value = message.get('value', '')

                if not typ:
                    continue

                elif typ == 'STATION.GRID':
                    logmsg(3, 'resp: ' + value)
                    js8call_api.set_my_grid(value)

                elif typ == 'STATION.CALLSIGN':
                    logmsg(3, 'resp: ' + value)
                    js8call_api.set_my_station(value)
                    js8call_api.set_my_blog(value)  # this is a temp measure until we fully implement blog names

                elif typ == 'RX.DIRECTED':  # we are only interested in messages directed to us, including @MB
                    # if we have received an @MB Q we need to handle differently to commands
                    if re.search(r"^\S+: @MB\s+Q", value):
                        mb_announcement.next_announcement = 0  # we might want to change this later to avoid clashes
                    else:
                        rsp_message = self.process(message)
                        if rsp_message:
                            logmsg(1, 'resp: ' + rsp_message)
                            js8call_api.send('TX.SEND_MESSAGE', rsp_message)

        finally:
            js8call_api.close()


def main():
    if len(blog_name) == 0:
        s = MbServer()
        s.run_server(blog_name)


if __name__ == '__main__':
    logmsg(1, 'info: Microblog Server ' + __version__)
    main()
