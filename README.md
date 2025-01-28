Python bosed Epson-EPOS libary
==============================

Current state:
--------------

Quickly hacked-together EPOS over IP generator. Can send basic formatted text and Graphics using Python Pillow.

Can send graphics up to 180x180 dpi, but it seems that my specific printer (TM-T88IV) sometimes glitches in 3-byte mode.

Can be used and installed via `pip install .`
Currently, it will create an executable `eposprint` which can directly print images to the thermo printer.
Interactive printing possible with `ipython` and similar terminals.

![20250126_175319](https://github.com/user-attachments/assets/e49a3bb3-e70b-4057-a594-f2bd6ed74cdf)


Future Ideas:
-------------
- Live writing
- Markdown converter
- Linux Terminal forwarding?
