import re
import time
import glob

from .server_settings import *
from .logging import logmsg


# The ApiRequest class is populated with all the information needed by the command processor,
# including the name of the correct command processor.  The key steps in the logic are:
#  1. match the incoming api_req against the regex expressions in the api_format list
#  2. from the matching row, save the proc, op and by values
#  3. extract post_ids or post_dates, and save them to post_list or date_list
#  4. convert dates in the date_list from yymdd (api short form) to yyyy-mm-dd (ISO format)
#     - if the request has come from the cli, step 4 is not necessary since the dates are already in ISO format
#
class ApiRequest:
    # the following is a list of valid commands and
    # their corresponding command processors in the CmdProcessors class
    # the following list contains regex patterns used to check inbound API requests
    # and the corresponding cmd processor
    api_format = [
        {'exp': '^L~', 'proc': 'process_mb_lst', 'op': 'tail', 'by': 'id'},
        {'exp': '^L(\\d+,)*\\d+~', 'proc': 'process_mb_lst', 'op': 'eq', 'by': 'id'},
        {'exp': '^LE\\d+~', 'proc': 'process_mb_lst', 'op': 'eq', 'by': 'id'},
        {'exp': '^LG\\d+~', 'proc': 'process_mb_lst', 'op': 'gt', 'by': 'id'},
        {'exp': '^ME\\d{5}~|^ME\\d{2}[A-C]\\d{2}~', 'proc': 'process_mb_lst', 'op': 'eq', 'by': 'date'},
        {'exp': '^MG\\d{5}~|^MG\\d{2}[A-C]\\d{2}~', 'proc': 'process_mb_lst', 'op': 'gt', 'by': 'date'},

        {'exp': '^E~', 'proc': 'process_mb_ext', 'op': 'tail', 'by': 'id'},
        {'exp': '^E(\\d+,)*\\d+~', 'proc': 'process_mb_ext', 'op': 'eq', 'by': 'id'},
        {'exp': '^EE\\d+~', 'proc': 'process_mb_ext', 'op': 'eq', 'by': 'id'},
        {'exp': '^EG\\d+~', 'proc': 'process_mb_ext', 'op': 'gt', 'by': 'id'},
        {'exp': '^FE\\d{5}~|^FE\\d{2}[A-C]\\d{2}~', 'proc': 'process_mb_ext', 'op': 'eq', 'by': 'date'},
        {'exp': '^FG\\d{5}~|^FG\\d{2}[A-C]\\d{2}~', 'proc': 'process_mb_ext', 'op': 'gt', 'by': 'date'},

        {'exp': '^G\\d+~', 'proc': 'process_mb_get', 'op': 'eq', 'by': 'id'},
        {'exp': '^GE\\d+~', 'proc': 'process_mb_get', 'op': 'eq', 'by': 'id'},

        # although the following is invalid, we need to pass it through to the cmd proc so
        # the used gets an appropriate error message
        {'exp': '^G\\d{4}-\\d{2}-\\d{2}~', 'proc': 'process_mb_get', 'op': 'gt', 'by': 'date2'},

        # these entries are to support cli format dates
        {'exp': '^L\\d{4}-\\d{2}-\\d{2}~', 'proc': 'process_mb_lst', 'op': 'eq', 'by': 'date2'},
        {'exp': '^ME\\d{4}-\\d{2}-\\d{2}~', 'proc': 'process_mb_lst', 'op': 'eq', 'by': 'date2'},
        {'exp': '^MG\\d{4}-\\d{2}-\\d{2}~', 'proc': 'process_mb_lst', 'op': 'gt', 'by': 'date2'},
        {'exp': '^E\\d{4}-\\d{2}-\\d{2}~', 'proc': 'process_mb_ext', 'op': 'eq', 'by': 'date2'},
        {'exp': '^FE\\d{4}-\\d{2}-\\d{2}~', 'proc': 'process_mb_ext', 'op': 'eq', 'by': 'date2'},
        {'exp': '^FG\\d{4}-\\d{2}-\\d{2}~', 'proc': 'process_mb_ext', 'op': 'gt', 'by': 'date2'},

        {'exp': '^WX~', 'proc': 'process_wx_get', 'op': 'eq', 'by': 'id'},
    ]

    caller = ''
    original_req_string = ''

    is_valid = False
    exp = ''
    proc = ''
    cmd = ''
    op = ''
    by = ''
    post_list = []
    date_list = []
    rc = -1  # default not a microblog command
    msg = ''

    def __init__(self, caller: str, original_req_string: str):
        # The command processor will need the caller's callsign to prefix any response and thereby direct
        # the response to the correct station.
        self.caller = caller
        # If the request we are processing has come from the CLI, the original request string will not
        # be the same as the api_req string that we process.  We need to reflect the original req string
        # in any response, and so we must save that in the object.
        self.original_req_string = original_req_string

    def parse(self, api_req: str) -> int:  # returns a return code of 0 if good
        self.post_list.clear()
        self.date_list.clear()

        for entry in self.api_format:
            # try to match the request
            result = re.search(entry['exp'], api_req)
            if result is None:
                continue
            else:
                self.is_valid = True
                self.rc = 0
                self.msg = "OK"
                self.cmd = (re.findall(r"^([A-Z]+)", api_req))[0]
                self.exp = entry['exp']
                self.proc = entry['proc']
                self.op = entry['op']
                self.by = entry['by']
                if self.by == 'id':
                    if self.op == 'tail':
                        file_list = sorted(glob.glob(posts_dir + '*.txt'))
                        filename = file_list[len(file_list) - 1]  # get the last filename
                        post = filename.replace(posts_dir, '')
                        post = post.replace('.txt', '')
                        temp = post.split(' ', 4)
                        latest_post_id = int(temp[0])
                        for i in range(latest_post_id - lst_limit + 1, latest_post_id + 1):
                            self.post_list.append(i)
                        self.op = 'eq'  # override the tail operation now we have a post_id list
                    else:
                        self.post_list = re.findall(r"(\d+),*", api_req)
                        # convert from list of strings to  list of integers
                        for i, post_id in enumerate(self.post_list):
                            self.post_list[i] = int(post_id)
                elif self.by == 'date' or self.by == 'date2':
                    if self.by == 'date':
                        self.date_list = re.findall(r"(\d{2})([\d,A-C])(\d{2})", api_req)
                    elif self.by == 'date2':
                        self.date_list = re.findall(r"(\d{4}-\d{2}-\d{2})", api_req)
                    for i, date in enumerate(self.date_list):
                        if self.by == 'date':
                            date = '20%s-0%s-%s' % (date[0], date[1], date[2])
                            date = date.replace('0A', '10')
                            date = date.replace('0B', '11')
                            date = date.replace('0C', '12')
                        elif self.by == 'date2':
                            # flip by = date2 to date
                            self.by = 'date'

                        try:
                            time.strptime(date, '%Y-%m-%d')
                            self.date_list[i] = date
                            self.rc = 0
                            self.msg = 'OK'
                        except ValueError:
                            self.is_valid = False
                    pass
                break

        if self.by == 'id' and not self.is_valid:
            self.rc = 102
            self.msg = 'PARAMETER NOT VALID INTEGER'
        elif self.by == 'date' and not self.is_valid:
            self.rc = 103
            self.msg = 'PARAMETER NOT VALID DATE'

        logmsg(1, 'api: info: ' + api_req)  # console trace of messages received

        return self.rc
