import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
APP_DIR = os.path.join(ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from main import app  # noqa: E402
from qrcoderesponse import (  # noqa: E402
    DEFAULT_LOGO_SCALE,
    MAX_LOGO_SCALE,
    _normalized_logo_scale,
    _safe_load_svg_drawing,
)


class QRCodeAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_root_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"QR Code Generator", response.data)
        self.assertIn(b"QR Content", response.data)
        self.assertIn(b'rel="noopener noreferrer"', response.data)

    def test_security_headers_are_set(self):
        response = self.client.get("/")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("default-src 'self'", response.headers.get("Content-Security-Policy", ""))

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

    def test_qr_rejects_invalid_color_parameters(self):
        response = self.client.get("/qr", query_string={"text": "hello", "fg_color": "not-a-color"})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid color parameter", response.data)

    def test_qr_returns_png_for_valid_text(self):
        response = self.client.get("/qr", query_string={"text": "hello world"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/png")
        self.assertTrue(response.data.startswith(b"\x89PNG"))

    def test_logo_scale_is_clamped_to_maximum(self):
        self.assertEqual(_normalized_logo_scale("999"), MAX_LOGO_SCALE)

    def test_logo_scale_uses_new_default(self):
        self.assertEqual(_normalized_logo_scale(None), DEFAULT_LOGO_SCALE)

    def test_svg_rejects_xxe_and_external_references(self):
        xxe_svg = io.BytesIO(
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><text>&xxe;</text></svg>'
        )
        with self.assertRaises(ValueError):
            _safe_load_svg_drawing(xxe_svg, 64)

        ext_ref_svg = io.BytesIO(
            b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            b'<use href="http://example.com/evil.svg#icon"/></svg>'
        )
        with self.assertRaises(ValueError):
            _safe_load_svg_drawing(ext_ref_svg, 64)

    def test_qr_accepts_valid_svg_logo(self):
        valid_svg = io.BytesIO(
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            b'<rect x="10" y="10" width="80" height="80" fill="#ff0000"/></svg>'
        )
        response = self.client.post(
            "/qr",
            data={
                "text": "https://raskitoma.com",
                "logo": (valid_svg, "logo.svg"),
                "logo_scale": "12",
                "fg_color": "#000000",
                "bg_color": "#ffffff",
                "drawer": "rounded",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/png")
        self.assertTrue(response.data.startswith(b"\x89PNG"))


if __name__ == "__main__":
    unittest.main()
