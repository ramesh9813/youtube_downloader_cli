import importlib
import os
import subprocess
import sys

from .config import LOCAL_DEPS_DIR, PROJECT_DIR, REQUIRED_PACKAGES


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

    importlib.invalidate_caches()


def import_yt_dlp():
    ensure_dependencies()
    try:
        import yt_dlp
    except ImportError:
        print("Missing dependency: yt-dlp")
        print("Run: python -m pip install -r requirements.txt")
        raise SystemExit(1)
    return yt_dlp


prepare_runtime_environment()

