import io
import os

from PIL import Image, ImageOps
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from flask import send_file

DEFAULT_PIXEL_WIDTH = 12
DEFAULT_FG_COLOR = "#000000"
DEFAULT_BG_COLOR = "#ffffff"
MIN_PIXEL_WIDTH = 1
MAX_PIXEL_WIDTH = 100
DEFAULT_LOGO_SCALE = 20
MIN_LOGO_SCALE = 5
MAX_LOGO_SCALE = 30


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


def _normalized_logo_scale(scale_value):
    try:
        scale = int(scale_value)
    except (TypeError, ValueError):
        return DEFAULT_LOGO_SCALE

    return max(MIN_LOGO_SCALE, min(MAX_LOGO_SCALE, scale))


def imagetoresponse(img):
    img_file = io.BytesIO()
    img.save(img_file, format="PNG")
    img_file.seek(0)
    return send_file(img_file, mimetype="image/png")


def _add_center_logo(qr_image, logo_file, logo_scale):
    qr_image = qr_image.convert("RGBA")
    logo = Image.open(logo_file).convert("RGBA")

    qr_width, qr_height = qr_image.size
    target_ratio = _normalized_logo_scale(logo_scale) / 100
    target_size = max(32, int(min(qr_width, qr_height) * target_ratio))

    logo.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

    padding = max(8, target_size // 8)
    background = Image.new(
        "RGBA",
        (logo.width + (padding * 2), logo.height + (padding * 2)),
        (255, 255, 255, 255),
    )
    background = ImageOps.expand(background, border=0, fill=(255, 255, 255, 255))

    pos = (
        (background.width - logo.width) // 2,
        (background.height - logo.height) // 2,
    )
    background.alpha_composite(logo, dest=pos)

    offset = (
        (qr_width - background.width) // 2,
        (qr_height - background.height) // 2,
    )
    qr_image.alpha_composite(background, dest=offset)
    return qr_image.convert("RGB")


def makeqrcode(text, logo_file=None, logo_scale=DEFAULT_LOGO_SCALE):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=PIXEL_WIDTH,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    image = qr.make_image(fill_color=FG_COLOR, back_color=BG_COLOR).convert("RGB")

    if logo_file and getattr(logo_file, "filename", ""):
        image = _add_center_logo(image, logo_file, logo_scale)

    return image


def qrcoderesponse(text, logo_file=None, logo_scale=DEFAULT_LOGO_SCALE):
    return imagetoresponse(makeqrcode(text, logo_file=logo_file, logo_scale=logo_scale))
