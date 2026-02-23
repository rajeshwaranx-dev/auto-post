"""
config.py – Centralised configuration loaded from environment variables.
Both bots import from this module; values are validated at startup.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Telegram API ───────────────────────────────────────────────────────────────
API_ID: int = int(os.environ["API_ID"])
API_HASH: str = os.environ["API_HASH"]

AUTO_POSTER_BOT_TOKEN: str = os.environ["AUTO_POSTER_BOT_TOKEN"]
FILE_STORE_BOT_TOKEN: str = os.environ["FILE_STORE_BOT_TOKEN"]

# Channel IDs (negative integers for supergroups/channels)
SOURCE_CHANNEL: int = int(os.environ["SOURCE_CHANNEL"])
MAIN_CHANNEL: int = int(os.environ["MAIN_CHANNEL"])

# FileStoreBot public username (no @) – used for deep-link generation
FILE_STORE_BOT_USERNAME: str = os.environ["FILE_STORE_BOT_USERNAME"]

# ── MongoDB ────────────────────────────────────────────────────────────────────
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "telegram_autopost")

# ── OMDb ───────────────────────────────────────────────────────────────────────
OMDB_API_KEY: str = os.environ["OMDB_API_KEY"]
OMDB_BASE_URL: str = "https://www.omdbapi.com/"

# ── Unique ID ──────────────────────────────────────────────────────────────────
UNIQUE_ID_LENGTH: int = 8

logger.info("Configuration loaded successfully.")
