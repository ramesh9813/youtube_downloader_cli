import os
from pathlib import Path


EXIT_COMMANDS = {"e", "exit", "quit"}
DEFAULT_VIDEO_QUALITY = 720
DEFAULT_DOWNLOAD_ATTEMPTS = 2
PROJECT_DIR = Path(__file__).resolve().parent.parent
LOCAL_DEPS_DIR = Path(
    os.environ.get("YTD_DEPS_DIR", PROJECT_DIR / ".ytd_env" / "site-packages")
)
BROWSER_LOCATIONS = {
    "firefox": [
        Path(os.environ.get("PROGRAMFILES", "")) / "Mozilla Firefox" / "firefox.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Mozilla Firefox" / "firefox.exe",
    ],
    "chrome": [
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Google"
        / "Chrome"
        / "Application"
        / "chrome.exe",
    ],
    "edge": [
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
    ],
    "brave": [
        Path(os.environ.get("PROGRAMFILES", ""))
        / "BraveSoftware"
        / "Brave-Browser"
        / "Application"
        / "brave.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "BraveSoftware"
        / "Brave-Browser"
        / "Application"
        / "brave.exe",
    ],
}
REQUIRED_PACKAGES = {
    "yt-dlp": "yt_dlp",
    "imageio-ffmpeg": "imageio_ffmpeg",
}
