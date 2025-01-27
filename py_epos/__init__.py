from .printer import *
import socket
from datetime import datetime
import argparse

densities = {
    'sd8' : Printer.Image.SD_8,
    'dd8' : Printer.Image.DD_8,
    'sd24' : Printer.Image.SD_24,
    'dd24' : Printer.Image.DD_24,
}

def printImage():
    parser = argparse.ArgumentParser("eposprint")
    parser.add_argument("image", help="The image to print", type=str)
    parser.add_argument("ip", help="IP address", type=str)
    parser.add_argument("port", help="EPOS TCP/IP Port", type=int, default=9100, nargs='?')

    parser.add_argument('--density',
                            help='The bit resolution density.',
                            choices=densities.keys(),
                            default='dd24')

    args = parser.parse_args()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    img = Printer.Image(args.image, resolution=densities[args.density])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.ip, args.port))
        p = Printer(s)
        p.println(SMALLFONT, Just.CENTER, now)
        p.println(BIGFONT, img.name)
        p.feed()
        p.printImage(img)
        p.cut()

# TODO: interactive!