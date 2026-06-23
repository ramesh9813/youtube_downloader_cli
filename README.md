# YouTube Downloader CLI

`ytd` is a small Python command line tool for downloading YouTube videos.
It supports both interactive downloads and direct one-line commands.

The downloader uses:

- `yt-dlp` to read YouTube video information and download media.
- `imageio-ffmpeg` to provide FFmpeg for merging video and audio into one file.
- Python's `argparse` module to handle command line options.
- A local `.ytd_env` dependency folder when required packages are not already installed.

## Features

- Run `ytd` from the terminal.
- Paste a YouTube link interactively.
- Paste a YouTube playlist link to download the complete playlist.
- Use `720p` automatically unless the session default is changed.
- Type `q` to choose a persistent video quality or audio bitrate.
- Type `a` to choose how many download attempts are made per format.
- Type `d` to display complete in-app documentation and every shortcut.
- Apply the selected video or audio preference to every later URL and batch file in the session.
- Apply the selected attempt count to every later URL and batch file in the session.
- Use the nearest available video quality or audio bitrate when an exact match is unavailable.
- Show the current video's audio formats when none is reasonably near the saved audio bitrate.
- Save that actual audio choice for the remaining URLs and batch entries in the session.
- Download directly with a link and quality, for example `ytd youtube.com/watch?v=VIDEO_ID 720`.
- Download many videos from a text file with `ytd @filename`.
- Continue remaining playlist items when one item is unavailable or fails.
- Print a final playlist summary table.
- Type `e`, `exit`, or `quit` to close the CLI.
- Continue downloading more videos in one CLI session.
- Show download progress with percentage, speed, and ETA when available.
- Show an animated connection status before download progress starts.
- Retry a failed format using the active attempt count, then automatically try another available format.
- Detect YouTube anti-bot verification and offer signed-in browser cookie authentication.
- Print a final summary with link, video title, quality, saved file, and directory.
- Save videos in the directory where the command prompt is open by default.
- Prepare required Python dependencies automatically on first download.

## Project Files

```text
video_downloader/
  ytd.py              Small compatibility entry point
  src/
    cli.py            Main command loop and user prompts
    parsing.py        Command-line and link parsing
    authentication.py Browser and cookie authentication
    metadata.py       YouTube metadata retrieval
    formats.py        Video/audio format selection
    downloads.py      Download, retry, and FFmpeg operations
    download_service.py Single-download workflow coordination
    preferences.py     Persistent video/audio quality preferences
    attempts.py        Persistent retry-attempt selection
    documentation.py   Complete in-app command documentation
    playlists.py       Playlist detection, entry URLs, and summary output
    batch.py          Batch-file processing and summary output
    console.py        Spinner, progress, and console helpers
    runtime.py        Dependency setup and runtime imports
    config.py         Shared constants and paths
  ytd.bat             Windows launcher for running .\ytd from this folder
  pyproject.toml      Package configuration and ytd command registration
  requirements.txt    Python dependencies
  .gitignore          Files and folders Git should ignore
  .ytd_env/           Auto-created local dependency folder, ignored by Git
  README.md           Project documentation
  tests/              Unit tests for CLI, downloads, playlists, and helpers
```

## Requirements

Install this before using the project:

- Python 3.8 or newer

An internet connection is required the first time dependencies need to be downloaded.

During Python installation on Windows, enable:

```text
Add Python to PATH
```

Check Python:

```powershell
python --version
```

## Fast Start

Open PowerShell or Command Prompt in the project folder:

```powershell
cd path\to\video_downloader
```

Run the downloader:

```powershell
.\ytd
```

On first use, the launcher sets temporary environment variables for this one process and the Python script checks whether the required packages are available.

If `yt-dlp` or `imageio-ffmpeg` is missing, the script installs the missing package into:

```text
.ytd_env\site-packages
```

This keeps dependencies inside the project folder. It does not permanently change the user's system environment.

When `ytd` exits, the launcher cleans the temporary environment variables automatically.

The user only needs Python installed.

## Optional Global Command Install

If you want to run `ytd` from any directory without typing `.\ytd`, install the command in editable mode:

```powershell
python -m pip install -e .
```

Editable mode means changes made to `ytd.py` are used immediately without reinstalling.

Alternative dependency-only install:

```powershell
python -m pip install -r requirements.txt
```

