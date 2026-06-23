import unittest
from unittest.mock import patch

from src.formats import (
    audio_fallback_order,
    nearest_audio_format,
    nearest_video_quality,
    video_fallback_order,
)
from src.preferences import (
    audio_preference,
    choose_available_audio_format,
    is_audio_format_near,
    preference_label,
    video_preference,
)


class PreferenceTests(unittest.TestCase):
    def test_video_preference_label(self):
        self.assertEqual(
            preference_label(video_preference(720)),
            "Video 720p",
        )

    def test_audio_preference_label(self):
        self.assertEqual(
            preference_label(audio_preference(128)),
            "Audio near 128 kbps",
        )

    def test_nearest_video_quality_is_selected(self):
        qualities = [{"height": 144}, {"height": 1080}]
        self.assertEqual(
            nearest_video_quality(qualities, 720),
            1080,
        )

    def test_nearest_video_quality_prefers_lower_on_tie(self):
        qualities = [{"height": 600}, {"height": 840}]
        self.assertEqual(
            nearest_video_quality(qualities, 720),
            600,
        )

    def test_video_fallbacks_are_ordered_by_distance(self):
        qualities = [
            {"height": 144},
            {"height": 720},
            {"height": 1080},
            {"height": 480},
        ]
        self.assertEqual(
            video_fallback_order(qualities, 720),
            [720, 480, 1080, 144],
        )

    def test_nearest_audio_bitrate_is_selected(self):
        formats = [
            {"format_id": "low", "abr": 64},
            {"format_id": "high", "abr": 160},
        ]
        self.assertEqual(
            nearest_audio_format(formats, 128)["format_id"],
            "high",
        )

    def test_audio_fallbacks_are_ordered_by_distance(self):
        formats = [
            {"format_id": "64", "abr": 64},
            {"format_id": "128", "abr": 128},
            {"format_id": "160", "abr": 160},
            {"format_id": "256", "abr": 256},
        ]
        selected = formats[1]
        self.assertEqual(
            [
                item["format_id"]
                for item in audio_fallback_order(formats, selected)
            ],
            ["128", "160", "64", "256"],
        )

    def test_audio_within_32_kbps_is_near(self):
        self.assertTrue(
            is_audio_format_near({"abr": 160}, 128)
        )
        self.assertFalse(
            is_audio_format_near({"abr": 160}, 320)
        )

    @patch("src.preferences.read_input", return_value="2")
    def test_available_audio_choice_updates_session_preference(
        self,
        read_input,
    ):
        formats = [
            {
                "format_id": "160",
                "ext": "webm",
                "acodec": "opus",
                "abr": 160,
            },
            {
                "format_id": "96",
                "ext": "m4a",
                "acodec": "mp4a",
                "abr": 96,
            },
        ]
        preference = audio_preference(320)

        selected = choose_available_audio_format(
            formats,
            preference,
        )

        self.assertEqual(selected["format_id"], "96")
        self.assertEqual(preference, audio_preference(96))


if __name__ == "__main__":
    unittest.main()
