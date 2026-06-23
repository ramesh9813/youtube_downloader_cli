from .authentication import (
    authentication_options,
    browser_failure_count,
    clear_active_authentication,
    is_bot_check_error,
    is_cookie_access_error,
    mark_browser_failed,
    prompt_for_authentication,
)
from .console import QuietDownloadLogger, Spinner, friendly_download_error
from .runtime import import_yt_dlp


def fetch_info(link, authentication):
    yt_dlp = import_yt_dlp()
    authentication["use_for_current"] = bool(authentication.get("forced"))
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
                print(
                    "\nYouTube blocked the anonymous request to confirm you are "
                    "not a bot."
                )
                if (
                    not authentication.get("use_for_current")
                    and (
                        authentication.get("browser")
                        or authentication.get("cookie_file")
                    )
                ):
                    authentication["use_for_current"] = True
                    print(
                        "Retrying with the authentication selected earlier in "
                        "this CLI session..."
                    )
                    continue
                if prompt_for_authentication(authentication):
                    continue
                raise RuntimeError(
                    "YouTube verification was cancelled."
                ) from exc
            if authentication and is_cookie_access_error(exc):
                failed_browser = authentication.get("browser")
                print(
                    "\nCould not read the selected browser cookies: "
                    f"{friendly_download_error(exc)}"
                )
                if failed_browser:
                    mark_browser_failed(authentication, failed_browser)
                    if (
                        browser_failure_count(
                            authentication,
                            failed_browser,
                        )
                        < 2
                    ):
                        print(
                            f"Fully close all {failed_browser.title()} windows "
                            "and background processes, then choose its final retry."
                        )
                    else:
                        print(
                            f"{failed_browser.title()} cookie access failed twice "
                            "and will not be offered again in this CLI session."
                        )
                else:
                    clear_active_authentication(authentication)
                if prompt_for_authentication(authentication):
                    continue
                raise RuntimeError(
                    "Browser authentication was cancelled."
                ) from exc
            raise
        finally:
            spinner.stop()
