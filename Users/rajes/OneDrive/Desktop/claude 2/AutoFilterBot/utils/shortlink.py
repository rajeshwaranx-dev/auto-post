"""Shortlink wrapper – supports shrinkme.io / mdiskshorten / droplink style APIs."""
import aiohttp
import logging

logger = logging.getLogger(__name__)


async def get_shortlink(url: str, api_url: str, api_key: str) -> str:
    """
    Return a shortened URL via the shortlink service.
    Compatible with: shrinkme.io, droplink.co, mdiskshorten.com, etc.
    """
    endpoint = f"https://{api_url}/api?api={api_key}&url={url}&format=text"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    short = (await resp.text()).strip()
                    if short.startswith("http"):
                        return short
    except Exception as e:
        logger.warning(f"Shortlink error: {e}")
    return url   # fall back to original URL


async def generate_verify_link(bot_username: str, user_id: int, api_url: str, api_key: str) -> str:
    """Build a deep-link verify URL and shorten it."""
    deep = f"https://t.me/{bot_username}?start=verify_{user_id}"
    return await get_shortlink(deep, api_url, api_key)
