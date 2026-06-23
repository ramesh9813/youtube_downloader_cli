"""Compatibility entry point for the YouTube downloader CLI."""

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
