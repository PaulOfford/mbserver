import re

from logging import getLogger
from .config import SETTINGS

msg_terminator = SETTINGS.msg_terminator

logger = getLogger(__name__)


def cli_translate(command: str) -> str:
    # the following is a list of valid commands and
    # their corresponding command processors in the CmdProcessors class
    # the following list contains regex patterns used to check inbound API requests
    # and the corresponding cmd processor
    cli_format = [
        {'exp': r'^M.E$', 'xlat': 'E~', 'by': 'id'},
        {'exp': r'^M.E +(\d+)$', 'xlat': 'E{param}~', 'by': 'id'},
        {'exp': r'^M.E +(\d{4}-\d{2}-\d{2})$', 'xlat': 'E{param}~', 'by': 'date'},

        {'exp': r'^M.G +(\d+)$', 'xlat': 'G{param}~', 'by': 'id'},

        {'exp': r'^M.WX$', 'xlat': 'G0~', 'by': 'id'},

        {'exp': r'^M.I$', 'xlat': 'I~', 'by': 'id'},
        {'exp': r'^M.\?$', 'xlat': 'I~', 'by': 'id'},

        # The following commands are deprecated and now return extended listings.
        {'exp': r'^M.L$', 'xlat': 'E~', 'by': 'id'},
        {'exp': r'^M.L +(\d+)$', 'xlat': 'E{param}~', 'by': 'id'},
        {'exp': r'^M.L +(\d{4}-\d{2}-\d{2})$', 'xlat': 'E{param}~', 'by': 'date'},
    ]

    translated_command = ""

    command = command.replace(msg_terminator, '')
    command = command.strip()

    for entry in cli_format:
        # try to match the request
        result = re.findall(entry['exp'], command)
        if not result:
            continue

        # ToDo: We need to add code here to handle invalid commands

        translated_command = str(entry['xlat']).format(param=str(result[0]))
        logger.info(f"Translated {command} to {translated_command}")
        break

    return translated_command