If you only use `requirements.txt`, run the tool from the project folder with:

```powershell
.\ytd
```

This optional install is not required for the local launcher.

## Basic Usage

Interactive mode:

```powershell
.\ytd
```

If you installed the global command with `python -m pip install -e .`, you can use `ytd` instead.

The CLI starts with a `720p` session default and shows:

```text
Current default: Video 720p
Current attempts: 2
Enter URL, file, q quality, a attempts, d docs, or e exit:
```

The first prompt accepts:

```text
url
file
q
a
d
e
```

Use `url` to download one video. Use `file` to choose a text file containing many YouTube links. Use `q` to change the session-wide video or audio preference. Use `a` to change the session-wide attempt count. Use `d` to show complete documentation. Use `e` to exit.

## Shortcut Reference

Every interactive shortcut is:

| Shortcut | Meaning |
|---|---|
| Paste a URL | Download that URL immediately |
| `url`, `u` | Ask for one YouTube URL |
| `file`, `f` | List files and select a batch text file |
| `@filename` | Use the named batch text file |
| `q` | Change persistent video quality or audio bitrate |
| `a` | Change persistent attempts per format |
| `d` | Display complete in-app documentation |
| `e` | Exit or cancel the current prompt |
| `exit` | Exit the CLI |
| `quit` | Exit the CLI |

Run `ytd d` to show the documentation at startup and continue interactively. The `d` shortcut also works at the main prompt and YouTube-link prompt. After documentation is displayed, the current quality and attempt settings remain unchanged.

You can also paste a YouTube link directly:

```text
youtube.com/watch?v=VIDEO_ID
```

The first download uses `720p` automatically. The same preference remains active for every later URL and batch file.

To change it, enter `q`:

```text
Current default: Video 720p
Video quality:
1. 4320p
2. 2160p
3. 1440p
4. 1080p
5. 720p
6. 480p
7. 360p
8. 240p
9. 144p
Audio quality:
10. Audio near 320 kbps
11. Audio near 256 kbps
12. Audio near 192 kbps
13. Audio near 160 kbps
14. Audio near 128 kbps
15. Audio near 96 kbps
16. Audio near 64 kbps
```

Selecting a video quality downloads video for all subsequent links. Selecting an audio bitrate downloads audio-only files for all subsequent links, including every entry in a batch file.

The preference describes the target quality. Since YouTube formats differ by video, the downloader resolves it separately for each link. If the exact height or bitrate is missing, it uses the nearest available option. Audio files keep the available extension, such as `.m4a` or `.webm`.

For audio, a format within 32 kbps of the saved target is considered near and is selected automatically. If every available audio format is farther away, the CLI shows the actual formats for that video:

```text
No audio format is near 320 kbps for this video.
Available audio formats:
1. webm (opus, 160 kbps)
2. m4a (mp4a.40.2, 128 kbps)
Choose an audio format number, or e to use the nearest format:
```

After a format is selected, its bitrate becomes the session audio target. The current download and all remaining single or batch downloads use that target until it is changed again.

To change retry attempts, enter `a`, then enter a positive whole number such as `5`. The downloader will try each selected format up to five times for all later URLs and batch entries until the value is changed again.

After the download finishes, the CLI asks for another link. Type `e` to exit.

## Playlist Usage

Paste a YouTube playlist URL anywhere a normal URL is accepted:

```text
https://www.youtube.com/playlist?list=PLAYLIST_ID
```

A video URL containing a playlist also downloads the complete playlist:

```text
https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID
```

Direct command:

```powershell
ytd "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

The downloader:

1. Detects playlist metadata automatically.
2. Reads every playlist entry in order.
3. Converts each entry into a clean single-video URL.
4. Applies the current video quality or audio bitrate to every item.
5. Applies the current attempt count to every item and format fallback.
6. Reuses the existing authentication, FFmpeg, progress, nearest-quality, and distant-audio behavior.
7. Records unavailable or failed entries and continues with the rest.
8. Prints a final playlist summary table.

If audio mode is active and an entry has no reasonably near bitrate, the actual audio list is shown. The selected replacement bitrate is then used for the remaining playlist entries.

Example summary:

```text
Playlist Summary: My Playlist
# | Status     | Quality | Video        | Saved File / Message
1 | downloaded | 720p    | First video  | D:\Videos\First video [id].mp4
2 | failed     | 720p    | Private video| This playlist entry is unavailable.
Downloaded: 1 | Failed: 1 | Cancelled: 0 | Total: 2
```

## Batch File Usage

Create a text file in the same directory where your command prompt is open.

Example file name:

```text
links.txt
```

Example file content:

```text
https://www.youtube.com/watch?v=VIDEO_ID_1
youtube.com/watch?v=VIDEO_ID_2
https://youtu.be/VIDEO_ID_3
```

Blank lines are ignored. Lines starting with `#` are ignored.

