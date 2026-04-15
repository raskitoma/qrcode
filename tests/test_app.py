import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
APP_DIR = os.path.join(ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from main import app  # noqa: E402
from qrcoderesponse import DEFAULT_LOGO_SCALE, MAX_LOGO_SCALE, _normalized_logo_scale  # noqa: E402


class QRCodeAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_root_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"QRCode contents:", response.data)

    def test_qr_requires_text(self):
        response = self.client.get("/qr")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"No text parameter", response.data)

    def test_qr_rejects_blank_text(self):
        response = self.client.get("/qr?text=   ")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Text parameter cannot be empty", response.data)

    def test_qr_rejects_too_long_text(self):
        response = self.client.get("/qr", query_string={"text": "a" * 2049})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Text parameter is too long", response.data)

    def test_qr_returns_png_for_valid_text(self):
        response = self.client.get("/qr", query_string={"text": "hello world"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/png")
        self.assertTrue(response.data.startswith(b"\x89PNG"))

    def test_logo_scale_is_clamped_to_maximum(self):
        self.assertEqual(_normalized_logo_scale("999"), MAX_LOGO_SCALE)

    def test_logo_scale_uses_new_default(self):
        self.assertEqual(_normalized_logo_scale(None), DEFAULT_LOGO_SCALE)


if __name__ == "__main__":
    unittest.main()
