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


def video_preference(quality):
    return {"type": "video", "quality": int(quality)}


def audio_preference(bitrate):
    return {"type": "audio", "bitrate": int(bitrate)}


def preference_label(preference):
    if preference["type"] == "audio":
        return f"Audio near {preference['bitrate']} kbps"
    return f"Video {preference['quality']}p"


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
