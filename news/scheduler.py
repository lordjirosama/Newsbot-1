import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config import AUTO_FETCH_INTERVAL, MAX_POSTS_PER_CYCLE
from database import get_latest_news, get_channels
from news.fetcher import fetch_all_sources
from news.formatter import format_article
from utils.keyboards import article_keyboard
from utils.logger import logger

_last_posted_ids: set[int] = set()


async def _post_to_channels(bot: Bot, articles: list[dict]) -> None:
    channels = await get_channels(enabled_only=True)
    if not channels:
        return

    for channel in channels:
        allowed_cats = [c.strip() for c in channel.get("categories", "").split(",") if c.strip()]
        chat_id = channel["chat_id"]

        for article in articles:
            if article["id"] in _last_posted_ids:
                continue
            if allowed_cats and article.get("category") not in allowed_cats:
                continue

            text = format_article(article)
            url = article.get("url", "")
            keyboard = article_keyboard(url)

            try:
                if article.get("image_url"):
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=article["image_url"],
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                        disable_web_page_preview=False,
                    )

                _last_posted_ids.add(article["id"])
                logger.info(f"Posted article {article['id']} to {chat_id}")
                await asyncio.sleep(2)  # rate-limit guard

            except TelegramError as e:
                logger.error(f"Telegram error posting to {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error posting to {chat_id}: {e}")


async def scheduler_loop(bot: Bot) -> None:
    """Main background loop: fetch → post → wait → repeat."""
    logger.info(f"Scheduler started. Interval: {AUTO_FETCH_INTERVAL}s")
    while True:
        try:
            count = await fetch_all_sources()
            if count > 0:
                # Get articles not yet posted, limited per cycle
                articles = await get_latest_news(limit=MAX_POSTS_PER_CYCLE * 3)
                fresh = [a for a in articles if a["id"] not in _last_posted_ids]
                fresh = fresh[:MAX_POSTS_PER_CYCLE]
                if fresh:
                    await _post_to_channels(bot, fresh)
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")

        await asyncio.sleep(AUTO_FETCH_INTERVAL)
