from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    max_video_size_mb: int
    temp_dir: Path
    max_audio_send_size_mb: int = 20

    @property
    def max_video_size_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024

    @property
    def max_audio_send_size_bytes(self) -> int:
        return self.max_audio_send_size_mb * 1024 * 1024


def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    max_video_size_mb = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))
    temp_dir = Path(os.getenv("TEMP_DIR", "./tmp"))

    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable")

    return Settings(
        telegram_bot_token=token,
        max_video_size_mb=max_video_size_mb,
        temp_dir=temp_dir,
    )
