from datetime import datetime, timezone

from .server_settings import *


def logmsg(log_level, msg_text):
    if log_level <= current_log_level:
        now = datetime.now(timezone.utc)
        date_time = now.strftime("%Y-%m-%d %H:%M:%SZ -")
        # we need to eliminate the message terminator as it's not supported by print in UTF8 mode
        print(date_time, msg_text.replace(msg_terminator, ''))
