# Configuration Parameters ############################################################################

# make sure you open port 2442 prior to opening JS8 application
# ubuntu command: sudo ufw allow 2442
# in JS8Call go to File -> Settings -> Reporting in API section check:
# Enable TCP Server API
# Accept TCP Requests

mb_revision = '13'

blog_name = None  # if None, defaults to the callsign

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

# posts_dir specifies the location of the microblog posts on your computer
# you can use \\ or / as path separators
# the posts_dir value must be enclosed in quotes and end with \\ or /
# the posts_dir value (and hence directory path) can contain spaces
posts_dir = 'C:\\Development\\microblog\\posts\\'

lst_limit = 5
replace_nl = False  # if True, \n characters in a post will be replaced with a space character

# when debugging this code, JS8Call must be running but a radio isn't needed
debug = False  # set to True to tests with simulated messages set in debug_json

#######################################################################################################
