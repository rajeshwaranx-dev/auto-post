"""
utils.py – Pure utility functions (no I/O, no network, fully synchronous).

Responsibilities:
    • Filename → cleaned movie title
    • Filename → quality tag
    • Generate cryptographically random unique IDs
    • Deep-link builder
"""

import re
import string
import secrets
import logging

from .config import UNIQUE_ID_LENGTH, FILE_STORE_BOT_USERNAME

logger = logging.getLogger(__name__)

# ── Shared separator character class ──────────────────────────────────────────
# We use this lookaround approach so that patterns match even when surrounded
# by underscores (which are \w in Python's regex engine, breaking plain \b).
# SEP matches: start/end of string OR any non-alphanumeric character.
_SEP = r"(?:(?<=[^a-zA-Z0-9])|(?=[^a-zA-Z0-9])|^|$)"

def _sep_wrap(inner: str) -> str:
    """Wrap a pattern so it only matches when surrounded by separators."""
    return r"(?:(?:^|(?<=[^a-zA-Z0-9]))(?:" + inner + r")(?=$|[^a-zA-Z0-9]))"

# ── Regex patterns (compiled once at import time) ──────────────────────────────

# Resolution / quality markers
_QUALITY_INNER = r"2160p|4k|uhd|1080p|1080i|720p|480p|360p|240p"
_RE_QUALITY = re.compile(_sep_wrap(_QUALITY_INNER), flags=re.IGNORECASE)

# Video / audio codecs — include standalone "hd" only when preceded by "dts-"
# to avoid removing the word "hd" that might appear as part of a title.
_RE_CODECS = re.compile(
    _sep_wrap(
        r"x264|x265|h264|h265|hevc|avc|xvid|divx|"
        r"aac|ac3|dts[-._]?hd|dts|mp3|flac|"
        r"dd5\.?1|truehd|atmos|hdr10\+?|hdr|dolby|dv|dovi"
    ),
    flags=re.IGNORECASE,
)

# Source / rip type tags
_RE_SOURCE = re.compile(
    _sep_wrap(
        r"blu[-._]?ray|bluray|bdrip|brrip|"
        r"web[-._]?dl|webrip|"
        r"hdrip|hdtv|hdcam|hd[-._]?cam|"
        r"dvdrip|dvdscr|dvd|"
        r"vodrip|amzn|nf|netflix|amazon|hulu|dsnp|disney|"
        r"ts|r5|workprint"
    ),
    flags=re.IGNORECASE,
)

# Audio / subtitle language tags
_RE_LANGUAGES = re.compile(
    _sep_wrap(
        r"tamil|telugu|hindi|malayalam|kannada|bengali|punjabi|marathi|"
        r"english|dual|multi|dubbed|subbed|esubs|esub|subs|sub|"
        r"hin|tam|tel|mal|kan|ben|eng"
    ),
    flags=re.IGNORECASE,
)

# Release group tags commonly appended after a hyphen (e.g. "-YIFY", "-RARBG")
_RE_RELEASE_GROUP = re.compile(
    r"[-]\s*(?:yify|yts|rarbg|ettv|eztv|publichd|fgt|ntb|ion10|cmrg|"
    r"sparks|geckos|tigole|hive-cm8|qxr|framestor|rovers|cakes|"
    r"flux|nhanc3|d3g|msd|mkv|[a-z0-9]{2,8})\s*$",
    flags=re.IGNORECASE,
)

# Year patterns (1900–2099)
_RE_YEAR = re.compile(r"(?:^|(?<=[^a-zA-Z]))(19|20)\d{2}(?=[^a-zA-Z]|$)")

# Hyphens that are BETWEEN two letters should be preserved (e.g. Spider-Man).
# Hyphens that are isolated (surrounded by spaces or at word/separator boundary)
# should be removed.  We handle this in clean_title() explicitly.

# Leftover standalone separator characters after keyword removal
_RE_LEFTOVER_SEP = re.compile(r"(?:^|\s)[._\-\[\](){}|+,]+(?=\s|$)")

# Multiple consecutive spaces
_RE_MULTI_SPACE = re.compile(r"\s{2,}")

# File extension (last dot + up to 5 chars, end of string)
_RE_EXTENSION = re.compile(r"\.[a-zA-Z0-9]{2,5}$")

# ── Quality extraction ─────────────────────────────────────────────────────────

