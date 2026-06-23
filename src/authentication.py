import shutil
from pathlib import Path

from .config import BROWSER_LOCATIONS
from .console import read_input
from .parsing import is_exit_command


def authentication_options(authentication):
    if not authentication.get(
        "use_for_current",
        authentication.get("forced", False),
    ):
        return {}
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
        if shutil.which(executable_names[browser]) or any(
            path.is_file() for path in locations
        ):
            browsers.append(browser)
    return browsers


def browser_failure_count(authentication, browser):
    return authentication.get("browser_failures", {}).get(browser, 0)


def mark_browser_failed(authentication, browser):
    failures = authentication.setdefault("browser_failures", {})
    failures[browser] = failures.get(browser, 0) + 1
    authentication.pop("browser", None)
    authentication.pop("cookie_file", None)
    authentication["use_for_current"] = False


def clear_active_authentication(authentication):
    authentication.pop("browser", None)
    authentication.pop("cookie_file", None)
    authentication["use_for_current"] = False


def prompt_for_authentication(authentication):
    browsers = [
        browser
        for browser in detected_browsers()
        if browser_failure_count(authentication, browser) < 2
    ]

    print("\nYouTube requested browser verification.")
    print(
        "Open YouTube in a browser, sign in, and complete any verification "
        "shown there."
    )
    print(
        "Then fully close every window of that browser before selecting it below."
    )
    print(
        "The selected browser cookies are read locally and used only by this "
        "downloader process."
    )
    print("Available authentication choices:")
    for index, browser in enumerate(browsers, start=1):
        if browser_failure_count(authentication, browser):
            print(
                f"{index}. Retry {browser.title()} cookies after closing it "
                "(final attempt)"
            )
        else:
            print(f"{index}. Use {browser.title()} cookies")
    cookie_file_index = len(browsers) + 1
    print(f"{cookie_file_index}. Use a cookies.txt file")

    while True:
        selected = read_input(
            "Choose authentication number, or e to cancel this download: "
        )
        if is_exit_command(selected):
            return False
        if not selected.isdigit():
            print("Enter a valid number from the list.")
            continue

        index = int(selected)
        if 1 <= index <= len(browsers):
            browser = browsers[index - 1]
            authentication.pop("cookie_file", None)
            authentication["browser"] = browser
            authentication["use_for_current"] = True
            print(
                f"Using signed-in {browser.title()} cookies for this CLI session."
            )
            print("Retrying video information...")
            return True
        if index == cookie_file_index:
            cookie_file = read_input(
                "Enter path to cookies.txt, or e to cancel: "
            )
            if is_exit_command(cookie_file):
                return False
            path = Path(cookie_file.strip('"').strip("'")).expanduser()
            if not path.is_absolute():
                path = Path.cwd() / path
            if not path.is_file():
                print(f"Cookie file not found: {path}")
                continue
            authentication.pop("browser", None)
            authentication["cookie_file"] = str(path.resolve())
            authentication["use_for_current"] = True
            print("Using the selected cookies.txt file for this CLI session.")
            print("Retrying video information...")
            return True
        print("Enter a valid number from the list.")


