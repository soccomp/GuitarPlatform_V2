import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services import index_store


class IndexStoreTests(unittest.TestCase):
    def test_clean_relative_path_normalizes_slashes_and_whitespace(self):
        self.assertEqual(
            index_store.clean_relative_path(r"  songs\Beyond\demo.mp3/ "),
            "songs/Beyond/demo.mp3",
        )

    def test_normalize_index_fills_missing_defaults(self):
        normalized = index_store.normalize_index(
            {
                "courses": [{"id": "course-1", "title": "Lesson A"}],
                "songs": [{"id": "song-1", "title": "Song A", "versions": [{}]}],
                "videos": [{"id": "video-1", "title": "Clip A"}],
            }
        )

        self.assertEqual(normalized["courses"][0]["series"], "未分类课程")
        self.assertEqual(normalized["songs"][0]["versions"][0]["name"], "默认版")
        self.assertEqual(normalized["videos"][0]["type"], "collected")

    def test_resolve_under_rejects_escaping_base_directory(self):
        with self.assertRaises(ValueError):
            index_store.resolve_under(Path("/tmp/library"), "../secret.txt")

    def test_resolve_under_allows_nested_relative_path(self):
        resolved = index_store.resolve_under(Path("/tmp/library"), "songs/demo/file.mp3")
        self.assertEqual(resolved, Path("/tmp/library/songs/demo/file.mp3").resolve())


if __name__ == "__main__":
    unittest.main()