Run batch mode directly in PowerShell or Command Prompt:

```powershell
ytd --file links.txt
```

This direct form also works:

```powershell
ytd file links.txt
```

In Command Prompt, this form works too:

```powershell
ytd @links.txt
```

In PowerShell, use quotes if you want the `@filename` form:

```powershell
ytd '@links.txt'
```

PowerShell treats bare `@` as special syntax, so `ytd --file links.txt` is the safest command on Windows.

These commands download each video at `720p` by default and save the files in the current command prompt directory. In an interactive session, a preference selected with `q` applies to the complete batch. If audio is selected, every valid batch entry downloads as an audio-only file.

You can also list files in the current directory and select one. Start the CLI:

```powershell
ytd
```

Then enter:

```text
Enter URL, file, q quality, a attempts, d docs, or e exit: file
```

The CLI lists files in the current directory:

```text
Files in D:\Videos:
1. links.txt
2. my_playlist.txt
Choose file number, enter filename, or e to exit:
```

Enter the file number, for example:

```text
1
```

The downloader processes videos one by one. If one link fails, it prints the error, skips that link, and continues with the next link.

After all links are processed, the CLI prints a batch summary table:

```text
Batch Summary
# | Status     | Quality | Video / Link | Saved File / Message
1 | downloaded | 720p    | Video title  | D:\Videos\Video title [id].mp4
2 | failed     | 720p    | bad line     | Line 2: Invalid YouTube link format.
```

## Direct Command Usage

Download with full options:

```powershell
ytd --link "https://www.youtube.com/watch?v=VIDEO_ID" --quality 720
```

Short form:

```powershell
ytd "https://www.youtube.com/watch?v=VIDEO_ID" 720
```

Without `https://`:

```powershell
ytd youtube.com/watch?v=VIDEO_ID 720
```

Use cookies from a browser where you are signed into YouTube:

```powershell
ytd youtube.com/watch?v=VIDEO_ID 720 --cookies-from-browser chrome
```

Or use a Netscape-format cookies file:

```powershell
ytd youtube.com/watch?v=VIDEO_ID 720 --cookies "cookies.txt"
```

Download many videos from a text file:

```powershell
ytd --file links.txt
```

Download a complete playlist:

