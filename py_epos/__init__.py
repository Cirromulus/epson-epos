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

    parser.add_argument('--no-header',
                        help="Disable printing name and date",
                        action='store_true',
                        )

    parser.add_argument('--no-cut',
                        help="Disable cutting after finished print",
                        action='store_true',
                        )

    parser.add_argument('--extra-text',
                        type=str,
                        nargs="*",
                        help='Print extra text after image. Will newline for every quoted group of text, i.e. 123 "345 678" will produce two lines.')

    args = parser.parse_args()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    img = Printer.Image(args.image, resolution=densities[args.density])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.ip, args.port))
        p = Printer(s)
        if not args.no_header:
            p.println(SMALLFONT, Just.CENTER, now)
            p.println(BIGFONT, img.name)
            p.feed()
        p.printImage(img)
        if args.extra_text:
            for line in args.extra_text:
                p.println(Just.CENTER, line)
        if not args.no_cut:
            p.cut()

# TODO: interactive!