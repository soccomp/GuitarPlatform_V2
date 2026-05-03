import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app
from services.coach import build_preview_rhythm_analysis


class CoachServiceTests(unittest.TestCase):
    def test_preview_analysis_returns_structured_payload(self):
        payload = build_preview_rhythm_analysis(
            song_id="song-1",
            song_title="灰色轨迹",
            version="录音室尾奏",
            playback_rate=0.75,
            audio_bytes=b"1234567890",
            mime_type="audio/webm",
            segment_label="尾奏",
            recorded_duration=14.2,
        )

        self.assertEqual(payload["mode"], "local_preview")
        self.assertEqual(payload["segment"], "尾奏")
        self.assertEqual(payload["tempo_mode"], "0.75x")
        self.assertGreaterEqual(payload["stability_score"], 62)
        self.assertEqual(payload["received"]["size_kb"], 1)
        self.assertTrue(payload["advice"])


class CoachRouterTests(unittest.TestCase):
    def test_analyze_rhythm_accepts_uploaded_audio(self):
        client = TestClient(app)

        response = client.post(
            "/api/coach/analyze-rhythm",
            data={
                "song_id": "song-1",
                "song_title": "灰色轨迹",
                "version": "Live SOLO",
                "playback_rate": "0.80",
                "segment_label": "尾奏",
                "recorded_duration": "11.5",
            },
            files={"audio": ("take.webm", b"fake-audio-data", "audio/webm")},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "local_preview")
        self.assertEqual(body["song_title"], "灰色轨迹")
        self.assertEqual(body["segment"], "尾奏")
        self.assertEqual(body["received"]["mime_type"], "audio/webm")


if __name__ == "__main__":
    unittest.main()
