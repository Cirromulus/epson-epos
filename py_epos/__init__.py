from .printer import *
import socket
from datetime import datetime
import argparse
from sys import stdin
from wand.image import Image as wimage
from io import BytesIO
from os import path

densities = {
    'sd8' : Printer.Image.SD_8,
    'dd8' : Printer.Image.DD_8,
    'sd24' : Printer.Image.SD_24,
    'dd24' : Printer.Image.DD_24,
}

def addDefaultArguments(parser: argparse.ArgumentParser):
    parser.add_argument("ip", help="IP address", type=str)
    parser.add_argument("port", help="EPOS TCP/IP Port", type=int, default=9100, nargs='?')

    parser.add_argument('--density',
                            help='The bit resolution density.',
                            choices=densities.keys(),
                            default='dd24')

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

def printImage():
    parser = argparse.ArgumentParser(
            prog="eposprint",
            description="Sends Images in different formats to Epson EPOS printers through TCP")

    addDefaultArguments(parser)

    parser.add_argument("file", help="The image / PDF to print", type=str, nargs='+')

    parser.add_argument('--no-header',
                        help="Disable printing name and date",
                        action='store_true',
                        )

    parser.add_argument('--no-workaround-24-bug',
                        help="Sometimes, in 24 bit mode, image transmission gets corrupted and it gets only filled into page mode without printing the buffer. I really don't know how this happens. It seems that if sometimes, some of the triplet bytes, is between 4 and 6, thransmission errors happen. Or something. Perhaps it is a Page-Mode bug? Without page mode, we have tiny gaps between columns. I am just glad that all tested images work with that workaround, and it is not a huge impact on quality. Don't hate me, I am just a program",
                        action='store_true'
                        )

    parser.add_argument('--extra-text',
                        type=str,
                        nargs="*",
                        help='Print extra text after image. Will newline for every quoted group of text, i.e. 123 "345 678" will produce two lines.')

    parser.add_argument('--auto-rotate',
                        action='store_true',
                        help='Rotate images to always be in portrait mode to increase print size')

    args = parser.parse_args()

    actually_workaround_24_bug = "24" in args.density
    if not args.no_workaround_24_bug:
        actually_workaround_24_bug = False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    images = []

    for imagepath in args.file:
        if imagepath.endswith('.pdf'):
            with wimage(filename=imagepath,
                        resolution=(densities[args.density].hor_dpi, densities[args.density].vert_dpi),
                        ) as img:
                for i, page in enumerate(img.sequence):
                    page_rendered = wimage(page).make_blob(format="png")

                    # with open("page.png", "wb") as f:
                    #     f.write(BytesIO(page_rendered).getbuffer())
                    
                    images.append(Printer.Image(BytesIO(page_rendered),
                                resolution=densities[args.density],
                                modify_contrast=args.contrast,
                                modify_brightness=args.brightness,
                                name=path.basename(imagepath + f"_{i}")))
        else:
            image = PIL.Image.open(imagepath)
            if args.auto_rotate and image.size[0] > image.size[1]:
                print ("Image is landscape, auto-rotating for portrait")
                image = image.rotate(90, expand=True)
            images.append(Printer.Image(image,
                                resolution=densities[args.density],
                                modify_contrast=args.contrast,
                                modify_brightness=args.brightness))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.ip, args.port))
        p = Printer(s)
        if not args.no_header:
            p.println(SMALLFONT, Just.CENTER, now)
            for file in args.file:
                p.println(BIGFONT, path.basename(file))
            p.feed()

        for img in images:
            p.printImage(img, ugly_workaround=actually_workaround_24_bug)
        if args.extra_text:
            for line in args.extra_text:
                p.println(Just.CENTER, line)
        if not args.no_cut:
            p.cut()

def interactiveText():
    parser = argparse.ArgumentParser(
            prog="epostext",
            description="\"Typesets\" text to Epson EPOS printers through TCP")
    
    addDefaultArguments(parser)

    parser.add_argument('--font',
                help="Font type. A is bigger than B.",
                choices=['A', 'B'],
                default='A'
                )
  
    args = parser.parse_args()
    font = Font.FONT_A
    if args.font.lower() == 'b':
        font = Font.FONT_B

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.ip, args.port))
        p = Printer(s)

        print ("Connected. Exit with Ctrl-D.")

        for line in stdin:
            p.typeSet(line.rstrip(), font=font)

        if not args.no_cut:
            p.cut()
