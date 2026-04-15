import io
import os
from PIL import Image, ImageOps
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer
)
from qrcode.image.styles.colormasks import SolidFillColorMask
from flask import send_file

# Optional SVG support
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
except ImportError:
    svg2rlg = None

DEFAULT_PIXEL_WIDTH = 20
DEFAULT_FG_COLOR = "#000000"
DEFAULT_BG_COLOR = "#ffffff"
MIN_PIXEL_WIDTH = 1
MAX_PIXEL_WIDTH = 100
DEFAULT_LOGO_SCALE = 12
MIN_LOGO_SCALE = 5
MAX_LOGO_SCALE = 15

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

def _normalized_logo_scale(scale_value):
    try:
        scale = int(scale_value)
    except (TypeError, ValueError):
        return DEFAULT_LOGO_SCALE
    return max(MIN_LOGO_SCALE, min(MAX_LOGO_SCALE, scale))

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_module_drawer(drawer_name):
    drawers = {
        'square': SquareModuleDrawer(),
        'gapped': GappedSquareModuleDrawer(),
        'circle': CircleModuleDrawer(),
        'rounded': RoundedModuleDrawer(),
        'vertical': VerticalBarsDrawer(),
        'horizontal': HorizontalBarsDrawer()
    }
    return drawers.get(drawer_name, SquareModuleDrawer())

def imagetoresponse(img):
    img_file = io.BytesIO()
    img.save(img_file, format="PNG")
    img_file.seek(0)
    return send_file(img_file, mimetype="image/png")

def _add_center_logo(qr_image, logo_file, logo_scale, bg_color="#ffffff"):
    qr_image = qr_image.convert("RGBA")
    try:
        # Check if it's an SVG and we have libraries
        is_svg = getattr(logo_file, "filename", "").lower().endswith(".svg")
        if is_svg and svg2rlg:
            drawing = svg2rlg(logo_file)
            logo_png = io.BytesIO()
            renderPM.drawToFile(drawing, logo_png, fmt="PNG")
            logo_png.seek(0)
            logo = Image.open(logo_png).convert("RGBA")
        else:
            logo = Image.open(logo_file).convert("RGBA")
    except Exception:
        # Fallback: if SVG fails or Pillow doesn't support, we skip the logo part
        return qr_image.convert("RGB")

    qr_width, qr_height = qr_image.size
    target_ratio = _normalized_logo_scale(logo_scale) / 100
    target_size = max(32, int(min(qr_width, qr_height) * target_ratio))

    logo.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

    padding = max(4, target_size // 12)  # Reduced padding
    bg_rgb = hex_to_rgb(bg_color)
    background = Image.new(
        "RGBA",
        (logo.width + (padding * 2), logo.height + (padding * 2)),
        (*bg_rgb, 255),
    )
    
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

def makeqrcode(text, logo_file=None, logo_scale=DEFAULT_LOGO_SCALE, 
               fg_color=DEFAULT_FG_COLOR, bg_color=DEFAULT_BG_COLOR,
               drawer_name='square'):
    
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=PIXEL_WIDTH,
        border=2,  # Reduced border
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    # Advanced styling using StyledPilImage
    # (Removed eye_drawer as it's missing in some installations)
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=get_module_drawer(drawer_name),
        color_mask=SolidFillColorMask(
            back_color=hex_to_rgb(bg_color),
            front_color=hex_to_rgb(fg_color)
        )
    ).convert("RGB")

    if logo_file and getattr(logo_file, "filename", ""):
        img = _add_center_logo(img, logo_file, logo_scale, bg_color=bg_color)

    return img

def qrcoderesponse(text, **kwargs):
    return imagetoresponse(makeqrcode(text, **kwargs))
