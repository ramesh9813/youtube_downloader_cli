# YouTube Downloader CLI

`ytd` is a small Python command line tool for downloading YouTube videos.
It supports both interactive downloads and direct one-line commands.

The downloader uses:

- `yt-dlp` to read YouTube video information and download media.
- `imageio-ffmpeg` to provide FFmpeg for merging video and audio into one file.
- Python's `argparse` module to handle command line options.

## Features

- Run `ytd` from the terminal.
- Paste a YouTube link interactively.
- Choose a video quality from a numbered list.
- Download directly with a link and quality, for example `ytd youtube.com/watch?v=VIDEO_ID 720`.
- Type `e`, `exit`, `q`, or `quit` to close the CLI.
- Continue downloading more videos in one CLI session.
- Show download progress with percentage, speed, and ETA when available.
- Print a final summary with link, video title, quality, saved file, and directory.
- Save videos in the directory where the command prompt is open by default.

## Project Files

```text
video_downloader/
  ytd.py              Main Python CLI source code
  ytd.bat             Windows launcher for running .\ytd from this folder
  pyproject.toml      Package configuration and ytd command registration
  requirements.txt    Python dependencies
  .gitignore          Files and folders Git should ignore
  README.md           Project documentation
```

## Requirements

Install these before using the project:

- Python 3.8 or newer
- Internet connection
- Windows PowerShell or Command Prompt

During Python installation on Windows, enable:

```text
Add Python to PATH
```

Check Python:

```powershell
python --version
```

## Installation

Open PowerShell or Command Prompt in the project folder:

```powershell
cd F:\desktop_july_19_2024\ramesh_file\project\software_project\youtube_update\video_downloader
```

Install the project in editable mode:

```powershell
python -m pip install -e .
```

This installs:

- The `ytd` command.
- `yt-dlp`.
- `imageio-ffmpeg`.

Editable mode means changes made to `ytd.py` are used immediately without reinstalling.

Alternative dependency-only install:

```powershell
python -m pip install -r requirements.txt
```

If you only use `requirements.txt`, run the tool from the project folder with:

```powershell
.\ytd
```

## Basic Usage

Interactive mode:

```powershell
ytd
```

The CLI shows:

```text
Saving videos to: current_directory
Type e to exit.

Enter YouTube link, or e to exit:
```

Paste a YouTube link:

```text
youtube.com/watch?v=VIDEO_ID
```

Then choose a quality from the numbered list:

```text
Available qualities:
1. 1080p (mp4, webm)
2. 720p (mp4, webm)
3. 480p (mp4)
Choose quality number, or e to exit:
```

Enter a number such as:

```text
2
```

After the download finishes, the CLI asks for another link. Type `e` to exit.

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
2. Normalize the YouTube link.
3. Fetch video metadata using `yt-dlp`.
4. Read available video formats from the metadata.
5. Group available formats by video height, such as 1080p, 720p, and 480p.
6. Ask the user to select a quality, unless quality was already provided.
7. Select the best video and audio streams for the requested quality.
8. Download the media.
9. Use FFmpeg to merge video and audio into an MP4 file when separate streams are used.
10. Print the download summary.
11. Ask for another link until the user exits.

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

The parser also accepts accidental input like:

```powershell
ytd ---link-- URL --720--
```

The script cleans those values before passing them to `argparse`.

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

The `list_qualities()` function checks all available video formats and groups them by height.

Example qualities:

```text
1080p
720p
480p
360p
```

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

It displays:

- Download percentage
- Speed
- ETA

Example:

```text
Downloading 42.8% at 2.14MiB/s ETA 00:20
```

### Repeat Downloads

The `main()` function runs a loop.

After each successful download:

1. It clears the current link and quality.
2. It asks for another YouTube link.
3. It exits only when the user types `e`, `exit`, `q`, or `quit`.

## Example Session

```text
Saving videos to: F:\Videos
Type e to exit.

Enter YouTube link, or e to exit: youtube.com/watch?v=s5WrmvC8oZ8
Available qualities:
1. 1080p (webm)
2. 720p (mp4, webm)
3. 480p (mp4)
Choose quality number, or e to exit: 2
Downloading 100.0%
Download finished. Processing media...

Summary
Link: https://youtube.com/watch?v=s5WrmvC8oZ8
Video name: Deep Sea Robots: Unveiling The Ocean's Deepest Mysteries
Quality: 720p
Saved file: F:\Videos\Deep Sea Robots... [s5WrmvC8oZ8].mp4
Downloaded directory: F:\Videos

Enter YouTube link, or e to exit: e
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
python -m pip install -e .
```

Then they can use:

```powershell
ytd
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
.venv/
venv/
env/
ENV/
```

These are virtual environment folders. They can be very large and are specific to one computer.

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
```

These are local configuration files. If the project later uses API keys or private settings, they should stay out of Git.

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

Run this again inside the project folder:

```powershell
python -m pip install -e .
```

Or run from the project folder with:

```powershell
.\ytd
```

### Video and audio do not merge

Reinstall dependencies:

```powershell
python -m pip install -e .
```

This installs `imageio-ffmpeg`, which provides FFmpeg.

### YouTube download fails

Update `yt-dlp`:

```powershell
python -m pip install --upgrade yt-dlp
```

YouTube changes often, so keeping `yt-dlp` updated is important.

## Important Note

Use this tool only for videos you have the right to download. Respect YouTube's terms, copyright rules, and the rights of content owners.
"# youtube_downloader_cli" 
