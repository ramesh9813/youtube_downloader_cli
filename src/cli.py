import sys
from pathlib import Path

from .attempts import choose_session_attempts
from .batch import download_batch
from .config import DEFAULT_DOWNLOAD_ATTEMPTS, DEFAULT_VIDEO_QUALITY
from .console import read_input
from .documentation import print_documentation
from .download_service import download_one_result
from .parsing import (
    is_batch_reference,
    is_exit_command,
    is_probable_url,
    normalize_batch_filename,
    normalize_link,
    parse_args,
)
from .preferences import (
    choose_session_preference,
    preference_label,
    video_preference,
)


def prompt_for_action():
    value = read_input(
        "Enter URL, file, q quality, a attempts, d docs, or e exit: "
    )
    if is_exit_command(value):
        return "exit", None
    if value.lower() == "q":
        return "quality", None
    if value.lower() == "a":
        return "attempts", None
    if value.lower() == "d":
        return "documentation", None
    if value.lower() in {"url", "u"}:
        return "url", None
    if value.lower() in {"file", "f"}:
        return "file", ""
    if is_batch_reference(value):
        return "file", normalize_batch_filename(value)
    if is_probable_url(value):
        return "url", normalize_link(value)
    print(
        "Enter a URL, file, q for quality, a for attempts, "
        "d for documentation, or e to exit."
    )
    return None, None


def prompt_for_link():
    value = read_input(
        "Enter YouTube link, q quality, a attempts, d docs, or e exit: "
    )
    if is_exit_command(value):
        return "exit", None
    if value.lower() == "q":
        return "quality", None
    if value.lower() == "a":
        return "attempts", None
    if value.lower() == "d":
        return "documentation", None
    return "url", normalize_link(value)


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
    batch_file = args.batch_file
    preference = video_preference(
        args.quality or DEFAULT_VIDEO_QUALITY
    )
    attempts = DEFAULT_DOWNLOAD_ATTEMPTS
    authentication = build_authentication(args)
    if authentication is None:
        return 2

    if args.change_quality:
        preference = choose_session_preference(preference)
    if args.change_attempts:
        attempts = choose_session_attempts(attempts)
    if args.show_documentation:
        print_documentation()

    print(f"Current default: {preference_label(preference)}")
    print(f"Current attempts: {attempts}")

    while True:
        if batch_file is not None:
            download_batch(
                batch_file,
                args.output,
                authentication,
                preference,
                attempts,
            )
            batch_file = None
            link = None
            continue

        if not link:
            action, value = prompt_for_action()
            if action is None:
                continue
            if action == "exit":
                print("Exited.")
                return 0
            if action == "quality":
                preference = choose_session_preference(preference)
                continue
            if action == "attempts":
                attempts = choose_session_attempts(attempts)
                continue
            if action == "documentation":
                print_documentation()
                continue
            if action == "file":
                batch_file = value
                continue

            if value:
                link = value
            else:
                link_action, link_value = prompt_for_link()
                if link_action == "exit":
                    print("Exited.")
                    return 0
                if link_action == "quality":
                    preference = choose_session_preference(preference)
                    continue
                if link_action == "attempts":
                    attempts = choose_session_attempts(attempts)
                    continue
                if link_action == "documentation":
                    print_documentation()
                    continue
                link = link_value

        result = download_one_result(
            link,
            preference,
            args.output,
            authentication,
            attempts,
        )
        if result["status"] == "cancelled":
            return 0

        link = None
