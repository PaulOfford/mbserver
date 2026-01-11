import re

from logging import logmsg
from server_settings import msg_terminator

class CliCmd:
    # the following is a list of valid commands and
    # their corresponding command processors in the CmdProcessors class
    # the following list contains regex patterns used to check inbound API requests
    # and the corresponding cmd processor
    cli_informat = [
        {'exp': '^M.L$', 'xlat': 'L~', 'by': 'id'},
        {'exp': '^M.LST$', 'xlat': 'L~', 'by': 'id'},
        {'exp': '^M.L +(\\d+)$', 'xlat': 'L{param}~', 'by': 'id'},
        {'exp': '^M.LST +(\\d+)$', 'xlat': 'L{param}~', 'by': 'id'},
        {'exp': '^M.L +> *(\\d+)$', 'xlat': 'LG{param}~', 'by': 'id'},
        {'exp': '^M.LST +> *(\\d+)$', 'xlat': 'LG{param}~', 'by': 'id'},
        {'exp': '^M.E$', 'xlat': 'E~', 'by': 'id'},
        {'exp': '^M.EST$', 'xlat': 'E~', 'by': 'id'},
        {'exp': '^M.E +(\\d+)$', 'xlat': 'E{param}~', 'by': 'id'},
        {'exp': '^M.EXT +(\\d+)$', 'xlat': 'E{param}~', 'by': 'id'},
        {'exp': '^M.E +> *(\\d+)$', 'xlat': 'EG{param}~', 'by': 'id'},
        {'exp': '^M.EXT +> *(\\d+)$', 'xlat': 'EG{param}~', 'by': 'id'},

        {'exp': '^M.L +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'L{param}~', 'by': 'date'},
        {'exp': '^M.LST +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'L{param}~', 'by': 'date'},
        {'exp': '^M.L +> *(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'MG{param}~', 'by': 'date'},
        {'exp': '^M.LST +> *(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'MG{param}~', 'by': 'date'},

        {'exp': '^M.E +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'E{param}~', 'by': 'date'},
        {'exp': '^M.EXT +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'E{param}~', 'by': 'date'},
        {'exp': '^M.E +> *(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'FG{param}~', 'by': 'date'},
        {'exp': '^M.EXT +> *(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'FG{param}~', 'by': 'date'},

        {'exp': '^M.G +(\\d+)$', 'xlat': 'G{param}~', 'by': 'id'},
        {'exp': '^M.GET +(\\d+)$', 'xlat': 'G{param}~', 'by': 'id'},

        # although the following is invalid, we need to pass it through to the API parser so
        # the used gets an appropriate error message
        {'exp': '^M.G +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'G{param}~', 'by': 'id'},
        {'exp': '^M.GET +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'G{param}~', 'by': 'id'},

        {'exp': '^M.WX$', 'xlat': 'WX~', 'by': 'id'},
    ]

    is_cli = False
    api_cmd = ''

    def __init__(self, command: str):

        api_format_cmd = ''  # we will return with this value if this isn't a cli command

        command = command.replace(msg_terminator, '')
        command = command.strip()

        for entry in self.cli_informat:
            # try to match the request
            result = re.findall(entry['exp'], command)
            if result == []:
                continue
            else:
                self.api_cmd = str(entry['xlat']).format(param=str(result[0]))
                self.is_cli = True
                logmsg(1, f"cli: info: translated {command} to {self.api_cmd}")
                break

        return
