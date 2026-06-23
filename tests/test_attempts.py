import unittest
from unittest.mock import patch

from src.attempts import choose_session_attempts
from src.downloads import download_with_retries


class AttemptTests(unittest.TestCase):
    @patch("src.attempts.read_input", side_effect=["0", "abc", "5"])
    def test_attempt_prompt_requires_positive_number(self, read_input):
        self.assertEqual(choose_session_attempts(2), 5)

    @patch("src.attempts.read_input", return_value="e")
    def test_attempt_prompt_can_keep_current_value(self, read_input):
        self.assertEqual(choose_session_attempts(3), 3)

    def test_retry_loop_uses_selected_attempt_count(self):
        calls = 0

        def fail():
            nonlocal calls
            calls += 1
            raise RuntimeError("failed")

        with self.assertRaises(RuntimeError):
            download_with_retries("Video 720p", fail, {}, 5)

        self.assertEqual(calls, 5)


if __name__ == "__main__":
    unittest.main()
