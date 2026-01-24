import unittest
import re
import os

from mb_server import MbServer
from mb_server import logmsg
from server_settings import *

api_tests = [
    ['CLIENT: SERVER  L~ ♢', 'CLIENT \+L~\n6 - US RESTART FEE COVID TESTS[\\s\\S]*10 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  L7~ ♢', 'CLIENT \+L7~\n7 - HAWAII FIRES - RETURN TO LAHAINA'],
    ['CLIENT: SERVER  L7,10~ ♢', 'CLIENT \+L7,10~\n'
                                  '7 - HAWAII FIRES - RETURN TO LAHAINA\n10 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  LE7~ ♢', 'CLIENT \+LE7~\n7 - HAWAII FIRES - RETURN TO LAHAINA'],
    ['CLIENT: SERVER  LE999~ ♢', 'CLIENT \+LE999~\nNO POSTS FOUND'],
    ['CLIENT: SERVER  LG7~ ♢', 'CLIENT \+LG7~\n8 - ICRC AID TO NAGORNO-KARABAKH[\\s\\S]*'
                                '10 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  ME23A01~ ♢', 'CLIENT \+ME23A01~\n10 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  ME23922~ ♢', 'CLIENT \+ME23922~\n4 - K7RA SOLAR UPDATE\n5 - TRIAL OF HIV VACCINE IN RSA AND US'],
    ['CLIENT: SERVER  ME23E05~ ♢', None],
    ['CLIENT: SERVER  MG23922~ ♢', 'CLIENT \+MG23922~\n6 - US RESTART FEE COVID TESTS[\\s\\S]*'
                                    '10 - FLOODS CLOSE WOODHULL HOSPITAL'],

    ['CLIENT: SERVER  E~ ♢', 'CLIENT \+E~\n6 - 2023-09-25 - US RESTART FEE COVID TESTS[\\s\\S]*'
                              '10 - 2023-10-01 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  E7~ ♢', 'CLIENT \+E7~\n7 - 2023-09-27 - HAWAII FIRES - RETURN TO LAHAINA'],
    ['CLIENT: SERVER  E7,10~ ♢', 'CLIENT \+E7,10~\n'
                                  '7 - 2023-09-27 - HAWAII FIRES - RETURN TO LAHAINA\n'
                                 '10 - 2023-10-01 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  EE7~ ♢', 'CLIENT \+EE7~\n7 - 2023-09-27 - HAWAII FIRES - RETURN TO LAHAINA'],
    ['CLIENT: SERVER  EE999~ ♢', 'CLIENT \+EE999~\nNO POSTS FOUND'],

    ['CLIENT: SERVER  FE23922~ ♢', 'CLIENT \+FE23922~\n'
                                    '4 - 2023-09-22 - K7RA SOLAR UPDATE\n'
                                    '5 - 2023-09-22 - TRIAL OF HIV VACCINE IN RSA AND US'],
    ['CLIENT: SERVER  FE23E20~ ♢', None],
    ['CLIENT: SERVER  FG23922~ ♢', 'CLIENT \+FG23922~\n'
                                    '6 - 2023-09-25 - US RESTART FEE COVID TESTS[\\s\\S]*'
                                    '10 - 2023-10-01 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  GE9~ ♢',
        'CLIENT \+GE9~[\\s\\S]*LEAVE THE UK AROUND 06:00 GMT THU 29 SEP 2023.'],

    ['CLIENT: SERVER  WX~ ♢', 'CLIENT \+WX~[\\s\\S]*PRESSURE: 1019[\\s\\S]*'],

    ['CLIENT: SERVER  ME2023-09-22~ ♢', 'CLIENT \+ME2023-09-22~\n'
                                         '4 - K7RA SOLAR UPDATE\n5 - TRIAL OF HIV VACCINE IN RSA AND US'],
    ['CLIENT: SERVER  ME2023-14-20~ ♢', 'CLIENT -ME PARAMETER NOT VALID DATE'],
    ['CLIENT: SERVER  MG2023-09-22~ ♢', 'CLIENT \+MG2023-09-22~\n'
                                         '6 - US RESTART FEE COVID TESTS[\\s\\S]*10 - FLOODS CLOSE WOODHULL HOSPITAL'],
]

