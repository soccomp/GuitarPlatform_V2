import tempfile
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.ai_assistant import (
    DEFAULT_MINIMAX_BASE_URL,
    extract_assistant_content,
    extract_provider_error,
    get_minimax_base_url,
    normalize_api_key,
    read_env_value,
)


class AiAssistantConfigTests(unittest.TestCase):
    def test_read_env_value_supports_quoted_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "# local secrets\nMINIMAX_API_KEY='test-key-123'\nOTHER=value\n",
                encoding="utf-8",
            )

            self.assertEqual(read_env_value(env_file, "MINIMAX_API_KEY"), "test-key-123")

    def test_read_env_value_returns_empty_for_missing_file(self):
        self.assertEqual(read_env_value(Path("/tmp/not-a-real-guitar-platform-env"), "MINIMAX_API_KEY"), "")

    def test_extract_assistant_content_reads_choice_message(self):
        result = {"choices": [{"message": {"content": "可以这样练。"}}]}

        self.assertEqual(extract_assistant_content(result), "可以这样练。")

    def test_extract_assistant_content_reads_anthropic_content_blocks(self):
        result = {"content": [{"type": "text", "text": "Token Plan 可以这样练。"}]}

        self.assertEqual(extract_assistant_content(result), "Token Plan 可以这样练。")

    def test_extract_provider_error_reads_base_response(self):
        result = {"base_resp": {"status_code": 1008, "status_msg": "invalid model"}}

        self.assertEqual(extract_provider_error(result), "invalid model")

    def test_extract_provider_error_reads_anthropic_error(self):
        result = {"error": {"type": "authentication_error", "message": "invalid api key"}}

        self.assertEqual(extract_provider_error(result), "invalid api key")

    def test_normalize_api_key_removes_bearer_prefix(self):
        self.assertEqual(normalize_api_key("Bearer test-key-123"), "test-key-123")

    def test_get_minimax_base_url_uses_default_chat_endpoint(self):
        self.assertEqual(get_minimax_base_url(), DEFAULT_MINIMAX_BASE_URL)


if __name__ == "__main__":
    unittest.main()
