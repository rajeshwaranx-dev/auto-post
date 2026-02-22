"""Decorators for access control."""
from functools import wraps
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from config import Config
from database.users_db import get_user


def admin_only(func):
    """Restrict handler to bot admins."""
    @wraps(func)
    async def wrapper(client: Client, update, *args, **kwargs):
        user_id = update.from_user.id if update.from_user else 0
        if user_id not in Config.ADMINS:
            if isinstance(update, CallbackQuery):
                await update.answer("⛔ Admins only.", show_alert=True)
            else:
                await update.reply("⛔ This command is for admins only.")
            return
        return await func(client, update, *args, **kwargs)
    return wrapper


def premium_or_admin(func):
    """Allow premium users and admins."""
    @wraps(func)
    async def wrapper(client: Client, update, *args, **kwargs):
        user_id = update.from_user.id if update.from_user else 0
        if user_id in Config.ADMINS:
            return await func(client, update, *args, **kwargs)
        user = await get_user(user_id)
        if not user.get("premium"):
            if isinstance(update, CallbackQuery):
                await update.answer("⭐ This feature is for premium users.", show_alert=True)
            else:
                await update.reply("⭐ Upgrade to premium to use this feature.")
            return
        return await func(client, update, *args, **kwargs)
    return wrapper


def group_admin_only(func):
    """Restrict to group administrators (within a group chat)."""
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        user_id = message.from_user.id
        if user_id in Config.ADMINS:
            return await func(client, message, *args, **kwargs)
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status not in ("administrator", "creator"):
            await message.reply("⛔ Group admins only.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
