"""
AutoFilter Bot — Entry Point
"""
import asyncio
import logging

from pyrogram import Client
from pyrogram.types import BotCommand

from config import Config
from database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class AutoFilterBot(Client):
    def __init__(self):
        super().__init__(
            name="AutoFilterBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins={"root": "plugins"},
        )

    async def start(self):
        await init_db()
        await super().start()

        me = await self.get_me()
        logger.info(f"✅ Bot started: @{me.username} ({me.id})")

        # Set bot commands visible in Telegram UI
        await self.set_bot_commands([
            BotCommand("start",         "Check bot status"),
            BotCommand("help",          "Show help"),
            BotCommand("myplan",        "Check your plan"),
            BotCommand("plan",          "Available plans"),
            BotCommand("shortlink",     "Set shortlink"),
            BotCommand("tutorial",      "Set tutorial video"),
            BotCommand("caption",       "Set file caption"),
            BotCommand("template",      "Set IMDB template"),
            BotCommand("fsub",          "Set force-subscribe channel"),
            BotCommand("log",           "Set log channel"),
            BotCommand("ginfo",         "Get group/channel info"),
            BotCommand("index",         "Index files"),
            BotCommand("addpremium",    "Add premium user"),
            BotCommand("removepremium", "Remove premium user"),
            BotCommand("premiumuser",   "List premium users"),
            BotCommand("broadcast",     "Broadcast to users"),
            BotCommand("gbroadcast",    "Broadcast to groups"),
            BotCommand("deleteall",     "Delete all files"),
            BotCommand("deletefiles",   "Delete files by name"),
            BotCommand("setverify",     "Toggle verification on/off"),
            BotCommand("setprotect",    "Toggle content protection"),
        ])

        if Config.LOG_CHANNEL:
            try:
                await self.send_message(Config.LOG_CHANNEL, f"🚀 **Bot started!** @{me.username}")
            except Exception:
                logger.warning("Could not send start message to log channel.")

    async def stop(self, *args):
        logger.info("Bot stopping…")
        await super().stop()


bot = AutoFilterBot()


async def main():
    async with bot:
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
