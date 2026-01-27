import re
import logging
from pathlib import Path

from .config import SETTINGS
from .server_cli import cli_translate

lst_limit = SETTINGS.lst_limit
posts_dir = SETTINGS.posts_dir

logger = logging.getLogger(__name__)


def api_get_ids_for_date(date: str) -> list:
    # The request looks like this {'cmd': api_request, 'verb': 'LIST', 'by': 'DATE', 'date': date}
    id_list = []

    file_list = sorted(Path(posts_dir).glob(f"*{date}*.txt"), reverse=True)
    file_names = [f.name for f in file_list]

    for fn in file_names:
        post_id = re.findall(r'^(\d+) - \d{4}-\d{2}-\d{2} - [\S\s]*\.txt', fn)[0]
        if post_id:
            id_list.append(int(post_id))

    return id_list


def api_get_ids_for_recent() -> list:
    # The request looks like this {'cmd': api_request, 'verb': 'LIST', 'by': 'ID', 'id_list': []]}
    id_list = []

    file_list = sorted(Path(posts_dir).glob(f"*.txt"), reverse=True)
    file_names = [f.name for f in file_list]

    for i, fn in enumerate(file_names):
        if i >= lst_limit:
            break

        post_id = re.findall(r'^(\d+) - \d{4}-\d{2}-\d{2} - [\S\s]*\.txt', fn)[0]
        if post_id:
            id_list.append(int(post_id))

    return id_list


def api_parse_list(api_request: str, match: dict) -> dict:
    # {'cmd': 'E~', 'verb': 'LIST', 'by': 'ID', 'id_list': []}  -> lists the most recent
    # {'cmd': 'E6~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6]}  -> list #6, #10 and #12
    # {'cmd': 'E6,10,12~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6, 10, 12]}  -> list #6, #10 and #12
    # {'cmd': 'E2026-01-25~', 'verb': 'LIST', 'by': 'DATE', 'date': '2026-01-25'}  -> list 2026-01-25

    post_id_list = []  # We'll return this list, which will be empty if we have no matching lists

    if match['by'] == 'ID':
        if re.fullmatch(r'E\d+(?:,\d+)*~', api_request):
            post_id_list = list(map(int, re.findall(r'\d+', api_request)))

        # If we didn't get a match, the api_request must be E~

        return {
            'cmd': api_request,
            'verb': 'LIST',
            'by': 'ID',
            'id_list': post_id_list
        }

    elif match['by'] == 'DATE':
        date = re.findall(r'^E(\d{4}-\d{2}-\d{2})~', match['date'])[0]

        return {
            'cmd': api_request,
            'verb': 'LIST',
            'by': 'DATE',
            'date': date
        }

    return {}


def api_parse_get(api_request: str) -> dict:
    # {'cmd': 'G12~', 'verb': 'GET', 'post_id': 6}  -> get #12
    post_id_list = list(map(int, re.findall(r'\d+', api_request)))

    return {
        'cmd': api_request,
        'verb': 'GET',
        'by': 'ID',
        'id_list': post_id_list
    }


def api_parse_req(api_req: str) -> dict:
    # Here we normalise the input to produce a dictionary that we return to the caller.
    # The dictionary looks like one of these:
    # {'cmd': 'E~', 'verb': 'LIST', 'by': 'ID', 'id_list': []}  -> lists the most recent
    # {'cmd': 'E6~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6]}  -> list #6, #10 and #12
    # {'cmd': 'E6,10,12~', 'verb': 'LIST', 'by': 'ID', 'id_list': [6, 10, 12]}  -> list #6, #10 and #12
    # {'cmd': 'E2026-01-25~', 'verb': 'LIST', 'by': 'DATE', 'date': '2026-01-25'}  -> list 2026-01-25
    # {'cmd': 'G12~', 'verb': 'GET', 'post_id': 6}  -> get #12

    # the following is a list of valid commands and
    # their corresponding command processors in the CmdProcessors class
    # the following list contains regex patterns used to check inbound API requests
    # and the corresponding cmd processor
    api_format = [
        {'exp': r'^E~', 'verb': 'LIST', 'by': 'ID'},
        {'exp': r'^E(\d+,)*\d+~', 'verb': 'LIST', 'by': 'ID'},
        {'exp': r'^E\d{4}-\d{2}-\d{2}~', 'verb': 'LIST', 'by': 'ID'},

        {'exp': r'^G\d+~', 'verb': 'GET', 'by': 'ID'},
    ]

    req_dict = {}
    
    for entry in api_format:
        # try to match the request
        m = re.search(entry['exp'], api_req)
        if m is None:
            continue

        if entry['verb'] == 'LIST':
            req_dict = api_parse_list(api_req, entry)
        elif entry['verb'] == 'GET':
            req_dict = api_parse_get(api_req)

    return req_dict

def api_get_req_components(req: str) -> dict:
    components = re.findall(r'^([A-Z0-9]+): *([A-Z0-9]+) *([\S ]*)$', req)[0]
    return {
        'source': components[0],
        'destination': components[1],
        'cmd': components[2],
    }

def api_get_req_structure(req: str) -> dict:
    # req is in the format _source_: _destination_ _mb_cmd_

    logger.info('REQ <- : ' + req)  # console trace of messages received

    components = api_get_req_components(req)
    # client = components['source']  # No using this line at the moment
    cmd = components['cmd']

    if cmd[:2] == 'M.':
        # This is a CLI command that we need to translate to an api command
        cmd = cli_translate(cmd)

    req_dict = api_parse_req(cmd)

    if req_dict == {}:
        return req_dict
    
    if req_dict['by'] == 'DATE':
        id_list = api_get_ids_for_date(req_dict['date'])
        req_dict['id_list'] = id_list

    if req_dict['by'] == 'ID' and len(req_dict['id_list']) == 0:
        id_list = api_get_ids_for_recent()
        req_dict['id_list'] = id_list
        
    return req_dict
