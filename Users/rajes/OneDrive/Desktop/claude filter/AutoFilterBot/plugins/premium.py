"""
Plugin: premium.py
Commands: /addpremium, /removepremium, /premiumuser, /myplan, /plan
"""
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

from database.users_db import (
    add_premium, remove_premium, get_premium_users, get_plan, get_user
)
from utils.decorators import admin_only

logger = logging.getLogger(__name__)

PLANS = {
    "basic":   {"days": 7,   "label": "Basic",    "price": "$2"},
    "premium": {"days": 30,  "label": "Premium",  "price": "$5"},
    "vip":     {"days": 90,  "label": "VIP",      "price": "$10"},
    "lifetime":{"days": 3650,"label": "Lifetime", "price": "$25"},
}


# ─── /plan ────────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("plan"))
async def cmd_plan(client: Client, message: Message):
    text = "⭐ **Available Plans**\n\n"
    for key, info in PLANS.items():
        text += (
            f"**{info['label']}** — {info['price']}\n"
            f"  ⏳ Duration: {info['days']} days\n\n"
        )
    text += "Contact @YourAdmin to purchase a plan."
    await message.reply(text)


# ─── /myplan ──────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("myplan"))
async def cmd_myplan(client: Client, message: Message):
    user_id   = message.from_user.id
    plan_info = await get_plan(user_id)
    plan      = plan_info.get("plan", "free").capitalize()
    expiry    = plan_info.get("expiry")
    premium   = plan_info.get("premium", False)

    if premium and expiry:
        remaining = (expiry - datetime.utcnow()).days
        exp_str   = expiry.strftime("%d %b %Y")
        status    = f"⭐ **Active Premium**\n📅 Expires: {exp_str} ({remaining} days left)"
    else:
        status = "🆓 **Free Plan** — Verification required every 24h."

    user = await get_user(user_id)
    await message.reply(
        f"👤 **Your Plan**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"📛 Name: {message.from_user.first_name}\n"
        f"📦 Plan: **{plan}**\n"
        f"{status}\n\n"
        "Use /plan to see upgrade options."
    )


# ─── /addpremium ──────────────────────────────────────────────────────────────
@Client.on_message(filters.command("addpremium"))
@admin_only
async def cmd_add_premium(client: Client, message: Message):
    """Usage: /addpremium <user_id> [plan] [days]"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "**Usage:** `/addpremium <user_id> [plan] [days]`\n"
            "Example: `/addpremium 123456789 premium 30`\n\n"
            "Available plans: " + ", ".join(PLANS.keys())
        )
        return
    try:
        target_id = int(args[1])
        plan_name = args[2] if len(args) > 2 else "premium"
        days      = int(args[3]) if len(args) > 3 else PLANS.get(plan_name, {}).get("days", 30)
    except (ValueError, IndexError):
        await message.reply("❗ Invalid arguments.")
        return

    if plan_name not in PLANS:
        await message.reply(f"❗ Unknown plan. Choose from: {', '.join(PLANS.keys())}")
        return

    await add_premium(target_id, plan_name, days)
    try:
        await client.send_message(
            target_id,
            f"🎉 **Congratulations!**\n\n"
            f"You've been upgraded to **{plan_name.capitalize()}** plan for **{days} days**!"
        )
    except Exception:
        pass
    await message.reply(
        f"✅ User `{target_id}` added to **{plan_name.capitalize()}** for {days} days."
    )


# ─── /removepremium ───────────────────────────────────────────────────────────
@Client.on_message(filters.command("removepremium"))
@admin_only
async def cmd_remove_premium(client: Client, message: Message):
    """Usage: /removepremium <user_id>"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("**Usage:** `/removepremium <user_id>`")
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❗ Invalid user ID.")
        return

    await remove_premium(target_id)
    try:
        await client.send_message(target_id, "ℹ️ Your premium plan has been removed.")
    except Exception:
        pass
    await message.reply(f"✅ Premium removed from `{target_id}`.")


# ─── /premiumuser ─────────────────────────────────────────────────────────────
@Client.on_message(filters.command("premiumuser"))
@admin_only
async def cmd_premium_users(client: Client, message: Message):
    users = await get_premium_users()
    if not users:
        await message.reply("📭 No premium users found.")
        return
    lines = ["⭐ **Premium Users**\n"]
    for u in users:
        expiry = u.get("plan_expiry")
        exp_str = expiry.strftime("%d %b %Y") if expiry else "Lifetime"
        lines.append(
            f"• `{u['user_id']}` — **{u.get('plan','premium').capitalize()}** (exp: {exp_str})"
        )
    await message.reply("\n".join(lines))