cli_tests = [
    ['CLIENT: SERVER  M.L ♢', 'CLIENT \+M.L\n6 - US RESTART FEE COVID TESTS[\\s\\S]*'
                               '10 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  M.L 7 ♢', 'CLIENT \+M.L 7\n7 - HAWAII FIRES - RETURN TO LAHAINA'],
    ['CLIENT: SERVER  M.L 999 ♢', 'CLIENT \+M.L 999\nNO POSTS FOUND'],
    ['CLIENT: SERVER  M.L >7 ♢', 'CLIENT \+M.L >7\n'
                                  '8 - ICRC AID TO NAGORNO-KARABAKH[\\s\\S]*10 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  M.L 2023-09-22 ♢', 'CLIENT \+M.L 2023-09-22\n'
                                          '4 - K7RA SOLAR UPDATE\n5 - TRIAL OF HIV VACCINE IN RSA AND US'],
    ['CLIENT: SERVER  M.L 2023-0A-25 ♢', None],
    ['CLIENT: SERVER  M.L >2023-09-22 ♢', 'CLIENT \+M.L \>2023-09-22\n'
                                           '6 - US RESTART FEE COVID TESTS[\\s\\S]*'
                                           '10 - FLOODS CLOSE WOODHULL HOSPITAL'],

    ['CLIENT: SERVER  M.E 7 ♢', 'CLIENT \+M.E 7\n7 - 2023-09-27 - HAWAII FIRES - RETURN TO LAHAINA'],
    ['CLIENT: SERVER  M.E 999 ♢', 'CLIENT \+M.E 999\nNO POSTS FOUND'],

    ['CLIENT: SERVER  M.E 2023-09-22 ♢', 'CLIENT \+M.E 2023-09-22\n4 - 2023-09-22 - K7RA SOLAR UPDATE\n'
                                           '5 - 2023-09-22 - TRIAL OF HIV VACCINE IN RSA AND US'],
    ['CLIENT: SERVER  M.E 2023-0A-20 ♢', None],
    ['CLIENT: SERVER  M.E >2023-09-22 ♢', 'CLIENT \+M.E \>2023-09-22\n'
                                  '6 - 2023-09-25 - US RESTART FEE COVID TESTS[\\s\\S]*'
                                  '10 - 2023-10-01 - FLOODS CLOSE WOODHULL HOSPITAL'],
    ['CLIENT: SERVER  M.G 8 ♢', 'CLIENT \+M.G 8\nICRC DISPATCHED FOOD[\\s\\S]*NOT YET POSSIBLE.'],
    ['CLIENT: SERVER  M.G 2023-09-25 ♢', 'CLIENT -M.G 2023-09-25 BY DATE UNSUPPORTED'],

    ['CLIENT: SERVER  M.WX ♢', 'CLIENT \+M.WX[\\s\\S]*PRESSURE: 1019[\\s\\S]*'],
]

debug = True


class TestProcess(unittest.TestCase):

    def setUp(self) -> None:
        # check the posts directory looks OK
        if not os.path.exists(posts_dir):
            logmsg(1, "err: Can't find the posts directory")
            logmsg(1, 'info: Check that the posts_dir value in server_settings.py is correct')
            logmsg(1, "err: ** THE FOLLOWING TESTS WILL FAIL **")

        self.s = MbServer()

    def test_api(self):
        for test in api_tests:
            print("\n------------------------------------------------------------")
            result = self.s.process({
                'type': 'RX.DIRECTED',
                'value': test[0],
                'params': None
            }
            )
            if debug:
                print('test[1]: ', test[1])
            if test[1] is None:
                self.assertIsNone(result)
            else:
                if debug:
                    print('result: ' + str(result))
                self.assertIsNotNone(result)
                self.assertIsNotNone(re.search(test[1], result))
                logmsg(1, 'Success: ' + test[0].replace(msg_terminator, ''))

    def test_cli(self):
        for test in cli_tests:
            print("\n------------------------------------------------------------")
            result = self.s.process({
                'type': 'RX.DIRECTED',
                'value': test[0],
                'params': None
            }
            )
            if debug:
                print('test[1]: ', test[1])
            if test[1] is None:
                self.assertIsNone(result)
                logmsg(1, 'Success: ' + test[0].replace(msg_terminator, ''))
            else:
                if debug:
                    print('result: ' + result)
                self.assertIsNotNone(result)
                self.assertIsNotNone(re.search(test[1], result))
                logmsg(1, 'Success: ' + test[0].replace(msg_terminator, ''))
