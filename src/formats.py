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


def nearest_video_quality(qualities, requested):
    if not requested:
        return None
    available = [item["height"] for item in qualities]
    if not available:
        return None
    return min(
        available,
        key=lambda height: (
            abs(height - requested),
            height > requested,
            height,
        ),
    )


def nearest_audio_format(audio_formats, requested_bitrate):
    if not audio_formats:
        return None
    with_bitrate = [
        item for item in audio_formats if item.get("abr")
    ]
    if not with_bitrate:
        return audio_formats[0]
    return min(
        with_bitrate,
        key=lambda item: (
            abs(item["abr"] - requested_bitrate),
            item["abr"] > requested_bitrate,
            item["abr"],
        ),
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
    return sorted(
        available,
        key=lambda height: (
            height != selected_quality,
            abs(height - selected_quality),
            height > selected_quality,
            height,
        ),
    )


def audio_fallback_order(audio_formats, selected_format):
    selected_bitrate = selected_format.get("abr") or 0
    return sorted(
        audio_formats,
        key=lambda item: (
            item["format_id"] != selected_format["format_id"],
            abs((item.get("abr") or 0) - selected_bitrate),
            (item.get("abr") or 0) > selected_bitrate,
            item.get("abr") or 0,
        ),
    )
