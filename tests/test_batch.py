import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.batch import download_batch
from src.preferences import audio_preference


class BatchTests(unittest.TestCase):
    @patch("src.batch.download_one_result")
    def test_audio_preference_applies_to_every_batch_link(
        self,
        download_one_result,
    ):
        download_one_result.return_value = {
            "status": "downloaded",
            "link": "",
            "quality": "Audio webm (opus)",
            "title": "Audio",
            "saved_path": "Audio.webm",
            "message": "Downloaded.",
        }
        preference = audio_preference(128)

        with tempfile.TemporaryDirectory() as directory:
            batch_file = Path(directory) / "links.txt"
            batch_file.write_text(
                "https://youtu.be/one\nhttps://youtu.be/two\n",
                encoding="utf-8",
            )
            download_batch(
                str(batch_file),
                directory,
                {},
                preference,
                5,
            )

        self.assertEqual(download_one_result.call_count, 2)
        self.assertEqual(
            [
                call.args[1]
                for call in download_one_result.call_args_list
            ],
            [preference, preference],
        )
        self.assertEqual(
            [
                call.args[4]
                for call in download_one_result.call_args_list
            ],
            [5, 5],
        )

    @patch("src.batch.download_one_result")
    def test_audio_choice_change_is_used_by_remaining_batch_links(
        self,
        download_one_result,
    ):
        seen_bitrates = []

        def download(
            link,
            preference,
            output_dir,
            authentication,
            attempts,
            show_summary,
        ):
            seen_bitrates.append(preference["bitrate"])
            if len(seen_bitrates) == 1:
                preference["bitrate"] = 160
            return {
                "status": "downloaded",
                "link": link,
                "quality": "Audio webm (opus, 160 kbps)",
                "title": "Audio",
                "saved_path": "Audio.webm",
                "message": "Downloaded.",
            }

        download_one_result.side_effect = download
        preference = audio_preference(320)

        with tempfile.TemporaryDirectory() as directory:
            batch_file = Path(directory) / "links.txt"
            batch_file.write_text(
                "https://youtu.be/one\nhttps://youtu.be/two\n",
                encoding="utf-8",
            )
            download_batch(
                str(batch_file),
                directory,
                {},
                preference,
                2,
            )

        self.assertEqual(seen_bitrates, [320, 160])
        self.assertEqual(preference, audio_preference(160))


if __name__ == "__main__":
    unittest.main()
