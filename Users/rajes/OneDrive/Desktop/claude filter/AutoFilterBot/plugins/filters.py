"""
Plugin: filters.py
─────────────────────────────────────────────────────────────────────────────
Complete flow:

  Group search
      │
      ▼
  Verified?  ──No──▶  Save pending query  ──▶  Send Shortlink button
      │                                           │
      │                                    User clicks shortlink page
      │                                           │
      │                              Bot DM: /start?start=verify_{uid}_{gid}
      │                                           │
      │                                  Mark user verified
      │                                           ▼
      │                                  FSub joined?
      │                                  Yes       No
      │                                   │         │
      ▼                                   ▼         ▼
  FSub joined?                    Deliver files   "Join Channel"
  Yes       No                    from pending    + "✅ I've Joined"
   │         │                    query                 button
   │         │                                          │
   ▼         ▼                                   User clicks
  Deliver   Show FSub wall                             │
  files     + "Try Again"                        Check FSub again
            button                               Yes       No
                                                  │         │
                                            Deliver      Repeat
                                            pending
─────────────────────────────────────────────────────────────────────────────
"""
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from pyrogram.errors import FloodWait, UserNotParticipant

from config import Config
from database.files_db import get_files, get_group_settings
from database.users_db import (
    add_user, is_verified, verify_user,
    save_pending_request, get_pending_request, clear_pending_request
)
from utils.helpers import spell_check_query
from utils.shortlink import generate_verify_link

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

async def check_fsub(client: Client, user_id: int, fsub_id: int) -> bool:
    """Return True if user is subscribed — or if FSub is disabled."""
    if not fsub_id:
        return True
    try:
        member = await client.get_chat_member(fsub_id, user_id)
        return member.status not in ("left", "kicked", "banned")
    except UserNotParticipant:
        return False
    except Exception:
        return True   # don't block on API errors


