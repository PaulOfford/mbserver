import unittest
import re
from mb_server import MbServer
from mb_server import logmsg
from settings import *

api_tests = [
    ['CLIENT: SERVER  L22~ ♢', 'CLIENT \+LE 22\n22 - HAARP THANKS HAMS'],
    ['CLIENT: SERVER  L23,27~ ♢', 'CLIENT \+LG >22\n23 - K7RA SOLAR UPDATE\n27 - RSGB PROPOGATION NEWS'],
    ['CLIENT: SERVER  LE22~ ♢', 'CLIENT \+LE 22\n22 - HAARP THANKS HAMS'],
    ['CLIENT: SERVER  LE999~ ♢', 'CLIENT \+LE 999\nNO POSTS FOUND'],
    ['CLIENT: SERVER  LG22~ ♢', 'CLIENT \+LG >22\n23 - K7RA SOLAR UPDATE[\\s\\S]*27 - RSGB PROPOGATION NEWS'],
    ['CLIENT: SERVER  ME23120~ ♢', 'CLIENT \+ME 2023-01-20\n25 - FALCONSAT[\\s\\S]*WORLD RADIO'],
    ['CLIENT: SERVER  ME23E20~ ♢', None],
    ['CLIENT: SERVER  MG23120~ ♢', 'CLIENT \+MG \>2023-01-20\n27 - RSGB PROPOGATION[\\s\\S]*29 - RSGB PROPOGATION NEWS'],

    ['CLIENT: SERVER  E22~ ♢', 'CLIENT \+EE 22\n22 - 2023-01-13 - HAARP THANKS HAMS'],
    ['CLIENT: SERVER  E27,29~ ♢', 'CLIENT \+FG \>2023-01-20\n'
                                  '27 - 2023-01-22 - RSGB PROPOGATION NEWS\n29 - 2023-01-27 - RSGB PROPOGATION NEWS'],
    ['CLIENT: SERVER  EE22~ ♢', 'CLIENT \+EE 22\n22 - 2023-01-13 - HAARP THANKS HAMS'],
    ['CLIENT: SERVER  EE999~ ♢', 'CLIENT \+EE 999\nNO POSTS FOUND'],

    ['CLIENT: SERVER  FE23120~ ♢', 'CLIENT \+FE 2023-01-20\n25 - 2023-01-20 - FALCONSAT-3 NEARS REENTRY[\\s\\S]*WORLD RADIO'],
    ['CLIENT: SERVER  FE23E20~ ♢', None],
    ['CLIENT: SERVER  FG23120~ ♢', 'CLIENT \+FG \>2023-01-20\n'
                                  '27 - 2023-01-22 - RSGB PROPOGATION NEWS[\\s\\S]*29 - 2023-01-27 - RSGB PROPOGATION NEWS'],
    ['CLIENT: SERVER  GE24~ ♢',
     'CLIENT \+GE 24[\\s\\S]*WE CURRENTLY HAVE AN SFI IN THE 190S.'],
]

cli_tests = [
    ['CLIENT: SERVER  M.L ♢',
     'CLIENT \+M.L >0\n20 - MARINES TO GAIN RADIO OP EXPERIENCE[\\s\\S]*24 - RSGB PROPOGATION NEWS'],
    ['CLIENT: SERVER  M.L 22 ♢', 'CLIENT \+M.L 22\n22 - HAARP THANKS HAMS'],
    ['CLIENT: SERVER  M.L 999 ♢', 'CLIENT \+M.L 999\nNO POSTS FOUND'],
    ['CLIENT: SERVER  M.L >22 ♢', 'CLIENT \+M.L >22\n23 - K7RA SOLAR UPDATE[\\s\\S]*27 - RSGB PROPOGATION NEWS'],
    ['CLIENT: SERVER  M.L 2023-01-20 ♢', 'CLIENT \+M.L 2023-01-20\n25 - FALCONSAT[\\s\\S]*WORLD RADIO'],
    ['CLIENT: SERVER  M.L 2023-0A-25 ♢', 'CLIENT -M.L PARAMETER NOT INTEGER OR DATE'],
    ['CLIENT: SERVER  M.L >2023-01-20 ♢', 'CLIENT \+M.L \>2023-01-20\n27 - RSGB PROPOGATION[\\s\\S]*29 - RSGB PROPOGATION NEWS'],

    ['CLIENT: SERVER  M.E 22 ♢', 'CLIENT \+M.E 22\n22 - 2023-01-13 - HAARP THANKS HAMS'],
    ['CLIENT: SERVER  M.E 999 ♢', 'CLIENT \+M.E 999\nNO POSTS FOUND'],

    ['CLIENT: SERVER  M.E 2023-01-20 ♢', 'CLIENT \+M.E 2023-01-20\n25 - 2023-01-20 - FALCONSAT-3 NEARS REENTRY[\\s\\S]*WORLD RADIO'],
    ['CLIENT: SERVER  M.E 2023-0A-20 ♢', 'CLIENT -M.E PARAMETER NOT INTEGER OR DATE'],
    ['CLIENT: SERVER  M.E >2023-01-20 ♢', 'CLIENT \+M.E \>2023-01-20\n'
                                  '27 - 2023-01-22 - RSGB PROPOGATION NEWS[\\s\\S]*29 - 2023-01-27 - RSGB PROPOGATION NEWS'],
    ['CLIENT: SERVER  M.G 24 ♢',
     'CLIENT \+M.G 24[\\s\\S]*WE CURRENTLY HAVE AN SFI IN THE 190S.'],
    ['CLIENT: SERVER  M.G 2023-01-20 ♢',
     'CLIENT -M.G 2023-01-20 BY DATE UNSUPPORTED'],
]

debug = False


class TestProcess(unittest.TestCase):

    def setUp(self) -> None:
        self.s = MbServer()

    def test_api(self):
        for test in api_tests:
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
                    print('result: ' + result)
                self.assertIsNotNone(result)
                self.assertIsNotNone(re.search(test[1], result))
                logmsg(1, 'Success: ' + test[0].replace(msg_terminator, ''))

    def test_cli(self):
        for test in cli_tests:
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
                    print('result: ' + result)
                self.assertIsNotNone(result)
                self.assertIsNotNone(re.search(test[1], result))
                logmsg(1, 'Success: ' + test[0].replace(msg_terminator, ''))
