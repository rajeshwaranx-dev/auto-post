"""
Plugin: fsub.py
Handles new members arriving via a join-request enabled FSub channel.
Also tracks bot being added/removed from groups.
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message, ChatJoinRequest, ChatMemberUpdated
)

from database.users_db import add_user, add_group, deactivate_group
from config import Config

logger = logging.getLogger(__name__)


# ─── Auto-approve join requests (Request-to-Join mode) ───────────────────────
@Client.on_chat_join_request()
async def approve_join_request(client: Client, request: ChatJoinRequest):
    """Auto-approve join requests for the FSub channel."""
    try:
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
    except Exception as e:
        logger.warning(f"Could not approve join request: {e}")


# ─── Track when bot is added to or removed from a group ──────────────────────
@Client.on_message(filters.group & filters.new_chat_members)
async def bot_added_to_group(client: Client, message: Message):
    me = await client.get_me()
    for member in message.new_chat_members:
        if member.id == me.id:
            await add_group(message.chat.id, message.chat.title)
            if Config.LOG_CHANNEL:
                try:
                    await client.send_message(
                        Config.LOG_CHANNEL,
                        f"➕ **Bot added to group**\n"
                        f"📛 {message.chat.title}\n"
                        f"🆔 `{message.chat.id}`"
                    )
                except Exception:
                    pass
        else:
            await add_user(member.id, member.first_name, member.username or "")


@Client.on_message(filters.group & filters.left_chat_member)
async def bot_left_group(client: Client, message: Message):
    me = await client.get_me()
    if message.left_chat_member.id == me.id:
        await deactivate_group(message.chat.id)
        if Config.LOG_CHANNEL:
            try:
                await client.send_message(
                    Config.LOG_CHANNEL,
                    f"➖ **Bot removed from group**\n"
                    f"📛 {message.chat.title}\n"
                    f"🆔 `{message.chat.id}`"
                )
            except Exception:
                pass
