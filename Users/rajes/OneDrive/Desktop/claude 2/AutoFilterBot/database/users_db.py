"""
Users Database  –  stores user/group registration, verification, premium, and stats.
"""
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

_client = AsyncIOMotorClient(Config.USERS_DB_URI)
_db     = _client[Config.USERS_DB_NAME]

users_col  = _db["users"]
groups_col = _db["groups"]


# ─── Indexes ─────────────────────────────────────────────────────────────────
async def ensure_indexes():
    await users_col.create_index("user_id", unique=True)
    await groups_col.create_index("group_id", unique=True)


# ─── User CRUD ────────────────────────────────────────────────────────────────
async def add_user(user_id: int, name: str = "", username: str = ""):
    await users_col.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {
            "user_id":      user_id,
            "name":         name,
            "username":     username,
            "lang":         Config.DEFAULT_LANG,
            "premium":      False,
            "plan":         "free",
            "plan_expiry":  None,
            "verified":     False,
            "verify_time":  None,
            "last_active":  datetime.utcnow(),
            "total_searches": 0,
            "joined":       datetime.utcnow(),
        }},
        upsert=True
    )


async def get_user(user_id: int) -> dict:
    return await users_col.find_one({"user_id": user_id}) or {}


async def update_user(user_id: int, data: dict):
    await users_col.update_one({"user_id": user_id}, {"$set": data}, upsert=True)


async def all_users():
    return await users_col.find({}, {"user_id": 1}).to_list(length=None)


async def total_users():
    return await users_col.count_documents({})


# ─── Verification ─────────────────────────────────────────────────────────────
async def is_verified(user_id: int) -> bool:
    user = await get_user(user_id)
    if user.get("premium"):
        return True
    if user.get("admin"):
        return True
    if not user.get("verified"):
        return False
    expiry = user.get("verify_time")
    if expiry and datetime.utcnow() < expiry:
        return True
    await update_user(user_id, {"verified": False, "verify_time": None})
    return False


async def verify_user(user_id: int, hours: int = None):
    hours = hours or (Config.VERIFY_EXPIRE // 3600)
    expiry = datetime.utcnow() + timedelta(hours=hours)
    await update_user(user_id, {"verified": True, "verify_time": expiry})


# ─── Premium ──────────────────────────────────────────────────────────────────
async def add_premium(user_id: int, plan: str = "premium", days: int = 30):
    expiry = datetime.utcnow() + timedelta(days=days)
    await update_user(user_id, {"premium": True, "plan": plan, "plan_expiry": expiry})


async def remove_premium(user_id: int):
    await update_user(user_id, {"premium": False, "plan": "free", "plan_expiry": None})


async def get_premium_users():
    return await users_col.find({"premium": True}).to_list(length=None)


async def get_plan(user_id: int) -> dict:
    user = await get_user(user_id)
    plan    = user.get("plan", "free")
    expiry  = user.get("plan_expiry")
    premium = user.get("premium", False)
    if premium and expiry and datetime.utcnow() > expiry:
        await remove_premium(user_id)
        return {"plan": "free", "expiry": None, "premium": False}
    return {"plan": plan, "expiry": expiry, "premium": premium}


# ─── Pending File Request ─────────────────────────────────────────────────────
async def save_pending_request(user_id: int, group_id: int, query: str):
    """Store the search query a user was trying when they hit the verify/fsub wall."""
    await update_user(user_id, {
        "pending_group_id": group_id,
        "pending_query":    query,
    })


async def get_pending_request(user_id: int) -> dict:
    """Retrieve the stored pending request for a user."""
    user = await get_user(user_id)
    return {
        "group_id": user.get("pending_group_id"),
        "query":    user.get("pending_query"),
    }


async def clear_pending_request(user_id: int):
    """Remove the pending request after it's been handled."""
    await users_col.update_one(
        {"user_id": user_id},
        {"$unset": {"pending_group_id": "", "pending_query": ""}}
    )


# ─── Language ─────────────────────────────────────────────────────────────────
async def set_lang(user_id: int, lang: str):
    await update_user(user_id, {"lang": lang})


async def get_lang(user_id: int) -> str:
    user = await get_user(user_id)
    return user.get("lang", Config.DEFAULT_LANG)


# ─── Group CRUD ───────────────────────────────────────────────────────────────
async def add_group(group_id: int, title: str = ""):
    await groups_col.update_one(
        {"group_id": group_id},
        {"$setOnInsert": {
            "group_id": group_id,
            "title":    title,
            "joined":   datetime.utcnow(),
            "active":   True,
        }},
        upsert=True
    )


async def all_groups():
    return await groups_col.find({"active": True}, {"group_id": 1}).to_list(length=None)


async def total_groups():
    return await groups_col.count_documents({"active": True})


async def deactivate_group(group_id: int):
    await groups_col.update_one({"group_id": group_id}, {"$set": {"active": False}})
