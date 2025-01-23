#!/usr/bin/python3

import socket

HOST = "192.168.0.250"
PORT = 9100  # The port used by the server

group = chr(0x1D)
escape = chr(0x1B)

# seems not to work
_emph = escape + 'E'
EMPH_OFF = _emph + chr(0)
EMPH_ON = _emph + chr(1)

class Font:
    BASE = escape + 'M'

    FONT_A = BASE + chr(0)
    FONT_B = BASE + chr(1)

SMALLFONT = Font.FONT_B
BIGFONT = Font.FONT_A

class Feed:
    def __init__(self, lines = 1):
        self.lines = lines

    def feed(self):
        return escape + 'J' + chr(self.lines)

defaultFeed = Feed(2).feed()

class Cut:
    BASE = group + 'V'

    def __init__(self, feed = 1, less = False):
        self.feed = feed
        self.less = 1 if less else 0

    def PLAIN_CUT(self):
        return self.BASE + chr(0 + self.less)

    def FEED_CUT(self):
        return self.BASE + chr(65 + self.less) + chr(self.feed)

    # not supported by T88IV :'(
    def FEED_CUT_REVERSE(self):
        return self.BASE + chr(103 + self.less) + chr(self.feed)

defaultCut = Cut(feed=5, less=False)

class Underline:
    BASE = escape + '-'

    NONE = BASE + chr(0)
    ONE = BASE + chr(1)
    TWO = BASE + chr(2)

class DoubleStrike:
    _BASE = escape + 'G'
    ON = _BASE + chr(1)
    OFF = _BASE + chr(0)

class Emph:
    _BASE = escape + 'E'
    ON = _BASE + chr(1)
    OFF = _BASE + chr(0)

class Just:
    _BASE = escape + 'a'
    LEFT = _BASE + chr(0)
    CENTER = _BASE + chr(1)
    RIGHT = _BASE + chr(2)

class Printer():
    WIDTH = 56

    class CodeTable:
        BASE = escape + 't'
        SET_NORDIC = BASE + chr(5)
        nordic = 'cp865'

    def __init__(self, socket):
        self.socket = socket
        self.encoding = 'ascii'

    def setCodePage(self):
        # todo: actual parameter
        print(Printer.CodeTable.SET_NORDIC)
        self.encoding = Printer.CodeTable.nordic

    def resetFormatting(self):
        print(escape + '@')

    def print(self, *argv):
        print (argv)
        for string in argv:
            self.socket.sendall(string.encode(self.encoding))

    def println(self, *argv):
        self.print(*argv, "\r\n")




from datetime import datetime

# datetime object containing current date and time
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    p = Printer(s)
    p.resetFormatting()
    p.setCodePage()
    p.print(defaultFeed)
    p.println(BIGFONT, "ICH SAGE ES MAL GANZ DEUTLICH...")
    p.println(SMALLFONT, Emph.ON, "Ronny hat kleine Hände", Emph.OFF)
    p.print(defaultFeed)
    p.println(SMALLFONT, "... und darauf ist er auch noch ", Underline.TWO, "stolz", Underline.NONE)
    p.println(Printer.WIDTH * "─")
    p.println(Just.CENTER, now, Just.LEFT)
    # p.println(DoubleStrike.ON, "double", DoubleStrike.OFF)
    # p.println(Emph.ON, "emph", Emph.OFF)

    p.print(defaultCut.FEED_CUT())
    s.close()