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

import os

from js8call_driver import *
from server_api import *
from server_cli import *
from logging import *
from server_settings import lst_limit
from upstream import UpstreamStore
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

    this_blog = ""
    latest_post_id = 0
    latest_post_date = '2000-01-01'
    next_announcement = 0

    def __init__(self, blog: str):
        self.this_blog = blog

    def latest_post_meta(self) -> tuple:
        dir_informat = r"^.*[\\\\|/](\d+) - (\d\d\d\d-\d\d-\d\d) - (.+\.txt)"

        file_list = sorted(glob.glob(posts_dir + '*.txt'), reverse=True)
        for entry in file_list:
            post_details = (re.findall(dir_informat, entry))
            if len(post_details) > 0:
                self.latest_post_id = int(post_details[0][0])
                self.latest_post_date = post_details[0][1]
                return (self.latest_post_id, self.latest_post_date)

        return (0, "1970-01-01")

    def is_announcement_needed(self):
        epoch = time.time()
        if epoch > self.next_announcement and announce:
            return True
        else:
            return False

    def send_mb_announcement(self, js8call_api: Js8CallApi):
        # get the current epoch
        epoch = time.time()
        if epoch > self.next_announcement:
            self.latest_post_meta()  # update with the latest post info

            # compress the date from yyyy-mm-dd into yymmdd
            compressed_latest_post_date = self.latest_post_date[2:4] + self.latest_post_date[5:7] + self.latest_post_date[8:10]

            message = f"@MB {self.latest_post_id} {compressed_latest_post_date}"
            js8call_api.send('TX.SEND_MESSAGE', message)
            # update the next announcement epoch
            self.next_announcement = epoch + (mb_announcement_timer * 60)


class MbServer:

    this_blog = ''
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

                    # we need to set the blog name
                    if this_blog:
                        self.this_blog = this_blog[0]
                    else:
                        self.this_blog = value  # default blog name is the station callsign
            else:
                logmsg(1, 'Unable to get My Callsign.')
                logmsg(1, 'Check in File -> Settings -> General -> Station -> Station Details -> My Callsign')

        mb_announcement = MbAnnouncement(self.this_blog)

        # this debug code block processes simulated incoming commands

        try:
            while js8call_api.connected:
                if mb_announcement.is_announcement_needed():
                    # refresh the blog with new posts
                    if posts_url_root:
                        blog_store = UpstreamStore(posts_url_root, posts_dir, self.this_blog)
                        meta = mb_announcement.latest_post_meta()
                        next_post_needed = meta[0] + 1
                        logmsg(1, "info: Checking central store for new posts")
                        blog_store.get_new_content(starting_at=next_post_needed)

                    mb_announcement.send_mb_announcement(js8call_api)

                message = js8call_api.listen()
                # message = js8call_api.listen_mock()

                if not message:
                    continue

                typ = message.get('type', '')
                value = message.get('value', '')

                if not typ:
                    continue

                elif typ == 'STATION.CALLSIGN':
                    logmsg(3, 'resp: ' + value)
                    js8call_api.set_my_station(value)

                    # we need to set the blog name
                    if this_blog:
                        self.this_blog = this_blog
                    else:
                        self.this_blog = value  # default blog name is the station callsign

                elif typ == 'RX.DIRECTED':  # we are only interested in messages directed to us, including @MB
                    # if we have received an @MB Q we need to handle differently to commands
                    if re.search(r"^\S+: @MB\s+Q", value):
                        mb_announcement.next_announcement = 0  # we might want to change this later to avoid clashes
                    else:
                        # ToDo: implement RAD
                        # instantiate a RadMessage object here
                        # call message = decode_rad(message) here - the method would have no affect if not rad
                        # the RadMessage object holds rad_requested status, cell_size and any specified cell list
                        # the default cell list would be a single "entire message" specification
                        # decode_rad() should strip the cell list from the incoming request
                        rsp_message = self.process(message)
                        if rsp_message:
                            logmsg(1, 'resp: ' + rsp_message)
                            # call rsp_message = encode_rad(rsp_message) here - no affect if not rad
                            # encode_rad should use the cell list held over from the request
                            js8call_api.send('TX.SEND_MESSAGE', rsp_message)

        finally:
            js8call_api.close()


def main():
    s = MbServer()
    s.run_server(None)


if __name__ == '__main__':
    logmsg(1, 'info: Microblog Server ' + __version__)
    main()
