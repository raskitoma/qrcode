from flask import Flask, render_template, request
from qrcoderesponse import qrcoderesponse

MAX_QR_TEXT_LENGTH = 2048

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)
app.config.setdefault("MAX_QR_TEXT_LENGTH", MAX_QR_TEXT_LENGTH)


@app.route("/")
def show_form():
    return render_template("index.html")


@app.route("/qr")
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

    return qrcoderesponse(text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
