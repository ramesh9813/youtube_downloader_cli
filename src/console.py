import itertools
import threading
import time


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


def read_input(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return "e"


def short_text(value, limit):
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def friendly_download_error(exc):
    message = str(exc).replace("\r", " ").replace("\n", " ").strip()
    lowered = message.lower()
    if "could not copy" in lowered and "cookie database" in lowered:
        return "The browser cookie database is locked or unavailable."
    if "failed to decrypt" in lowered and "cookie" in lowered:
        return "The browser cookies could not be decrypted."
    if "timed out" in lowered or "timeout" in lowered:
        return "The media server timed out while sending data."
    if "http error 403" in lowered:
        return "The media server refused this format (HTTP 403)."
    if "http error 429" in lowered:
        return "YouTube temporarily rate-limited the request (HTTP 429)."
    if "unable to download" in lowered:
        return "The selected media stream could not be downloaded."
    return short_text(message, 180)


def format_file_size(size_bytes):
    if not size_bytes:
        return ""
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(size_bytes)
    unit = units[0]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            break
        size /= 1024
    if unit == "B":
        return f"{size:.0f}{unit}"
    return f"{size:.2f}{unit}"


def progress_total_size(status):
    formatted = (status.get("_total_bytes_str") or "").strip()
    if formatted and formatted.lower() not in {"unknown", "n/a"}:
        return formatted
    total_bytes = (
        status.get("total_bytes")
        or status.get("total_bytes_estimate")
    )
    return format_file_size(total_bytes)


def progress_downloaded_size(status):
    formatted = (status.get("_downloaded_bytes_str") or "").strip()
    if formatted and formatted.lower() not in {"unknown", "n/a"}:
        return formatted
    return format_file_size(status.get("downloaded_bytes"))


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
            total_size = progress_total_size(status)
            downloaded_size = progress_downloaded_size(status)
            text = f"Downloading {percent}"
            if total_size or downloaded_size:
                size_parts = []
                if total_size:
                    size_parts.append(f"Total {total_size}")
                if downloaded_size:
                    size_parts.append(f"Downloaded {downloaded_size}")
                text += " | " + " / ".join(size_parts)
            if speed:
                text += f" | Speed {speed}"
            if eta:
                text += f" | ETA {eta}"
            padding = " " * max(0, last_line_len - len(text))
            print(f"\r{text}{padding}", end="", flush=True)
            last_line_len = len(text)
        elif status.get("status") == "finished":
            print("\rDownload finished. Processing media..." + " " * 20)

    return hook
