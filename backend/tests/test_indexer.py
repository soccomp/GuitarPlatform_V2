import shutil
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services import indexer


class IndexerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="gp-indexer-tests-"))
        self.original_courses_dir = indexer.COURSES_DIR
        self.original_songs_dir = indexer.SONGS_DIR
        self.original_collected_dir = indexer.COLLECTED_DIR
        self.original_generate_video_thumbnail = indexer.generate_video_thumbnail

        self.courses_dir = self.temp_dir / "courses"
        self.songs_dir = self.temp_dir / "songs"
        self.collected_dir = self.temp_dir / "collected"
        self.courses_dir.mkdir()
        self.songs_dir.mkdir()
        self.collected_dir.mkdir()

        indexer.COURSES_DIR = self.courses_dir
        indexer.SONGS_DIR = self.songs_dir
        indexer.COLLECTED_DIR = self.collected_dir

    def tearDown(self):
        indexer.COURSES_DIR = self.original_courses_dir
        indexer.SONGS_DIR = self.original_songs_dir
        indexer.COLLECTED_DIR = self.original_collected_dir
        indexer.generate_video_thumbnail = self.original_generate_video_thumbnail
        shutil.rmtree(self.temp_dir)

    def test_scan_course_library_collects_video_transcript_and_materials(self):
        lesson_dir = self.courses_dir / "吉他新思维" / "01-必要乐理【视频】" / "第一课"
        lesson_dir.mkdir(parents=True)
        (lesson_dir / "01-十二平均律.mp4").write_bytes(b"video")
        (lesson_dir / "transcript.md").write_text("lesson transcript", encoding="utf-8")
        (lesson_dir / "练习谱.pdf").write_bytes(b"pdf")
        (lesson_dir / "主奏.gp5").write_bytes(b"gp")
        (lesson_dir / "伴奏.mp3").write_bytes(b"audio")

        courses = indexer.scan_course_library()

        self.assertEqual(len(courses), 1)
        course = courses[0]
        self.assertEqual(course["series"], "吉他新思维")
        self.assertEqual(course["level"], "01-必要乐理【视频】")
        self.assertEqual(course["title"], "01-十二平均律")
        self.assertEqual(course["video_path"], "吉他新思维/01-必要乐理【视频】/第一课/01-十二平均律.mp4")
        self.assertEqual(course["transcript_path"], "吉他新思维/01-必要乐理【视频】/第一课/transcript.md")
        self.assertEqual(course["tags"], ["01-必要乐理【视频】", "第一课"])
        self.assertEqual(course["materials"]["pdf"], ["吉他新思维/01-必要乐理【视频】/第一课/练习谱.pdf"])
        self.assertEqual(course["materials"]["gp"], ["吉他新思维/01-必要乐理【视频】/第一课/主奏.gp5"])
        self.assertEqual(course["materials"]["audio"], ["吉他新思维/01-必要乐理【视频】/第一课/伴奏.mp3"])

    def test_scan_song_library_collects_root_and_nested_versions(self):
        song_dir = self.songs_dir / "灰色轨迹"
        song_dir.mkdir()
        (song_dir / "原曲.mp3").write_bytes(b"root audio")

        live_dir = song_dir / "91 Live版"
        live_dir.mkdir()
        (live_dir / "原曲视频.mp4").write_bytes(b"video")

        outro_dir = live_dir / "尾奏"
        outro_dir.mkdir()
        (outro_dir / "尾奏.gp").write_bytes(b"gp")
        (outro_dir / "尾奏.pdf").write_bytes(b"pdf")
        (outro_dir / "尾奏伴奏.mp3").write_bytes(b"audio")

        songs = indexer.scan_song_library()

        self.assertEqual(len(songs), 1)
        song = songs[0]
        self.assertEqual(song["title"], "灰色轨迹")
        self.assertEqual(song["path"], "灰色轨迹")

        versions = {version["name"]: version["files"] for version in song["versions"]}
        self.assertIn("默认版", versions)
        self.assertEqual(versions["默认版"]["audio"], "原曲.mp3")
        self.assertIn("91 Live版", versions)
        self.assertEqual(versions["91 Live版"]["video"], "91 Live版/原曲视频.mp4")
        self.assertIn("91 Live版 / 尾奏", versions)
        self.assertEqual(versions["91 Live版 / 尾奏"]["gp"], "91 Live版/尾奏/尾奏.gp")
        self.assertEqual(versions["91 Live版 / 尾奏"]["pdf"], "91 Live版/尾奏/尾奏.pdf")
        self.assertEqual(versions["91 Live版 / 尾奏"]["audio"], "91 Live版/尾奏/尾奏伴奏.mp3")

    def test_stable_suffix_keeps_non_ascii_inputs_unique(self):
        first = indexer.stable_suffix("灰色轨迹")
        second = indexer.stable_suffix("海阔天空")
        self.assertNotEqual(first, second)
        self.assertTrue(first)
        self.assertTrue(second)

    def test_scan_collected_video_library_uses_folder_as_category(self):
        video_dir = self.collected_dir / "未分类"
        video_dir.mkdir()
        (video_dir / "如何记忆指板.mp4").write_bytes(b"video")
        indexer.generate_video_thumbnail = lambda video_file, thumbnail_path: False

        videos = indexer.scan_collected_video_library()

        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["title"], "如何记忆指板")
        self.assertEqual(videos[0]["source"], "local")
        self.assertEqual(videos[0]["category"], "未分类")
        self.assertEqual(videos[0]["path"], "未分类/如何记忆指板.mp4")
        self.assertEqual(videos[0]["thumbnail"], "")

    def test_scan_collected_video_library_adds_thumbnail_path(self):
        video_dir = self.collected_dir / "技巧"
        video_dir.mkdir()
        video_file = video_dir / "和弦如何变强.mp4"
        video_file.write_bytes(b"video")

        def fake_thumbnail(_video_file, thumbnail_path):
            thumbnail_path.write_bytes(b"jpg")
            return True

        indexer.generate_video_thumbnail = fake_thumbnail

        videos = indexer.scan_collected_video_library()

        self.assertEqual(len(videos), 1)
        self.assertTrue(videos[0]["thumbnail"].startswith(".thumbnails/"))
        self.assertTrue(videos[0]["thumbnail"].endswith(".jpg"))
        self.assertTrue((self.collected_dir / videos[0]["thumbnail"]).exists())


if __name__ == "__main__":
    unittest.main()
