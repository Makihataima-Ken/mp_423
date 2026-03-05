from __future__ import annotations

import logging
import time
from pathlib import Path

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import Settings, get_settings
from utils.ffmpeg_utils import (
    FFmpegError,
    FFmpegNotInstalledError,
    NoAudioTrackError,
    ensure_ffmpeg_installed,
    extract_audio_to_mp3,
    extract_audio_to_ogg,
)
from utils.file_utils import cleanup_files, ensure_temp_dir, unique_file_path

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message is None:
        return
    await update.message.reply_text("Send me a video and I will extract the audio.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    settings: Settings = context.bot_data["settings"]
    await update.message.reply_text(
        "Supported input: Telegram video and video documents.\n"
        f"Max video size: {settings.max_video_size_mb}MB.\n"
        "Default output: MP3 audio.\n"
        "Use /voice before sending a video to receive OGG voice output.\n"
        f"Max output size for sending: {settings.max_audio_send_size_mb}MB."
    )


async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    context.user_data["next_output_mode"] = "voice"
    await update.message.reply_text("Voice mode enabled for your next video. Send it now.")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None:
        return

    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id if update.effective_user else -1

    media = message.video
    file_name_hint = "video.mp4"

    if media is None and message.document and message.document.mime_type:
        if message.document.mime_type.startswith("video/"):
            media = message.document
            file_name_hint = message.document.file_name or file_name_hint

    if media is None:
        await message.reply_text("Please send a valid video file.")
        return

    file_size = media.file_size or 0
    logger.info("user_id=%s received_video size_bytes=%s", user_id, file_size)

    if file_size > settings.max_video_size_bytes:
        await message.reply_text(
            f"File is too large. Maximum allowed size is {settings.max_video_size_mb}MB."
        )
        logger.warning("user_id=%s rejected_video_too_large size_bytes=%s", user_id, file_size)
        return

    ensure_temp_dir(settings.temp_dir)
    input_suffix = Path(file_name_hint).suffix or ".mp4"
    input_path = unique_file_path(settings.temp_dir, input_suffix)

    output_mode = context.user_data.pop("next_output_mode", "audio")
    output_suffix = ".ogg" if output_mode == "voice" else ".mp3"
    output_path = unique_file_path(settings.temp_dir, output_suffix)

    started_at = time.perf_counter()

    try:
        tg_file = await media.get_file()
        await tg_file.download_to_drive(custom_path=str(input_path))

        if output_mode == "voice":
            await extract_audio_to_ogg(input_path, output_path)
        else:
            await extract_audio_to_mp3(input_path, output_path)

        if not output_path.exists():
            raise FFmpegError("ffmpeg did not produce an output file")

        audio_size = output_path.stat().st_size
        if audio_size > settings.max_audio_send_size_bytes:
            await message.reply_text(
                "Extracted audio is too large to send via Telegram in this bot configuration."
            )
            logger.warning("user_id=%s output_too_large size_bytes=%s", user_id, audio_size)
            return

        if output_mode == "voice":
            with output_path.open("rb") as voice_stream:
                await message.reply_voice(voice=voice_stream)
        else:
            with output_path.open("rb") as audio_stream:
                await message.reply_audio(audio=audio_stream, filename=f"extracted{output_suffix}")

        elapsed = time.perf_counter() - started_at
        logger.info(
            "user_id=%s processed_success input_bytes=%s output_bytes=%s elapsed_sec=%.2f mode=%s",
            user_id,
            file_size,
            audio_size,
            elapsed,
            output_mode,
        )

    except FFmpegNotInstalledError:
        logger.exception("user_id=%s ffmpeg_not_installed", user_id)
        await message.reply_text("Server error: ffmpeg is not installed.")
    except NoAudioTrackError:
        logger.warning("user_id=%s no_audio_track", user_id)
        await message.reply_text("This video does not appear to have an audio track.")
    except TelegramError:
        logger.exception("user_id=%s telegram_error_during_download_or_send", user_id)
        await message.reply_text("Telegram file operation failed. Please try again.")
    except FFmpegError:
        logger.exception("user_id=%s ffmpeg_error", user_id)
        await message.reply_text("Failed to extract audio from this video.")
    except Exception:
        logger.exception("user_id=%s unexpected_error", user_id)
        await message.reply_text("Unexpected error while processing your video.")
    finally:
        cleanup_files(input_path, output_path)


def build_application(settings: Settings) -> Application:
    ensure_ffmpeg_installed()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("voice", voice_command))
    app.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)
    )

    return app


def main() -> None:
    settings = get_settings()
    app = build_application(settings)
    logger.info("Bot starting with max_video_size_mb=%s", settings.max_video_size_mb)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
