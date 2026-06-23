import unittest
from pathlib import Path
from unittest.mock import patch

from src.download_service import download_one_result
from src.preferences import audio_preference, video_preference


VIDEO_INFO = {
    "formats": [
        {
            "format_id": "video-480",
            "height": 480,
            "vcodec": "avc1",
            "acodec": "none",
            "ext": "mp4",
        },
        {
            "format_id": "video-1080",
            "height": 1080,
            "vcodec": "vp9",
            "acodec": "none",
            "ext": "webm",
        },
        {
            "format_id": "audio-96",
            "height": None,
            "vcodec": "none",
            "acodec": "opus",
            "ext": "webm",
            "abr": 96,
        },
        {
            "format_id": "audio-160",
            "height": None,
            "vcodec": "none",
            "acodec": "opus",
            "ext": "webm",
            "abr": 160,
        },
    ]
}


class DownloadServiceTests(unittest.TestCase):
    @patch("src.download_service.download_with_retries")
    @patch("src.download_service.download_video")
    @patch("src.download_service.fetch_info", return_value=VIDEO_INFO)
    def test_video_preference_uses_nearest_quality(
        self,
        fetch_info,
        download_video,
        download_with_retries,
    ):
        download_video.return_value = (
            {"title": "Video"},
            Path("Video.mp4"),
        )
        download_with_retries.side_effect = (
            lambda label, action, authentication: action()
        )

        result = download_one_result(
            "https://youtu.be/example",
            video_preference(720),
            ".",
            {},
            show_summary=False,
        )

        self.assertEqual(result["quality"], "480p")
        self.assertEqual(download_video.call_args.args[1], 480)

    @patch("src.download_service.download_with_retries")
    @patch("src.download_service.download_audio")
    @patch("src.download_service.fetch_info", return_value=VIDEO_INFO)
    def test_audio_preference_resolves_for_each_video(
        self,
        fetch_info,
        download_audio,
        download_with_retries,
    ):
        download_audio.return_value = (
            {"title": "Audio"},
            Path("Audio.webm"),
        )
        download_with_retries.side_effect = (
            lambda label, action, authentication: action()
        )

        result = download_one_result(
            "https://youtu.be/example",
            audio_preference(128),
            ".",
            {},
            show_summary=False,
        )

        selected = download_audio.call_args.args[1]
        self.assertEqual(selected["format_id"], "audio-160")
        self.assertTrue(result["quality"].startswith("Audio webm"))


if __name__ == "__main__":
    unittest.main()

