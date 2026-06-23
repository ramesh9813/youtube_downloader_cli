import shutil
from pathlib import Path

from .authentication import (
    authentication_options,
    browser_failure_count,
    clear_active_authentication,
    is_bot_check_error,
    is_cookie_access_error,
    mark_browser_failed,
    prompt_for_authentication,
)
from .config import DOWNLOAD_ATTEMPTS
from .console import (
    QuietDownloadLogger,
    Spinner,
    friendly_download_error,
    make_progress_hook,
)
from .formats import (
    audio_format_label,
)
from .runtime import ensure_dependencies, import_yt_dlp


def download_with_retries(label, download_action, authentication):
    last_error = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        print(f"\n{label} - attempt {attempt}/{DOWNLOAD_ATTEMPTS}")
        while True:
            try:
                return download_action()
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                if is_bot_check_error(exc):
                    print(
                        "\nYouTube requested verification during the download."
                    )
                    if (
                        not authentication.get("use_for_current")
                        and (
                            authentication.get("browser")
                            or authentication.get("cookie_file")
                        )
                    ):
                        authentication["use_for_current"] = True
                        print(
                            f"Retrying {label} with authentication from this "
                            "CLI session..."
                        )
                        continue
                    if prompt_for_authentication(authentication):
                        print(
                            f"Retrying {label} with browser authentication..."
                        )
                        continue
                    raise RuntimeError(
                        "YouTube verification was cancelled."
                    ) from exc
                if authentication and is_cookie_access_error(exc):
                    failed_browser = authentication.get("browser")
                    print(
                        "\nCould not read the selected browser cookies: "
                        f"{friendly_download_error(exc)}"
                    )
                    if failed_browser:
                        mark_browser_failed(authentication, failed_browser)
                        if (
                            browser_failure_count(
                                authentication,
                                failed_browser,
                            )
                            < 2
                        ):
                            print(
                                f"Fully close all {failed_browser.title()} "
                                "windows and background processes before the "
                                "final retry."
                            )
                        else:
                            print(
                                f"{failed_browser.title()} cookie access failed "
                                "twice and is now disabled for this CLI session."
                            )
                    else:
                        clear_active_authentication(authentication)
                    if prompt_for_authentication(authentication):
                        print(
                            f"Retrying {label} with new authentication..."
                        )
                        continue
                    raise RuntimeError(
                        "Browser authentication was cancelled."
                    ) from exc
                last_error = exc
                print(
                    f"Attempt {attempt} failed: "
                    f"{friendly_download_error(exc)}"
                )
                if attempt < DOWNLOAD_ATTEMPTS:
                    print("Retrying automatically...")
                break

    raise last_error


def find_ffmpeg_location():
    ensure_dependencies()
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return None

    try:
        import imageio_ffmpeg
    except ImportError:
        return None

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    if ffmpeg_path and Path(ffmpeg_path).exists():
        return ffmpeg_path
    return None


def download_video(link, quality, output_dir, authentication):
    yt_dlp = import_yt_dlp()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    ffmpeg_location = find_ffmpeg_location()
    has_ffmpeg = bool(shutil.which("ffmpeg") or ffmpeg_location)
    if has_ffmpeg:
        format_selector = (
            f"bestvideo[height<={quality}]+bestaudio/"
            f"best[height<={quality}]/best"
        )
    else:
        print(
            "FFmpeg was not found. Install dependencies with: "
            "python -m pip install -e ."
        )
        print("Downloading the best single-file video format available.")
        format_selector = f"best[height<={quality}]/best"

    activity = Spinner(f"Connecting to media server for {quality}p")
    options = {
        "format": format_selector,
        "merge_output_format": "mp4",
        "outtmpl": str(
            output_path / "%(title)s [%(id)s].%(ext)s"
        ),
        "progress_hooks": [make_progress_hook(activity)],
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "logger": QuietDownloadLogger(),
        "retries": 0,
        "fragment_retries": 0,
        **authentication_options(authentication),
    }
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location

    activity.start()
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            result = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(result)
            final_path = Path(filename)
            if final_path.suffix != ".mp4":
                mp4_path = final_path.with_suffix(".mp4")
                if mp4_path.exists():
                    final_path = mp4_path
            return result, final_path
    finally:
        activity.stop()


def download_audio(link, audio_format, output_dir, authentication):
    yt_dlp = import_yt_dlp()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    label = audio_format_label(audio_format)
    activity = Spinner(
        f"Connecting to media server for audio {label}"
    )
    options = {
        "format": audio_format["format_id"],
        "outtmpl": str(
            output_path / "%(title)s [%(id)s].%(ext)s"
        ),
        "progress_hooks": [make_progress_hook(activity)],
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "logger": QuietDownloadLogger(),
        "retries": 0,
        "fragment_retries": 0,
        **authentication_options(authentication),
    }

    activity.start()
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            result = ydl.extract_info(link, download=True)
            return result, Path(ydl.prepare_filename(result))
    finally:
        activity.stop()


