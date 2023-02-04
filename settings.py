# Configuration Parameters ############################################################################

# make sure you open port 2442 prior to opening JS8 application
# ubuntu command: sudo ufw allow 2442
# in JS8Call go to File -> Settings -> Reporting in API section check:
# Enable TCP Server API
# Accept TCP Requests

server = ('127.0.0.1', 2442)
capabilities = 'LEG'
announce = True
mb_announcement_timer = 300
languages = 'EN-GB'

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
debug_request = 'NOT AN MB REQUEST'
# debug_request = 'MB.L'
# debug_request = 'MB.E'
# debug_request = 'M.L >22'
# debug_request = 'M.E >22'
# debug_request = 'M.L > 22'
# debug_request = 'M.L 2023-01-13'
# debug_request = 'M.E 2023-01-13'
# debug_request = 'M.E FRED'
# debug_request = 'M.L >2023-01-06'
# debug_request = 'M.E >2023-01-06'
# debug_request = 'M.L > 2023-01-06'
# debug_request = 'M.G 24'
# debug_request = 'M.G 9999'
# debug_request = 'M.G 2023-01-13'

#######################################################################################################
