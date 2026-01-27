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
import sys
import argparse

from .js8call_driver import *
from .server_api import *
from .server_cli import *
import logging

from .logging_setup import configure_logging
from .config import SETTINGS
from .upstream import UpstreamStore

logger = logging.getLogger(__name__)

# Config (loaded from config.ini at the repo root, next to mbserver.bat)
server = SETTINGS.server
posts_dir = SETTINGS.posts_dir
msg_terminator = SETTINGS.msg_terminator
replace_nl = SETTINGS.replace_nl
posts_url_root = SETTINGS.posts_url_root
announce = SETTINGS.announce
mb_announcement_timer = SETTINGS.mb_announcement_timer
lst_limit = SETTINGS.lst_limit

# Logging config
LOG_LEVEL = SETTINGS.log_level
LOG_TO_FILE = SETTINGS.log_to_file
LOG_FILE = SETTINGS.log_file
LOG_MAX_BYTES = SETTINGS.log_max_bytes
LOG_BACKUP_COUNT = SETTINGS.log_backup_count


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
    def list_posts(request: dict) -> str:
        list_of_posts = []

        for post_id in request['id_list']:
            post_id_str = f"{post_id:04d}"
            file_list = sorted(Path(posts_dir).glob(f"{post_id_str}*.txt"), reverse=True)
            file_name = [f.name for f in file_list]
            if len(file_name) > 0:
                list_entry = re.findall(r"^([\S\s]+).txt", file_name[0])[0]
                list_of_posts.append(list_entry)

        if len(list_of_posts) == 0:
            return 'NO POSTS FOUND'
        else:
            return '\n'.join(list_of_posts)


    def verb_list(self, req: dict):
        # The req structure will look like one of these
        # {'cmd': 'E6~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6]}  -> list #6, #10 and #12
        # {'cmd': 'E6,10,12~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6, 10, 12]}  -> list #6, #10 and #12

        success = '+'
        listing = self.list_posts(req)
        if listing == 'NO POSTS FOUND':
            success = '-'
        return f"{success}{req['cmd']}\n{listing}"

    @staticmethod
    def get_post_content(filename):
        f = open(filename)
        post = f.read()
        f.close()
        return post

    def verb_get(self, req: dict) -> str:
        # The req structure will look like this:
        # {'cmd': 'G12~', 'verb': 'GET', 'id_list': [12]}  -> get #12

        success = '-'  # Assume the worst.
        post_content = 'POST NOT FOUND'

        file_search = f"{req['id_list'][0]:04d}*.txt"

        file_path_name = sorted(Path(posts_dir).glob(file_search), reverse=True)

        if len(file_path_name) > 0:
            post_content = self.get_post_content(file_path_name[0])

        if post_content:
            # We can give a positive response.
            success = '+'

            # Tidy the post content.
            post_content = post_content.replace('\r\n', '\n')
            if replace_nl:
                post_content = post_content.replace('\n', ' ')  # temp code until NL fixed

        return f"{success}{req['cmd']}\n{post_content}"


class MbAnnouncement:

    this_blog = ""
    latest_post_id = 0
    latest_post_date = '2000-01-01'
    next_announcement = 0

    def __init__(self, blog: str):
        self.this_blog = blog

    @staticmethod
    def latest_post_meta() -> dict:
        file_list = sorted(Path(posts_dir).glob(f"*.txt"), reverse=True)
        latest_meta = [f.name for f in file_list][0]

        post_id, post_date = re.findall(r'^(\d+) - (\d{4}-\d{2}-\d{2}) - [\S\s]*\.txt', latest_meta)[0]

        if post_id:
            return {'post_id': int(post_id), 'post_date': post_date}
        else:
            return {'post_id': 0, 'post_date': "1970-01-01"}


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
            meta = self.latest_post_meta()  # update with the latest post info

            # compress the date from yyyy-mm-dd into yymmdd
            compressed_latest_post_date = meta['post_date'].replace('-', '')[2:]

            message = f"@MB {meta['post_id']} {compressed_latest_post_date}"
            js8call_api.send('TX.SEND_MESSAGE', message)
            logger.info("SIG -> : " + message)
            # update the next announcement epoch
            self.next_announcement = epoch + (mb_announcement_timer * 60)


