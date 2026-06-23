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
    @patch("src.download_service.print_playlist_summary")
    @patch("src.download_service.download_with_retries")
    @patch("src.download_service.download_video")
    @patch("src.download_service.fetch_info")
    def test_playlist_downloads_every_entry_with_existing_settings(
        self,
        fetch_info,
        download_video,
        download_with_retries,
        print_playlist_summary,
    ):
        playlist_info = {
            "_type": "playlist",
            "title": "My Playlist",
            "entries": [
                {"id": "one", "title": "First"},
                {"id": "two", "title": "Second"},
            ],
        }
        fetch_info.side_effect = [
            playlist_info,
            VIDEO_INFO,
            VIDEO_INFO,
        ]
        download_video.side_effect = [
            ({"title": "First"}, Path("First.mp4")),
            ({"title": "Second"}, Path("Second.mp4")),
        ]
        download_with_retries.side_effect = (
            lambda label, action, authentication, attempts: action()
        )

        result = download_one_result(
            "https://www.youtube.com/playlist?list=PL123",
            video_preference(720),
            ".",
            {},
            5,
            show_summary=False,
        )

        self.assertEqual(result["status"], "downloaded")
        self.assertEqual(result["title"], "My Playlist")
        self.assertEqual(download_video.call_count, 2)
        self.assertEqual(
            [
                call.args[0]
                for call in download_video.call_args_list
            ],
            [
                "https://www.youtube.com/watch?v=one",
                "https://www.youtube.com/watch?v=two",
            ],
        )
        self.assertEqual(
            [
                call.args[3]
                for call in download_with_retries.call_args_list
            ],
            [5, 5],
        )
        print_playlist_summary.assert_called_once()

    @patch("src.download_service.print_playlist_summary")
    @patch("src.download_service.download_one_result")
    def test_playlist_continues_after_failed_entry(
        self,
        download_one_result_mock,
        print_playlist_summary,
    ):
        download_one_result_mock.side_effect = [
            {
                "status": "failed",
                "link": "one",
                "quality": "720p",
                "title": "First",
                "saved_path": "",
                "message": "Failed.",
            },
            {
                "status": "downloaded",
                "link": "two",
                "quality": "720p",
                "title": "Second",
                "saved_path": "Second.mp4",
                "message": "Downloaded.",
            },
        ]
        from src.download_service import download_playlist_result

        result = download_playlist_result(
            "playlist-link",
            {
                "_type": "playlist",
                "title": "Playlist",
                "entries": [
                    {"id": "one", "title": "First"},
                    {"id": "two", "title": "Second"},
                ],
            },
            video_preference(720),
            ".",
            {},
            2,
        )

        self.assertEqual(result["status"], "downloaded")
        self.assertEqual(download_one_result_mock.call_count, 2)

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
            lambda label, action, authentication, attempts: action()
        )

        result = download_one_result(
            "https://youtu.be/example",
            video_preference(720),
            ".",
            {},
            5,
            show_summary=False,
        )

        self.assertEqual(result["quality"], "480p")
        self.assertEqual(download_video.call_args.args[1], 480)
        self.assertEqual(download_with_retries.call_args.args[3], 5)

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
            lambda label, action, authentication, attempts: action()
        )

        result = download_one_result(
            "https://youtu.be/example",
            audio_preference(128),
            ".",
            {},
            4,
            show_summary=False,
        )

        selected = download_audio.call_args.args[1]
        self.assertEqual(selected["format_id"], "audio-160")
        self.assertTrue(result["quality"].startswith("Audio webm"))
        self.assertEqual(download_with_retries.call_args.args[3], 4)

    @patch(
        "src.download_service.choose_available_audio_format"
    )
    @patch("src.download_service.download_with_retries")
    @patch("src.download_service.download_audio")
    @patch("src.download_service.fetch_info", return_value=VIDEO_INFO)
    def test_distant_audio_prompts_and_updates_session_preference(
        self,
        fetch_info,
        download_audio,
        download_with_retries,
        choose_available_audio_format,
    ):
        preference = audio_preference(320)
        chosen = {
            "type": "audio",
            "format_id": "audio-160",
            "ext": "webm",
            "acodec": "opus",
            "abr": 160,
        }

        def choose(audio_formats, current_preference):
            current_preference["bitrate"] = 160
            return chosen

        choose_available_audio_format.side_effect = choose
        download_audio.return_value = (
            {"title": "Audio"},
            Path("Audio.webm"),
        )
        download_with_retries.side_effect = (
            lambda label, action, authentication, attempts: action()
        )

        result = download_one_result(
            "https://youtu.be/example",
            preference,
            ".",
            {},
            3,
            show_summary=False,
        )

        choose_available_audio_format.assert_called_once()
        self.assertEqual(preference, audio_preference(160))
        self.assertEqual(
            download_audio.call_args.args[1]["format_id"],
            "audio-160",
        )
        self.assertEqual(result["status"], "downloaded")


if __name__ == "__main__":
    unittest.main()
