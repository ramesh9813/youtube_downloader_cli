import io
import unittest
from contextlib import redirect_stdout

from src.console import (
    format_file_size,
    make_progress_hook,
    progress_downloaded_size,
    progress_total_size,
)


class ConsoleProgressTests(unittest.TestCase):
    def test_formats_total_size_in_mebibytes(self):
        self.assertEqual(
            format_file_size(44_695_142),
            "42.62MiB",
        )

    def test_uses_exact_total_size_before_estimate(self):
        self.assertEqual(
            progress_total_size(
                {
                    "total_bytes": 10 * 1024 * 1024,
                    "total_bytes_estimate": 20 * 1024 * 1024,
                }
            ),
            "10.00MiB",
        )

    def test_uses_yt_dlp_formatted_total_size(self):
        self.assertEqual(
            progress_total_size(
                {
                    "_total_bytes_str": " 42.75MiB ",
                    "total_bytes": 10,
                }
            ),
            "42.75MiB",
        )

    def test_uses_estimated_total_when_exact_is_missing(self):
        self.assertEqual(
            progress_total_size(
                {"total_bytes_estimate": 20 * 1024 * 1024}
            ),
            "20.00MiB",
        )

    def test_formats_downloaded_real_size(self):
        self.assertEqual(
            progress_downloaded_size(
                {"downloaded_bytes": 34 * 1024 * 1024}
            ),
            "34.00MiB",
        )

    def test_progress_line_includes_total_size(self):
        output = io.StringIO()
        hook = make_progress_hook()

        with redirect_stdout(output):
            hook(
                {
                    "status": "downloading",
                    "_percent_str": "80.2%",
                    "_speed_str": "3.60MiB/s",
                    "_eta_str": "00:04",
                    "total_bytes": 42 * 1024 * 1024,
                    "downloaded_bytes": 34 * 1024 * 1024,
                }
            )

        self.assertIn(
            "Downloading 80.2% | Total 42.00MiB / "
            "Downloaded 34.00MiB | Speed 3.60MiB/s | ETA 00:04",
            output.getvalue(),
        )

    def test_progress_line_omits_size_when_unknown(self):
        output = io.StringIO()
        hook = make_progress_hook()

        with redirect_stdout(output):
            hook(
                {
                    "status": "downloading",
                    "_percent_str": "80.2%",
                    "_speed_str": "3.60MiB/s",
                    "_eta_str": "00:04",
                }
            )

        self.assertIn(
            "Downloading 80.2% | Speed 3.60MiB/s | ETA 00:04",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
