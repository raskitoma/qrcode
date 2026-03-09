import io
import os

import qrcode
from flask import send_file

DEFAULT_PIXEL_WIDTH = 50
DEFAULT_FG_COLOR = "#000000"
DEFAULT_BG_COLOR = "#ffffff"
MIN_PIXEL_WIDTH = 1
MAX_PIXEL_WIDTH = 100


def _pixel_width_from_env():
    raw_value = os.getenv("PIXEL_WIDTH")
    if raw_value is None:
        return DEFAULT_PIXEL_WIDTH

    try:
        pixel_width = int(raw_value)
    except ValueError:
        return DEFAULT_PIXEL_WIDTH

    return max(MIN_PIXEL_WIDTH, min(MAX_PIXEL_WIDTH, pixel_width))


PIXEL_WIDTH = _pixel_width_from_env()
FG_COLOR = os.getenv("FG_COLOR", DEFAULT_FG_COLOR)
BG_COLOR = os.getenv("BG_COLOR", DEFAULT_BG_COLOR)


def imagetoresponse(img):
    img_file = io.BytesIO()
    img.save(img_file, format="PNG")
    img_file.seek(0)
    return send_file(img_file, mimetype="image/png")


def makeqrcode(text):
    qr = qrcode.QRCode(
        version=1,
        box_size=PIXEL_WIDTH,
        border=4,
    )
    qr.add_data(text)
    return qr.make_image(fill_color=FG_COLOR, back_color=BG_COLOR)


def qrcoderesponse(text):
    return imagetoresponse(makeqrcode(text))
