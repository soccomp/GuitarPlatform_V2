import shutil
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services import indexer, resource_manager


class ResourceManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="gp-resource-tests-"))
        self.original_courses_dir = resource_manager.COURSES_DIR
        self.original_songs_dir = resource_manager.SONGS_DIR
        self.original_collected_dir = resource_manager.COLLECTED_DIR
        self.original_indexer_courses_dir = indexer.COURSES_DIR
        self.original_indexer_songs_dir = indexer.SONGS_DIR
        self.original_indexer_collected_dir = indexer.COLLECTED_DIR
        self.original_generate_video_thumbnail = indexer.generate_video_thumbnail

        self.courses_dir = self.temp_dir / "courses"
        self.songs_dir = self.temp_dir / "songs"
        self.collected_dir = self.temp_dir / "collected"
        self.courses_dir.mkdir()
        self.songs_dir.mkdir()
        self.collected_dir.mkdir()

        resource_manager.COURSES_DIR = self.courses_dir
        resource_manager.SONGS_DIR = self.songs_dir
        resource_manager.COLLECTED_DIR = self.collected_dir
        indexer.COURSES_DIR = self.courses_dir
        indexer.SONGS_DIR = self.songs_dir
        indexer.COLLECTED_DIR = self.collected_dir
        indexer.generate_video_thumbnail = lambda _video_file, _thumbnail_path: False

    def tearDown(self):
        resource_manager.COURSES_DIR = self.original_courses_dir
        resource_manager.SONGS_DIR = self.original_songs_dir
        resource_manager.COLLECTED_DIR = self.original_collected_dir
        indexer.COURSES_DIR = self.original_indexer_courses_dir
        indexer.SONGS_DIR = self.original_indexer_songs_dir
        indexer.COLLECTED_DIR = self.original_indexer_collected_dir
        indexer.generate_video_thumbnail = self.original_generate_video_thumbnail
        shutil.rmtree(self.temp_dir)

    def test_delete_video_resource_removes_video_and_thumbnail(self):
        video_dir = self.collected_dir / "技巧"
        video_dir.mkdir()
        video_file = video_dir / "练习.mp4"
        video_file.write_bytes(b"video")

        relative_path = Path("技巧/练习.mp4")
        thumbnail_relative = indexer.build_collected_thumbnail_path(relative_path)
        thumbnail_file = self.collected_dir / thumbnail_relative
        thumbnail_file.parent.mkdir(parents=True, exist_ok=True)
        thumbnail_file.write_bytes(b"jpg")

        videos = resource_manager.delete_video_resource(
            {
                "id": "video_1",
                "title": "练习",
                "path": relative_path.as_posix(),
                "thumbnail": thumbnail_relative.as_posix(),
            }
        )

        self.assertEqual(videos, [])
        self.assertFalse(video_file.exists())
        self.assertFalse(thumbnail_file.exists())

    def test_delete_song_resource_removes_entire_song_directory(self):
        song_dir = self.songs_dir / "灰色轨迹"
        outro_dir = song_dir / "尾奏"
        outro_dir.mkdir(parents=True)
        (outro_dir / "尾奏.mp3").write_bytes(b"audio")

        songs = resource_manager.delete_song_resource(
            {
                "id": "song_1",
                "title": "灰色轨迹",
                "path": "灰色轨迹",
            }
        )

        self.assertEqual(songs, [])
        self.assertFalse(song_dir.exists())

    def test_delete_course_resource_removes_lesson_directory(self):
        lesson_dir = self.courses_dir / "吉他新思维" / "01-乐理" / "第一课"
        lesson_dir.mkdir(parents=True)
        video_file = lesson_dir / "01-音程.mp4"
        video_file.write_bytes(b"video")
        (lesson_dir / "transcript.md").write_text("notes", encoding="utf-8")
        (lesson_dir / "练习谱.pdf").write_bytes(b"pdf")

        courses = resource_manager.delete_course_resource(
            {
                "id": "course_1",
                "title": "01-音程",
                "video_path": "吉他新思维/01-乐理/第一课/01-音程.mp4",
                "transcript_path": "吉他新思维/01-乐理/第一课/transcript.md",
                "materials": {
                    "pdf": ["吉他新思维/01-乐理/第一课/练习谱.pdf"],
                },
            }
        )

        self.assertEqual(courses, [])
        self.assertFalse(lesson_dir.exists())
        self.assertTrue((self.courses_dir / "吉他新思维").exists())

    def test_delete_course_resource_keeps_series_root_when_course_is_direct_child(self):
        series_dir = self.courses_dir / "吉他新思维"
        series_dir.mkdir(parents=True)
        video_file = series_dir / "欢迎课.mp4"
        video_file.write_bytes(b"video")
        notes_file = series_dir / "transcript.md"
        notes_file.write_text("notes", encoding="utf-8")

        courses = resource_manager.delete_course_resource(
            {
                "id": "course_1",
                "title": "欢迎课",
                "video_path": "吉他新思维/欢迎课.mp4",
                "transcript_path": "吉他新思维/transcript.md",
                "materials": {},
            }
        )

        self.assertEqual(courses, [])
        self.assertTrue(series_dir.exists())
        self.assertFalse(video_file.exists())
        self.assertFalse(notes_file.exists())


if __name__ == "__main__":
    unittest.main()
