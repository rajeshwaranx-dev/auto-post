"""
FileStoreBot – main.py
═══════════════════════
Entry point for the FileStoreBot.

Responsibilities:
    • /start                → welcome message
    • /start <unique_id>    → look up file_id in MongoDB and send the file
                              privately to the requesting user
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from shared.config import API_ID, API_HASH, FILE_STORE_BOT_TOKEN
from shared.database import init_db, close_db, get_movie_by_unique_id

logger = logging.getLogger(__name__)

# ── Pyrogram client ────────────────────────────────────────────────────────────
app = Client(
    name="FileStoreBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=FILE_STORE_BOT_TOKEN,
)

# ── Message templates ──────────────────────────────────────────────────────────

_WELCOME_TEXT = (
    "👋 <b>Welcome to FileStoreBot!</b>\n\n"
    "Click a <b>Download</b> link from our main channel to receive a file here.\n\n"
    "🔒 Files are delivered privately – only you can see them."
)

_NOT_FOUND_TEXT = (
    "❌ <b>File Not Found</b>\n\n"
    "The link you used is invalid or the file has been removed.\n"
    "Please check the main channel for an updated link."
)

_SENDING_TEXT = "⏳ Fetching your file, please wait…"

_ERROR_TEXT = (
    "⚠️ <b>Delivery Error</b>\n\n"
    "Something went wrong while sending your file.\n"
    "Please try again in a moment."
)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _send_file(client: Client, chat_id: int, file_id: str, movie: dict) -> None:
    """
    Forward the stored file to *chat_id* using its cached file_id.
    Handles both video and document types transparently – Telegram
    infers the media type from the file_id.
    """
    title = movie.get("cleaned_title", "Movie")
    quality = movie.get("quality", "")
    caption = f"🎬 <b>{title}</b>  [{quality}]"

    try:
        # Try sending as video first; fall back to document on failure.
        await client.send_video(
            chat_id=chat_id,
            video=file_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await client.send_document(
            chat_id=chat_id,
            document=file_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )


# ── /start handler ─────────────────────────────────────────────────────────────

@app.on_message(filters.private & filters.command("start"))
async def handle_start(client: Client, message: Message) -> None:
    """
    Dispatch /start commands:
        /start           → welcome message
        /start <uid>     → deliver file identified by <uid>
    """
    parts = message.text.split(maxsplit=1)

    # ── Plain /start (no payload) ──────────────────────────────────────────
    if len(parts) == 1:
        await message.reply_text(
            _WELCOME_TEXT,
            parse_mode=ParseMode.HTML,
        )
        return

    unique_id = parts[1].strip()

    # ── Validate ID format (must be alphanumeric, exactly UNIQUE_ID_LENGTH) ──
    if not unique_id.isalnum() or len(unique_id) != 8:
        await message.reply_text(_NOT_FOUND_TEXT, parse_mode=ParseMode.HTML)
        return

    # ── Lookup in MongoDB ─────────────────────────────────────────────────
    movie = await get_movie_by_unique_id(unique_id)

    if movie is None:
        logger.info("Unknown unique_id='%s' requested by user %s", unique_id, message.from_user.id)
        await message.reply_text(_NOT_FOUND_TEXT, parse_mode=ParseMode.HTML)
        return

    # ── Acknowledge and deliver ───────────────────────────────────────────
    ack = await message.reply_text(_SENDING_TEXT)

    try:
        await _send_file(client, message.chat.id, movie["file_id"], movie)
        await ack.delete()

        logger.info(
            "File '%s' (%s) delivered to user %s",
            movie.get("cleaned_title"),
            movie.get("quality"),
            message.from_user.id,
        )

    except FloodWait as exc:
        logger.warning("FloodWait: sleeping %s seconds.", exc.value)
        await asyncio.sleep(exc.value)
        await _send_file(client, message.chat.id, movie["file_id"], movie)
        await ack.delete()

    except (UserIsBlocked, InputUserDeactivated) as exc:
        logger.warning("Cannot deliver to user %s: %s", message.from_user.id, exc)
        # Silently swallow – the user blocked the bot

    except Exception as exc:
        logger.error(
            "Unexpected error delivering '%s' to user %s: %s",
            unique_id,
            message.from_user.id,
            exc,
        )
        try:
            await ack.edit_text(_ERROR_TEXT, parse_mode=ParseMode.HTML)
        except Exception:
            pass


# ── Lifecycle ──────────────────────────────────────────────────────────────────

async def main() -> None:
    await init_db()
    await app.start()
    logger.info("FileStoreBot is running…")
    await idle()
    await app.stop()
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
