from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import OWNER_ID, BOT_NAME, BOT_VERSION, RSS_SOURCES, AUTO_FETCH_INTERVAL
from database import (
    get_news_count, get_user_count, get_channel_count, clean_old_news
)
from news.fetcher import fetch_all_sources


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    total = await get_news_count()
    today = await get_news_count(today_only=True)
    users = await get_user_count()
    channels = await get_channel_count()
    sources_total = len(RSS_SOURCES)
    sources_active = sum(1 for s in RSS_SOURCES if s.get("enabled", True))

    text = (
        f"<b>{BOT_NAME}  v{BOT_VERSION}</b>\n\n"
        f"Status     : Running\n"
        f"Fetch every: {AUTO_FETCH_INTERVAL // 60} min\n\n"
        f"<b>Database</b>\n"
        f"Total news : {total}\n"
        f"Today      : {today}\n"
        f"Users      : {users}\n"
        f"Channels   : {channels}\n\n"
        f"<b>Sources</b>\n"
        f"Total      : {sources_total}\n"
        f"Active     : {sources_active}\n"
        f"Disabled   : {sources_total - sources_active}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def fetch_now_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("This command is for admins only.")
        return
    msg = await update.message.reply_text("Fetching news from all sources...")
    count = await fetch_all_sources()
    await msg.edit_text(f"Fetch complete. {count} new article(s) saved.")


async def cleandb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("This command is for admins only.")
        return
    removed = await clean_old_news()
    await update.message.reply_text(f"Cleaned {removed} old article(s) from database.")


async def sources_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["<b>Configured Sources</b>\n"]
    for s in RSS_SOURCES:
        status = "ON" if s.get("enabled", True) else "OFF"
        lines.append(f"[{status}] {s['name']}  [{s['category']}]")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
