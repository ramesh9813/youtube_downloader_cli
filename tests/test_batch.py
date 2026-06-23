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
            )

        self.assertEqual(download_one_result.call_count, 2)
        self.assertEqual(
            [
                call.args[1]
                for call in download_one_result.call_args_list
            ],
            [preference, preference],
        )


if __name__ == "__main__":
    unittest.main()
