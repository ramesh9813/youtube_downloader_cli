import unittest
from unittest.mock import patch

from src.cli import main, prompt_for_action, prompt_for_link
from src.parsing import parse_args
from src.preferences import audio_preference


class CliTests(unittest.TestCase):
    @patch("src.cli.read_input", return_value="d")
    def test_d_shortcut_is_available_at_main_prompt(self, read_input):
        self.assertEqual(
            prompt_for_action(),
            ("documentation", None),
        )

    @patch("src.cli.read_input", return_value="d")
    def test_d_shortcut_is_available_at_link_prompt(self, read_input):
        self.assertEqual(
            prompt_for_link(),
            ("documentation", None),
        )

    def test_explicit_quality_option_remains_valid(self):
        args = parse_args(
            ["--file", "links.txt", "--quality", "480"]
        )
        self.assertEqual(args.batch_file, "links.txt")
        self.assertEqual(args.quality, 480)

    def test_short_quality_option_remains_valid(self):
        args = parse_args(
            ["-q", "360", "https://youtu.be/example"]
        )
        self.assertEqual(args.link, "https://youtu.be/example")
        self.assertEqual(args.quality, 360)

    def test_attempt_command_is_parsed(self):
        args = parse_args(["a"])
        self.assertTrue(args.change_attempts)

    def test_documentation_command_is_parsed(self):
        args = parse_args(["d"])
        self.assertTrue(args.show_documentation)

    @patch("src.cli.download_one_result")
    @patch("src.cli.print_documentation")
    @patch("src.cli.prompt_for_action")
    def test_documentation_returns_to_main_prompt(
        self,
        prompt_for_action,
        print_documentation,
        download_one_result,
    ):
        prompt_for_action.side_effect = [
            ("documentation", None),
            ("url", "https://youtu.be/one"),
            ("exit", None),
        ]
        download_one_result.return_value = {"status": "downloaded"}

        exit_code = main([])

        self.assertEqual(exit_code, 0)
        print_documentation.assert_called_once()
        download_one_result.assert_called_once()

    @patch("src.cli.download_one_result")
    @patch("src.cli.choose_session_attempts", return_value=5)
    @patch("src.cli.prompt_for_action")
    def test_changed_attempts_persist_for_later_links(
        self,
        prompt_for_action,
        choose_session_attempts,
        download_one_result,
    ):
        prompt_for_action.side_effect = [
            ("attempts", None),
            ("url", "https://youtu.be/one"),
            ("url", "https://youtu.be/two"),
            ("exit", None),
        ]
        download_one_result.return_value = {"status": "downloaded"}

        exit_code = main([])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [
                call.args[4]
                for call in download_one_result.call_args_list
            ],
            [5, 5],
        )

    @patch("src.cli.download_one_result")
    @patch("src.cli.choose_session_preference")
    @patch("src.cli.prompt_for_action")
    def test_changed_quality_persists_for_later_links(
        self,
        prompt_for_action,
        choose_session_preference,
        download_one_result,
    ):
        prompt_for_action.side_effect = [
            ("quality", None),
            ("url", "https://youtu.be/one"),
            ("url", "https://youtu.be/two"),
            ("exit", None),
        ]
        choose_session_preference.return_value = audio_preference(128)
        download_one_result.return_value = {"status": "downloaded"}

        exit_code = main([])

        self.assertEqual(exit_code, 0)
        preferences = [
            call.args[1] for call in download_one_result.call_args_list
        ]
        self.assertEqual(
            preferences,
            [audio_preference(128), audio_preference(128)],
        )

    @patch("src.cli.download_one_result")
    @patch("src.cli.prompt_for_action")
    def test_default_quality_is_720p(
        self,
        prompt_for_action,
        download_one_result,
    ):
        prompt_for_action.side_effect = [
            ("url", "https://youtu.be/one"),
            ("exit", None),
        ]
        download_one_result.return_value = {"status": "downloaded"}

        main([])

        self.assertEqual(
            download_one_result.call_args.args[1],
            {"type": "video", "quality": 720},
        )


if __name__ == "__main__":
    unittest.main()
