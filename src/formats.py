from .console import read_input
from .parsing import is_exit_command


def list_qualities(info):
    choices = {}
    for fmt in info.get("formats", []):
        height = fmt.get("height")
        vcodec = fmt.get("vcodec")
        if not height or not vcodec or vcodec == "none":
            continue
        ext = fmt.get("ext") or "unknown"
        fps = fmt.get("fps")
        label = f"{height}p"
        if fps and fps > 30:
            label += f"{int(fps)}"
        choices.setdefault(
            height,
            {"height": height, "exts": set(), "label": label},
        )
        choices[height]["exts"].add(ext)

    return sorted(
        choices.values(),
        key=lambda item: item["height"],
        reverse=True,
    )


def list_audio_formats(info):
    choices = {}
    for fmt in info.get("formats", []):
        if (
            not fmt.get("format_id")
            or fmt.get("vcodec") != "none"
            or fmt.get("acodec") in {None, "none"}
        ):
            continue

        ext = fmt.get("ext") or "unknown"
        abr = fmt.get("abr") or fmt.get("tbr") or 0
        key = (ext, fmt.get("acodec") or "unknown")
        current = choices.get(key)
        if current is None or abr > current["abr"]:
            choices[key] = {
                "type": "audio",
                "format_id": fmt.get("format_id"),
                "ext": ext,
                "acodec": fmt.get("acodec") or "unknown",
                "abr": abr,
            }

    return sorted(
        choices.values(),
        key=lambda item: (item["abr"], item["ext"]),
        reverse=True,
    )


def choose_format(qualities, audio_formats):
    if not qualities:
        raise RuntimeError(
            "No downloadable video qualities were found for this link."
        )

    choices = []
    print("Available video qualities:")
    for index, item in enumerate(qualities, start=1):
        extensions = ", ".join(sorted(item["exts"]))
        print(f"{index}. {item['height']}p ({extensions})")
        choices.append({"type": "video", "quality": item["height"]})

    if audio_formats:
        print("Available audio formats:")
        for item in audio_formats:
            index = len(choices) + 1
            bitrate = f", {item['abr']:.0f} kbps" if item["abr"] else ""
            print(
                f"{index}. Audio {item['ext']} "
                f"({item['acodec']}{bitrate})"
            )
            choices.append(item)

    while True:
        selected = read_input(
            "Choose video or audio number, or e to exit: "
        )
        if is_exit_command(selected):
            return None
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(choices):
                choice = choices[index - 1]
                if choice["type"] == "video":
                    print(
                        f"Selected video quality: {choice['quality']}p"
                    )
                else:
                    print(
                        f"Selected audio format: "
                        f"{audio_format_label(choice)}"
                    )
                return choice
        print("Enter a valid number from the list.")


def best_quality_at_or_below(qualities, requested):
    if not requested:
        return None
    exact = [
        item["height"]
        for item in qualities
        if item["height"] == requested
    ]
    if exact:
        return exact[0]
    lower = [
        item["height"]
        for item in qualities
        if item["height"] <= requested
    ]
    return max(lower) if lower else min(
        item["height"] for item in qualities
    )


def audio_format_label(audio_format):
    bitrate = (
        f", {audio_format['abr']:.0f} kbps"
        if audio_format.get("abr")
        else ""
    )
    return (
        f"{audio_format['ext']} "
        f"({audio_format['acodec']}{bitrate})"
    )


def video_fallback_order(qualities, selected_quality):
    available = [item["height"] for item in qualities]
    lower = sorted(
        (height for height in available if height < selected_quality),
        reverse=True,
    )
    higher = sorted(
        height for height in available if height > selected_quality
    )
    return [selected_quality, *lower, *higher]


def audio_fallback_order(audio_formats, selected_format):
    return [
        selected_format,
        *[
            item
            for item in audio_formats
            if item["format_id"] != selected_format["format_id"]
        ],
    ]

