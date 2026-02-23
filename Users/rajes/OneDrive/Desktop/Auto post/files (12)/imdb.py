"""
imdb.py – Async OMDb API wrapper.

Returns a normalised dict so the rest of the codebase never touches
raw OMDb response keys directly.
"""

import logging
from typing import Optional

import aiohttp

from .config import OMDB_API_KEY, OMDB_BASE_URL

logger = logging.getLogger(__name__)


# Internal sentinel for "not found / unavailable"
_NA = "N/A"


def _clean_value(value: Optional[str]) -> str:
    """Return the value as-is unless it is None, empty, or the OMDb 'N/A'."""
    if not value or value.strip() == _NA:
        return _NA
    return value.strip()


async def fetch_imdb_data(title: str) -> dict:
    """
    Query the OMDb API for *title* and return a normalised dict.

    Returned keys
    ─────────────
        title    : str
        year     : str
        rating   : str  (e.g. "8.3")
        genre    : str  (e.g. "Action, Thriller")
        director : str
        plot     : str
        poster   : str  (URL or "N/A")

    On any network / API error a dict full of "N/A" values is returned
    so the caller can always proceed safely.
    """
    default = {
        "title": title,
        "year": _NA,
        "rating": _NA,
        "genre": _NA,
        "director": _NA,
        "plot": _NA,
        "poster": _NA,
    }

    params = {
        "apikey": OMDB_API_KEY,
        "t": title,
        "type": "movie",
        "plot": "short",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                OMDB_BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "OMDb returned HTTP %s for title='%s'", resp.status, title
                    )
                    return default

                data = await resp.json(content_type=None)

    except aiohttp.ClientError as exc:
        logger.error("OMDb network error for '%s': %s", title, exc)
        return default
    except Exception as exc:
        logger.error("Unexpected OMDb error for '%s': %s", title, exc)
        return default

    if data.get("Response") != "True":
        logger.info(
            "OMDb: no results for '%s' (reason: %s)",
            title,
            data.get("Error", "unknown"),
        )
        return default

    result = {
        "title": _clean_value(data.get("Title")) or title,
        "year": _clean_value(data.get("Year")),
        "rating": _clean_value(data.get("imdbRating")),
        "genre": _clean_value(data.get("Genre")),
        "director": _clean_value(data.get("Director")),
        "plot": _clean_value(data.get("Plot")),
        "poster": _clean_value(data.get("Poster")),
    }

    logger.debug("OMDb hit: %s (%s) – ★ %s", result["title"], result["year"], result["rating"])
    return result
