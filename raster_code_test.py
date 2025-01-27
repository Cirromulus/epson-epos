#!/usr/bin/python

from py_epos.printer import *
from datetime import datetime
from random import random
import socket

HOST = "192.168.0.250"
PORT = 9100  # The port used by the server

# datetime object containing current date and time
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

pattern = [0xFF, 0xAA, 0x55]
data_cols = 3
data = bytes(pattern * data_cols)
print (data)

def send(printer : Printer, code : int):
        ESC = 0x1B
        BASE = bytes([ESC, ord('*')])
        printer.println(SMALLFONT, f"Testpattern code {code}:")
        message = bytearray()
        message += BASE
        message.append(code)
        message += bigEndian(data_cols, width_bytes=2)
        message += data
        print ("message: ", end='')
        for b in message:
             print (f"{b:02X} ", end='')
        print()
        printer.send(message)
        printer.feed(mm=5)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    p = Printer(s)

    for code in [0, 1, 32, 33]:
        send(p, code)

    p.print(defaultCut.FEED_CUT())
    s.close()