```powershell
ytd "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

Command Prompt also supports:

```powershell
ytd @links.txt
```

PowerShell supports the `@filename` form when quoted:

```powershell
ytd '@links.txt'
```

Show complete in-app documentation:

```powershell
ytd d
```

Show concise argparse option help:

```powershell
ytd --help
```

The script automatically changes this:

```text
youtube.com/watch?v=VIDEO_ID
```

into:

```text
https://youtube.com/watch?v=VIDEO_ID
```

## Save Directory

By default, videos are saved in the directory where the terminal is open.

Example:

```powershell
cd D:\Videos
ytd youtube.com/watch?v=VIDEO_ID 720
```

The downloaded video is saved in:

```text
D:\Videos
```

To save somewhere else, use `--output`:

```powershell
ytd youtube.com/watch?v=VIDEO_ID 720 --output "D:\MyDownloads"
```

## Runtime Environment

The Windows launcher `ytd.bat` uses `setlocal`, which means environment changes exist only while the command is running.

It sets these temporary values:

```text
YTD_PROJECT_DIR
YTD_DEPS_DIR
PYTHONUTF8
PYTHONIOENCODING
PYTHONPATH
```

Purpose:

- `YTD_PROJECT_DIR` points to the project folder.
- `YTD_DEPS_DIR` points to `.ytd_env\site-packages`.
- `PYTHONUTF8` and `PYTHONIOENCODING` improve terminal text handling.
- `PYTHONPATH` lets Python import packages installed in `.ytd_env`.

When the command exits, `endlocal` removes these temporary environment changes.

No permanent system environment variable is created.

## Exit Commands

You can exit by typing any of these:

```text
e
exit
quit
```

These work at the main prompt and link prompt. Other reserved shortcuts are `q` for quality, `a` for attempts, and `d` for documentation.

## How It Works

The program flow is:

1. Parse command line arguments.
2. Start with a persistent `720p` session preference.
3. Ask whether the user wants `url`, `file`, `q`, `a`, `d`, or `e`.
4. When `q` is entered, save the selected video height or audio bitrate for the rest of the session.
5. When `a` is entered, save the attempt count for the rest of the session.
6. When `d` is entered, print complete documentation without changing session settings.
7. Normalize the pasted YouTube link.
8. For file mode, read YouTube links from the selected text file.
9. Fetch metadata using `yt-dlp`.
10. If metadata is a playlist, process every entry in order.
11. Read available video and audio-only formats for each video.
12. Resolve the session preference to the nearest available format for that link.
13. Download video or audio using the active quality and attempt settings.
14. Use FFmpeg to merge video and audio into an MP4 file when separate video streams are used.
15. Print a single, batch, or playlist summary.
16. Repeat with the same settings until the user changes them or exits.

## Code Methodology

### Argument Parsing

The `parse_args()` function handles command line input.

It supports normal commands:

```powershell
ytd --link URL --quality 720
```

It also supports short input:

```powershell
ytd URL 720
```

It also supports batch file input:

```powershell
ytd --file links.txt
ytd file links.txt
ytd @links.txt
```

The parser also accepts accidental input like:

```powershell
ytd ---link-- URL --720--
```

The script cleans those values before passing them to `argparse`.

### Batch File Detection

The script treats input starting with `@` as a batch file request.

Examples:

```powershell
ytd --file links.txt
ytd file links.txt
ytd @links.txt
```

`--file links.txt`, `file links.txt`, and `@links.txt` mean read links from `links.txt`.

In interactive mode, entering `file` or `@` means show the files in the current directory and ask the user to choose one.

### Link Normalization

The `normalize_link()` function makes pasted links easier to use.

If the user enters:

```text
youtube.com/watch?v=VIDEO_ID
```

the script converts it to:

```text
https://youtube.com/watch?v=VIDEO_ID
```

Supported link starts include:

- `https://`
- `http://`
- `www.`
- `youtube.com/`
- `youtu.be/`
- `m.youtube.com/`

### Quality Detection

The `fetch_info()` function asks `yt-dlp` for video information without downloading.

The `list_qualities()` function checks all available video formats and groups them by height. The `list_audio_formats()` function finds audio-only streams and keeps the best bitrate for each extension and codec combination.

Example qualities:

```text
1080p
720p
480p
360p
```

Example audio choices:

```text
Audio m4a (mp4a.40.2, 129 kbps)
Audio webm (opus, 128 kbps)
```

Selecting an audio preference downloads only an audio stream and preserves its available extension. It does not download or merge the video stream.

If direct quality is provided, for example `720`, the script saves `720p` as the initial session preference.

`nearest_video_quality()` and `nearest_audio_format()` choose the closest available height or bitrate for each link. If two options are equally close, the lower one is preferred.

An audio difference of up to 32 kbps is accepted automatically. For a larger difference, `choose_available_audio_format()` displays the video's actual audio streams and updates the shared session preference with the user's selection.

### Download Method

The `download_video()` function performs the actual download.

When FFmpeg is available, this format rule is used:

```text
bestvideo[height<=QUALITY]+bestaudio/best[height<=QUALITY]/best
```

Meaning:

- Prefer the best video stream at or below the selected quality.
- Add the best audio stream.
- If separate streams are not available, use the best combined stream.
- If that also fails, use the best available format.

The output file pattern is:

```text
Video Title [YouTubeID].extension
```

Example:

```text
Deep Sea Robots - Unveiling The Ocean's Deepest Mysteries [s5WrmvC8oZ8].mp4
```

### Batch Download Method

The `download_batch()` function handles text-file downloads.

It reads the selected file line by line:

- Empty lines are skipped.
- Lines starting with `#` are skipped.
- Valid YouTube links are normalized.
- Invalid lines are added to the final table as failed rows.

