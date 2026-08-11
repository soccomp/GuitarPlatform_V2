import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, mock

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services import coach
from services.coach import build_preview_rhythm_analysis


def load_backend_app():
    spec = importlib.util.spec_from_file_location("backend_main_for_tests", BACKEND_DIR / "main.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.app


app = load_backend_app()


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
        self.assertIn("经验丰富", payload["teacher_prompt_preview"])


class CoachRoutingTests(IsolatedAsyncioTestCase):
    async def test_analyze_practice_audio_falls_back_to_preview_when_node_missing(self):
        with mock.patch.object(coach, "get_coach_node_url", return_value=""):
            payload = await coach.analyze_practice_audio(
                song_id="song-1",
                song_title="灰色轨迹",
                version="Live SOLO",
                playback_rate=0.8,
                audio_bytes=b"test-audio",
                mime_type="audio/webm",
                segment_label="尾奏",
                recorded_duration=10.0,
            )

        self.assertEqual(payload["mode"], "local_preview")
        self.assertEqual(payload["segment"], "尾奏")

    async def test_analyze_practice_audio_uses_remote_node_when_configured(self):
        expected = {"mode": "remote_node", "segment": "尾奏"}
        with mock.patch.object(coach, "get_coach_node_url", return_value="http://192.168.2.186:9000/api/coach/analyze-rhythm"):
            with mock.patch.object(coach, "send_to_coach_node", return_value=expected) as mocked:
                payload = await coach.analyze_practice_audio(
                    song_id="song-1",
                    song_title="灰色轨迹",
                    version="Live SOLO",
                    playback_rate=0.8,
                    audio_bytes=b"test-audio",
                    mime_type="audio/webm",
                    segment_label="尾奏",
                    recorded_duration=10.0,
                    reference_audio_bytes=b"reference-audio",
                    reference_mime_type="audio/mpeg",
                    reference_label="伴奏2.mp3",
                    coach_model="deepseek-r1:8b",
                )

        self.assertEqual(payload, expected)
        mocked.assert_awaited_once()


class CoachRouterTests(unittest.TestCase):
    def test_analyze_rhythm_accepts_uploaded_audio(self):
        client = TestClient(app)
        with mock.patch("routers.coach.create_session") as mocked_create:
            mocked_create.return_value = {
                "id": "session-1",
                "song_id": "song-1",
                "song_title": "灰色轨迹",
                "version": "Live SOLO",
                "segment": "尾奏",
                "coach_model": "qwen3:8b",
                "created_at": "2026-05-03T12:00:00+08:00",
                "recording_duration": 11.5,
                "analysis": {
                    "mode": "local_preview",
                    "song_title": "灰色轨迹",
                    "version": "Live SOLO",
                    "segment": "尾奏",
                    "tempo_mode": "0.80x",
                    "stability_score": 72,
                    "issues": [],
                    "advice": [],
                    "coach_feedback": "",
                },
            }

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
        self.assertIn(body["mode"], {"local_preview", "local_preview_fallback"})
        self.assertEqual(body["song_title"], "灰色轨迹")
        self.assertEqual(body["segment"], "尾奏")
        self.assertEqual(body["session_id"], "session-1")
        self.assertTrue(body["recording_url"].endswith("/api/coach/sessions/session-1/recording"))

    def test_list_sessions_returns_saved_results(self):
        client = TestClient(app)
        with mock.patch("routers.coach.list_sessions", return_value=[{
            "id": "session-1",
            "song_id": "song-1",
            "song_title": "灰色轨迹",
            "version": "Live SOLO",
            "segment": "尾奏",
            "coach_model": "qwen3:8b",
            "created_at": "2026-05-03T12:00:00+08:00",
            "recording_duration": 11.5,
            "analysis": {"mode": "remote_node", "song_title": "灰色轨迹", "version": "Live SOLO", "segment": "尾奏"},
        }]):
            response = client.get("/api/coach/sessions")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["session_id"], "session-1")

    def test_export_sessions_returns_zip(self):
        client = TestClient(app)
        with mock.patch("routers.coach.export_sessions_zip", return_value=(b"zip-bytes", "coach-sessions.zip")):
            response = client.get("/api/coach/sessions/export?ids=session-1,session-2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/zip")


if __name__ == "__main__":
    unittest.main()
