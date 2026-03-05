# MP 4 2 3

A production-ready Telegram bot that extracts audio from user videos using FFmpeg.

## Features

- `/start` command to explain bot purpose
- `/help` command with formats and size limits
- `/voice` command to request OGG voice output for the next video
- Accepts Telegram video uploads up to configurable size (default: 100MB)
- Async handlers with concurrent user processing
- Non-blocking FFmpeg execution via `asyncio.create_subprocess_exec`
- Structured logging for user ID, file sizes, processing time, and errors
- Temporary file cleanup after each job

## Project Structure

```text
mp_423/
├── .env.example
├── bot.py
├── config.py
├── utils/
│   ├── ffmpeg_utils.py
│   └── file_utils.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

`.env.example` content:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
MAX_VIDEO_SIZE_MB=100
TEMP_DIR=./tmp
```

## Install FFmpeg

### Windows

- Download FFmpeg from the official builds page.
- Add the `bin` directory (contains `ffmpeg.exe`) to your `PATH`.
- Verify with:

```powershell
ffmpeg -version
```

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### macOS (Homebrew)

```bash
brew install ffmpeg
```

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies.
3. Set environment variables.
4. Run the bot.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

## Run with Docker

Build image:

```bash
docker build -t mp_423 .
```

Run container:

```bash
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=your_bot_token \
  -e MAX_VIDEO_SIZE_MB=100 \
  -e TEMP_DIR=./tmp \
  mp_423
```

## Deploy on a VPS

1. Provision a Linux VPS (Ubuntu 22.04+ recommended).
2. Install Docker (or Python 3.10+ and FFmpeg for non-Docker mode).
3. Copy project files to the server.
4. Set secure environment variables (use `.env` with restricted permissions).
5. Run with Docker as a restartable service:

```bash
docker run -d \
  --name mp_423 \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=your_bot_token \
  -e MAX_VIDEO_SIZE_MB=100 \
  -e TEMP_DIR=./tmp \
  mp_423
```

### Non-Docker VPS with systemd

1. Create app directory and copy project files to `/opt/telegram-audio-bot`.
2. Create virtual environment and install dependencies.
3. Copy `.env.example` to `.env` and set real values.
4. Install the service file from `deploy/telegram-audio-bot.service` into `/etc/systemd/system/`.
5. Update `User`, `WorkingDirectory`, `EnvironmentFile`, and `ExecStart` inside the service file to match your server.
6. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-audio-bot
sudo systemctl start telegram-audio-bot
sudo systemctl status telegram-audio-bot
```

## Notes

- Default output is MP3 audio.
- If `/voice` is sent before a video, the next processed output is OGG (`libopus`) and sent as a voice message.
- The bot rejects videos over `MAX_VIDEO_SIZE_MB`.
- The bot refuses to send output audio larger than 20MB.