Each valid link is downloaded separately using the active session preference. The default is `720p`, but a video or audio choice made with `q` applies to the entire batch. If an audio target is not reasonably available, the user chooses from the first affected video's actual formats and that new target is used for the remaining batch links. If one download fails, the error is saved in the result table and the next link starts.

This keeps long batch downloads running even when one link is unavailable, private, removed, or typed incorrectly.

### FFmpeg Handling

The script first checks whether system FFmpeg exists:

```text
ffmpeg
```

If system FFmpeg is not found, it uses FFmpeg from:

```text
imageio-ffmpeg
```

This avoids requiring users to manually install FFmpeg on Windows.

If FFmpeg is not available at all, the script falls back to a single-file video download.

### Progress Display

The `make_progress_hook()` function receives progress updates from `yt-dlp`.

Before progress data is available, an animated status shows that the downloader is connecting to the media server. It then displays:

- Download percentage
- Total file size when reported or estimated by `yt-dlp`
- Actual bytes downloaded so far
- Speed
- ETA

Example:

```text
Downloading 42.8% | Total 86.35MiB / Downloaded 36.96MiB | Speed 2.14MiB/s | ETA 00:20
```

If the media server does not provide enough information to determine total or downloaded size, the unavailable value is omitted.

### Automatic Retry And Format Fallback

Every selected video quality or audio format uses the active session attempt count. The default is two attempts. Enter `a` at the main or link prompt to change it.

The CLI reports each stage:

```text
Video 720p - attempt 1/5
| Connecting to media server for 720p
Attempt 1 failed: The media server timed out while sending data.
Retrying automatically...
Video 720p - attempt 2/5
```

If all attempts for a video format fail, the downloader tries the next available quality in nearest-first order. When two alternatives are equally close, the lower quality is tried first.

```text
All attempts failed for video 720p.
Trying another video quality: 480p
```

Audio downloads use the same behavior. After two failures, the downloader automatically tries another available audio-only stream.

Raw `yt-dlp` timeout messages are hidden and replaced with these shorter status messages so the user can see what the application is doing.

### YouTube Anti-Bot Verification

YouTube may allow several downloads and then require verification:

```text
Sign in to confirm you're not a bot
```

The downloader detects this response, hides the repeated raw error, and asks whether it should use cookies from a signed-in browser:

```text
YouTube requested browser verification.
Available authentication choices:
1. Use Firefox cookies
2. Use Chrome cookies
3. Use Edge cookies
4. Use a cookies.txt file
Choose authentication number, or e to cancel this download:
```

Before choosing:

1. Open YouTube in the browser.
2. Sign into YouTube.
3. Complete any CAPTCHA or verification shown by YouTube.
4. Return to the CLI and select that browser.

The cookies are read locally by `yt-dlp`. The script does not export them or save them in the project. The selected authentication is reused only for the current CLI session, including the remaining links in batch mode.

For every link, the downloader first tries the normal anonymous request. It uses browser authentication only if YouTube responds with a verification requirement. If authentication was already selected earlier in the CLI session, it retries with that method without asking again.

Firefox often works more reliably for cookie access. Chromium browsers can lock or restrict their cookie database while the browser is running. For Chrome or Edge:

1. Open YouTube and sign in.
2. Complete YouTube's CAPTCHA or verification.
3. Fully close every browser window.
4. Check Task Manager and close remaining browser background processes if necessary.
5. Select that browser in `ytd`.

If browser cookie access fails, the CLI offers one clearly marked final retry. After a second failure, that browser is removed from the choices for the current session. This prevents the authentication prompt from looping forever.

If the browser still cannot be read, use a Netscape-format `cookies.txt` file. Keep it private and delete it when it is no longer needed.

Using an account for many automated requests can cause temporary limits or account risk. Download at a reasonable rate and use browser cookies only when YouTube requires verification.

### Repeat Downloads

The `main()` function runs a loop.

After each successful download:

1. It clears the current link or file.
2. It keeps the active video or audio preference.
3. It asks for `url`, `file`, `q`, `a`, `d`, or `e`.
4. It exits only when the user types `e`, `exit`, or `quit`.

## Example Session