async def get_fsub_invite(client: Client, fsub_id: int) -> str:
    """Return the best invite link for the FSub channel."""
    try:
        chat = await client.get_chat(fsub_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        if chat.invite_link:
            return chat.invite_link
        return await client.export_chat_invite_link(fsub_id)
    except Exception:
        return ""


async def search_files(query: str, group_id: int) -> list:
    """Search files with automatic spell-check fallback."""
    files = await get_files(query, group_id, per_page=Config.MAX_RESULTS)
    if not files and Config.SPELL_CHECK:
        for variant in spell_check_query(query):
            if variant == query:
                continue
            files = await get_files(variant, group_id, per_page=Config.MAX_RESULTS)
            if files:
                break
    return files


async def deliver_files(client: Client, chat_id: int, files: list, settings: dict) -> list:
    """
    Send file results to chat_id.
    Returns list of sent Message objects (for auto-delete tracking).
    """
    protect     = settings.get("protect_content", Config.PROTECT_CONTENT)
    caption_tpl = settings.get("caption", Config.DEFAULT_CAPTION)
    link_mode   = settings.get("link_mode", Config.LINK_MODE)
    sent_msgs   = []

    if link_mode:
        me      = await client.get_me()
        buttons = []
        for f in files:
            label = f["file_name"][:50]
            url   = f"https://t.me/{me.username}?start=file_{f['file_id']}"
            buttons.append([InlineKeyboardButton(f"📁 {label}", url=url)])
        await client.send_message(
            chat_id,
            f"🔎 Found **{len(files)}** file(s):",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return sent_msgs

    for f in files:
        try:
            caption = caption_tpl.format(
                file_name=f.get("file_name", ""),
                file_size=f.get("file_size", ""),
                file_type=f.get("file_type", ""),
            )
            sent = await client.send_cached_media(
                chat_id=chat_id,
                file_id=f["file_id"],
                caption=caption,
                protect_content=protect,
            )
            sent_msgs.append(sent)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as ex:
            logger.warning(f"Error sending {f.get('file_id')}: {ex}")

    return sent_msgs


async def auto_delete(client: Client, messages: list, settings: dict, notify_chat: int):
    """Schedule auto-deletion of sent file messages."""
    delay = settings.get("auto_delete", Config.AUTO_DELETE)
    if not delay or not messages:
        return
    note = await client.send_message(
        notify_chat,
        f"⏳ These files will be auto-deleted in **{delay // 60} min**."
    )
    await asyncio.sleep(delay)
    for m in messages:
        try:
            await m.delete()
        except Exception:
            pass
    try:
        await note.delete()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# FSub wall  (reused from multiple entry points)
# ══════════════════════════════════════════════════════════════════════════════

def build_fsub_wall_markup(invite: str, user_id: int, group_id: int, query: str):
    """Build the InlineKeyboardMarkup for the FSub subscription wall."""
    payload = f"{user_id}|{group_id}|{query}"
    buttons = []
    if invite:
        buttons.append([InlineKeyboardButton("📢 Join Channel", url=invite)])
    buttons.append([
        InlineKeyboardButton(
            "✅ I've Joined — Try Again",
            callback_data=f"fsub_check|{payload}",
        )
    ])
    return InlineKeyboardMarkup(buttons)


async def show_fsub_wall(
    client: Client,
    *,
    chat_id: int,
    user_id: int,
    fsub_id: int,
    group_id: int,
    query: str,
    reply_to: Message = None,
):
    """Send the FSub join wall with a persistent Try-Again button."""
    invite  = await get_fsub_invite(client, fsub_id)
    markup  = build_fsub_wall_markup(invite, user_id, group_id, query)
    text    = (
        "🔒 **Channel subscription required!**\n\n"
        "You must join our channel to receive files.\n\n"
        "1️⃣ Tap **📢 Join Channel**\n"
        "2️⃣ Join the channel\n"
        "3️⃣ Come back and tap **✅ I've Joined — Try Again**\n\n"
        "The bot will check your membership and deliver your files instantly."
    )
    if reply_to:
        await reply_to.reply(text, reply_markup=markup)
    else:
        await client.send_message(chat_id, text, reply_markup=markup)


# ══════════════════════════════════════════════════════════════════════════════
# Pending-query delivery helper
# ══════════════════════════════════════════════════════════════════════════════

async def deliver_pending_or_redirect(
    client: Client,
    origin: Message,
    user_id: int,
    group_id: int,
    query: str,
):
    """
    Search for the pending query and deliver files to the user in PM.
    Falls back to a redirect message if nothing is found.
    """
    await clear_pending_request(user_id)

    if not query or not group_id:
        await origin.reply(
            "✅ **All done!**\n\n"
            "Go back to the group and search for your file."
        )
        return

    settings = await get_group_settings(group_id)
    files    = await search_files(query, group_id)

    if not files:
        try:
            chat = await client.get_chat(group_id)
            link = f"https://t.me/{chat.username}" if chat.username else None
        except Exception:
            link = None
        buttons = [[InlineKeyboardButton("🔙 Back to Group", url=link)]] if link else []
        await origin.reply(
            f"✅ **Verified!**\n\n"
            f"❌ No results found for **{query}**.\n"
            "Go back to the group and try a different keyword.",
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
        )
        return

    await origin.reply(
        f"✅ **Access granted!**\n\n"
        f"Here are the results for **{query}**:"
    )
    sent = await deliver_files(client, user_id, files, settings)
    asyncio.create_task(auto_delete(client, sent, settings, user_id))


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT 1 — Group text message  →  AutoFilter
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.group & filters.text & ~filters.command(""))
async def auto_filter(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    query = message.text.strip()
    if len(query) < 2:
        return

    await add_user(user.id, user.first_name, user.username or "")
    settings = await get_group_settings(message.chat.id)

    # ── GATE 1: Shortlink Verification ───────────────────────────────────────
    verify_on = settings.get("verification_on", Config.VERIFICATION_ON)
    if verify_on and not await is_verified(user.id):

        # Persist what the user wanted so we can deliver it after verification
        await save_pending_request(user.id, message.chat.id, query)

        sl_url = settings.get("shortlink_url") or Config.SHORTLINK_URL
        sl_api = settings.get("shortlink_api") or Config.SHORTLINK_API
        tut    = settings.get("tutorial_video") or Config.TUTORIAL_VIDEO
        me     = await client.get_me()

        # Deep-link encodes both uid and group_id so /start can recover them
        deep_payload = f"verify_{user.id}_{message.chat.id}"
        if sl_url and sl_api:
            raw_link = f"https://t.me/{me.username}?start={deep_payload}"
            link     = await generate_verify_link(raw_link, sl_url, sl_api)
        else:
            link = f"https://t.me/{me.username}?start={deep_payload}"

        buttons = [[InlineKeyboardButton("🔗 Click Here to Verify", url=link)]]
        if tut:
            buttons.append([InlineKeyboardButton("📹 How to Verify?", url=tut)])

        await message.reply(
            "🔐 **Verification Required**\n\n"
            "To access files you must verify once every 24 hours.\n\n"
            "**Steps:**\n"
            "1️⃣ Tap **Click Here to Verify**\n"
            "2️⃣ Complete the shortlink page\n"
            "3️⃣ The bot will send your files automatically ✅",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # ── GATE 2: Force Subscribe ───────────────────────────────────────────────
    fsub_id = settings.get("fsub_channel") or Config.FSUB_CHANNEL
    if not await check_fsub(client, user.id, fsub_id):
        await save_pending_request(user.id, message.chat.id, query)
        await show_fsub_wall(
            client,
            chat_id=message.chat.id,
            user_id=user.id,
            fsub_id=fsub_id,
            group_id=message.chat.id,
            query=query,
            reply_to=message,
        )
        return

    # ── DELIVER ───────────────────────────────────────────────────────────────
    files = await search_files(query, message.chat.id)
    if not files:
        await message.reply(
            f"❌ No results for **{query}**.\n"
            "Try a shorter or different keyword."
        )
        return

    sent = await deliver_files(client, message.chat.id, files, settings)
    asyncio.create_task(auto_delete(client, sent, settings, message.chat.id))


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT 2 — /start in PM  →  Verification deep-link handler
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("start") & filters.private)
async def start_pm(client: Client, message: Message):
    user = message.from_user
    await add_user(user.id, user.first_name, user.username or "")

    args = message.command[1] if len(message.command) > 1 else ""

    # ── Verification deep-link  →  verify_{uid}_{gid} ─────────────────────────
    if args.startswith("verify_"):
        parts = args.split("_")          # ["verify", uid, gid]
        try:
            target_uid = int(parts[1])
            group_id   = int(parts[2]) if len(parts) > 2 else 0
        except (IndexError, ValueError):
            await message.reply("❌ Invalid or expired verification link.")
            return

        if user.id != target_uid:
            await message.reply("❌ This link isn't yours.")
            return

        if await is_verified(user.id):
            await message.reply(
                "✅ **Already verified!**\n\n"
                "Go back to the group — your file search is waiting."
            )
            return

        # ✅ Mark verified
        await verify_user(user.id)

        # Recover pending request (may differ from group_id in the link)
        pending  = await get_pending_request(user.id)
        grp_id   = pending.get("group_id") or group_id
        query    = pending.get("query", "")

        # Resolve FSub channel for this group
        fsub_id = Config.FSUB_CHANNEL
        if grp_id:
            grp_settings = await get_group_settings(grp_id)
            fsub_id      = grp_settings.get("fsub_channel") or Config.FSUB_CHANNEL

        # ── Still need to pass FSub? ─────────────────────────────────────────
        if fsub_id and not await check_fsub(client, user.id, fsub_id):
            await message.reply(
                "✅ **Shortlink verified!**\n\n"
                "One last step — join our channel to receive your files."
            )
            await show_fsub_wall(
                client,
                chat_id=user.id,
                user_id=user.id,
                fsub_id=fsub_id,
                group_id=grp_id,
                query=query,
            )
            return

        # ── Both gates cleared → deliver ──────────────────────────────────────
        await message.reply("✅ **Verification complete!** Fetching your files…")
        await deliver_pending_or_redirect(client, message, user.id, grp_id, query)
        return

    # ── Default /start (no args or unknown) ───────────────────────────────────
    me = await client.get_me()
    await message.reply(
        f"👋 Hello **{user.first_name}**!\n\n"
        "I'm an **AutoFilter Bot** — add me to your group to find files instantly.\n\n"
        "/help — list of commands",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add to Group",
                                  url=f"https://t.me/{me.username}?startgroup=true")],
            [InlineKeyboardButton("📢 Updates", url="https://t.me/YourChannel"),
             InlineKeyboardButton("🆘 Support", url="https://t.me/YourSupport")],
        ]),
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT 3 — "✅ I've Joined — Try Again" callback  (loops until joined)
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^fsub_check\|"))
async def fsub_try_again(client: Client, cb: CallbackQuery):
    """
    Callback data format:
        fsub_check|{user_id}|{group_id}|{query}

    The query may contain | characters so we split on the first three | only.
    """
    # Parse payload
    raw = cb.data[len("fsub_check|"):]           # strip prefix
    parts = raw.split("|", 2)                     # [uid, gid, query]
    if len(parts) < 3:
        await cb.answer("❌ Corrupt callback data.", show_alert=True)
        return

    try:
        user_id  = int(parts[0])
        group_id = int(parts[1])
        query    = parts[2]
    except ValueError:
        await cb.answer("❌ Invalid callback data.", show_alert=True)
        return

    # Security: only the intended user may tap this button
    if cb.from_user.id != user_id:
        await cb.answer("⚠️ This button is not for you.", show_alert=True)
        return

    await cb.answer("🔄 Checking membership…")

    # Resolve FSub channel
    fsub_id = Config.FSUB_CHANNEL
    if group_id:
        grp_settings = await get_group_settings(group_id)
        fsub_id      = grp_settings.get("fsub_channel") or Config.FSUB_CHANNEL

    # ── NOT joined yet — update the message and wait ──────────────────────────
    if not await check_fsub(client, user_id, fsub_id):
        invite  = await get_fsub_invite(client, fsub_id)
        markup  = build_fsub_wall_markup(invite, user_id, group_id, query)
        try:
            await cb.message.edit_text(
                "❌ **You haven't joined yet!**\n\n"
                "Please join the channel first, then tap **Try Again**.\n\n"
                "🔒 **Channel subscription required!**\n\n"
                "1️⃣ Tap **📢 Join Channel**\n"
                "2️⃣ Join the channel\n"
                "3️⃣ Come back and tap **✅ I've Joined — Try Again**",
                reply_markup=markup,
            )
        except Exception:
            pass
        return

    # ── Joined! ───────────────────────────────────────────────────────────────
    try:
        await cb.message.edit_text("✅ **Subscription verified!** Fetching your files…")
    except Exception:
        pass

    # Prefer fresh pending_request from DB (most up-to-date)
    pending = await get_pending_request(user_id)
    grp_id  = pending.get("group_id") or group_id
    q       = pending.get("query") or query

    await deliver_pending_or_redirect(client, cb.message, user_id, grp_id, q)
