import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass   # dotenv optional; env vars set directly on the platform


class Config:
    # ── Bot Credentials ──────────────────────────────────────────────────────
    BOT_TOKEN       = os.environ.get("BOT_TOKEN", "")
    API_ID          = int(os.environ.get("API_ID", 0))
    API_HASH        = os.environ.get("API_HASH", "")

    # ── MongoDB (two separate databases) ────────────────────────────────────
    FILES_DB_URI    = os.environ.get("FILES_DB_URI", "")
    USERS_DB_URI    = os.environ.get("USERS_DB_URI", "")
    FILES_DB_NAME   = os.environ.get("FILES_DB_NAME", "AutoFilterFiles")
    USERS_DB_NAME   = os.environ.get("USERS_DB_NAME", "AutoFilterUsers")

    # ── Channels ─────────────────────────────────────────────────────────────
    LOG_CHANNEL     = int(os.environ.get("LOG_CHANNEL", 0))
    FSUB_CHANNEL    = int(os.environ.get("FSUB_CHANNEL", 0))   # 0 = disabled

    # ── Admins (space-separated user IDs) ────────────────────────────────────
    ADMINS          = list(map(int, os.environ.get("ADMINS", "").split()))

    # ── Shortlink ────────────────────────────────────────────────────────────
    SHORTLINK_URL   = os.environ.get("SHORTLINK_URL", "")
    SHORTLINK_API   = os.environ.get("SHORTLINK_API", "")
    VERIFY_EXPIRE   = int(os.environ.get("VERIFY_EXPIRE", 86400))   # seconds

    # ── Feature Toggles ──────────────────────────────────────────────────────
    VERIFICATION_ON  = os.environ.get("VERIFICATION_ON", "true").lower() == "true"
    PROTECT_CONTENT  = os.environ.get("PROTECT_CONTENT", "false").lower() == "true"
    AUTO_DELETE      = int(os.environ.get("AUTO_DELETE", 300))   # 0 = off
    SPELL_CHECK      = os.environ.get("SPELL_CHECK", "true").lower() == "true"
    LINK_MODE        = os.environ.get("LINK_MODE", "false").lower() == "true"
    PM_SEARCH        = os.environ.get("PM_SEARCH", "true").lower() == "true"

    # ── Default Templates ────────────────────────────────────────────────────
    DEFAULT_CAPTION = os.environ.get(
        "DEFAULT_CAPTION",
        "📁 **{file_name}**\n💾 Size: {file_size}\n🗂 Type: {file_type}"
    )
    IMDB_TEMPLATE   = os.environ.get(
        "IMDB_TEMPLATE",
        "🎬 **{title}** ({year})\n⭐ Rating: {rating}\n🎭 Genre: {genres}\n📖 {plot}"
    )
    TUTORIAL_VIDEO  = os.environ.get("TUTORIAL_VIDEO", "")

    # ── Misc ─────────────────────────────────────────────────────────────────
    MAX_RESULTS     = int(os.environ.get("MAX_RESULTS", 10))
    DEFAULT_LANG    = os.environ.get("DEFAULT_LANG", "en")
