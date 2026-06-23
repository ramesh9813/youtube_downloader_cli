DOCUMENTATION = """
YTD DOCUMENTATION
=================

PURPOSE
  Download YouTube video, audio, a complete playlist, or a text-file batch.
  The CLI keeps quality and attempt settings for the current session.

INTERACTIVE SHORTCUTS
  Paste URL       Download that YouTube URL immediately.
  url or u        Ask for one YouTube URL.
  file or f       List local files and choose a batch text file.
  @filename       Use filename as a batch text file.
  q               Change the session video quality or audio bitrate.
  a               Change download attempts per format for this session.
  d               Show this complete documentation.
  e               Exit or cancel the current prompt.
  exit            Exit.
  quit            Exit.

DEFAULTS
  Quality         Video 720p.
  Attempts        2 attempts per selected format.
  Output          Current terminal directory.
  File name       Video Title [YouTubeID].extension

QUALITY SHORTCUT: q
  Video choices:
    4320p, 2160p, 1440p, 1080p, 720p, 480p, 360p, 240p, 144p
  Audio choices:
    320, 256, 192, 160, 128, 96, and 64 kbps targets

  The selected preference applies to all later single and batch downloads
  until q is used again or the CLI exits.

  Video:
    If the exact height is unavailable, the nearest available height is used.
    If two heights are equally near, the lower height is preferred.

  Audio:
    An available stream within 32 kbps of the target is used automatically.
    If no stream is within 32 kbps, the video's actual audio formats are shown.
    Choosing one updates the session audio target for the current and remaining
    single or batch downloads. Enter e there to use the nearest stream without
    changing the saved target.

ATTEMPT SHORTCUT: a
  Enter any whole number greater than zero, such as 5.
  That number is used for every later video/audio format attempt in the session.
  After all attempts fail, another available format is tried in nearest order.
  Enter e in the attempt prompt to keep the current number.

BATCH DOWNLOADS
  Accepted forms:
    file
    f
    @links.txt
    ytd --file links.txt
    ytd file links.txt
    ytd '@links.txt'       Recommended quoting for PowerShell @ syntax

  Batch-file rules:
    One URL per line.
    Blank lines are ignored.
    Lines beginning with # are comments and are ignored.
    Invalid lines appear as failures in the final batch summary.
    A failed URL does not stop the remaining batch.
    The current quality/audio and attempt settings apply to every batch entry.

PLAYLIST DOWNLOADS
  Paste a YouTube playlist URL anywhere a normal URL is accepted.
  The complete playlist is detected automatically and downloaded in order.
  Each playlist video uses the active video/audio quality and attempt settings.
  Existing nearest-quality, distant-audio selection, retries, authentication,
  progress, FFmpeg, and fallback behavior applies independently to every item.
  A failed or unavailable item is recorded and the remaining playlist continues.
  A final playlist table shows downloaded, failed, cancelled, and total items.

  Examples:
    ytd https://www.youtube.com/playlist?list=PLAYLIST_ID
    ytd "https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID"

DIRECT COMMANDS
  ytd URL
  ytd URL 720
  ytd --link URL --quality 720
  ytd --file links.txt
  ytd https://www.youtube.com/playlist?list=PLAYLIST_ID
  ytd --output D:\\Videos URL
  ytd --cookies-from-browser chrome URL
  ytd --cookies cookies.txt URL
  ytd q                    Open quality selection, then continue interactively.
  ytd a                    Open attempt selection, then continue interactively.
  ytd d                    Show this documentation, then continue interactively.

COMMAND-LINE OPTIONS
  -h, --help
      Show argparse command help.
  -l, --link URL
      Provide one YouTube URL.
  -q, --quality HEIGHT
      Set the initial video height, for example 720.
  -f, --file PATH
      Read YouTube URLs from a text file.
  -o, --output DIRECTORY
      Select the download directory.
  --cookies-from-browser BROWSER
      Read signed-in cookies using yt-dlp, for example chrome or firefox.
  --cookies FILE
      Use a Netscape-format cookies.txt file.

PROGRESS DISPLAY
  Example:
    Downloading 80.2% | Total 42.62MiB / Downloaded 34.18MiB |
    Speed 3.60MiB/s | ETA 00:04

  Total may be exact or estimated by yt-dlp. Unknown values are omitted.
  Downloaded is the actual transferred byte count reported by yt-dlp.

VIDEO DOWNLOADS
  With FFmpeg, the downloader prefers separate best video and audio streams,
  then merges them into MP4. If FFmpeg is unavailable, it uses the best
  compatible single-file format.

AUDIO DOWNLOADS
  Audio mode downloads only the selected audio stream. Its available container
  is preserved, such as m4a or webm.

YOUTUBE VERIFICATION AND COOKIES
  If YouTube requests sign-in or bot verification, the CLI can use cookies from
  a detected signed-in browser or a cookies.txt file. Browser cookies are read
  locally by yt-dlp and reused only during the current CLI process.

  Fully close Chromium-based browsers before reading cookies if their cookie
  database is locked. Browser access is disabled for the session after two
  failed cookie-read attempts.

DEPENDENCIES
  Required: Python 3.8+, yt-dlp, imageio-ffmpeg.
  Missing dependencies can be installed into .ytd_env/site-packages.
  Install the global editable command with:
    python -m pip install -e .

MORE DOCUMENTATION
  See README.md in the project directory for project structure, installation,
  troubleshooting, sharing, and implementation details.
""".strip()


def print_documentation():
    print()
    print(DOCUMENTATION)
    print()
