import re

from logging import getLogger
from .config import SETTINGS

msg_terminator = SETTINGS.msg_terminator

logger = getLogger(__name__)


class CliCmd:
    # the following is a list of valid commands and
    # their corresponding command processors in the CmdProcessors class
    # the following list contains regex patterns used to check inbound API requests
    # and the corresponding cmd processor
    cli_format = [
        {'exp': '^M.E$', 'xlat': 'E~', 'by': 'id'},
        {'exp': '^M.E +(\\d+)$', 'xlat': 'E{param}~', 'by': 'id'},
        {'exp': '^M.E +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'E{param}~', 'by': 'date'},

        {'exp': '^M.G +(\\d+)$', 'xlat': 'G{param}~', 'by': 'id'},

        {'exp': '^M.WX$', 'xlat': 'G0~', 'by': 'id'},

        # The following commands are deprecated and now return extended listings.
        {'exp': '^M.L$', 'xlat': 'E~', 'by': 'id'},
        {'exp': '^M.L +(\\d+)$', 'xlat': 'E{param}~', 'by': 'id'},
        {'exp': '^M.L +(\\d{4}-\\d{2}-\\d{2})$', 'xlat': 'E{param}~', 'by': 'date'},
    ]

    is_cli = False
    api_cmd = ''

    def __init__(self, command: str):

        command = command.replace(msg_terminator, '')
        command = command.strip()

        for entry in self.cli_format:
            # try to match the request
            result = re.findall(entry['exp'], command)
            if not result:
                continue

            # ToDo: We need to add code here to handle invalid commands

            self.api_cmd = str(entry['xlat']).format(param=str(result[0]))
            self.is_cli = True
            logger.info(f"Translated {command} to {self.api_cmd}")
            break

        return
