"""General helper utilities."""
import re
import math
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def humanbytes(size: int) -> str:
    """Convert bytes to human-readable string."""
    if not size:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    return f"{size / p:.2f} {units[i]}"


def get_file_type(message) -> str:
    for attr in ("document", "video", "audio", "photo", "sticker", "animation"):
        if getattr(message, attr, None):
            return attr
    return "unknown"


def extract_file_info(message) -> dict:
    """Extract file metadata from a Pyrogram message."""
    media = (
        message.document or message.video or message.audio
        or message.photo or message.animation
    )
    if not media:
        return {}
    file_name = getattr(media, "file_name", None) or "untitled"
    file_size = humanbytes(getattr(media, "file_size", 0))
    file_id   = media.file_id
    file_type = get_file_type(message)
    return {
        "file_id":    file_id,
        "file_name":  file_name,
        "file_size":  file_size,
        "file_type":  file_type,
        "caption":    message.caption or "",
        "group_id":   message.chat.id,
        "indexed_at": datetime.utcnow(),
    }


def spell_check_query(query: str) -> list[str]:
    """
    Generate spelling alternatives by inserting spaces, removing special chars,
    and creating basic phonetic variants – lightweight, no external lib required.
    """
    query   = query.strip()
    cleaned = re.sub(r"[^\w\s]", " ", query).strip()
    parts   = cleaned.split()
    variants = {query, cleaned, " ".join(parts)}
    # Common substitutions
    subs = [("0", "o"), ("1", "i"), ("3", "e"), ("@", "a"), ("$", "s")]
    for old, new in subs:
        variants.add(query.replace(old, new))
    return list(variants)


def paginate(data: list, page: int, per_page: int = 10):
    """Slice a list for pagination and return (slice, total_pages)."""
    start = page * per_page
    total = math.ceil(len(data) / per_page)
    return data[start:start + per_page], total


def format_timedelta(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"
