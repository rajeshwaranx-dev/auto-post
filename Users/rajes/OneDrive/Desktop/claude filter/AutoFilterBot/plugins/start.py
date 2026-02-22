"""
Plugin: start.py
Only /help — /start is handled inside filters.py alongside the full verify→fsub flow.
"""
from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    await message.reply(
        "**📖 AutoFilter Bot — Help**\n\n"
        "**User Commands:**\n"
        "/start – Check bot status\n"
        "/myplan – View your plan\n"
        "/plan – See available plans\n\n"
        "**Admin Commands:**\n"
        "/shortlink – Set shortlink API\n"
        "/tutorial – Set tutorial video\n"
        "/caption – Set custom caption\n"
        "/template – Set IMDB template\n"
        "/fsub – Set force-subscribe channel\n"
        "/log – Set log channel\n"
        "/index – Index files\n"
        "/ginfo – Group/channel info\n"
        "/setverify on|off – Toggle verification\n"
        "/setprotect on|off – Toggle content protection\n"
        "/addpremium – Add premium user\n"
        "/removepremium – Remove premium user\n"
        "/premiumuser – List premium users\n"
        "/broadcast – Broadcast to users\n"
        "/gbroadcast – Broadcast to groups\n"
        "/deleteall – Delete all files\n"
        "/deletefiles – Delete files by name\n"
    )
