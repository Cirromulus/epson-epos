#!/usr/bin/python3

import PIL.Image # todo: somewhere else
import socket
import os.path

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
FeedForward = chr(12)

def Unidirectional(on = True):
    return escape + "U" + chr(1 if on else 0)

class Printer():
    class PaperWidth:
        def __init__(self, w):
            self.width = w

    SMALLPAPER = PaperWidth(58)
    WIDEPAPER = PaperWidth(80)

    configuredPaper = WIDEPAPER

    def getMaxCharacterWidth(font = SMALLFONT):
        assert(Printer.configuredPaper == Printer.WIDEPAPER, "hardcoded currently")

        if font == SMALLFONT:
            return 56
        elif font == BIGFONT:
            return 42

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
        # self.send(bytes([ord(group), ord("P"), 180, 180]))



    class List:
        def __init__(self, printer, font = BIGFONT):
            self.items = []
            self.printer = printer
            self.font = font

        def addItem(self, nameleft, thingright):
            self.items.append([nameleft, thingright])

        def print(self):
            self.printer.print(escape + '@')    # reset existing formatting
            self.printer.print(self.font)
            width = Printer.getMaxCharacterWidth(self.font)
            maxWidthRight = max([len(right) for (_, right) in self.items])
            self.printer.setHorizontalTabPos(width - maxWidthRight)
            for (left, right) in self.items:
                self.printer.println(Just.LEFT, Emph.ON, left, Emph.OFF, Tab,
                                        right.rjust(maxWidthRight))

    def newList(self, *args, **kwargs):
        return Printer.List(self, *args, **kwargs)

    def setPageMode(self, on = True):
        if on:
            self.send(bytes([escape, 'L']))
        else:
            self.send(bytes(FeedForward))

    class Image:
        class Resolution:
            def __init__(self, hor_dpi, max_hor_dots, vert_dpi, bits_per_line, code):
                self.hor_dpi = hor_dpi
                self.max_hor_dots = max_hor_dots
                self.vert_dpi = vert_dpi
                self.bits_per_line = bits_per_line
                self.code = code

            def __str__(self):
                return f"Resolution: h_dpi {self.hor_dpi} (max {self.max_hor_dots}), v_dpi {self.vert_dpi}, bpl {self.bits_per_line}"

        # Hardcoded to 80mm paper currently
        # also, https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/esc_asterisk.html
        # seems to be incorrect (half DPI than said!?)
        # SD seems to not work, but DD code "1" works with SD resolution.?!
        # class Official:
        #     SD_8 = Resolution(hor_dpi=90, max_hor_dots=256, vert_dpi=60, bits_per_line=8, code=0)
        #     DD_8 = Resolution(hor_dpi=180, max_hor_dots=512, vert_dpi=60, bits_per_line=8, code=1)
        #     SD_24 = Resolution(hor_dpi=90, max_hor_dots=256, vert_dpi=180, bits_per_line=24, code=32)
        #     DD_24 = Resolution(hor_dpi=180, max_hor_dots=512, vert_dpi=180, bits_per_line=24, code=33)
        # SD_8 = Resolution(hor_dpi=90, max_hor_dots=256, vert_dpi=60, bits_per_line=8, code=0)
        DD_8 = Resolution(hor_dpi=180/2, max_hor_dots=512/2, vert_dpi=60, bits_per_line=8, code=1)
        SD_24 = Resolution(hor_dpi=90, max_hor_dots=256, vert_dpi=180, bits_per_line=24, code=32)
        DD_24 = Resolution(hor_dpi=180, max_hor_dots=512, vert_dpi=180, bits_per_line=24, code=33)


        def __init__(self, imagepath, resolution : Resolution, desired_width_ratio = 1):
            desired_width = int(resolution.max_hor_dots * desired_width_ratio)
            height_stretch_ratio = resolution.hor_dpi / resolution.vert_dpi # higher number for higher stretching
            print (f"Image: Opening {imagepath}")
            img = PIL.Image.open(imagepath) # open colour image
            wpercent = (desired_width / float(img.size[0]))
            hsize = int(img.size[1] * wpercent / height_stretch_ratio)
            scaled_size = (desired_width, hsize)
            print (f"Image: {resolution}")
            print (f"Image: Scaling from {img.size} to {scaled_size}")
            img = img.resize(scaled_size, PIL.Image.Resampling.LANCZOS)
            img = img.convert('1') # convert image to black and white
            img.save(f'intended_image_{os.path.basename(imagepath)}.png')

            self.resolution = resolution
            self.img = img

    def printImage(self, image : Image):
        # ASCII ESC * m nL nH d1 ... dk

        BASE = escape + '*'

        # When printing multiple line bit images, selecting unidirectional print mode
        # with ESC U enables printing patterns in which the top and bottom parts are
        # aligned vertically.
        self.print(Just.CENTER)
        self.print(Unidirectional(True))
        num_horizontal_dots = image.img.size[0]
        num_vertical_dots = image.img.size[1]
        # if num_horizontal_dots > TM_T88IV_max_horizontal_dots:
        #     print (num_horizontal_dots, " > ", TM_T88IV_max_horizontal_dots)
        # "big endian"
        num_dots_serialized = bytes([num_horizontal_dots % 256, int(num_horizontal_dots / 256)])

        base_y = 0
        while base_y < num_vertical_dots:
            data = bytearray()
            for x in range(num_horizontal_dots):
                boyt = 0
                for offs_y in range(min(num_vertical_dots - base_y, image.resolution.bits_per_line)):
                    byteoffs = offs_y % 8
                    coord = (x, base_y + offs_y)
                    px = image.img.getpixel(coord)
                    # print (f"pixul: {px}")
                    px = 1 - min(px, 1)
                    # print (f"pixul: {px}")
                    boyt = boyt + (px << ((8-1) - byteoffs))
                    print (f"coord= {coord}, offs_y={offs_y}-> bit {px} boyt {boyt}")
                    if byteoffs == 8 - 1:
                        print (f"dotgroup {x} (len {len(data)}) of {num_horizontal_dots} : {boyt}")
                        data.append(boyt)
            base_y += image.resolution.bits_per_line
            print (f"sending image row {base_y / image.resolution.bits_per_line} of {num_vertical_dots / image.resolution.bits_per_line}")
            print (data)
            self.send(BASE.encode(self.encoding), bytes(image.resolution.code), num_dots_serialized, data)
        self.resetFormatting()

    def feed(self, times = 1, motionUnits = 20):
        self.print(escape + 'J' + chr(times * motionUnits))

    def print(self, *argv):
        print (argv)
        for string in argv:
            self.socket.sendall(string.encode(self.encoding))

    def send(self, *argv):
        for binary in argv:
            print (f"send({len(binary)})")
            self.socket.sendall(binary)

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
# now = '2025-01-26 00:01:15'


