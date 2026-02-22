import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Bot Credentials ──────────────────────────────────────────────────────
    BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
    API_ID           = int(os.environ.get("API_ID", 0))
    API_HASH         = os.environ.get("API_HASH", "")

    # ── MongoDB ──────────────────────────────────────────────────────────────
    FILES_DB_URI     = os.environ.get("FILES_DB_URI", "mongodb://localhost:27017")
    USERS_DB_URI     = os.environ.get("USERS_DB_URI", "mongodb://localhost:27017")
    FILES_DB_NAME    = os.environ.get("FILES_DB_NAME", "AutoFilterFiles")
    USERS_DB_NAME    = os.environ.get("USERS_DB_NAME", "AutoFilterUsers")

    # ── Channels ─────────────────────────────────────────────────────────────
    LOG_CHANNEL      = int(os.environ.get("LOG_CHANNEL", 0))
    FSUB_CHANNEL     = int(os.environ.get("FSUB_CHANNEL", 0))  # 0 = disabled

    # ── Admins ───────────────────────────────────────────────────────────────
    ADMINS           = list(map(int, os.environ.get("ADMINS", "").split()))

    # ── Shortlink ────────────────────────────────────────────────────────────
    SHORTLINK_URL    = os.environ.get("SHORTLINK_URL", "")    # e.g. shrinkme.io
    SHORTLINK_API    = os.environ.get("SHORTLINK_API", "")
    VERIFY_EXPIRE    = int(os.environ.get("VERIFY_EXPIRE", 86400))  # seconds (24h)

    # ── Features ─────────────────────────────────────────────────────────────
    VERIFICATION_ON  = os.environ.get("VERIFICATION_ON", "true").lower() == "true"
    PROTECT_CONTENT  = os.environ.get("PROTECT_CONTENT", "false").lower() == "true"
    AUTO_DELETE      = int(os.environ.get("AUTO_DELETE", 300))   # seconds; 0 = off
    SPELL_CHECK      = os.environ.get("SPELL_CHECK", "true").lower() == "true"
    LINK_MODE        = os.environ.get("LINK_MODE", "false").lower() == "true"
    PM_SEARCH        = os.environ.get("PM_SEARCH", "true").lower() == "true"

    # ── Templates ────────────────────────────────────────────────────────────
    DEFAULT_CAPTION  = os.environ.get(
        "DEFAULT_CAPTION",
        "📁 **{file_name}**\n💾 Size: {file_size}\n🗂 Type: {file_type}"
    )
    IMDB_TEMPLATE    = os.environ.get(
        "IMDB_TEMPLATE",
        "🎬 **{title}** ({year})\n⭐ Rating: {rating}\n🎭 Genre: {genres}\n📖 {plot}"
    )

    # ── Misc ─────────────────────────────────────────────────────────────────
    MAX_RESULTS      = int(os.environ.get("MAX_RESULTS", 10))
    LANGUAGES        = ["en", "hi", "ar"]
    DEFAULT_LANG     = os.environ.get("DEFAULT_LANG", "en")
    TUTORIAL_VIDEO   = os.environ.get("TUTORIAL_VIDEO", "")