```text
Current default: Video 720p
Current attempts: 2
Enter URL, file, q quality, a attempts, d docs, or e exit: youtube.com/watch?v=s5WrmvC8oZ8
Downloading 100.0%
Download finished. Processing media...

Summary
Link: https://youtube.com/watch?v=s5WrmvC8oZ8
Video name: Deep Sea Robots: Unveiling The Ocean's Deepest Mysteries
Quality: 720p
Saved file: F:\Videos\Deep Sea Robots... [s5WrmvC8oZ8].mp4
Your video downloaded at this: F:\Videos

Enter URL, file, q quality, a attempts, d docs, or e exit: e
Exited.
```

## Sharing The Project

To share with another person:

1. Compress the whole `video_downloader` folder into a `.zip` file.
2. Send the `.zip` file.
3. The other person extracts it.
4. They open PowerShell in the extracted folder.
5. They run:

```powershell
.\ytd
```

The first download prepares dependencies automatically inside `.ytd_env` if they are missing.

If they want a global `ytd` command, they can optionally run:

```powershell
python -m pip install -e .
```

## Git Ignore File

The project includes a `.gitignore` file. This file tells Git which local files should not be committed or shared in the source code repository.

Keep these project files:

```text
ytd.py
ytd.bat
pyproject.toml
requirements.txt
README.md
.gitignore
```

Ignore these generated or local-only files:

```text
__pycache__/
*.py[cod]
*$py.class
```

These are Python bytecode/cache files. Python creates them automatically when the script runs.

```text
build/
dist/
*.egg-info/
.eggs/
*.egg
```

These are package/build outputs. For this project, `ytd_downloader_cli.egg-info/` is created after running `python -m pip install -e .`.

```text
.ytd_env/
.venv/
venv/
env/
ENV/
```

These are local dependency or virtual environment folders. They can be very large and are specific to one computer.

For this project, `.ytd_env/` is auto-created when the app installs missing dependencies locally.

```text
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
```

These are test, lint, type-checking, and coverage cache files.

```text
downloads/
*.mp4
*.mkv
*.webm
*.avi
*.mov
*.flv
*.part
*.ytdl
*.temp.*
```

These are downloaded videos and temporary download files. Video files should not be committed because they are large and are user output, not source code.

```text
.env
.env.*
*.local
cookies.txt
*cookies*.txt
```

These are local configuration and secret files. Cookie files contain private browser login session data and must never be committed or shared.

```text
.vscode/
.idea/
*.swp
*.swo
```

These are editor and IDE files. They depend on each developer's local setup.

```text
Thumbs.db
Desktop.ini
.DS_Store
```

These are operating system files created by Windows or macOS.

Before sharing through Git, check ignored files with:

```powershell
git status --ignored
```

If you are sharing by zip file instead of Git, remove or skip these folders before sending:

```text
__pycache__/
ytd_downloader_cli.egg-info/
.ytd_env/
downloads/
.venv/
venv/
```

## Troubleshooting

### `python` is not recognized

Install Python from:

```text
https://www.python.org/downloads/
```

During installation, enable:

```text
Add Python to PATH
```

### `ytd` is not recognized

From PowerShell, run the local launcher with:

```powershell
.\ytd
```

From Command Prompt, this works from the project folder:

```cmd
ytd
```

To make `ytd` work globally, run this inside the project folder:

```powershell
python -m pip install -e .
```

### Video and audio do not merge

Run the local launcher once so it can prepare dependencies:

```powershell
.\ytd
```

This prepares `imageio-ffmpeg`, which provides FFmpeg.

### YouTube download fails

Update `yt-dlp`:

```powershell
python -m pip install --upgrade yt-dlp
```

YouTube changes often, so keeping `yt-dlp` updated is important.

### Sign in to confirm you are not a bot

Open YouTube in a signed-in browser and complete any verification. Run the download again. When prompted, select that browser.

For Chrome and Edge on Windows, fully close the browser before selecting it. An open Chromium browser can lock its cookie database and cause:

```text
Could not copy Chrome cookie database
```

The downloader permits one final browser retry, then removes that failed browser from the current session to avoid repeated prompts.

You can also select the browser directly:

```powershell
ytd URL 720 --cookies-from-browser firefox
ytd URL 720 --cookies-from-browser chrome
ytd URL 720 --cookies-from-browser edge
```

For a cookie file:

```powershell
ytd URL 720 --cookies "cookies.txt"
```

Do not commit or share cookie files. They contain private login session data.

## Important Note

Use this tool only for videos you have the right to download. Respect YouTube's terms, copyright rules, and the rights of content owners.
