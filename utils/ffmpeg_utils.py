from __future__ import annotations

import asyncio
import shutil
from pathlib import Path


class FFmpegError(Exception):
    pass


class FFmpegNotInstalledError(FFmpegError):
    pass


class NoAudioTrackError(FFmpegError):
    pass


def ensure_ffmpeg_installed() -> None:
    if shutil.which("ffmpeg") is None:
        raise FFmpegNotInstalledError("ffmpeg executable was not found in PATH")


async def extract_audio_to_mp3(input_path: Path, output_path: Path) -> None:
    await _run_ffmpeg(
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
    )


async def extract_audio_to_ogg(input_path: Path, output_path: Path) -> None:
    await _run_ffmpeg(
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-c:a",
        "libopus",
        str(output_path),
    )


async def _run_ffmpeg(*args: str) -> None:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _stdout, stderr = await process.communicate()

    if process.returncode == 0:
        return

    err_text = stderr.decode("utf-8", errors="ignore")
    no_audio_markers = (
        "does not contain any stream",
        "matches no streams",
        "output file #0 does not contain any stream",
    )
    if any(marker in err_text.lower() for marker in no_audio_markers):
        raise NoAudioTrackError("Input video does not contain an audio track")

    raise FFmpegError(err_text.strip() or "ffmpeg failed with unknown error")
