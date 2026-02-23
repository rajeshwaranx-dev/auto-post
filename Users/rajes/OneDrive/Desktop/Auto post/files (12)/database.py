"""
database.py – Async MongoDB interface using Motor.

Collection schema (movies):
    _id          : ObjectId (auto)
    unique_id    : str  – 8-char alphanumeric, indexed unique
    file_id      : str  – Telegram file_id
    cleaned_title: str  – human-readable movie title
    quality      : str  – 4K | 1080p | 720p | 480p | HD
    imdb         : dict – title, year, rating, genre, director, plot, poster
    created_at   : datetime (UTC)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import motor.motor_asyncio
from pymongo import ASCENDING, IndexModel

from .config import MONGO_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)

# ── Motor client (module-level singleton) ─────────────────────────────────────
_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Return the database handle; raises if not initialised."""
    if _db is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _db


async def init_db() -> None:
    """Connect to MongoDB and ensure required indexes exist."""
    global _client, _db

    _client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    _db = _client[MONGO_DB_NAME]

    # Verify connectivity
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB at %s (db=%s)", MONGO_URI, MONGO_DB_NAME)

    # Ensure indexes
    movies = _db["movies"]
    await movies.create_indexes(
        [
            IndexModel([("unique_id", ASCENDING)], unique=True, name="idx_unique_id"),
            IndexModel(
                [("cleaned_title", ASCENDING), ("quality", ASCENDING)],
                unique=False,
                name="idx_title_quality",
            ),
        ]
    )
    logger.info("MongoDB indexes verified.")


async def close_db() -> None:
    """Gracefully close the MongoDB connection."""
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed.")


# ── CRUD helpers ───────────────────────────────────────────────────────────────

async def insert_movie(document: dict) -> bool:
    """
    Insert a movie document.
    Returns True on success, False if the document already exists.
    """
    db = get_db()
    document["created_at"] = datetime.now(tz=timezone.utc)
    try:
        await db["movies"].insert_one(document)
        logger.debug("Inserted movie: %s (%s)", document["cleaned_title"], document["quality"])
        return True
    except Exception as exc:
        logger.warning("Insert failed (likely duplicate): %s", exc)
        return False


async def movie_exists(cleaned_title: str, quality: str) -> bool:
    """
    Duplicate protection: check whether a movie with the same title
    and quality has already been stored.
    """
    db = get_db()
    doc = await db["movies"].find_one(
        {"cleaned_title": cleaned_title, "quality": quality},
        projection={"_id": 1},
    )
    return doc is not None


async def get_movie_by_unique_id(unique_id: str) -> Optional[dict]:
    """Fetch a movie document by its unique_id."""
    db = get_db()
    return await db["movies"].find_one({"unique_id": unique_id})
