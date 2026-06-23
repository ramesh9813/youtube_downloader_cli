from pathlib import Path

from .console import read_input, short_text
from .download_service import download_one_result
from .parsing import (
    is_batch_reference,
    is_exit_command,
    is_probable_url,
    normalize_batch_filename,
    normalize_link,
)


def list_files_for_selection(directory):
    return sorted(
        [path for path in Path(directory).iterdir() if path.is_file()],
        key=lambda path: path.name.lower(),
    )


def choose_file(directory):
    files = list_files_for_selection(directory)
    if not files:
        print(f"No files found in: {Path(directory).resolve()}")
        return None

    print(f"\nFiles in {Path(directory).resolve()}:")
    for index, path in enumerate(files, start=1):
        print(f"{index}. {path.name}")

    while True:
        selected = read_input(
            "Choose file number, enter filename, or e to exit: "
        )
        if is_exit_command(selected):
            return None
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(files):
                return files[index - 1]

        selected_name = (
            normalize_batch_filename(selected)
            if is_batch_reference(selected)
            else selected
        )
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
                links.append(
                    {
                        "line": line_number,
                        "link": normalize_link(value),
                        "error": "",
                    }
                )
            else:
                links.append(
                    {
                        "line": line_number,
                        "link": value,
                        "error": "Invalid YouTube link format.",
                    }
                )
    return links


def print_batch_table(results):
    rows = []
    for index, result in enumerate(results, start=1):
        details = (
            result.get("saved_path")
            or result.get("message")
            or ""
        )
        rows.append(
            [
                str(index),
                result.get("status", ""),
                result.get("quality", ""),
                short_text(
                    result.get("title") or result.get("link"),
                    40,
                ),
                short_text(details, 60),
            ]
        )

    headers = [
        "#",
        "Status",
        "Quality",
        "Video / Link",
        "Saved File / Message",
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    separator = "+".join("-" * (width + 2) for width in widths)
    print("\nBatch Summary")
    print(separator)
    print(
        " | ".join(
            header.ljust(widths[index])
            for index, header in enumerate(headers)
        )
    )
    print(separator)
    for row in rows:
        print(
            " | ".join(
                value.ljust(widths[index])
                for index, value in enumerate(row)
            )
        )
    print(separator)

    downloaded = sum(
        1 for result in results if result.get("status") == "downloaded"
    )
    failed = sum(
        1 for result in results if result.get("status") == "failed"
    )
    print(
        f"Downloaded: {downloaded} | Failed: {failed} | "
        f"Total: {len(results)}"
    )


def download_batch(
    batch_file,
    output_dir,
    authentication,
    quality,
):
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
                    "message": (
                        f"Line {item['line']}: {item['error']}"
                    ),
                }
            )
            continue

        result = download_one_result(
            link,
            quality,
            output_dir,
            authentication,
            allow_quality_prompt=False,
            show_summary=False,
        )
        if result["status"] == "cancelled":
            results.append(result)
            break
        results.append(result)

    print_batch_table(results)
    return True
