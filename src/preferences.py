from .console import read_input
from .parsing import is_exit_command


VIDEO_QUALITY_OPTIONS = (
    4320,
    2160,
    1440,
    1080,
    720,
    480,
    360,
    240,
    144,
)
AUDIO_BITRATE_OPTIONS = (320, 256, 192, 160, 128, 96, 64)
AUDIO_NEAR_TOLERANCE_KBPS = 32


def video_preference(quality):
    return {"type": "video", "quality": int(quality)}


def audio_preference(bitrate):
    return {"type": "audio", "bitrate": int(bitrate)}


def preference_label(preference):
    if preference["type"] == "audio":
        return f"Audio near {preference['bitrate']} kbps"
    return f"Video {preference['quality']}p"


def is_audio_format_near(audio_format, requested_bitrate):
    bitrate = audio_format.get("abr") or 0
    return bool(bitrate) and (
        abs(bitrate - requested_bitrate)
        <= AUDIO_NEAR_TOLERANCE_KBPS
    )


def choose_available_audio_format(audio_formats, preference):
    print(
        f"\nNo audio format is near {preference['bitrate']} kbps "
        "for this video."
    )
    print("Available audio formats:")
    for index, audio_format in enumerate(audio_formats, start=1):
        bitrate = (
            f", {audio_format['abr']:.0f} kbps"
            if audio_format.get("abr")
            else ""
        )
        print(
            f"{index}. {audio_format['ext']} "
            f"({audio_format['acodec']}{bitrate})"
        )

    while True:
        selected = read_input(
            "Choose an audio format number, or e to use the nearest format: "
        )
        if is_exit_command(selected):
            return None
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(audio_formats):
                audio_format = audio_formats[index - 1]
                bitrate = audio_format.get("abr")
                if bitrate:
                    preference["bitrate"] = round(bitrate)
                    print(
                        f"Audio default changed to near "
                        f"{preference['bitrate']} kbps for the rest of "
                        "this session."
                    )
                return audio_format
        print("Enter a valid number from the list.")


def choose_session_preference(current):
    choices = []
    print(f"\nCurrent default: {preference_label(current)}")
    print("Video quality:")
    for quality in VIDEO_QUALITY_OPTIONS:
        choices.append(video_preference(quality))
        print(f"{len(choices)}. {quality}p")

    print("Audio quality:")
    for bitrate in AUDIO_BITRATE_OPTIONS:
        choices.append(audio_preference(bitrate))
        print(f"{len(choices)}. Audio near {bitrate} kbps")

    while True:
        selected = read_input(
            "Choose a default quality number, or e to keep the current default: "
        )
        if is_exit_command(selected):
            return current
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(choices):
                preference = choices[index - 1]
                print(
                    f"Default changed to {preference_label(preference)}. "
                    "It will be used until you change it or exit."
                )
                return preference
        print("Enter a valid number from the list.")
