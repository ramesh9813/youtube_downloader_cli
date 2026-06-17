import argparse
import itertools
import re
import shutil
import sys
import threading
import time
from pathlib import Path

EXIT_COMMANDS = {"e", "exit", "q", "quit"}
BATCH_QUALITY = 720


def import_yt_dlp():
    try:
        import yt_dlp
    except ImportError:
        print("Missing dependency: yt-dlp")
        print("Install it with: python -m pip install -r requirements.txt")
        raise SystemExit(1)
    return yt_dlp


class Spinner:
    def __init__(self, message):
        self.message = message
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=1)
        print("\r" + " " * 80 + "\r", end="", flush=True)

    def _run(self):
        for frame in itertools.cycle("|/-\\"):
            if self._stop.is_set():
                break
            print(f"\r{frame} {self.message}", end="", flush=True)
            time.sleep(0.12)


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


def fetch_info(link):
    yt_dlp = import_yt_dlp()
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    spinner = Spinner("Fetching available qualities")
    spinner.start()
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(link, download=False)
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


def choose_quality(qualities):
    if not qualities:
        raise RuntimeError("No downloadable video qualities were found for this link.")

    print("Available qualities:")
    for index, item in enumerate(qualities, start=1):
        extensions = ", ".join(sorted(item["exts"]))
        print(f"{index}. {item['height']}p ({extensions})")

    while True:
        selected = read_input("Choose quality number, or e to exit: ")
        if is_exit_command(selected):
            return None
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(qualities):
                return qualities[index - 1]["height"]
        print("Enter a valid number from the list.")


def best_quality_at_or_below(qualities, requested):
    if not requested:
        return None
    exact = [item["height"] for item in qualities if item["height"] == requested]
    if exact:
        return exact[0]
    lower = [item["height"] for item in qualities if item["height"] <= requested]
    return max(lower) if lower else min(item["height"] for item in qualities)


def make_progress_hook():
    last_line_len = 0

    def hook(status):
        nonlocal last_line_len
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


def find_ffmpeg_location():
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


def download_video(link, quality, output_dir):
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

    options = {
        "format": format_selector,
        "merge_output_format": "mp4",
        "outtmpl": str(output_path / "%(title)s [%(id)s].%(ext)s"),
        "progress_hooks": [make_progress_hook()],
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
    }
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location

    with yt_dlp.YoutubeDL(options) as ydl:
        result = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(result)
        final_path = Path(filename)
        if final_path.suffix != ".mp4":
            mp4_path = final_path.with_suffix(".mp4")
            if mp4_path.exists():
                final_path = mp4_path
        return result, final_path


def download_one_result(link, requested_quality, output_dir, allow_quality_prompt=True, show_summary=True):
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
        info = fetch_info(link)
        qualities = list_qualities(info)
        selected_quality = best_quality_at_or_below(qualities, requested_quality)

        if not selected_quality:
            if not allow_quality_prompt:
                raise RuntimeError("No downloadable video quality was found.")
            selected_quality = choose_quality(qualities)
            if selected_quality is None:
                return {
                    "status": "cancelled",
                    "link": link,
                    "quality": "",
                    "title": "",
                    "saved_path": "",
                    "message": "Cancelled.",
                }
        elif requested_quality and selected_quality != requested_quality:
            print(f"Requested {requested_quality}p is not available. Using {selected_quality}p instead.")

        result, saved_path = download_video(link, selected_quality, output_dir)
        title = result.get("title", "Unknown title")

        if show_summary:
            print("\nSummary")
            print(f"Link: {link}")
            print(f"Video name: {title}")
            print(f"Quality: {selected_quality}p")
            print(f"Saved file: {saved_path}")
            print(f"Downloaded directory: {saved_path.parent}")

        return {
            "status": "downloaded",
            "link": link,
            "quality": f"{selected_quality}p",
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
        print(f"\nError: {exc}")
        return {
            "status": "failed",
            "link": link,
            "quality": f"{requested_quality}p" if requested_quality else "",
            "title": "",
            "saved_path": "",
            "message": str(exc),
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


def download_batch(batch_file, output_dir, quality=BATCH_QUALITY):
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
    value = read_input("\nEnter url, file, or e to exit: ")
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

    print(f"Saving videos to: {Path(args.output).resolve()}")
    print("Type e to exit.")

    while True:
        if batch_file is not None:
            download_batch(batch_file, args.output, requested_quality or BATCH_QUALITY)
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

        result = download_one_result(link, requested_quality, args.output)
        if result["status"] == "cancelled":
            return 0

        link = None
        requested_quality = None


if __name__ == "__main__":
    raise SystemExit(main())
