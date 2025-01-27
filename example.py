#!/usr/bin/python

from py_epos.printer import *
from datetime import datetime
from random import random
import socket

HOST = "192.168.0.250"
PORT = 9100  # The port used by the server

# datetime object containing current date and time
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

path = "cat.png"
images = {
    "sd_8" : Printer.Image(path, resolution=Printer.Image.SD_8),
    "dd_8" : Printer.Image(path, resolution=Printer.Image.DD_8),
    "sd_24" : Printer.Image(path, resolution=Printer.Image.SD_24),
    "dd_24" : Printer.Image(path, resolution=Printer.Image.DD_24),
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    p = Printer(s)

    p.println(SMALLFONT, Just.CENTER, now)
    for (desc, img) in images.items():
        p.resetFormatting()
        print(desc, " ", img.resolution)
        p.println(SMALLFONT, desc, "  ", BIGFONT, img.name)
        p.println(SMALLFONT, str(img.resolution))
        p.printImage(img)
        p.feed()

    # p.println(Underline.ONE, "Zusammenfassung Geburtstagsgruß", Underline.NONE)
    # p.feed()

    # list = p.newList(BIGFONT)
    # list.addItem("Name", "Name Vorname")
    # list.addItem("Alter", "31")
    # list.addItem("Lieblingsfarbe", "Musik")
    # list.addItem("Nasenlöcher", "2")
    # list.addItem("Fernbedienungdinger", "0")
    # list.addItem("Schenkung", "Jetzt")
    # list.print()

    # p.feed(times=2)
    # p.print(SMALLFONT)
    # p.println("Lieber Name,")
    # p.feed()
    # p.println("Bla.")
    # p.feed()
    # p.println("Bla")

    # p.feed(times=2)

    # p.println("Es bediente Sie")
    # p.feed()
    # p.println("Freund 1 / Freund 2")


    # # p.println(SMALLFONT, Emph.ON, "Ronny hat kleine Hände", Emph.OFF)
    # p.println(Printer.WIDTH * "─")
    # p.println(Just.RIGHT, "... und darauf ist er auch noch ", Underline.TWO, "stolz", Underline.NONE, " ", Just.LEFT)
    # # p.println(DoubleStrike.ON, "double", DoubleStrike.OFF)
    # # p.println(Emph.ON, "emph", Emph.OFF)


    # p.print(Just.CENTER, Barcode.Setup() + Barcode.send("PIMMEL"))
    # p.feed(times= 2)

    p.print(defaultCut.FEED_CUT())
    s.close()