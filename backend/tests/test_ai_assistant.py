import tempfile
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.ai_assistant import read_env_value


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


if __name__ == "__main__":
    unittest.main()
