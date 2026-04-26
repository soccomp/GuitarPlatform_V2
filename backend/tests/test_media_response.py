import tempfile
import unittest
from pathlib import Path

from services.media_response import media_file_response, parse_range_header


class DummyRequest:
    def __init__(self, headers):
        self.headers = headers


class MediaResponseTests(unittest.TestCase):
    def test_parse_range_header_bounds_open_ended_range(self):
        self.assertEqual(parse_range_header("bytes=5-", 12), (5, 11))

    def test_parse_range_header_bounds_suffix_range(self):
        self.assertEqual(parse_range_header("bytes=-4", 12), (8, 11))

    def test_range_response_supports_non_ascii_file_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            media_path = Path(tmpdir) / "灰色轨迹.mp3"
            media_path.write_bytes(b"abcdef")

            response = media_file_response(media_path, DummyRequest({"range": "bytes=1-2"}))

            self.assertEqual(response.status_code, 206)
            self.assertEqual(response.headers["content-range"], "bytes 1-2/6")
            self.assertEqual(response.headers["content-length"], "2")
            self.assertEqual(response.headers["accept-ranges"], "bytes")
            self.assertNotIn("content-disposition", response.headers)


if __name__ == "__main__":
    unittest.main()
