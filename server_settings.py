# Configuration Parameters ############################################################################

# make sure you open port 2442 prior to opening JS8 application
# ubuntu command: sudo ufw allow 2442
# in JS8Call go to File -> Settings -> Reporting in API section check:
# Enable TCP Server API
# Accept TCP Requests

mb_revision = '9'

server = ('127.0.0.1', 2442)
msg_terminator = '♢'
capabilities = 'LEG'
announce = True
mb_announcement_timer = 60  # in minutes, suggested values are 60, 30 and 15

# current_log_level = 0  # no logging
current_log_level = 1  # normal logging
# current_log_level = 2  # verbose logging
# current_log_level = 3  # debug level logging
# current_log_level = 4  # verbose debug level logging

posts_dir = 'C:\\Development\\microblog\\posts\\'  # location of the microblog posts
lst_limit = 5
replace_nl = False  # if True, \n characters in a post will be replaced with a space character

# when debugging this code, JS8Call must be running but a radio isn't needed
debug = False  # set to True to tests with simulated messages set in debug_json

#######################################################################################################
