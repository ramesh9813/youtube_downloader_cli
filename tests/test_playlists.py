import unittest

from src.playlists import (
    is_playlist_info,
    list_playlist_entries,
    playlist_entry_link,
    remove_playlist_parameters,
)


class PlaylistTests(unittest.TestCase):
    def test_detects_playlist_metadata(self):
        self.assertTrue(
            is_playlist_info(
                {"_type": "playlist", "entries": []}
            )
        )
        self.assertFalse(
            is_playlist_info({"_type": "video", "entries": []})
        )

    def test_builds_youtube_url_from_entry_id(self):
        self.assertEqual(
            playlist_entry_link({"id": "abc123"}),
            "https://www.youtube.com/watch?v=abc123",
        )

    def test_removes_playlist_parameters_from_video_url(self):
        self.assertEqual(
            remove_playlist_parameters(
                "https://www.youtube.com/watch?v=abc&list=PL123&index=2"
            ),
            "https://www.youtube.com/watch?v=abc",
        )

    def test_lists_unavailable_entries_as_failures(self):
        entries = list_playlist_entries(
            {
                "entries": [
                    None,
                    {
                        "id": "abc",
                        "title": "Available",
                    },
                ]
            }
        )
        self.assertTrue(entries[0]["error"])
        self.assertEqual(
            entries[1]["link"],
            "https://www.youtube.com/watch?v=abc",
        )


if __name__ == "__main__":
    unittest.main()
