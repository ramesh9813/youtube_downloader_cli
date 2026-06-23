from .console import friendly_download_error
from .downloads import (
    download_audio,
    download_video,
    download_with_retries,
)
from .formats import (
    audio_fallback_order,
    audio_format_label,
    list_audio_formats,
    list_qualities,
    nearest_audio_format,
    nearest_video_quality,
    video_fallback_order,
)
from .metadata import fetch_info
from .playlists import (
    is_playlist_info,
    list_playlist_entries,
    print_playlist_summary,
)
from .preferences import (
    choose_available_audio_format,
    is_audio_format_near,
    preference_label,
)


def download_one_result(
    link,
    preference,
    output_dir,
    authentication,
    attempts,
    show_summary=True,
    allow_playlist=True,
):
    if not link:
        print("No link provided.")
        return {
            "status": "failed",
            "link": link,
            "quality": "",
            "title": "",
            "saved_path": "",
            "message": "No link provided.",
        }

    try:
        info = fetch_info(link, authentication)
        if allow_playlist and is_playlist_info(info):
            return download_playlist_result(
                link,
                info,
                preference,
                output_dir,
                authentication,
                attempts,
            )
        qualities = list_qualities(info)
        audio_formats = list_audio_formats(info)
        if preference["type"] == "audio":
            selected_format = nearest_audio_format(
                audio_formats,
                preference["bitrate"],
            )
            if selected_format is None:
                raise RuntimeError(
                    "No downloadable audio format was found."
                )
            if not is_audio_format_near(
                selected_format,
                preference["bitrate"],
            ):
                chosen_format = choose_available_audio_format(
                    audio_formats,
                    preference,
                )
                if chosen_format is not None:
                    selected_format = chosen_format
            selected_bitrate = selected_format.get("abr") or 0
            if selected_bitrate != preference["bitrate"]:
                print(
                    f"Audio near {preference['bitrate']} kbps is not available. "
                    f"Using {audio_format_label(selected_format)} instead."
                )
            (
                result,
                saved_path,
                selected_format,
            ) = download_selected_audio(
                link,
                selected_format,
                audio_formats,
                output_dir,
                authentication,
                attempts,
            )
            format_label = (
                f"Audio {audio_format_label(selected_format)}"
            )
            media_name = "Audio name"
            format_name = "Audio format"
            location_name = "Your audio downloaded at this"
        else:
            selected_quality = nearest_video_quality(
                qualities,
                preference["quality"],
            )
            if selected_quality is None:
                raise RuntimeError(
                    "No downloadable video quality was found."
                )
            if selected_quality != preference["quality"]:
                print(
                    f"Requested {preference['quality']}p is not available. "
                    f"Using {selected_quality}p instead."
                )
            (
                result,
                saved_path,
                selected_quality,
            ) = download_selected_video(
                link,
                selected_quality,
                qualities,
                output_dir,
                authentication,
                attempts,
            )
            format_label = f"{selected_quality}p"
            media_name = "Video name"
            format_name = "Quality"
            location_name = "Your video downloaded at this"

        title = result.get("title", "Unknown title")
        if show_summary:
            print_download_summary(
                link,
                title,
                format_label,
                saved_path,
                media_name,
                format_name,
                location_name,
            )

        return {
            "status": "downloaded",
            "link": link,
            "quality": format_label,
            "title": title,
            "saved_path": str(saved_path),
            "message": "Downloaded.",
        }
    except KeyboardInterrupt:
        print("\nCancelled.")
        return cancelled_result(link)
    except Exception as exc:
        message = friendly_download_error(exc)
        print(f"\nError: {message}")
        return {
            "status": "failed",
            "link": link,
            "quality": preference_label(preference),
            "title": "",
            "saved_path": "",
            "message": message,
        }


def download_playlist_result(
    link,
    info,
    preference,
    output_dir,
    authentication,
    attempts,
):
    title = info.get("title") or "YouTube Playlist"
    entries = list_playlist_entries(info)
    if not entries:
        raise RuntimeError("No downloadable videos were found in the playlist.")

    print(f"\nPlaylist: {title}")
    print(f"Videos found: {len(entries)}")
    print(
        f"Using {preference_label(preference)} with "
        f"{attempts} attempt(s) per format."
    )

    results = []
    for index, entry in enumerate(entries, start=1):
        print(
            f"\n[Playlist {index}/{len(entries)}] "
            f"{entry['title']}"
        )
        if entry["error"]:
            print(f"Skipped: {entry['error']}")
            results.append(
                {
                    "status": "failed",
                    "link": entry["link"],
                    "quality": preference_label(preference),
                    "title": entry["title"],
                    "saved_path": "",
                    "message": entry["error"],
                }
            )
            continue

        result = download_one_result(
            entry["link"],
            preference,
            output_dir,
            authentication,
            attempts,
            show_summary=False,
            allow_playlist=False,
        )
        if not result.get("title"):
            result["title"] = entry["title"]
        results.append(result)
        if result["status"] == "cancelled":
            break

    print_playlist_summary(title, results)
    downloaded = sum(
        result.get("status") == "downloaded" for result in results
    )
    failed = sum(
        result.get("status") == "failed" for result in results
    )
    cancelled = any(
        result.get("status") == "cancelled" for result in results
    )
    if cancelled:
        status = "cancelled"
    elif downloaded:
        status = "downloaded"
    else:
        status = "failed"

    return {
        "status": status,
        "link": link,
        "quality": preference_label(preference),
        "title": title,
        "saved_path": "",
        "message": (
            f"Playlist downloaded: {downloaded}; failed: {failed}; "
            f"total processed: {len(results)}."
        ),
    }


def download_selected_audio(
    link,
    selected_format,
    audio_formats,
    output_dir,
    authentication,
    attempts,
):
    candidates = audio_fallback_order(audio_formats, selected_format)
    for index, audio_format in enumerate(candidates):
        label = f"Audio {audio_format_label(audio_format)}"
        try:
            result, saved_path = download_with_retries(
                label,
                lambda item=audio_format: download_audio(
                    link,
                    item,
                    output_dir,
                    authentication,
                ),
                authentication,
                attempts,
            )
            return result, saved_path, audio_format
        except Exception:
            if index + 1 >= len(candidates):
                raise
            next_label = audio_format_label(candidates[index + 1])
            print(f"All {attempts} attempts failed for {label}.")
            print(f"Trying another audio format: {next_label}")


def download_selected_video(
    link,
    selected_quality,
    qualities,
    output_dir,
    authentication,
    attempts,
):
    candidates = video_fallback_order(qualities, selected_quality)
    for index, quality in enumerate(candidates):
        try:
            result, saved_path = download_with_retries(
                f"Video {quality}p",
                lambda value=quality: download_video(
                    link,
                    value,
                    output_dir,
                    authentication,
                ),
                authentication,
                attempts,
            )
            return result, saved_path, quality
        except Exception:
            if index + 1 >= len(candidates):
                raise
            next_quality = candidates[index + 1]
            print(
                f"All {attempts} attempts failed for video {quality}p."
            )
            print(f"Trying another video quality: {next_quality}p")


def print_download_summary(
    link,
    title,
    format_label,
    saved_path,
    media_name,
    format_name,
    location_name,
):
    print("\nSummary")
    print(f"Link: {link}")
    print(f"{media_name}: {title}")
    print(f"{format_name}: {format_label}")
    print(f"Saved file: {saved_path}")
    print(f"{location_name}: {saved_path.parent}")


def cancelled_result(link):
    return {
        "status": "cancelled",
        "link": link,
        "quality": "",
        "title": "",
        "saved_path": "",
        "message": "Cancelled.",
    }
