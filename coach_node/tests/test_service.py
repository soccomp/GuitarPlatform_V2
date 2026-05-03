import sys
import unittest
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, mock

from fastapi.testclient import TestClient


COACH_NODE_DIR = Path(__file__).resolve().parents[1]
if str(COACH_NODE_DIR) not in sys.path:
    sys.path.insert(0, str(COACH_NODE_DIR))

from main import app
from service import (
    analyze_with_ollama,
    build_node_preview_analysis,
    build_ollama_messages,
    extract_ollama_message,
)


class CoachNodeServiceTests(unittest.TestCase):
    def test_preview_analysis_contains_expected_shape(self):
        result = build_node_preview_analysis(
            song_id="song-1",
            song_title="灰色轨迹",
            version="Live SOLO",
            segment_label="尾奏",
            playback_rate=0.8,
            recorded_duration=12.5,
            mime_type="audio/webm",
            audio_size_bytes=4096,
            model_name="qwen3:8b",
        )
        self.assertEqual(result["mode"], "remote_node_preview")
        self.assertEqual(result["segment"], "尾奏")
        self.assertEqual(result["provider"], "ollama")
        self.assertTrue(result["advice"])

    def test_build_ollama_messages_uses_teacher_prompt(self):
        preview = build_node_preview_analysis(
            song_id="song-1",
            song_title="灰色轨迹",
            version="Live SOLO",
            segment_label="尾奏",
            playback_rate=0.8,
            recorded_duration=12.5,
            mime_type="audio/webm",
            audio_size_bytes=4096,
            model_name="qwen3:8b",
        )
        messages = build_ollama_messages(
            teacher_prompt="你是一位电吉他陪练老师。",
            preview_analysis=preview,
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("电吉他陪练老师", messages[0]["content"])

    def test_extract_ollama_message_reads_message_content(self):
        self.assertEqual(
            extract_ollama_message({"message": {"content": "老师反馈"}}),
            "老师反馈",
        )


class CoachNodeRuntimeTests(IsolatedAsyncioTestCase):
    async def test_analyze_with_ollama_falls_back_when_model_unavailable(self):
        with mock.patch("service.request_ollama_feedback", side_effect=RuntimeError("connection refused")):
            result = await analyze_with_ollama(
                song_id="song-1",
                song_title="灰色轨迹",
                version="Live SOLO",
                segment_label="尾奏",
                playback_rate=0.8,
                recorded_duration=12.0,
                mime_type="audio/webm",
                audio_bytes=b"123456",
                teacher_prompt="你是一位电吉他陪练老师。",
                requested_model="qwen3:8b",
            )
        self.assertIn(result["mode"], {"remote_node_preview", "remote_node"})
        self.assertTrue(result["coach_feedback"])


class CoachNodeRouterTests(unittest.TestCase):
    def test_router_accepts_audio_upload(self):
        client = TestClient(app)
        response = client.post(
            "/api/coach/analyze-rhythm",
            data={
                "song_id": "song-1",
                "song_title": "灰色轨迹",
                "version": "Live SOLO",
                "segment_label": "尾奏",
                "playback_rate": "0.8",
                "recorded_duration": "10.0",
                "coach_model": "qwen3:8b",
                "teacher_prompt": "你是一位电吉他陪练老师。",
            },
            files={"audio": ("take.webm", b"fake-audio", "audio/webm")},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["song_title"], "灰色轨迹")
        self.assertIn("mode", body)


if __name__ == "__main__":
    unittest.main()
