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
- Choose a video quality or an available audio-only format from a numbered list.
- Download directly with a link and quality, for example `ytd youtube.com/watch?v=VIDEO_ID 720`.
- Download many videos from a text file with `ytd @filename`.
- Type `e`, `exit`, `q`, or `quit` to close the CLI.
- Continue downloading more videos in one CLI session.
- Show download progress with percentage, speed, and ETA when available.
- Show an animated connection status before download progress starts.
- Retry a failed format twice, then automatically try another available format.
- Detect YouTube anti-bot verification and offer signed-in browser cookie authentication.
- Print a final summary with link, video title, quality, saved file, and directory.
- Save videos in the directory where the command prompt is open by default.
- Prepare required Python dependencies automatically on first download.

## Project Files

```text
video_downloader/
  ytd.py              Main Python CLI source code
  ytd.bat             Windows launcher for running .\ytd from this folder
  pyproject.toml      Package configuration and ytd command registration
  requirements.txt    Python dependencies
  .gitignore          Files and folders Git should ignore
  .ytd_env/           Auto-created local dependency folder, ignored by Git
  README.md           Project documentation
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

The CLI shows:

```text
Enter url, file, e for exit:
```

The first prompt accepts:

```text
url
file
e
```

Use `url` to download one video. Use `file` to choose a text file containing many YouTube links. Use `e` to exit.

Paste a YouTube link:

```text
youtube.com/watch?v=VIDEO_ID
```

Then choose a video quality or audio-only format from the numbered list:

```text
Available video qualities:
1. 1080p (mp4, webm)
2. 720p (mp4, webm)
3. 480p (mp4)
Available audio formats:
4. Audio m4a (mp4a.40.2, 129 kbps)
5. Audio webm (opus, 128 kbps)
Choose video or audio number, or e to exit:
```

Enter a video number such as `2`, or an audio number such as `4`.

```text
4
```

Audio choices are the audio-only streams actually available for that YouTube link. The downloaded file keeps the listed format, such as `.m4a` or `.webm`.

After the download finishes, the CLI asks for another link. Type `e` to exit.

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

These commands download each video at `720p` by default and save the files in the current command prompt directory.

You can also list files in the current directory and select one. Start the CLI:

```powershell
ytd
```

Then enter:

```text
Enter url, file, e for exit: file
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

Command Prompt also supports:

```powershell
ytd @links.txt
```

PowerShell supports the `@filename` form when quoted:

```powershell
ytd '@links.txt'
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
q
quit
```

These work when the CLI asks for:

- A YouTube link
- A quality number

## How It Works

The program flow is:

1. Parse command line arguments.
2. Ask whether the user wants `url`, `file`, or `e`.
3. For single video mode, normalize the YouTube link.
4. For file mode, read YouTube links from the selected text file.
5. Fetch video metadata using `yt-dlp`.
6. Read available video and audio-only formats from the metadata.
7. Group video formats by height and audio formats by extension and codec.
8. Ask the user to select a video quality or audio format for single video mode, unless video quality was already provided.
9. Use `720p` automatically for batch file mode.
10. Select the best video and audio streams for the requested quality.
11. Download the media.
12. Use FFmpeg to merge video and audio into an MP4 file when separate streams are used.
13. Print the download summary.
14. Ask for another action until the user exits.

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

Selecting an audio choice downloads only that stream and preserves its available extension. It does not download or merge the video stream.

If direct quality is provided, for example `720`, the script tries to use exact `720p`.

If exact quality is not available, `best_quality_at_or_below()` chooses the closest lower quality. If no lower quality exists, it chooses the lowest available quality.

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

Each valid link is downloaded separately at `720p` by default. If one download fails, the error is saved in the result table and the next link starts.

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
- Speed
- ETA

Example:

```text
Downloading 42.8% at 2.14MiB/s ETA 00:20
```

### Automatic Retry And Format Fallback

Every selected video quality or audio format is attempted up to two times.

The CLI reports each stage:

```text
Video 720p - attempt 1/2
| Connecting to media server for 720p
Attempt 1 failed: The media server timed out while sending data.
Retrying automatically...
Video 720p - attempt 2/2
```

If both video attempts fail, the downloader tries the next available quality. Lower qualities are tried first because they usually require less bandwidth. If no lower quality remains, it tries another available higher quality.

```text
Both attempts failed for video 720p.
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

Firefox often works more reliably for cookie access. Chromium browsers can sometimes lock or restrict their cookie database. If one browser fails, the CLI lets you select another browser or a `cookies.txt` file.

Using an account for many automated requests can cause temporary limits or account risk. Download at a reasonable rate and use browser cookies only when YouTube requires verification.

### Repeat Downloads

The `main()` function runs a loop.

After each successful download:

1. It clears the current link, file, and quality.
2. It asks for `url`, `file`, or `e`.
3. It exits only when the user types `e`, `exit`, `q`, or `quit`.

## Example Session

```text
Enter url, file, e for exit: url
Enter YouTube link, or e to exit: youtube.com/watch?v=s5WrmvC8oZ8
Available qualities:
1. 1080p (webm)
2. 720p (mp4, webm)
3. 480p (mp4)
Available audio formats:
4. Audio m4a (mp4a.40.2, 129 kbps)
5. Audio webm (opus, 128 kbps)
Choose video or audio number, or e to exit: 2
Downloading 100.0%
Download finished. Processing media...

Summary
Link: https://youtube.com/watch?v=s5WrmvC8oZ8
Video name: Deep Sea Robots: Unveiling The Ocean's Deepest Mysteries
Quality: 720p
Saved file: F:\Videos\Deep Sea Robots... [s5WrmvC8oZ8].mp4
Your video downloaded at this: F:\Videos

Enter url, file, e for exit: e
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
