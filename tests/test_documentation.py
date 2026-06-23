import io
import unittest
from contextlib import redirect_stdout

from src.documentation import DOCUMENTATION, print_documentation


class DocumentationTests(unittest.TestCase):
    def test_documentation_contains_every_interactive_shortcut(self):
        for shortcut in (
            "url or u",
            "file or f",
            "@filename",
            "q",
            "a",
            "d",
            "e",
            "exit",
            "quit",
        ):
            self.assertIn(shortcut, DOCUMENTATION)

    def test_documentation_contains_every_command_option(self):
        for option in (
            "--help",
            "--link",
            "--quality",
            "--file",
            "--output",
            "--cookies-from-browser",
            "--cookies",
        ):
            self.assertIn(option, DOCUMENTATION)

    def test_documentation_contains_major_behavior_sections(self):
        for section in (
            "DEFAULTS",
            "QUALITY SHORTCUT",
            "ATTEMPT SHORTCUT",
            "BATCH DOWNLOADS",
            "PLAYLIST DOWNLOADS",
            "PROGRESS DISPLAY",
            "VIDEO DOWNLOADS",
            "AUDIO DOWNLOADS",
            "YOUTUBE VERIFICATION AND COOKIES",
            "DEPENDENCIES",
        ):
            self.assertIn(section, DOCUMENTATION)

    def test_print_documentation_outputs_full_document(self):
        output = io.StringIO()
        with redirect_stdout(output):
            print_documentation()
        self.assertIn(DOCUMENTATION, output.getvalue())


if __name__ == "__main__":
    unittest.main()
