"""
Plugin: admin.py
All admin / group-admin commands: shortlink, tutorial, caption, template,
fsub, log, ginfo, index, deleteall, deletefiles.
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from database.files_db import (
    set_caption, set_imdb_template, set_shortlink, set_tutorial,
    set_log_channel, set_fsub, toggle_verification, toggle_protect_content,
    delete_all_files, delete_files_by_name, total_files, save_file, get_group_settings
)
from utils.decorators import admin_only, group_admin_only
from utils.helpers import extract_file_info

logger = logging.getLogger(__name__)


# ─── /shortlink ──────────────────────────────────────────────────────────────
@Client.on_message(filters.command("shortlink") & (filters.group | filters.private))
@group_admin_only
async def cmd_shortlink(client: Client, message: Message):
    """Usage: /shortlink <API_URL> <API_KEY>"""
    args = message.text.split(None, 2)
    if len(args) < 3:
        settings = await get_group_settings(message.chat.id)
        current  = settings.get("shortlink_url", "Not set")
        await message.reply(
            f"**Current shortlink:** `{current}`\n\n"
            "**Usage:** `/shortlink <api_url> <api_key>`\n"
            "Example: `/shortlink shrinkme.io XXXX`"
        )
        return
    api_url, api_key = args[1], args[2]
    await set_shortlink(message.chat.id, api_url, api_key)
    await message.reply(f"✅ Shortlink set to `{api_url}`")


# ─── /tutorial ───────────────────────────────────────────────────────────────
@Client.on_message(filters.command("tutorial") & (filters.group | filters.private))
@group_admin_only
async def cmd_tutorial(client: Client, message: Message):
    """Reply to a video or pass a file_id to set the tutorial."""
    if message.reply_to_message and message.reply_to_message.video:
        vid_id = message.reply_to_message.video.file_id
        await set_tutorial(message.chat.id, vid_id)
        await message.reply("✅ Tutorial video updated!")
    else:
        await message.reply("❗ Please reply to a video with /tutorial")


# ─── /caption ────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("caption") & (filters.group | filters.private))
@group_admin_only
async def cmd_caption(client: Client, message: Message):
    """Usage: /caption <caption text>"""
    args = message.text.split(None, 1)
    if len(args) < 2:
        settings = await get_group_settings(message.chat.id)
        current  = settings.get("caption", Config.DEFAULT_CAPTION)
        await message.reply(
            f"**Current caption:**\n`{current}`\n\n"
            "**Usage:** `/caption <your caption text>`\n"
            "**Variables:** `{file_name}` `{file_size}` `{file_type}`"
        )
        return
    await set_caption(message.chat.id, args[1])
    await message.reply("✅ Caption updated!")


# ─── /template ───────────────────────────────────────────────────────────────
@Client.on_message(filters.command("template") & (filters.group | filters.private))
@group_admin_only
async def cmd_template(client: Client, message: Message):
    """Usage: /template <IMDB template>"""
    args = message.text.split(None, 1)
    if len(args) < 2:
        settings = await get_group_settings(message.chat.id)
        current  = settings.get("imdb_template", Config.IMDB_TEMPLATE)
        await message.reply(
            f"**Current IMDB template:**\n`{current}`\n\n"
            "**Variables:** `{title}` `{year}` `{rating}` `{genres}` `{plot}`"
        )
        return
    await set_imdb_template(message.chat.id, args[1])
    await message.reply("✅ IMDB template updated!")


# ─── /fsub ───────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("fsub") & (filters.group | filters.private))
@group_admin_only
async def cmd_fsub(client: Client, message: Message):
    """Usage: /fsub <channel_id>  or  /fsub off"""
    args = message.text.split(None, 1)
    if len(args) < 2:
        settings = await get_group_settings(message.chat.id)
        current  = settings.get("fsub_channel", "Not set")
        await message.reply(
            f"**FSub channel:** `{current}`\n\n"
            "**Usage:** `/fsub <channel_id>` or `/fsub off`"
        )
        return
    if args[1].lower() == "off":
        await set_fsub(message.chat.id, 0)
        await message.reply("✅ Force Subscribe disabled.")
    else:
        try:
            fsub_id = int(args[1])
            await set_fsub(message.chat.id, fsub_id)
            await message.reply(f"✅ FSub channel set to `{fsub_id}`")
        except ValueError:
            await message.reply("❗ Invalid channel ID.")


# ─── /log ────────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("log") & (filters.group | filters.private))
@group_admin_only
async def cmd_log(client: Client, message: Message):
    """Usage: /log <channel_id>"""
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("**Usage:** `/log <channel_id>`")
        return
    try:
        log_id = int(args[1])
        await set_log_channel(message.chat.id, log_id)
        await message.reply(f"✅ Log channel set to `{log_id}`")
    except ValueError:
        await message.reply("❗ Invalid channel ID.")


# ─── /ginfo ──────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("ginfo"))
@admin_only
async def cmd_ginfo(client: Client, message: Message):
    args  = message.text.split(None, 1)
    chat_id = args[1] if len(args) > 1 else message.chat.id
    try:
        chat = await client.get_chat(chat_id)
        await message.reply(
            f"**📋 Chat Info**\n\n"
            f"🆔 **ID:** `{chat.id}`\n"
            f"📛 **Title:** {chat.title}\n"
            f"🔗 **Username:** @{chat.username or 'Private'}\n"
            f"👥 **Members:** {chat.members_count or 'N/A'}\n"
            f"📂 **Type:** {chat.type}"
        )
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ─── /index ──────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("index"))
@group_admin_only
async def cmd_index(client: Client, message: Message):
    """Index files from the current chat (forward files to the bot to index them)."""
    await message.reply(
        "📥 **Indexing mode**\n\n"
        "Forward files to this chat. Each file will be indexed automatically.\n"
        "Send /stopindex to stop.\n\n"
        f"**Currently indexed:** {await total_files(message.chat.id)} files"
    )


# ─── Auto-index on file messages ─────────────────────────────────────────────
@Client.on_message(
    filters.group
    & (filters.document | filters.video | filters.audio | filters.animation)
)
async def auto_index(client: Client, message: Message):
    file_info = extract_file_info(message)
    if not file_info:
        return
    await save_file(file_info)
    settings = await get_group_settings(message.chat.id)
    log_ch   = settings.get("log_channel") or Config.LOG_CHANNEL
    if log_ch:
        try:
            await client.send_message(
                log_ch,
                f"📄 **Indexed:** `{file_info['file_name']}`\n"
                f"📁 **Type:** {file_info['file_type']}\n"
                f"💾 **Size:** {file_info['file_size']}\n"
                f"🏠 **Group:** `{message.chat.id}`"
            )
        except Exception:
            pass


# ─── /deleteall ──────────────────────────────────────────────────────────────
@Client.on_message(filters.command("deleteall") & (filters.group | filters.private))
@group_admin_only
async def cmd_deleteall(client: Client, message: Message):
    confirm = message.text.split(None, 1)
    if len(confirm) < 2 or confirm[1].lower() != "confirm":
        await message.reply(
            "⚠️ This will delete **ALL** indexed files from this group!\n"
            "Type `/deleteall confirm` to proceed."
        )
        return
    count = await delete_all_files(message.chat.id)
    await message.reply(f"🗑 Deleted **{count}** files from the database.")


# ─── /deletefiles ─────────────────────────────────────────────────────────────
@Client.on_message(filters.command("deletefiles") & (filters.group | filters.private))
@group_admin_only
async def cmd_deletefiles(client: Client, message: Message):
    """Usage: /deletefiles <name>"""
    args = message.text.split(None, 1)
    if len(args) < 2:
        await message.reply("**Usage:** `/deletefiles <file name or pattern>`")
        return
    count = await delete_files_by_name(args[1], message.chat.id)
    await message.reply(f"🗑 Deleted **{count}** matching file(s).")


# ─── Toggle verification ──────────────────────────────────────────────────────
@Client.on_message(filters.command("setverify") & (filters.group | filters.private))
@group_admin_only
async def cmd_set_verify(client: Client, message: Message):
    """Usage: /setverify on|off"""
    args = message.text.split(None, 1)
    if len(args) < 2 or args[1].lower() not in ("on", "off"):
        await message.reply("**Usage:** `/setverify on` or `/setverify off`")
        return
    state = args[1].lower() == "on"
    await toggle_verification(message.chat.id, state)
    await message.reply(f"✅ Verification {'enabled' if state else 'disabled'}.")


# ─── Toggle protect content ───────────────────────────────────────────────────
@Client.on_message(filters.command("setprotect") & (filters.group | filters.private))
@group_admin_only
async def cmd_set_protect(client: Client, message: Message):
    """Usage: /setprotect on|off"""
    args = message.text.split(None, 1)
    if len(args) < 2 or args[1].lower() not in ("on", "off"):
        await message.reply("**Usage:** `/setprotect on` or `/setprotect off`")
        return
    state = args[1].lower() == "on"
    await toggle_protect_content(message.chat.id, state)
    await message.reply(f"✅ Content protection {'enabled' if state else 'disabled'}.")
