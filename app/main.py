from flask import Flask, render_template, request
import os
from urllib.parse import urlparse
from qrcoderesponse import (
    BG_COLOR,
    DEFAULT_LOGO_SCALE,
    FG_COLOR,
    HEX_COLOR_RE,
    qrcoderesponse,
)

MAX_QR_TEXT_LENGTH = 2048
MAX_LOGO_BYTES = 2 * 1024 * 1024
DEFAULT_LOGO_DARK_URL = "/img/rask_logo-white.svg"
DEFAULT_LOGO_LIGHT_URL = "/img/rask_logo-black.svg"

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)
app.config.setdefault("MAX_QR_TEXT_LENGTH", MAX_QR_TEXT_LENGTH)
app.config.setdefault("MAX_CONTENT_LENGTH", MAX_LOGO_BYTES)


def _safe_logo_url(raw_url, default_url):
    if not raw_url or not isinstance(raw_url, str):
        return default_url
    candidate = raw_url.strip()
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    parsed = urlparse(candidate)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return candidate
    return default_url


@app.after_request
def apply_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "img-src 'self' blob: data: https:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'",
    )
    return response


@app.route("/")
def show_form():
    logo_dark = _safe_logo_url(os.getenv("LOGO_DARK_URL"), DEFAULT_LOGO_DARK_URL)
    logo_light = _safe_logo_url(os.getenv("LOGO_LIGHT_URL"), DEFAULT_LOGO_LIGHT_URL)
    return render_template(
        "index.html",
        logo_dark=logo_dark,
        logo_light=logo_light,
        fg_color=FG_COLOR,
        bg_color=BG_COLOR,
    )


@app.route("/qr", methods=["GET", "POST"])
def generate_qrcode():
    text = request.values.get("text")

    if text is None:
        return "No text parameter", 400

    text = text.strip()
    if not text:
        return "Text parameter cannot be empty", 400

    max_length = app.config.get("MAX_QR_TEXT_LENGTH", MAX_QR_TEXT_LENGTH)
    if len(text) > max_length:
        return f"Text parameter is too long (max {max_length} characters)", 400

    fg_color = request.values.get("fg_color", FG_COLOR).strip()
    bg_color = request.values.get("bg_color", BG_COLOR).strip()
    if not HEX_COLOR_RE.match(fg_color) or not HEX_COLOR_RE.match(bg_color):
        return "Invalid color parameter (expected 6-digit hex color)", 400

    logo_file = request.files.get("logo")
    logo_scale = request.values.get("logo_scale", DEFAULT_LOGO_SCALE)
    drawer = request.values.get("drawer", "square")

    return qrcoderesponse(
        text,
        logo_file=logo_file,
        logo_scale=logo_scale,
        fg_color=fg_color,
        bg_color=bg_color,
        drawer_name=drawer,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
