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
    parser = argparse.ArgumentParser(
            prog="eposprint",
            description="Sends Images in different formats to Epson EPOS printers through TCP",
            epilog="Sometimes, in 24 bit mode, image transmission gets corrupted and it gets only filled into page mode, without printing the buffer. I really don't know how this happens. It seems that if sometimes, some of the triplet bytes, is between 4 and 6, thransmission errors happen. Or something. Perhaps it is a Page-Mode bug? Without page mode, we have tiny gaps between columns. I am just glad that all tested images work with that workaround, and it is not a huge impact on quality. Don't hate me, I am just a program")

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

    parser.add_argument('--workaround-24-bug',
                        help="If you experience non- or half printing images in 24 bit mode, turn this on. It modifies the byte stream to avoid problematic sequences (...?)",
                        action='store_true',
                        )

    parser.add_argument('--no-cut',
                        help="Disable cutting after finished print",
                        action='store_true',
                        )

    parser.add_argument('--brightness',
                        help="Change brightness as ratio. '1' results in no effect.",
                        type=float,
                        nargs="?",
                        )

    parser.add_argument('--contrast',
                        help="Change contrast as ratio. '1' results in no effect.",
                        type=float,
                        nargs="?",
                        )

    parser.add_argument('--extra-text',
                        type=str,
                        nargs="*",
                        help='Print extra text after image. Will newline for every quoted group of text, i.e. 123 "345 678" will produce two lines.')

    args = parser.parse_args()

    if args.workaround_24_bug and "24" not in args.density:
        parser.error(f"Ugly workaround only applies to 24 bit transmissions. You have chosen {args.density}.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    img = Printer.Image(args.image,
                        resolution=densities[args.density],
                        modify_contrast=args.contrast,
                        modify_brightness=args.brightness)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.ip, args.port))
        p = Printer(s)
        if not args.no_header:
            p.println(SMALLFONT, Just.CENTER, now)
            p.println(BIGFONT, img.name)
            p.feed()
        p.printImage(img, ugly_workaround=args.workaround_24_bug)
        if args.extra_text:
            for line in args.extra_text:
                p.println(Just.CENTER, line)
        if not args.no_cut:
            p.cut()

# TODO: interactive!