import argparse
import itertools
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

EXIT_COMMANDS = {"e", "exit", "q", "quit"}
BATCH_QUALITY = 720
DOWNLOAD_ATTEMPTS = 2
PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_DEPS_DIR = Path(os.environ.get("YTD_DEPS_DIR", PROJECT_DIR / ".ytd_env" / "site-packages"))
BROWSER_LOCATIONS = {
    "firefox": [
        Path(os.environ.get("PROGRAMFILES", "")) / "Mozilla Firefox" / "firefox.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Mozilla Firefox" / "firefox.exe",
    ],
    "chrome": [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ],
    "edge": [
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ],
    "brave": [
        Path(os.environ.get("PROGRAMFILES", "")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
    ],
}
REQUIRED_PACKAGES = {
    "yt-dlp": "yt_dlp",
    "imageio-ffmpeg": "imageio_ffmpeg",
}


def prepare_runtime_environment():
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("YTD_PROJECT_DIR", str(PROJECT_DIR))
    os.environ.setdefault("YTD_DEPS_DIR", str(LOCAL_DEPS_DIR))
    local_deps = str(LOCAL_DEPS_DIR)
    if local_deps not in sys.path:
        sys.path.insert(0, local_deps)


def ensure_dependencies():
    prepare_runtime_environment()
    missing = []
    for package_name, module_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if not missing:
        return

    LOCAL_DEPS_DIR.mkdir(parents=True, exist_ok=True)
    print("Preparing local dependencies. This is needed only the first time.")
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--target",
        str(LOCAL_DEPS_DIR),
        *missing,
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as exc:
        print("Failed to install required dependencies automatically.")
        print("Run this manually from the project folder:")
        print("python -m pip install -r requirements.txt")
        raise SystemExit(exc.returncode)

    importlib_invalidate_caches()


def importlib_invalidate_caches():
    import importlib

    importlib.invalidate_caches()


prepare_runtime_environment()


def import_yt_dlp():
    ensure_dependencies()
    try:
        import yt_dlp
    except ImportError:
        print("Missing dependency: yt-dlp")
        print("Run: python -m pip install -r requirements.txt")
        raise SystemExit(1)
    return yt_dlp


class Spinner:
    def __init__(self, message):
        self.message = message
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._started = False
        self._stopped = False

    def start(self):
        self._started = True
        self._thread.start()

    def stop(self):
        if not self._started or self._stopped:
            return
        self._stopped = True
        self._stop.set()
        self._thread.join(timeout=1)
        print("\r" + " " * 80 + "\r", end="", flush=True)

    def _run(self):
        for frame in itertools.cycle("|/-\\"):
            if self._stop.is_set():
                break
            print(f"\r{frame} {self.message}", end="", flush=True)
            time.sleep(0.12)


class QuietDownloadLogger:
    def debug(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        pass


def normalize_quality(value):
    if not value:
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


def is_probable_url(value):
    lowered = value.lower().strip()
    return (
        lowered.startswith(("http://", "https://", "www."))
        or lowered.startswith(("youtube.com/", "youtu.be/", "m.youtube.com/"))
    )


def normalize_link(value):
    link = value.strip()
    if not link:
        return ""
    if link.startswith(("http://", "https://")):
        return link
    if is_probable_url(link):
        return f"https://{link}"
    return link


def is_exit_command(value):
    return value.strip().lower() in EXIT_COMMANDS


def read_input(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return "e"


def is_batch_reference(value):
    return value.strip().startswith("@")


def normalize_batch_filename(value):
    return value.strip()[1:].strip().strip('"').strip("'")


def parse_args(argv):
    cleaned = []
    for arg in argv:
        # Accept common accidental forms like ---link-- and --720--.
        lowered = arg.lower().strip()
        if lowered in {"---link--", "--link--", "---link", "link"}:
            cleaned.append("--link")
        elif re.fullmatch(r"-*\d+p?-*", lowered):
            cleaned.extend(["--quality", str(normalize_quality(lowered))])
        else:
            cleaned.append(arg)

    parser = argparse.ArgumentParser(
        prog="ytd",
        description="Download a YouTube video by quality.",
    )
    parser.add_argument("positional", nargs="*", help="Optional URL and quality, for example: ytd URL 720")
    parser.add_argument("--link", "-l", nargs="?", help="YouTube video link")
    parser.add_argument("--quality", "-q", help="Preferred video quality, for example: 720")
    parser.add_argument("--file", "-f", dest="batch_file", help="Text file containing YouTube links")
    parser.add_argument("--output", "-o", default=".", help="Download directory")
    parser.add_argument(
        "--cookies-from-browser",
        dest="cookies_browser",
        help="Use YouTube cookies from a signed-in browser, for example: chrome",
    )
    parser.add_argument("--cookies", dest="cookie_file", help="Netscape-format cookies.txt file")
    args = parser.parse_args(cleaned)

    skip_next = False
    for index, item in enumerate(args.positional):
        if skip_next:
            skip_next = False
            continue

        lowered = item.lower()
        next_item = args.positional[index + 1] if index + 1 < len(args.positional) else ""
        if lowered in {"file", "f"}:
            args.batch_file = normalize_batch_filename(next_item) if is_batch_reference(next_item) else next_item
            skip_next = bool(next_item)
        elif lowered in {"url", "u"} and next_item:
            args.link = args.link or normalize_link(next_item)
            skip_next = True
        if is_batch_reference(item):
            args.batch_file = normalize_batch_filename(item)
        elif is_probable_url(item):
            args.link = args.link or normalize_link(item)
        elif normalize_quality(item):
            args.quality = args.quality or str(normalize_quality(item))

    if args.link:
        args.link = normalize_link(args.link)
    args.quality = normalize_quality(args.quality)
    return args


def authentication_options(authentication):
    if authentication.get("browser"):
        return {"cookiesfrombrowser": (authentication["browser"],)}
    if authentication.get("cookie_file"):
        return {"cookiefile": authentication["cookie_file"]}
    return {}


def is_bot_check_error(exc):
    message = str(exc).lower()
    return (
        "sign in to confirm you" in message
        or "not a bot" in message
        or "confirm your age" in message
        or "login required" in message
    )


def is_cookie_access_error(exc):
    message = str(exc).lower()
    return "cookie" in message and any(
        text in message
        for text in (
            "could not copy",
            "failed to decrypt",
            "unable to load",
            "could not find",
            "permission",
            "database",
        )
    )


def detected_browsers():
    browsers = []
    executable_names = {
        "firefox": "firefox",
        "chrome": "chrome",
        "edge": "msedge",
        "brave": "brave",
    }
    for browser, locations in BROWSER_LOCATIONS.items():
        if shutil.which(executable_names[browser]) or any(path.is_file() for path in locations):
            browsers.append(browser)
    return browsers


def prompt_for_authentication(authentication):
    browsers = detected_browsers()
    if not browsers:
        browsers = ["firefox", "chrome", "edge", "brave"]

    print("\nYouTube requested browser verification.")
    print("Open YouTube in a browser, sign in, and complete any verification shown there.")
    print("The selected browser cookies are read locally and used only by this downloader process.")
    print("Available authentication choices:")
    for index, browser in enumerate(browsers, start=1):
        print(f"{index}. Use {browser.title()} cookies")
    cookie_file_index = len(browsers) + 1
    print(f"{cookie_file_index}. Use a cookies.txt file")

    while True:
        selected = read_input("Choose authentication number, or e to cancel this download: ")
        if is_exit_command(selected):
            return False
        if not selected.isdigit():
            print("Enter a valid number from the list.")
            continue

        index = int(selected)
        if 1 <= index <= len(browsers):
            browser = browsers[index - 1]
            authentication.clear()
            authentication["browser"] = browser
            print(f"Using signed-in {browser.title()} cookies for this CLI session.")
            print("Retrying video information...")
            return True
        if index == cookie_file_index:
            cookie_file = read_input("Enter path to cookies.txt, or e to cancel: ")
            if is_exit_command(cookie_file):
                return False
            path = Path(cookie_file.strip('"').strip("'")).expanduser()
            if not path.is_absolute():
                path = Path.cwd() / path
            if not path.is_file():
                print(f"Cookie file not found: {path}")
                continue
            authentication.clear()
            authentication["cookie_file"] = str(path.resolve())
            print("Using the selected cookies.txt file for this CLI session.")
            print("Retrying video information...")
            return True
        print("Enter a valid number from the list.")


def fetch_info(link, authentication):
    yt_dlp = import_yt_dlp()
    while True:
        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "logger": QuietDownloadLogger(),
            **authentication_options(authentication),
        }
        spinner = Spinner("Fetching available video and audio formats")
        spinner.start()
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(link, download=False)
        except Exception as exc:
            spinner.stop()
            if is_bot_check_error(exc):
                print("\nYouTube blocked the anonymous request to confirm you are not a bot.")
                if prompt_for_authentication(authentication):
                    continue
                raise RuntimeError("YouTube verification was cancelled.") from exc
            if authentication and is_cookie_access_error(exc):
                print(f"\nCould not read the selected browser cookies: {friendly_download_error(exc)}")
                authentication.clear()
                if prompt_for_authentication(authentication):
                    continue
            raise
        finally:
            spinner.stop()


def list_qualities(info):
    choices = {}
    for fmt in info.get("formats", []):
        height = fmt.get("height")
        vcodec = fmt.get("vcodec")
        if not height or not vcodec or vcodec == "none":
            continue
        ext = fmt.get("ext") or "unknown"
        fps = fmt.get("fps")
        label = f"{height}p"
        if fps and fps > 30:
            label += f"{int(fps)}"
        choices.setdefault(height, {"height": height, "exts": set(), "label": label})
        choices[height]["exts"].add(ext)

    return sorted(choices.values(), key=lambda item: item["height"], reverse=True)


def list_audio_formats(info):
    choices = {}
    for fmt in info.get("formats", []):
        if (
            not fmt.get("format_id")
            or fmt.get("vcodec") != "none"
            or fmt.get("acodec") in {None, "none"}
        ):
            continue

        ext = fmt.get("ext") or "unknown"
        abr = fmt.get("abr") or fmt.get("tbr") or 0
        key = (ext, fmt.get("acodec") or "unknown")
        current = choices.get(key)
        if current is None or abr > current["abr"]:
            choices[key] = {
                "type": "audio",
                "format_id": fmt.get("format_id"),
                "ext": ext,
                "acodec": fmt.get("acodec") or "unknown",
                "abr": abr,
            }

    return sorted(
        choices.values(),
        key=lambda item: (item["abr"], item["ext"]),
        reverse=True,
    )


def choose_format(qualities, audio_formats):
    if not qualities:
        raise RuntimeError("No downloadable video qualities were found for this link.")

    choices = []
    print("Available video qualities:")
    for index, item in enumerate(qualities, start=1):
        extensions = ", ".join(sorted(item["exts"]))
        print(f"{index}. {item['height']}p ({extensions})")
        choices.append({"type": "video", "quality": item["height"]})

    if audio_formats:
        print("Available audio formats:")
        for item in audio_formats:
            index = len(choices) + 1
            bitrate = f", {item['abr']:.0f} kbps" if item["abr"] else ""
            print(f"{index}. Audio {item['ext']} ({item['acodec']}{bitrate})")
            choices.append(item)

    while True:
        selected = read_input("Choose video or audio number, or e to exit: ")
        if is_exit_command(selected):
            return None
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(choices):
                choice = choices[index - 1]
                if choice["type"] == "video":
                    print(f"Selected video quality: {choice['quality']}p")
                else:
                    print(f"Selected audio format: {audio_format_label(choice)}")
                return choice
        print("Enter a valid number from the list.")


def best_quality_at_or_below(qualities, requested):
    if not requested:
        return None
    exact = [item["height"] for item in qualities if item["height"] == requested]
    if exact:
        return exact[0]
    lower = [item["height"] for item in qualities if item["height"] <= requested]
    return max(lower) if lower else min(item["height"] for item in qualities)


def audio_format_label(audio_format):
    bitrate = f", {audio_format['abr']:.0f} kbps" if audio_format.get("abr") else ""
    return f"{audio_format['ext']} ({audio_format['acodec']}{bitrate})"


def make_progress_hook(activity=None):
    last_line_len = 0

    def hook(status):
        nonlocal last_line_len
        if activity:
            activity.stop()
        if status.get("status") == "downloading":
            percent = status.get("_percent_str", "").strip()
            speed = status.get("_speed_str", "").strip()
            eta = status.get("_eta_str", "").strip()
            text = f"Downloading {percent}"
            if speed:
                text += f" at {speed}"
            if eta:
                text += f" ETA {eta}"
            padding = " " * max(0, last_line_len - len(text))
            print(f"\r{text}{padding}", end="", flush=True)
            last_line_len = len(text)
        elif status.get("status") == "finished":
            print("\rDownload finished. Processing media..." + " " * 20)

    return hook


def friendly_download_error(exc):
    message = str(exc).replace("\r", " ").replace("\n", " ").strip()
    lowered = message.lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "The media server timed out while sending data."
    if "http error 403" in lowered:
        return "The media server refused this format (HTTP 403)."
    if "http error 429" in lowered:
        return "YouTube temporarily rate-limited the request (HTTP 429)."
    if "unable to download" in lowered:
        return "The selected media stream could not be downloaded."
    return short_text(message, 180)


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
                    print("\nYouTube requested verification during the download.")
                    if prompt_for_authentication(authentication):
                        print(f"Retrying {label} with browser authentication...")
                        continue
                    raise RuntimeError("YouTube verification was cancelled.") from exc
                if authentication and is_cookie_access_error(exc):
                    print(f"\nCould not read the selected browser cookies: {friendly_download_error(exc)}")
                    authentication.clear()
                    if prompt_for_authentication(authentication):
                        print(f"Retrying {label} with new authentication...")
                        continue
                last_error = exc
                print(f"Attempt {attempt} failed: {friendly_download_error(exc)}")
                if attempt < DOWNLOAD_ATTEMPTS:
                    print("Retrying automatically...")
                break

    raise last_error


def video_fallback_order(qualities, selected_quality):
    available = [item["height"] for item in qualities]
    lower = sorted((height for height in available if height < selected_quality), reverse=True)
    higher = sorted(height for height in available if height > selected_quality)
    return [selected_quality, *lower, *higher]


def audio_fallback_order(audio_formats, selected_format):
    return [
        selected_format,
        *[
            item
            for item in audio_formats
            if item["format_id"] != selected_format["format_id"]
        ],
    ]


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
        format_selector = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
    else:
        print("FFmpeg was not found. Install dependencies with: python -m pip install -e .")
        print("Downloading the best single-file video format available.")
        format_selector = f"best[height<={quality}]/best"

    activity = Spinner(f"Connecting to media server for {quality}p")
    options = {
        "format": format_selector,
        "merge_output_format": "mp4",
        "outtmpl": str(output_path / "%(title)s [%(id)s].%(ext)s"),
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
    activity = Spinner(f"Connecting to media server for audio {label}")
    options = {
        "format": audio_format["format_id"],
        "outtmpl": str(output_path / "%(title)s [%(id)s].%(ext)s"),
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
        selected_quality = best_quality_at_or_below(qualities, requested_quality)
        selected_format = None

        if not selected_quality:
            if not allow_quality_prompt:
                raise RuntimeError("No downloadable video quality was found.")
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
            print(f"Requested {requested_quality}p is not available. Using {selected_quality}p instead.")

        if selected_format and selected_format["type"] == "audio":
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
                    selected_format = audio_format
                    break
                except Exception:
                    if index + 1 >= len(candidates):
                        raise
                    next_label = audio_format_label(candidates[index + 1])
                    print(f"Both attempts failed for {label}.")
                    print(f"Trying another audio format: {next_label}")

            format_label = f"Audio {selected_format['ext']} ({selected_format['acodec']})"
            media_name = "Audio name"
            format_name = "Audio format"
            location_name = "Your audio downloaded at this"
        else:
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
                    selected_quality = quality
                    break
                except Exception:
                    if index + 1 >= len(candidates):
                        raise
                    next_quality = candidates[index + 1]
                    print(f"Both attempts failed for video {quality}p.")
                    print(f"Trying another video quality: {next_quality}p")

            format_label = f"{selected_quality}p"
            media_name = "Video name"
            format_name = "Quality"
            location_name = "Your video downloaded at this"

        title = result.get("title", "Unknown title")

        if show_summary:
            print("\nSummary")
            print(f"Link: {link}")
            print(f"{media_name}: {title}")
            print(f"{format_name}: {format_label}")
            print(f"Saved file: {saved_path}")
            print(f"{location_name}: {saved_path.parent}")

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
        return {
            "status": "cancelled",
            "link": link,
            "quality": "",
            "title": "",
            "saved_path": "",
            "message": "Cancelled.",
        }
    except Exception as exc:
        print(f"\nError: {friendly_download_error(exc)}")
        return {
            "status": "failed",
            "link": link,
            "quality": f"{requested_quality}p" if requested_quality else "",
            "title": "",
            "saved_path": "",
            "message": friendly_download_error(exc),
        }


def list_files_for_selection(directory):
    return sorted([path for path in Path(directory).iterdir() if path.is_file()], key=lambda path: path.name.lower())


def choose_file(directory):
    files = list_files_for_selection(directory)
    if not files:
        print(f"No files found in: {Path(directory).resolve()}")
        return None

    print(f"\nFiles in {Path(directory).resolve()}:")
    for index, path in enumerate(files, start=1):
        print(f"{index}. {path.name}")

    while True:
        selected = read_input("Choose file number, enter filename, or e to exit: ")
        if is_exit_command(selected):
            return None
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(files):
                return files[index - 1]

        selected_name = normalize_batch_filename(selected) if is_batch_reference(selected) else selected
        selected_path = Path(directory) / selected_name
        if selected_path.is_file():
            return selected_path
        print("Enter a valid file number or filename.")


def resolve_batch_file(batch_file, directory):
    if batch_file is None:
        return None
    if batch_file == "":
        return choose_file(directory)

    path = Path(batch_file)
    if not path.is_absolute():
        path = Path(directory) / path
    if not path.is_file():
        print(f"File not found: {path}")
        return None
    return path


def read_links_from_file(path):
    links = []
    with Path(path).open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            if is_probable_url(value):
                links.append({"line": line_number, "link": normalize_link(value), "error": ""})
            else:
                links.append({"line": line_number, "link": value, "error": "Invalid YouTube link format."})
    return links


def short_text(value, limit):
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def print_batch_table(results):
    rows = []
    for index, result in enumerate(results, start=1):
        details = result.get("saved_path") or result.get("message") or ""
        rows.append(
            [
                str(index),
                result.get("status", ""),
                result.get("quality", ""),
                short_text(result.get("title") or result.get("link"), 40),
                short_text(details, 60),
            ]
        )

    headers = ["#", "Status", "Quality", "Video / Link", "Saved File / Message"]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    separator = "+".join("-" * (width + 2) for width in widths)
    print("\nBatch Summary")
    print(separator)
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print(separator)
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print(separator)

    downloaded = sum(1 for result in results if result.get("status") == "downloaded")
    failed = sum(1 for result in results if result.get("status") == "failed")
    print(f"Downloaded: {downloaded} | Failed: {failed} | Total: {len(results)}")


def download_batch(batch_file, output_dir, authentication, quality=BATCH_QUALITY):
    batch_path = resolve_batch_file(batch_file, Path.cwd())
    if batch_path is None:
        return True

    links = read_links_from_file(batch_path)
    if not links:
        print(f"No links found in: {batch_path}")
        return True

    print(f"\nBatch file: {batch_path}")
    print(f"Downloading {len(links)} item(s) at {quality}p.")

    results = []
    for index, item in enumerate(links, start=1):
        link = item["link"]
        print(f"\n[{index}/{len(links)}] {link}")
        if item["error"]:
            print(f"Skipped: {item['error']}")
            results.append(
                {
                    "status": "failed",
                    "link": link,
                    "quality": f"{quality}p",
                    "title": "",
                    "saved_path": "",
                    "message": f"Line {item['line']}: {item['error']}",
                }
            )
            continue

        result = download_one_result(
            link,
            quality,
            output_dir,
            authentication,
            allow_quality_prompt=False,
            show_summary=False,
        )
        if result["status"] == "cancelled":
            results.append(result)
            break
        results.append(result)

    print_batch_table(results)
    return True


def prompt_for_action():
    value = read_input("Enter url, file, e for exit: ")
    if is_exit_command(value):
        return "exit", None
    if value.lower() in {"url", "u"}:
        return "url", None
    if value.lower() in {"file", "f"}:
        return "file", ""
    if is_batch_reference(value):
        return "file", normalize_batch_filename(value)
    if is_probable_url(value):
        return "url", normalize_link(value)
    print("Enter url for one video, file for a text file list, or e to exit.")
    return None, None


def prompt_for_link():
    value = read_input("Enter YouTube link, or e to exit: ")
    if is_exit_command(value):
        return None
    return normalize_link(value)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    link = args.link
    requested_quality = args.quality
    batch_file = args.batch_file
    authentication = {}
    if args.cookies_browser:
        authentication["browser"] = args.cookies_browser.lower()
    elif args.cookie_file:
        cookie_file = Path(args.cookie_file).expanduser().resolve()
        if not cookie_file.is_file():
            print(f"Cookie file not found: {cookie_file}")
            return 2
        authentication["cookie_file"] = str(cookie_file)

    while True:
        if batch_file is not None:
            download_batch(
                batch_file,
                args.output,
                authentication,
                requested_quality or BATCH_QUALITY,
            )
            batch_file = None
            link = None
            requested_quality = None
            continue

        if not link:
            action, value = prompt_for_action()
            if action is None:
                continue
            if action == "exit":
                print("Exited.")
                return 0
            if action == "file":
                batch_file = value
                continue

            link = value or prompt_for_link()
            requested_quality = None
            if link is None:
                print("Exited.")
                return 0

        result = download_one_result(link, requested_quality, args.output, authentication)
        if result["status"] == "cancelled":
            return 0

        link = None
        requested_quality = None


if __name__ == "__main__":
    raise SystemExit(main())
