import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services import coach_sessions


class CoachSessionsDeleteTests(unittest.TestCase):
    def test_delete_sessions_skips_empty_mixed_path_without_touching_recordings_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            recordings_root = base / "coach_recordings"
            session_dir = recordings_root / "song-1" / "abc123"
            session_dir.mkdir(parents=True, exist_ok=True)
            recording_file = session_dir / "practice-take.webm"
            recording_file.write_bytes(b"audio")

            fake_store = {
                "sessions": [
                    {
                        "id": "abc123",
                        "song_id": "song-1",
                        "recording_path": "song-1/abc123/practice-take.webm",
                        "mixed_path": "",
                    }
                ]
            }

            saved_payloads = []

            def fake_save(data):
                saved_payloads.append(data)
                return data

            with mock.patch.object(coach_sessions, "COACH_RECORDINGS_DIR", recordings_root):
                with mock.patch.object(coach_sessions, "load_sessions", return_value=fake_store):
                    with mock.patch.object(coach_sessions, "save_sessions", side_effect=fake_save):
                        result = coach_sessions.delete_sessions(["abc123"])

            self.assertTrue(result["ok"])
            self.assertEqual(result["sessions"], [])
            self.assertFalse(recording_file.exists())
            self.assertTrue(recordings_root.exists())
            self.assertEqual(saved_payloads[-1]["sessions"], [])


if __name__ == "__main__":
    unittest.main()
