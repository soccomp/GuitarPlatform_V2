import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services import transcriber


class TranscriberTests(unittest.TestCase):
    def test_transcribe_media_raises_when_source_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "transcript.md"
            with self.assertRaises(transcriber.TranscriptionError):
                transcriber.transcribe_media("/tmp/not-a-real-course.mp4", output_path)

    def test_transcribe_media_writes_transcript_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            media_path = Path(tmpdir) / "lesson.mp4"
            output_path = Path(tmpdir) / "transcript.md"
            media_path.write_bytes(b"video")

            def fake_run(command, check, capture_output, text):
                self.assertIn("--output_dir", command)
                out_dir = Path(command[command.index("--output_dir") + 1])
                (out_dir / "lesson.txt").write_text("这是课程 transcript", encoding="utf-8")
                return None

            with mock.patch.object(shutil, "which", return_value="/opt/homebrew/bin/whisper"):
                with mock.patch.object(transcriber.subprocess, "run", side_effect=fake_run):
                    result = transcriber.transcribe_media(media_path, output_path)

            self.assertEqual(result, output_path.resolve())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "这是课程 transcript\n")


if __name__ == "__main__":
    unittest.main()
