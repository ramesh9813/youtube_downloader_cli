from .console import short_text
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


PLAYLIST_TYPES = {"playlist", "multi_video"}


def is_playlist_info(info):
    return (
        isinstance(info, dict)
        and info.get("_type") in PLAYLIST_TYPES
        and info.get("entries") is not None
    )


def playlist_entry_link(entry):
    if not isinstance(entry, dict):
        return ""
    for key in ("webpage_url", "original_url"):
        value = entry.get(key)
        if value:
            return remove_playlist_parameters(value)

    url = entry.get("url") or ""
    if url.startswith(("http://", "https://")):
        return remove_playlist_parameters(url)

    video_id = entry.get("id") or url
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return ""


def remove_playlist_parameters(url):
    parsed = urlsplit(url)
    if "youtube.com" not in parsed.netloc.lower():
        return url
    query = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if key not in {"list", "index", "start_radio"}
    ]
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urlencode(query),
            parsed.fragment,
        )
    )


def list_playlist_entries(info):
    entries = []
    for index, entry in enumerate(info.get("entries") or [], start=1):
        if entry is None:
            entries.append(
                {
                    "position": index,
                    "link": "",
                    "title": "Unavailable playlist entry",
                    "error": "This playlist entry is unavailable.",
                }
            )
            continue

        link = playlist_entry_link(entry)
        entries.append(
            {
                "position": index,
                "link": link,
                "title": entry.get("title") or f"Playlist item {index}",
                "error": "" if link else "Could not determine the video URL.",
            }
        )
    return entries


def print_playlist_summary(title, results):
    print(f"\nPlaylist Summary: {title}")
    headers = ["#", "Status", "Quality", "Video", "Saved File / Message"]
    rows = []
    for index, result in enumerate(results, start=1):
        rows.append(
            [
                str(index),
                result.get("status", ""),
                result.get("quality", ""),
                short_text(
                    result.get("title") or result.get("link"),
                    40,
                ),
                short_text(
                    result.get("saved_path")
                    or result.get("message")
                    or "",
                    60,
                ),
            ]
        )

    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    separator = "+".join("-" * (width + 2) for width in widths)
    print(separator)
    print(
        " | ".join(
            header.ljust(widths[index])
            for index, header in enumerate(headers)
        )
    )
    print(separator)
    for row in rows:
        print(
            " | ".join(
                value.ljust(widths[index])
                for index, value in enumerate(row)
            )
        )
    print(separator)

    downloaded = sum(
        result.get("status") == "downloaded" for result in results
    )
    failed = sum(
        result.get("status") == "failed" for result in results
    )
    cancelled = sum(
        result.get("status") == "cancelled" for result in results
    )
    print(
        f"Downloaded: {downloaded} | Failed: {failed} | "
        f"Cancelled: {cancelled} | Total: {len(results)}"
    )
