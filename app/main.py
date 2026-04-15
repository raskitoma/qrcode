from flask import Flask, render_template, request
import os
from qrcoderesponse import qrcoderesponse

MAX_QR_TEXT_LENGTH = 2048
MAX_LOGO_BYTES = 2 * 1024 * 1024

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)
app.config.setdefault("MAX_QR_TEXT_LENGTH", MAX_QR_TEXT_LENGTH)
app.config.setdefault("MAX_CONTENT_LENGTH", MAX_LOGO_BYTES)


@app.route("/")
def show_form():
    logo_dark = os.getenv("LOGO_DARK_URL", "/img/rask_logo-white.svg")
    logo_light = os.getenv("LOGO_LIGHT_URL", "/img/rask_logo-black.svg")
    return render_template("index.html", logo_dark=logo_dark, logo_light=logo_light)


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

    logo_file = request.files.get("logo")
    logo_scale = request.values.get("logo_scale", 15)
    fg_color = request.values.get("fg_color", "#000000")
    bg_color = request.values.get("bg_color", "#ffffff")
    drawer = request.values.get("drawer", "square")

    return qrcoderesponse(
        text, 
        logo_file=logo_file, 
        logo_scale=logo_scale,
        fg_color=fg_color,
        bg_color=bg_color,
        drawer_name=drawer
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
