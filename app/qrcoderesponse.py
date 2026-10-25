import io
import os
import re
from PIL import Image
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
    from lxml import etree
    from svglib.svglib import SvgRenderer
    from reportlab.graphics import renderPM
except ImportError:
    etree = None
    SvgRenderer = None
    renderPM = None

DEFAULT_PIXEL_WIDTH = 20
DEFAULT_FG_COLOR = "#000000"
DEFAULT_BG_COLOR = "#ffffff"
MIN_PIXEL_WIDTH = 1
MAX_PIXEL_WIDTH = 100
DEFAULT_LOGO_SCALE = 12
MIN_LOGO_SCALE = 5
MAX_LOGO_SCALE = 15
MAX_LOGO_IMAGE_PIXELS = 4096 * 4096

HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")
DISALLOWED_SVG_TAGS = {"script", "foreignobject", "image", "feimage", "iframe", "object", "embed"}


def _pixel_width_from_env():
    raw_value = os.getenv("PIXEL_WIDTH")
    if raw_value is None:
        return DEFAULT_PIXEL_WIDTH
    try:
        pixel_width = int(raw_value)
    except ValueError:
        return DEFAULT_PIXEL_WIDTH
    return max(MIN_PIXEL_WIDTH, min(MAX_PIXEL_WIDTH, pixel_width))


def _normalized_hex_color(color_value, fallback=DEFAULT_FG_COLOR):
    if not isinstance(color_value, str):
        return fallback
    cleaned = color_value.strip()
    if not HEX_COLOR_RE.match(cleaned):
        return fallback
    return f"#{cleaned.lstrip('#').lower()}"


PIXEL_WIDTH = _pixel_width_from_env()
FG_COLOR = _normalized_hex_color(os.getenv("FG_COLOR"), DEFAULT_FG_COLOR)
BG_COLOR = _normalized_hex_color(os.getenv("BG_COLOR"), DEFAULT_BG_COLOR)


def _normalized_logo_scale(scale_value):
    try:
        scale = int(scale_value)
    except (TypeError, ValueError):
        return DEFAULT_LOGO_SCALE
    return max(MIN_LOGO_SCALE, min(MAX_LOGO_SCALE, scale))


def hex_to_rgb(hex_color, fallback=DEFAULT_FG_COLOR):
    normalized = _normalized_hex_color(hex_color, fallback=fallback).lstrip("#")
    return tuple(int(normalized[i:i+2], 16) for i in (0, 2, 4))


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


def _safe_load_svg_drawing(logo_file, target_size):
    if not (etree and SvgRenderer and renderPM):
        return None

    if hasattr(logo_file, "seek"):
        logo_file.seek(0)
    raw_svg = logo_file.read()
    if isinstance(raw_svg, str):
        raw_svg = raw_svg.encode("utf-8")

    # Reject DOCTYPE / ENTITY declarations to prevent XXE or billion-laughs payloads
    upper_head = raw_svg[:4096].upper()
    if b"<!DOCTYPE" in upper_head or b"<!ENTITY" in upper_head:
        raise ValueError("Unsafe SVG declarations are not allowed")

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        dtd_validation=False,
        load_dtd=False,
        huge_tree=False,
        remove_comments=True,
        recover=False,
    )
    svg_root = etree.fromstring(raw_svg, parser=parser)

    for elem in svg_root.iter():
        if not isinstance(elem.tag, str):
            continue
        local_name = elem.tag.split("}")[-1].lower()
        if local_name in DISALLOWED_SVG_TAGS:
            raise ValueError(f"Disallowed SVG element: {local_name}")
        for attr_name, attr_val in elem.attrib.items():
            attr_local = attr_name.split("}")[-1].lower()
            if attr_local in ("href", "xlink:href") or attr_name.endswith("href"):
                val = attr_val.strip()
                if val and not val.startswith("#"):
                    raise ValueError("External SVG references are not allowed")

    renderer = SvgRenderer(path=io.BytesIO())
    drawing = renderer.render(svg_root)
    if drawing is None or drawing.width <= 0 or drawing.height <= 0:
        return None

    # Scale drawing bounds before rasterizing to prevent large canvas memory exhaustion
    max_dim = max(drawing.width, drawing.height)
    render_target = max(64, target_size * 2)
    if max_dim > 0:
        scale_factor = render_target / float(max_dim)
        drawing.width *= scale_factor
        drawing.height *= scale_factor
        drawing.scale(scale_factor, scale_factor)

    return drawing


def _add_center_logo(qr_image, logo_file, logo_scale, bg_color=DEFAULT_BG_COLOR):
    qr_image = qr_image.convert("RGBA")
    qr_width, qr_height = qr_image.size
    target_ratio = _normalized_logo_scale(logo_scale) / 100
    target_size = max(32, int(min(qr_width, qr_height) * target_ratio))

    try:
        is_svg = getattr(logo_file, "filename", "").lower().endswith(".svg")
        if is_svg and SvgRenderer and renderPM:
            drawing = _safe_load_svg_drawing(logo_file, target_size)
            if drawing is None:
                return qr_image.convert("RGB")
            logo_png = io.BytesIO()
            renderPM.drawToFile(drawing, logo_png, fmt="PNG")
            logo_png.seek(0)
            logo = Image.open(logo_png).convert("RGBA")
        else:
            if hasattr(logo_file, "seek"):
                logo_file.seek(0)
            with Image.open(logo_file) as opened_logo:
                if opened_logo.width * opened_logo.height > MAX_LOGO_IMAGE_PIXELS:
                    raise ValueError("Logo image dimensions exceed maximum allowed size")
                logo = opened_logo.convert("RGBA")
    except Exception:
        # Fallback: if SVG fails or Pillow doesn't support, we skip the logo part
        return qr_image.convert("RGB")

    logo.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

    padding = max(4, target_size // 12)  # Reduced padding
    bg_rgb = hex_to_rgb(bg_color, fallback=BG_COLOR)
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
               fg_color=None, bg_color=None,
               drawer_name='square'):
    resolved_fg = _normalized_hex_color(fg_color, fallback=FG_COLOR)
    resolved_bg = _normalized_hex_color(bg_color, fallback=BG_COLOR)

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
            back_color=hex_to_rgb(resolved_bg, fallback=BG_COLOR),
            front_color=hex_to_rgb(resolved_fg, fallback=FG_COLOR)
        )
    ).convert("RGB")

    if logo_file and getattr(logo_file, "filename", ""):
        img = _add_center_logo(img, logo_file, logo_scale, bg_color=resolved_bg)

    return img


def qrcoderesponse(text, **kwargs):
    return imagetoresponse(makeqrcode(text, **kwargs))