# Normalise filename for quality matching (replace separators with spaces)
def _normalise_for_quality(filename: str) -> str:
    return re.sub(r"[._\-]", " ", filename.lower())


def extract_quality(filename: str) -> str:
    """
    Detect video quality from filename.

    Priority: 2160p/4K > 1080p > 720p > 480p > HD (fallback)
    Uses space-normalised string so underscores don't fool word boundaries.
    """
    norm = _normalise_for_quality(filename)

    if re.search(r"\b(?:2160p|4k|uhd)\b", norm):
        return "4K"
    if re.search(r"\b1080[pi]\b", norm):
        return "1080p"
    if re.search(r"\b720p\b", norm):
        return "720p"
    if re.search(r"\b480p\b", norm):
        return "480p"

    return "HD"


# ── Title cleaning ─────────────────────────────────────────────────────────────

def clean_title(filename: str) -> str:
    """
    Extract a clean human-readable movie title from a raw filename.

    Steps
    ─────
    1. Strip the file extension.
    2. Replace dots and underscores with spaces.
    3. Remove trailing release-group tags (e.g. -YIFY).
    4. Iteratively remove quality, codec, source, language, and year tokens.
    5. Remove isolated separator characters.
    6. Strip and normalise internal whitespace.
    7. Title-case the result.

    Hyphens between two letters (e.g. Spider-Man) are deliberately preserved.
    """
    name = _RE_EXTENSION.sub("", filename)

    # Replace dots and underscores with spaces; preserve hyphens for now
    name = re.sub(r"[._]", " ", name)

    # Strip trailing release-group tags before further processing
    name = _RE_RELEASE_GROUP.sub("", name)

    # Remove keyword groups in priority order
    for pattern in (_RE_QUALITY, _RE_CODECS, _RE_SOURCE, _RE_LANGUAGES, _RE_YEAR):
        name = pattern.sub(" ", name)

    # Remove hyphens that are NOT between two letters (isolated separators)
    name = re.sub(r"(?<![a-zA-Z])-|-(?![a-zA-Z])", " ", name)

    # Remove other leftover punctuation standing alone
    name = re.sub(r"[\[\](){}|+,]+", " ", name)

    # Collapse whitespace
    name = _RE_MULTI_SPACE.sub(" ", name).strip()

    # Title-case (handles empty string safely)
    title = name.title() if name else filename

    logger.debug("clean_title: '%s' → '%s'", filename, title)
    return title


def generate_unique_id() -> str:
    """
    Return a URL-safe, cryptographically random alphanumeric string of
    length UNIQUE_ID_LENGTH (default 8).

    Alphabet: A-Z, a-z, 0-9  (62 chars → ≈47-bit entropy at length 8)
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(UNIQUE_ID_LENGTH))


def build_deep_link(unique_id: str) -> str:
    """
    Build a Telegram start deep-link pointing to FileStoreBot.
    e.g. https://t.me/FileStoreBot?start=aB3kR7Xz
    """
    return f"https://t.me/{FILE_STORE_BOT_USERNAME}?start={unique_id}"


def format_post_caption(
    cleaned_title: str,
    quality: str,
    deep_link: str,
    imdb: dict,
) -> str:
    """
    Build the HTML-formatted caption for the main channel post.

    Args:
        cleaned_title : Clean movie title string.
        quality       : Quality tag (4K / 1080p / 720p / 480p / HD).
        deep_link     : Download deep-link URL.
        imdb          : Dict with keys: title, year, rating, genre,
                        director, plot  (all strings, may be "N/A").
    """
    title_display = imdb.get("title") or cleaned_title
    year = imdb.get("year", "N/A")
    rating = imdb.get("rating", "N/A")
    genre = imdb.get("genre", "N/A")
    director = imdb.get("director", "N/A")
    plot = imdb.get("plot", "N/A")

    # Truncate long plots so captions stay within Telegram's 1024-char limit
    if plot and len(plot) > 300:
        plot = plot[:297] + "…"

    caption = (
        f"🎬 <b>{title_display}</b>  ({year})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ <b>IMDb Rating:</b> {rating}\n"
        f"🎭 <b>Genre:</b> {genre}\n"
        f"🎥 <b>Director:</b> {director}\n"
        f"📺 <b>Quality:</b> {quality}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Plot:</b> <i>{plot}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 <b><a href=\"{deep_link}\">Download / Get File</a></b>"
    )

    return caption
