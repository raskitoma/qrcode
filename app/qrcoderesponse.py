import io
import os

import qrcode
from flask import send_file

# Set default settings
PIXEL_WIDTH = 50
FG_COLOR = "#000000"
BG_COLOR = "#ffffff"

# Override settings with enviroment variables
if os.getenv("BG_COLOR"):
  BG_COLOR = os.getenv("BG_COLOR")
if os.getenv("FG_COLOR"):
  FG_COLOR = os.getenv("FG_COLOR")
if os.getenv("PIXEL_WIDTH"):
  try:
    PIXEL_WIDTH = int(os.getenv("PIXEL_WIDTH"))
  except ValueError:
    pass

def imagetoresponse(img):
  file = io.BytesIO()
  img.save(file, format="PNG")
  file.seek(0)
  return send_file(file, mimetype="image/png")

def makeqrcode(text):
  qr = qrcode.QRCode(
    version = 1,
    box_size = PIXEL_WIDTH,
    border = 4
  )
  qr.add_data(text)
  return qr.make_image(fill_color=FG_COLOR, back_color=BG_COLOR)
  
def qrcoderesponse(text):
  return imagetoresponse(makeqrcode(text))
