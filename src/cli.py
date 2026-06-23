import sys
from pathlib import Path

from .batch import download_batch
from .config import BATCH_QUALITY
from .console import read_input
from .download_service import download_one_result
from .parsing import (
    is_batch_reference,
    is_exit_command,
    is_probable_url,
    normalize_batch_filename,
    normalize_link,
    parse_args,
)


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


def build_authentication(args):
    authentication = {}
    if args.cookies_browser:
        authentication["browser"] = args.cookies_browser.lower()
        authentication["forced"] = True
        authentication["use_for_current"] = True
    elif args.cookie_file:
        cookie_file = Path(args.cookie_file).expanduser().resolve()
        if not cookie_file.is_file():
            print(f"Cookie file not found: {cookie_file}")
            return None
        authentication["cookie_file"] = str(cookie_file)
        authentication["forced"] = True
        authentication["use_for_current"] = True
    return authentication


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    link = args.link
    requested_quality = args.quality
    batch_file = args.batch_file
    authentication = build_authentication(args)
    if authentication is None:
        return 2

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

        result = download_one_result(
            link,
            requested_quality,
            args.output,
            authentication,
        )
        if result["status"] == "cancelled":
            return 0

        link = None
        requested_quality = None
