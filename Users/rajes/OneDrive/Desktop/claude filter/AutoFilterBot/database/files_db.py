"""
Files Database  –  stores file metadata, captions, and index info.
Collection: files
"""
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

_client = AsyncIOMotorClient(Config.FILES_DB_URI)
_db     = _client[Config.FILES_DB_NAME]

files_col   = _db["files"]
config_col  = _db["bot_config"]   # per-group settings


# ─── Indexes ─────────────────────────────────────────────────────────────────
async def ensure_indexes():
    await files_col.create_index("file_name")
    await files_col.create_index("file_id", unique=True)
    await files_col.create_index("group_id")


# ─── File CRUD ───────────────────────────────────────────────────────────────
async def save_file(file: dict):
    """Upsert a file document."""
    await files_col.update_one(
        {"file_id": file["file_id"]},
        {"$set": file},
        upsert=True
    )


async def get_files(query: str, group_id: int = None, page: int = 0, per_page: int = 10):
    """Full-text search with optional spell-check fallback."""
    flt = {"$text": {"$search": query}}
    if group_id:
        flt["group_id"] = group_id
    cursor = files_col.find(flt, {"score": {"$meta": "textScore"}})
    cursor = cursor.sort([("score", {"$meta": "textScore"})]).skip(page * per_page).limit(per_page)
    return await cursor.to_list(length=per_page)


async def delete_all_files(group_id: int = None):
    flt = {"group_id": group_id} if group_id else {}
    result = await files_col.delete_many(flt)
    return result.deleted_count


async def delete_files_by_name(name: str, group_id: int = None):
    flt = {"file_name": {"$regex": name, "$options": "i"}}
    if group_id:
        flt["group_id"] = group_id
    result = await files_col.delete_many(flt)
    return result.deleted_count


async def total_files(group_id: int = None):
    flt = {"group_id": group_id} if group_id else {}
    return await files_col.count_documents(flt)


# ─── Group / Bot Config ───────────────────────────────────────────────────────
async def get_group_settings(group_id: int) -> dict:
    doc = await config_col.find_one({"group_id": group_id})
    return doc or {}


async def update_group_settings(group_id: int, settings: dict):
    await config_col.update_one(
        {"group_id": group_id},
        {"$set": settings},
        upsert=True
    )


async def set_caption(group_id: int, caption: str):
    await update_group_settings(group_id, {"caption": caption})


async def set_imdb_template(group_id: int, template: str):
    await update_group_settings(group_id, {"imdb_template": template})


async def set_shortlink(group_id: int, url: str, api: str):
    await update_group_settings(group_id, {"shortlink_url": url, "shortlink_api": api})


async def set_tutorial(group_id: int, video_id: str):
    await update_group_settings(group_id, {"tutorial_video": video_id})


async def set_log_channel(group_id: int, log_id: int):
    await update_group_settings(group_id, {"log_channel": log_id})


async def set_fsub(group_id: int, fsub_id: int):
    await update_group_settings(group_id, {"fsub_channel": fsub_id})


async def toggle_verification(group_id: int, state: bool):
    await update_group_settings(group_id, {"verification_on": state})


async def toggle_protect_content(group_id: int, state: bool):
    await update_group_settings(group_id, {"protect_content": state})
