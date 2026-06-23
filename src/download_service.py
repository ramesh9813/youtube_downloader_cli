from .console import friendly_download_error
from .downloads import (
    download_audio,
    download_video,
    download_with_retries,
)
from .formats import (
    audio_fallback_order,
    audio_format_label,
    best_quality_at_or_below,
    choose_format,
    list_audio_formats,
    list_qualities,
    video_fallback_order,
)
from .metadata import fetch_info


def download_one_result(
    link,
    requested_quality,
    output_dir,
    authentication,
    allow_quality_prompt=True,
    show_summary=True,
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
        qualities = list_qualities(info)
        audio_formats = list_audio_formats(info)
        selected_quality = best_quality_at_or_below(
            qualities,
            requested_quality,
        )
        selected_format = None

        if not selected_quality:
            if not allow_quality_prompt:
                raise RuntimeError(
                    "No downloadable video quality was found."
                )
            selected_format = choose_format(qualities, audio_formats)
            if selected_format is None:
                return {
                    "status": "cancelled",
                    "link": link,
                    "quality": "",
                    "title": "",
                    "saved_path": "",
                    "message": "Cancelled.",
                }
            if selected_format["type"] == "video":
                selected_quality = selected_format["quality"]
        elif requested_quality and selected_quality != requested_quality:
            print(
                f"Requested {requested_quality}p is not available. "
                f"Using {selected_quality}p instead."
            )

        if selected_format and selected_format["type"] == "audio":
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
            )
            format_label = (
                f"Audio {selected_format['ext']} "
                f"({selected_format['acodec']})"
            )
            media_name = "Audio name"
            format_name = "Audio format"
            location_name = "Your audio downloaded at this"
        else:
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
            "quality": (
                f"{requested_quality}p" if requested_quality else ""
            ),
            "title": "",
            "saved_path": "",
            "message": message,
        }


def download_selected_audio(
    link,
    selected_format,
    audio_formats,
    output_dir,
    authentication,
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
            )
            return result, saved_path, audio_format
        except Exception:
            if index + 1 >= len(candidates):
                raise
            next_label = audio_format_label(candidates[index + 1])
            print(f"Both attempts failed for {label}.")
            print(f"Trying another audio format: {next_label}")


def download_selected_video(
    link,
    selected_quality,
    qualities,
    output_dir,
    authentication,
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
            )
            return result, saved_path, quality
        except Exception:
            if index + 1 >= len(candidates):
                raise
            next_quality = candidates[index + 1]
            print(f"Both attempts failed for video {quality}p.")
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
