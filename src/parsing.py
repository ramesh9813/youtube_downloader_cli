import argparse
import re

from .config import EXIT_COMMANDS


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


def is_batch_reference(value):
    return value.strip().startswith("@")


def normalize_batch_filename(value):
    return value.strip()[1:].strip().strip('"').strip("'")


def parse_args(argv):
    cleaned = []
    expecting_quality_value = False
    for arg in argv:
        lowered = arg.lower().strip()
        if expecting_quality_value:
            cleaned.append(str(normalize_quality(arg) or arg))
            expecting_quality_value = False
            continue
        if lowered in {"--quality", "-q"}:
            cleaned.append(lowered)
            expecting_quality_value = True
            continue
        if lowered in {"---link--", "--link--", "---link", "link"}:
            cleaned.append("--link")
        elif re.fullmatch(r"-*\d+p?-*", lowered):
            cleaned.extend(["--quality", str(normalize_quality(lowered))])
        else:
            cleaned.append(arg)

    parser = argparse.ArgumentParser(
        prog="ytd",
        description="Download a YouTube video by quality.",
        epilog=(
            "Interactive shortcuts: URL, url/u, file/f, @file, "
            "q=quality, a=attempts, d=documentation, "
            "e/exit/quit=exit."
        ),
    )
    parser.add_argument(
        "positional",
        nargs="*",
        help="Optional URL and quality, for example: ytd URL 720",
    )
    parser.add_argument("--link", "-l", nargs="?", help="YouTube video link")
    parser.add_argument(
        "--quality",
        "-q",
        help="Preferred video quality, for example: 720",
    )
    parser.add_argument(
        "--file",
        "-f",
        dest="batch_file",
        help="Text file containing YouTube links",
    )
    parser.add_argument("--output", "-o", default=".", help="Download directory")
    parser.add_argument(
        "--cookies-from-browser",
        dest="cookies_browser",
        help="Use YouTube cookies from a signed-in browser, for example: chrome",
    )
    parser.add_argument(
        "--cookies",
        dest="cookie_file",
        help="Netscape-format cookies.txt file",
    )
    args = parser.parse_args(cleaned)
    args.change_quality = False
    args.change_attempts = False
    args.show_documentation = False

    skip_next = False
    for index, item in enumerate(args.positional):
        if skip_next:
            skip_next = False
            continue

        lowered = item.lower()
        next_item = (
            args.positional[index + 1]
            if index + 1 < len(args.positional)
            else ""
        )
        if lowered in {"file", "f"}:
            args.batch_file = (
                normalize_batch_filename(next_item)
                if is_batch_reference(next_item)
                else next_item
            )
            skip_next = bool(next_item)
        elif lowered in {"url", "u"} and next_item:
            args.link = args.link or normalize_link(next_item)
            skip_next = True
        elif lowered == "q":
            args.change_quality = True
        elif lowered == "a":
            args.change_attempts = True
        elif lowered == "d":
            args.show_documentation = True
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
