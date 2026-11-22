import base64
import io
import unittest

from PIL import Image

from rxbondhu.camera import decode_capture


class TestCameraDecode(unittest.TestCase):
    def test_decodes_jpeg_data(self):
        buffer = io.BytesIO()
        Image.new("RGB", (16, 10), "green").save(buffer, format="JPEG")
        value = base64.b64encode(buffer.getvalue()).decode("ascii")
        image = decode_capture(value)
        self.assertIsNotNone(image)
        self.assertEqual(image.size, (16, 10))

    def test_invalid_value_returns_none(self):
        self.assertIsNone(decode_capture(None))
        self.assertIsNone(decode_capture("not-base64"))


if __name__ == "__main__":
    unittest.main()