class MbServer:

    this_blog = ''
    request = None

    @staticmethod
    def tidy(messy: str) -> str:
        # tidy up the message string
        value = messy.replace(' ' + msg_terminator, '')  # remove the message terminator
        value = value.replace(msg_terminator, '')  # remove the message terminator
        value = value.strip()
        clean = value.replace('  ', ' ')  # remove double spaces
        return clean

    def process(self, js8call_msg: dict):
        mb_rsp = ''

        mb_req = self.tidy(js8call_msg.get('value', ''))

        # mb_req is in the format _source_: _destination_ _mb_cmd_
        req = api_get_req_structure(mb_req)  # Go get a structured request

        if req == {}:
            logger.info('Not an MB request <- : ' + js8call_msg.get('value', ''))
            return None

        # The req structure will look like one of these
        # {'cmd': 'E6~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6]}  -> list #6, #10 and #12
        # {'cmd': 'E6,10,12~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6, 10, 12]}  -> list #6, #10 and #12
        # {'cmd': 'G12~', 'verb': 'GET', 'id_list': [12]}  -> get #12

        p = CmdProcessors()

        if req['verb'] == 'LIST':
            mb_rsp = p.verb_list(req)
        elif req['verb'] == 'GET':
            mb_rsp = p.verb_get(req)


        if len(mb_rsp) > 0:
            return mb_rsp.upper()
        else:
            return None

    def run_server(self):
        # check the posts directory looks OK
        if not os.path.exists(posts_dir):
            logger.info("Can't find the posts directory")
            logger.info("Check that the posts_dir value in config.ini is correct")
            exit(1)

        js8call_api = Js8CallApi()
        js8call_api.connect()

        js8call_api.send('STATION.GET_CALLSIGN', '')
        logger.info('TX -> : STATION.GET_CALLSIGN')
        if js8call_api.connected:
            messages = js8call_api.listen()
            if len(messages) > 0:
                for message in messages:
                    typ = message.get('type', '')
                    logger.info('RX <- : ' + typ)
                    value = message.get('value', '')
                    if typ == 'STATION.CALLSIGN':
                        js8call_api.set_my_station(value)
                        self.this_blog = value  # blog name is the station callsign
                        logger.info(f"This blog is: {self.this_blog}")
            else:
                logger.error('Unable to get my callsign.')

        mb_announcement = MbAnnouncement(self.this_blog)

        # this debug code block processes simulated incoming commands

        try:
            while js8call_api.connected:
                if mb_announcement.is_announcement_needed():
                    # refresh the blog with new posts
                    if posts_url_root:
                        blog_store = UpstreamStore()
                        meta = mb_announcement.latest_post_meta()
                        next_post_needed = meta['post_id'] + 1
                        logger.info("Checking central store for new posts")
                        blog_store.get_new_content(starting_at=next_post_needed)

                    mb_announcement.send_mb_announcement(js8call_api)

                messages = js8call_api.listen()
                # messages = js8call_api.listen_mock()

                if len(messages) == 0:
                    continue

                for message in messages:
                    typ = message.get('type', '')
                    logger.debug('RX <- : ' + typ)
                    value = message.get('value', '')

                    if not typ:
                        continue

                    elif typ == 'RX.DIRECTED':  # we are only interested in messages directed to us, including @MB
                        # if we have received an @MB Q we need to handle differently to commands
                        if re.search(r"^\S+: @MB\s+Q", value):
                            logger.info('RX <- : ' + value)
                            mb_announcement.next_announcement = 0  # we might want to change this later to avoid clashes

                        elif message['params']['TO'] == self.this_blog:
                            rsp = self.process(message)

                            if not rsp:
                                continue

                            rsp_message = f"{message['params']['FROM']} {rsp}"

                            log_msg = re.findall(r"^([\S\s]+~)", rsp_message)
                            if len(log_msg) > 0:
                                logger.info('RSP -> : ' + log_msg[0])
                            else:
                                logger.info('RSP -> : ' + rsp_message)

                            # Time to send the response.
                            js8call_api.send('TX.SEND_MESSAGE', rsp_message)

                        else:
                            logger.info('REQ not for me <- : ' + value)

        finally:
            js8call_api.close()


def main():
    """Application entry point.

    Supports optional CLI flags to override logging configuration.
    """

    parser = argparse.ArgumentParser(prog="mbserver", add_help=True)
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default=None,
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL or numeric).",
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        default=None,
        help="Path to rotating log file. Overrides config.ini [logging] log_file.",
    )
    parser.add_argument(
        "--no-log-file",
        dest="no_log_file",
        action="store_true",
        help="Disable file logging even if enabled in config.ini.",
    )
    parser.add_argument(
        "--max-log-bytes",
        dest="max_log_bytes",
        type=int,
        default=None,
        help="Rotate log file after this many bytes. Overrides config.ini [logging] log_max_bytes.",
    )
    parser.add_argument(
        "--log-backups",
        dest="log_backups",
        type=int,
        default=None,
        help="Number of rotated log files to keep. Overrides config.ini [logging] log_backup_count.",
    )

    args = parser.parse_args(sys.argv[1:])

    def _parse_level(v: str) -> int:
        if v is None:
            return int(LOG_LEVEL)
        s = str(v).strip()
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
        name = s.upper()
        if not hasattr(logging, name):
            raise SystemExit(f"Invalid --log-level: {v}")
        lvl = getattr(logging, name)
        if not isinstance(lvl, int):
            raise SystemExit(f"Invalid --log-level: {v}")
        return int(lvl)

    level = _parse_level(args.log_level)

    # Decide file logging
    if args.no_log_file:
        log_file = None
    elif args.log_file is not None:
        log_file = args.log_file
    else:
        log_file = LOG_FILE if LOG_TO_FILE else None

    max_bytes = int(args.max_log_bytes) if args.max_log_bytes is not None else int(LOG_MAX_BYTES)
    backup_count = int(args.log_backups) if args.log_backups is not None else int(LOG_BACKUP_COUNT)

    # Configure application logging (console + optional rotating file, UTC timestamps)
    configure_logging(
        level=level,
        terminator=msg_terminator,
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
        console=True,
    )

    srv = MbServer()
    srv.run_server()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
