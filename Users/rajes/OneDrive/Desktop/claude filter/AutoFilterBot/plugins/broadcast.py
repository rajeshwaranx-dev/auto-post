"""
Plugin: broadcast.py
Commands: /broadcast (to users), /gbroadcast (to groups)
"""
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from database.users_db import all_users, all_groups
from utils.decorators import admin_only

logger = logging.getLogger(__name__)


async def _broadcast(client: Client, ids: list, get_id, message: Message, label: str):
    """Generic broadcast helper."""
    total   = len(ids)
    success = 0
    failed  = 0

    status_msg = await message.reply(
        f"📢 **Broadcasting to {total} {label}s…**\n"
        "This may take a while."
    )

    for doc in ids:
        target_id = get_id(doc)
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(target_id)
            else:
                await client.send_message(target_id, message.text.split(None, 1)[1])
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                if message.reply_to_message:
                    await message.reply_to_message.copy(target_id)
                else:
                    await client.send_message(target_id, message.text.split(None, 1)[1])
                success += 1
            except Exception:
                failed += 1
        except (UserIsBlocked, InputUserDeactivated):
            failed += 1
        except Exception as e:
            logger.warning(f"Broadcast error to {target_id}: {e}")
            failed += 1
        await asyncio.sleep(0.05)   # rate-limit safety

    await status_msg.edit(
        f"✅ **Broadcast complete!**\n\n"
        f"📤 Sent:   {success}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total:  {total}"
    )


# ─── /broadcast ───────────────────────────────────────────────────────────────
@Client.on_message(filters.command("broadcast") & filters.private)
@admin_only
async def cmd_broadcast(client: Client, message: Message):
    """Reply to a message or add text after /broadcast"""
    if not message.reply_to_message and len(message.text.split(None, 1)) < 2:
        await message.reply(
            "**Usage:**\n"
            "• `/broadcast <message text>`\n"
            "• Reply to any message with `/broadcast`"
        )
        return
    users = await all_users()
    await _broadcast(client, users, lambda d: d["user_id"], message, "user")


# ─── /gbroadcast ──────────────────────────────────────────────────────────────
@Client.on_message(filters.command("gbroadcast") & filters.private)
@admin_only
async def cmd_gbroadcast(client: Client, message: Message):
    """Broadcast to all registered groups."""
    if not message.reply_to_message and len(message.text.split(None, 1)) < 2:
        await message.reply(
            "**Usage:**\n"
            "• `/gbroadcast <message text>`\n"
            "• Reply to any message with `/gbroadcast`"
        )
        return
    groups = await all_groups()
    await _broadcast(client, groups, lambda d: d["group_id"], message, "group")
