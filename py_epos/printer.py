#!/usr/bin/python3

import PIL.Image
import PIL.ImageEnhance

import os.path
import math # wow, for ceil
import time


"""TODO:
IS PERHAPS THE REALTIME COMMAND THE PROBLEM FOR BUG!?

"It is recommended to disable this function with GS ( D as it is possible
that data such as graphics or downloaded text might accidentally
include a data string corresponding to this function.
(The default for GS ( D of this function is "Enabled".) "

https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/realtime_commands.html
"""

MM_PER_INCH = 25.4
INCH_PER_MM = 1 / MM_PER_INCH

def bigEndian(value, width_bytes = 2):
    bytes = bytearray()
    for _ in range(width_bytes):
        low = value & 0xFF
        bytes.append(low)
        value >>= 8
    return bytes

group = chr(0x1D)
escape = chr(0x1B)

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
    reset = escape + "@" # reset not needed, but seems to make things more stable
    BASE = reset + group + 'V'

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

    # TM-T88IV
    DEFAULT_MOTION_UNIT = (180, 360)

    def getMaxCharacterWidth(font = SMALLFONT):
        # "hardcoded currently"
        assert(Printer.configuredPaper == Printer.WIDEPAPER)

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
        self.currentMotionUnit = Printer.DEFAULT_MOTION_UNIT

    def setHorizontalTabPos(self, *pos):
        _BASE = escape + 'D'

        tosend =_BASE
        for p in pos:
            tosend = tosend + chr(p)
        self.print(tosend + chr(0))

    def setPrintSpeed(self, speed = 0):
        # zero is default, one is slow
        BASE = group + '(K'
        command = bigEndian(2, width_bytes=2)
        function = 50
        self.send(BASE.encode(self.encoding), command, bytes([function + speed]))

    def setCodePage(self):
        # todo: actual parameter
        self.print(Printer.CodeTable.SET_NORDIC)
        self.encoding = Printer.CodeTable.nordic

    def resetFormatting(self):
        self.print(escape + '@')

    def getCurrentMotionUnitPerMM(self):
        units_per_mm = [m / MM_PER_INCH for m in self.currentMotionUnit]
        # print(f"current units_per_mm: {units_per_mm}")
        return units_per_mm

    def setMotionUnit(self, mm_per_unit = INCH_PER_MM):
        desired_units_per_inch = int(round(MM_PER_INCH / mm_per_unit))
        assert(desired_units_per_inch <= 256)
        self.currentMotionUnit = (desired_units_per_inch, desired_units_per_inch)
        # print (f"set current motion unit: {self.currentMotionUnit} (1 inch / x)")
        self.send(bytes([ord(group), ord("P"), desired_units_per_inch, desired_units_per_inch]))

    class List:
        def __init__(self, printer, font = BIGFONT):
            self.items = []
            self.printer = printer
            self.font = font

        def addItem(self, nameleft, thingright):
            self.items.append([nameleft, thingright])

        def print(self):
            self.printer.resetFormatting()
            self.printer.print(self.font)
            width = Printer.getMaxCharacterWidth(self.font)
            maxWidthRight = max([len(right) for (_, right) in self.items])
            self.printer.setHorizontalTabPos(width - maxWidthRight)
            for (left, right) in self.items:
                self.printer.println(Just.LEFT, Emph.ON, left, Emph.OFF, Tab,
                                        right.rjust(maxWidthRight))

    def newList(self, *args, **kwargs):
        return Printer.List(self, *args, **kwargs)

    class PageMode:
        def __init__(self, printer, size_hor_mm, size_vert_mm, mm_per_row = 0, origin_x_mm = 0, origin_y_mm = 0, resolution = .125):
            self.printer = printer
            self.mm_per_row = mm_per_row
            #The maximum print area height that can be set differs according to the printing control
            # (single color / two-color) setting.
            # Refer to GS ( E   <Function 5> for specifying printing control (single-color / two-color).
            # When single-color printing control is selected: 234.53 mm {3324/360 inches}
            MAX_VERT_SIZE_mm = 234.53
            if size_vert_mm > MAX_VERT_SIZE_mm:
                print (f"Error: Page mode only supports up to {MAX_VERT_SIZE_mm}mm, you have requested {size_vert_mm}")
                print ("TODO: Split large images into multiple page setups")
                size_vert_mm = MAX_VERT_SIZE_mm - .1

            self.setPageMode()
            self.printer.setMotionUnit(resolution)

            origin_x_units = int(round(origin_x_mm * self.printer.getCurrentMotionUnitPerMM()[0]))
            origin_y_units = int(round(origin_y_mm * self.printer.getCurrentMotionUnitPerMM()[1]))
            size_hor_units = int(round(size_hor_mm * self.printer.getCurrentMotionUnitPerMM()[0]))
            size_vert_units = int(round(size_vert_mm * self.printer.getCurrentMotionUnitPerMM()[1]))

            print (f"Setting up page at {origin_x_mm}:{origin_y_mm} {size_hor_mm}x{size_vert_mm} (mm)")
            print (f"                   {origin_x_units}:{origin_y_units} {size_hor_units}x{size_vert_units} (units)")
            print (f"                   with {mm_per_row}mm per row")

            self.printer.send(bytes([ord(escape), ord('W')]),
                    bigEndian(origin_x_units), bigEndian(origin_y_units),
                    bigEndian(size_hor_units), bigEndian(size_vert_units))

        def setPageMode(self):
            self.printer.print(escape + 'L')

        def finalizePrint(self):
            # print ("Page mode: Finalizing")
            # Weird, but this helps stability a bit
            time.sleep(.2)
            self.printer.print(FeedForward)
            time.sleep(.5)

        class Direction:
            upperLeft = 0 # Left to right
            lowerLeft = 1 # bottom to top
            lowerRight = 2 # right to left
            upperRight = 3 # top to bottom

        def setDirection(self, direction : Direction):
            self.printer.print(escape + 'T' + chr(direction))

        def nextRow(self):
            assert(self.mm_per_row > 0)
            # print (f"NextRow: feeding {self.mm_per_row} mm")
            self.printer.feed(mm=self.mm_per_row)

    def setupPage(self, **kwarg) -> PageMode:
        return Printer.PageMode(self, **kwarg)

    class Image:
        #thang @ https://stackoverflow.com/questions/43864101/python-pil-check-if-image-is-transparent
        def has_transparency(img : PIL.Image):
            if img.info.get("transparency", None) is not None:
                return True
            if img.mode == "P":
                transparent = img.info.get("transparency", -1)
                for _, index in img.getcolors():
                    if index == transparent:
                        return True
            elif img.mode == "RGBA":
                extrema = img.getextrema()
                if extrema[3][0] < 255:
                    return True

            return False

        class Resolution:
            def __init__(self, hor_dpi, max_hor_dots, vert_dpi, bits_per_line, code):
                self.hor_dpi = hor_dpi
                self.max_hor_dots = int(round(max_hor_dots))
                self.vert_dpi = vert_dpi
                self.bits_per_line = int(bits_per_line)
                self.code = code

            def __str__(self):
                return f"Resolution: h_dpi {self.hor_dpi} (max {self.max_hor_dots}), v_dpi {self.vert_dpi}, bpl {self.bits_per_line}" # (code {self.code})"

        # Hardcoded to 80mm paper currently
        SD_8 = Resolution(hor_dpi=90, max_hor_dots=256, vert_dpi=60, bits_per_line=8, code=0)
        DD_8 = Resolution(hor_dpi=180, max_hor_dots=512, vert_dpi=60, bits_per_line=8, code=1)
        SD_24 = Resolution(hor_dpi=90, max_hor_dots=256, vert_dpi=180, bits_per_line=24, code=32)
        DD_24 = Resolution(hor_dpi=180, max_hor_dots=512, vert_dpi=180, bits_per_line=24, code=33)


        def __init__(self,
                     image : str,   # or may be ByteIO
                     resolution : Resolution = DD_8,
                     desired_width_ratio = 1,
                     modify_contrast = None,
                     modify_brightness = None,
                     export_generated_image = False):
            desired_width = int(resolution.max_hor_dots * desired_width_ratio)
            height_stretch_ratio = resolution.hor_dpi / resolution.vert_dpi # higher number for higher stretching
            if isinstance(image, str):
                self.name = image
            else:
                self.name = type(image)
            print (f"Image: Opening {self.name}")

            img = PIL.Image.open(image) # open colour image

            if Printer.Image.has_transparency(img):
                print (f"Image has transparency. Replacing that with white.")
                white_bg = PIL.Image.new("RGBA", img.size, "WHITE") # Create a white rgba background
                white_bg.paste(img, (0, 0), img)
                img = white_bg

            if modify_contrast:
                print (f"Applying image correction: contrast: {modify_contrast}")
                img = PIL.ImageEnhance.Contrast(img).enhance(modify_contrast)
            if modify_brightness:
                print (f"Applying image correction: brightness: {modify_brightness}")
                img = PIL.ImageEnhance.Brightness(img).enhance(modify_brightness)

            wpercent = (desired_width / float(img.size[0]))
            hsize = int(img.size[1] * wpercent / height_stretch_ratio)
            scaled_size = (desired_width, hsize)
            print (f"Image: {resolution}")
            print (f"Image: Scaling from {img.size} to {scaled_size}")
            img = img.resize(scaled_size, PIL.Image.Resampling.LANCZOS)
            img = img.convert('1') # convert image to black and white
            if export_generated_image:
                img.save(f'intended_image_{os.path.basename(image)}.png')

            self.resolution = resolution
            self.img = img

    def printImage(self, image : Image, ugly_workaround = False):
        # ASCII ESC * m nL nH d1 ... dk

        def forbidden_byte(byte) -> bool:
            # (allowed byte) return byte > 6 or byte < 4 produces working result
            # (allowed byte) len(self.stream) % 3 != 1 or byte > 6 or byte < 4
            return byte <= 6 and byte >= 4

        class Bitconsumer:

            def resetByte(self):
                self.byteoffs = 0
                self.currentByte = 0

            def __init__(self):
                self.stream = bytearray()
                self.resetByte()

            def finishByte(self):
                # DEBUG
                if ugly_workaround and forbidden_byte(self.currentByte):
                    print (f"MODIFYING A BYTE for ugly workaround {self.currentByte:02x} -> ", end="")
                    self.currentByte <<= 1
                    print (f"{self.currentByte:02x}")
                self.stream.append(self.currentByte)
                self.resetByte()

            def consume(self, bit):
                # Populates MSB first!
                self.currentByte |= (bit & 1) << (7 - self.byteoffs)
                self.byteoffs += 1
                if (self.byteoffs == 8):
                    self.finishByte()

            def getBytes(self):
                if self.byteoffs != 0:
                    print ("warn: unfinished byte")
                    self.finishByte()
                return self.stream

        BASE = bytes([ord(escape), ord('*')])

        # self.print(Unidirectional(True))    # is suggested to avoid spacings between lines, but has no effect
        # If graphics data includes a data string matching DLE DC4 (fn = 1 or 2),
        # it is recommended to use this command in advance to disable the Real-time commands. (DUH!!!)
        self.enableRealtimeCommands(False)

        num_horizontal_dots = image.img.size[0]
        num_vertical_dots = image.img.size[1]
        needed_rows = num_vertical_dots / image.resolution.bits_per_line

        page = None
        if image.resolution.vert_dpi > 100:
            # It seems that the printer needs page mode to not produce fine gaps in "high density" mode
            print (f"Activating page mode for high-density image")
            error = .5
            size_hor_mm = (num_horizontal_dots + error) / image.resolution.hor_dpi * MM_PER_INCH
            mm_per_row = ((image.resolution.bits_per_line + error) / image.resolution.vert_dpi) * MM_PER_INCH
            # .. page mode needs rounding up to full row
            size_vert_mm = math.ceil(needed_rows) * mm_per_row
            page = self.setupPage(size_hor_mm=size_hor_mm, size_vert_mm=size_vert_mm,
                                  mm_per_row=mm_per_row, resolution= (1 / image.resolution.vert_dpi) * MM_PER_INCH)

        base_y = 0
        while base_y < num_vertical_dots:
            this_line_valid_bits = min(image.resolution.bits_per_line, num_vertical_dots - base_y)
            this_line_overflow_bits = image.resolution.bits_per_line - this_line_valid_bits
            current_row_nr = int(base_y / image.resolution.bits_per_line)
            print (f"sending image row {current_row_nr + 1} of {needed_rows} ({num_horizontal_dots} hor dots, {this_line_valid_bits} vert dots", end='')
            if this_line_overflow_bits > 0:
                print(f", filling blank {this_line_overflow_bits} dots)")
            else:
                print(")")

            stream = Bitconsumer()
            for x in range(num_horizontal_dots):
                for offs_y in range(this_line_valid_bits):
                    coord = (x, base_y + offs_y)
                    px = (~image.img.getpixel(coord)) & 1
                    stream.consume(px)
                for _ in range(this_line_overflow_bits):
                    stream.consume(0)

            assert(len(stream.getBytes()) == num_horizontal_dots * (image.resolution.bits_per_line / 8))

            self.send(BASE, bytes([image.resolution.code]), bigEndian(num_horizontal_dots, width_bytes=2),
                      stream.getBytes())
            base_y += image.resolution.bits_per_line

            if page:
                page.nextRow()
            else:
                # FIXME: Find out why "zero" is also ok instead of mm_per_line
                self.feed(mm=0)

        if page:
            page.finalizePrint()

        self.resetFormatting()

    def feed(self, times = 1, mm = 1, motionUnits = None):
        actual_motion_units = None
        if motionUnits:
            actual_motion_units = motionUnits
        else:
            actual_motion_units = mm * self.getCurrentMotionUnitPerMM()[1]

        self.print(escape + 'J' + chr(int(round(times * actual_motion_units))))


    def cut(self, type = defaultCut.FEED_CUT()):
        self.print(type)

    def print(self, *argv, echo= False):
        for string in argv:
            if echo:
                if string.isprintable:
                    print (string)
                else:
                    for b in string:
                        print (f"{b:02X} ", end='')
                    print()
            self.socket.sendall(string.encode(self.encoding))

    def send(self, *argv, echo = False):
        # print (f"send({[len(arg) for arg in argv]})")
        maxPrintBinLen = 2000
        for binary in argv:
            if echo:
                for b in binary[:maxPrintBinLen]:
                    print (f"{b:02X} ", end='')
                print ("..." if len(binary) > maxPrintBinLen else "")
            self.socket.sendall(binary)

    def println(self, *argv):
        self.print(*argv, "\n")

    # TODO: Get this "status" group somewhat encapsulated

    class Status():
        def __init__(self, byte):
            self.byte = byte

        def __str__(self):
            msg = f"{self.byte:08b} -> "
            if self.byte & 0b11 != 0b10:
                msg += " Fixed bytes incorrect!"
            return msg

    class General(Status):
        VALUE = 1

        def getKickout(self) -> bool:
            return self.byte & 0x04

        def isOnline(self) -> bool:
            return self.byte & 0x08

        def __str__(self):
            msg = super().__str__()
            msg += "GENERAL:"
            msg += "\n\tkickout: "
            msg += "high" if self.getKickout() else "low"
            msg += "\n\tonline: "
            msg += "yes" if self.isOnline() else "no"
            return msg

    class Offline(Status):
        VALUE = 2
        # TODO
        def __str__(self):
            return super().__str__() + "Offline cause TODO"

    class Error(Status):
        VALUE = 3
        # TODO
        def __str__(self):
            return super().__str__() + "Error cause TODO"

    class Paper(Status):
        VALUE = 4

        def isNearEnd(self) -> bool:
            return self.byte & 0x04

        def isPresent(self) -> bool:
            return self.byte & 0x40

        def __str__(self):
            msg = super().__str__()
            msg += "Paper Roll status."
            msg += "\n\tNear-End Sensor: "
            msg += "near-end" if self.isNearEnd() else "adequate"
            msg += "\n\tActual End Sensor: paper "
            msg += "not present" if self.isPresent() else "present"
            return msg

    def getStatus(self, requested_stati : list[object] = None) -> dict[object, Status]:
        BASE = bytes([16, 4])

        def getSingle(type : object) -> Printer.Status:

            self.socket.sendall(BASE + bytes([type.VALUE]))
            response = self.socket.recv(1)[0]
            return type(response)

        self.enableRealtimeCommands(True) # this is a realtime-command.

        if not requested_stati:
            requested_stati = [
                Printer.General,
                Printer.Paper
            ]
        return {s : getSingle(s) for s in requested_stati}

    def enableRealtimeCommands(self, enable = True):
        # This resets at ESC @.
        BASE = bytes([0x1D, ord("("), ord("D")])
        m = bytes([0x14]) # don't ask me why it is that way! Documentation says nothing about it.
        types = {
            "GENERATE_PULSE": 1,
            "POWER_OFF_SEQUENCE": 2,
            # no more in T88IV
        }
        onoff = 1 if enable else 0

        payload = bytearray()
        for val in types.values():
            payload.append(val)
            payload.append(onoff)


        encoded_len = bigEndian(1 + len(payload), width_bytes=2) # + 1 because of "m"
        self.send(BASE, encoded_len, m, payload)


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