gang_img = Printer.Image("drei.png", resolution=Printer.Image.DD_24)

# import sys; sys.exit(1)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    p = Printer(s)
    p.feed()

    # p.feed(times=2)
    # p.print(Just.CENTER)
    # p.println(BIGFONT, "Geburtstagsgrüße")
    # p.println(BIGFONT, "RIEBE / PIEPER")
    # p.feed()
    p.println(SMALLFONT, Just.CENTER, now)
    p.println(str(gang_img.resolution))
    # p.feed(times=2)
    p.resetFormatting()
    p.printImage(gang_img)

    # p.println(Underline.ONE, "Zusammenfassung Geburtstagsgruß", Underline.NONE)
    # p.feed()

    # list = p.newList(BIGFONT)
    # list.addItem("Name", "Lukas Bertram")
    # list.addItem("Alter", "31")
    # list.addItem("Lieblingsfarbe", "Musik")
    # list.addItem("Nasenlöcher", "2")
    # list.addItem("Fernbedienungdinger", "0")
    # list.addItem("Schenkung", "Jetzt")
    # list.print()

    # p.feed(times=2)
    # p.print(SMALLFONT)
    # p.println("Lieber Lukas,")
    # p.feed(motionUnits=5)
    # p.println("wir blicken auf viele musikalische Erfahrung zurück.")
    # p.println("Neben Gitarrenklängen gibt es vor allem ein Geräusch,")
    # p.println("das wir im Studio mit dir verbinden: ", EMPH_ON, '"RACKLACKGGG!!"', EMPH_OFF)
    # p.println("... wenn mal wieder eine Aufnahme einen fehler hatte,")
    # p.println("und wie du die mittlerweile im Muskelgedächnis")
    # p.println("eingebettete Kombination für ")
    # p.println('"Aufnahme beenden, Audiospuren löschen, dankeok"')
    # p.println("mit viel liebevollem Hass in deine Laptoptastatur\neinprügelst.")
    # p.feed(motionUnits=5)
    # p.println("Auch wenn das überwiegend schöne Erfahrungen sind,")
    # p.println("wollen wir dir auch mal die Möglichkeit geben,")
    # p.println("die Gitarre etwas angenehmer zu halten")
    # p.println("(um nicht das Laptop auf dem Schoß zu klemmen)")
    # p.println("und dir dafür dieses Fernbedienungsdings geben.")

    # p.feed(times=2)

    # p.println("Es bediente Sie")
    # p.feed(motionUnits=5)
    # p.println("Freund 1 / Freund 2")


    # # p.println(SMALLFONT, Emph.ON, "Ronny hat kleine Hände", Emph.OFF)
    # p.println(Printer.WIDTH * "─")
    # p.println(Just.RIGHT, "... und darauf ist er auch noch ", Underline.TWO, "stolz", Underline.NONE, " ", Just.LEFT)
    # # p.println(DoubleStrike.ON, "double", DoubleStrike.OFF)
    # # p.println(Emph.ON, "emph", Emph.OFF)

    # p.feed(times= 2)

    # p.print(Just.CENTER, Barcode.Setup() + Barcode.send("PIMMEL"))

    # p.feed(times= 2)
    p.print(defaultCut.FEED_CUT())
    s.close()