from py_epos.printer import *
from datetime import datetime
from random import random
import socket

HOST = "192.168.0.250"
PORT = 9100  # The port used by the server

# datetime object containing current date and time
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

an_img = Printer.Image("cat.png")
other_img = Printer.Image("cat_2.png")

lorem = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet."

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    p = Printer(s)

    # p.feed(times=2)
    # p.print(Just.CENTER)
    # p.println(BIGFONT, "Geburtstagsgrüße")
    # p.println(BIGFONT, "RIEBE / PIEPER")
    # p.feed()
    p.println(SMALLFONT, Just.CENTER, now)
    p.println(BIGFONT, an_img.name)
    p.feed()
    p.println(SMALLFONT, str(an_img.resolution))
    p.feed()
    p.resetFormatting()
    p.printImage(an_img)

    p.feed()
    p.println(lorem)
    p.feed(times=2)

    p.printImage(other_img)

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


    p.print(Just.CENTER, Barcode.Setup() + Barcode.send("PIMMEL"))
    p.feed(times= 2)

    p.print(defaultCut.FEED_CUT())
    s.close()