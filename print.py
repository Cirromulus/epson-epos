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

Tab = chr(9)

class Printer():
    WIDTH = 56

    class CodeTable:
        BASE = escape + 't'
        SET_NORDIC = BASE + chr(5)
        nordic = 'cp865'

    def __init__(self, socket):
        self.socket = socket
        self.encoding = 'cp437' # is default encoding
        self.setCodePage()  # this also allows high/low characters

    def setHorizontalTabPos(self, *pos):
        _BASE = escape + 'D'

        tosend =_BASE
        for p in pos:
            tosend = tosend + chr(p)
        self.print(tosend + chr(0))

    def setCodePage(self):
        # todo: actual parameter
        self.print(Printer.CodeTable.SET_NORDIC)
        self.encoding = Printer.CodeTable.nordic

    def resetFormatting(self):
        self.print(escape + '@')
        # 1 inch / 180 ... 0.1xx mm
        self.print(group + "P" + chr(180) + chr(180))

    class List:
        def __init__(self, printer):
            self.items = []
            self.printer = printer

        def addItem(self, nameleft, thingright):
            self.items.append([nameleft, thingright])

        def print(self):
            maxWidthRight = max([len(right) for (_, right) in self.items])
            self.printer.setHorizontalTabPos(Printer.WIDTH - maxWidthRight)
            for (left, right) in self.items:
                self.printer.println(Just.LEFT, Emph.ON, left, Emph.OFF, Tab,
                                        right.rjust(maxWidthRight))

    def newList(self):
        return Printer.List(self)

    def feed(self, times = 1, motionUnits = 20):
        self.print(escape + 'J' + chr(times * motionUnits))

    def print(self, *argv):
        print (argv)
        for string in argv:
            self.socket.sendall(string.encode(self.encoding))

    def println(self, *argv):
        self.print(*argv, "\n")


class Barcode:
    JAN8 = 2
    CODE39 = 4  # d = 48 – 57, 65 – 90, 32, 36, 37, 42, 43, 45, 46, 47

    def Setup(height=50):
        setHeight = group + 'h' + chr(height)
        setHriCharacterPos = group + 'H' + chr(2)   # 2: Below
        setHriCharacterFont = group + 'f' + chr(1) # font B
        return setHeight + setHriCharacterPos + setHriCharacterFont

    def send(data):
        return group + 'k' + chr(Barcode.CODE39) + data + chr(0)


from datetime import datetime
from random import random

# datetime object containing current date and time
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    p = Printer(s)
    p.setCodePage()
    p.feed()
    p.println(BIGFONT, Just.CENTER, "ABRECHNUNG RONNFRIED")
    p.println(SMALLFONT, now, Just.LEFT)
    p.feed()

    list = p.newList()
    list.addItem("Rönnies linke Hand", "Gicht")
    list.addItem("Rönnies rechte Hand", "Sehr klein")
    list.addItem("Rönnies Mittelfinger", "dreifach")
    list.addItem("Körperhöhe", str(round(random()*1.5 + .2, 2)) + 'm')
    list.addItem("Gewicht", "irrelevant")
    list.print()

    # p.println(SMALLFONT, Emph.ON, "Ronny hat kleine Hände", Emph.OFF)
    p.println(Printer.WIDTH * "─")
    p.println(Just.RIGHT, "... und darauf ist er auch noch ", Underline.TWO, "stolz", Underline.NONE, " ", Just.LEFT)
    # p.println(DoubleStrike.ON, "double", DoubleStrike.OFF)
    # p.println(Emph.ON, "emph", Emph.OFF)

    p.feed(times= 2)

    p.print(Just.CENTER, Barcode.Setup() + Barcode.send("ASSMASTER"))

    p.feed(times= 2)
    p.print(defaultCut.FEED_CUT())
    s.close()