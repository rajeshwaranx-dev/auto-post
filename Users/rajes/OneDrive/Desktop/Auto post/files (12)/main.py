"""
AutoPosterBot – main.py
════════════════════════
Entry point for the AutoPosterBot.

Responsibilities:
    • Watches the SOURCE_CHANNEL for new video / document messages.
    • Cleans the filename → title, detects quality.
    • Fetches IMDb metadata from OMDb.
    • Stores the record in MongoDB (with duplicate protection).
    • Posts an IMDb-poster + formatted caption to MAIN_CHANNEL.
"""

import asyncio
import logging
import sys
import os

# Allow `shared` package imports from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyrogram import Client, filters, idle
from pyrogram.types import Message, InputMediaPhoto
from pyrogram.enums import ParseMode

from shared.config import API_ID, API_HASH, AUTO_POSTER_BOT_TOKEN, SOURCE_CHANNEL, MAIN_CHANNEL
from shared.database import init_db, close_db, insert_movie, movie_exists
from shared.imdb import fetch_imdb_data
from shared.utils import clean_title, extract_quality, generate_unique_id, build_deep_link, format_post_caption

logger = logging.getLogger(__name__)

# ── Pyrogram client ────────────────────────────────────────────────────────────
app = Client(
    name="AutoPosterBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=AUTO_POSTER_BOT_TOKEN,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_media(message: Message):
    """Return the first media object that carries a file_name, or None."""
    return message.video or message.document


def _get_filename(message: Message) -> str | None:
    """Extract raw filename from a video or document message."""
    media = _get_media(message)
    if media is None:
        return None
    # .file_name may be None if Telegram did not provide one
    return getattr(media, "file_name", None)


def _get_file_id(message: Message) -> str | None:
    """Return the Telegram file_id for video or document."""
    media = _get_media(message)
    return media.file_id if media else None


async def _post_to_main_channel(
    client: Client,
    poster_url: str,
    caption: str,
) -> None:
    """
    Send the movie post to MAIN_CHANNEL.

    • If a valid poster URL is available → send as photo with caption.
    • Otherwise → send as text message.
    """
    if poster_url and poster_url != "N/A":
        try:
            await client.send_photo(
                chat_id=MAIN_CHANNEL,
                photo=poster_url,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception as exc:
            logger.warning("Poster send failed (%s), falling back to text post.", exc)

    await client.send_message(
        chat_id=MAIN_CHANNEL,
        text=caption,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=False,
    )


# ── Handler ────────────────────────────────────────────────────────────────────

@app.on_message(
    filters.chat(SOURCE_CHANNEL)
    & (filters.video | filters.document)
)
async def handle_new_file(client: Client, message: Message) -> None:
    """
    Core handler: called whenever a video or document is posted to
    SOURCE_CHANNEL.
    """
    filename = _get_filename(message)
    file_id = _get_file_id(message)

    if not filename or not file_id:
        logger.debug("Message %s has no filename/file_id – skipped.", message.id)
        return

    logger.info("New file detected: '%s'", filename)

    # ── Step 1: Extract metadata from filename ─────────────────────────────
    quality = extract_quality(filename)
    cleaned = clean_title(filename)

    logger.info("Cleaned title='%s'  quality='%s'", cleaned, quality)

    # ── Step 2: Duplicate protection ───────────────────────────────────────
    if await movie_exists(cleaned, quality):
        logger.info("Duplicate detected – '%s' (%s) already in DB. Skipping.", cleaned, quality)
        return

    # ── Step 3: IMDb data ──────────────────────────────────────────────────
    imdb_data = await fetch_imdb_data(cleaned)

    # ── Step 4: Generate unique ID & persist ───────────────────────────────
    unique_id = generate_unique_id()

    # Collision guard (extremely unlikely but correct to handle)
    from shared.database import get_movie_by_unique_id
    attempts = 0
    while await get_movie_by_unique_id(unique_id) is not None:
        unique_id = generate_unique_id()
        attempts += 1
        if attempts > 10:
            logger.error("Could not generate a unique ID after 10 attempts. Aborting.")
            return

    document = {
        "unique_id": unique_id,
        "file_id": file_id,
        "cleaned_title": cleaned,
        "quality": quality,
        "imdb": imdb_data,
    }

    success = await insert_movie(document)
    if not success:
        logger.error("DB insert failed for '%s' – aborting post.", cleaned)
        return

    logger.info("Stored movie with unique_id='%s'", unique_id)

    # ── Step 5: Build caption & post ──────────────────────────────────────
    deep_link = build_deep_link(unique_id)
    caption = format_post_caption(cleaned, quality, deep_link, imdb_data)

    await _post_to_main_channel(client, imdb_data.get("poster", "N/A"), caption)
    logger.info("Posted '%s' (%s) to main channel.", cleaned, quality)


# ── Lifecycle ──────────────────────────────────────────────────────────────────

async def main() -> None:
    await init_db()
    await app.start()
    logger.info("AutoPosterBot is running…")
    await idle()
    await app.stop()
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
