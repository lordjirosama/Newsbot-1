import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_latest_news
from news.formatter import format_article
from utils.keyboards import (
    categories_keyboard,
    news_list_keyboard,
    article_keyboard,
    main_menu_keyboard,
)

PAGE_SIZE = 7


def _paginate(articles: list[dict], page: int) -> tuple[list[dict], int]:
    total_pages = max(1, math.ceil(len(articles) / PAGE_SIZE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    return articles[start : start + PAGE_SIZE], total_pages


async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    articles = await get_latest_news(limit=50)
    page_articles, total_pages = _paginate(articles, 1)

    if not page_articles:
        await update.message.reply_text(
            "No news available yet. Check back shortly.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        f"<b>Latest News</b>  ({len(articles)} articles)",
        parse_mode="HTML",
        reply_markup=news_list_keyboard(page_articles, 1, total_pages, prefix="news"),
    )


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "<b>Select a Category</b>",
        parse_mode="HTML",
        reply_markup=categories_keyboard(),
    )


# ── Callbacks ────────────────────────────────────────────────────────────────

async def news_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data  # e.g. "news:detail:42" or "news:page:2"

    parts = data.split(":")

    if parts[1] == "detail":
        article_id = int(parts[2])
        articles = await get_latest_news(limit=200)
        article = next((a for a in articles if a["id"] == article_id), None)
        if not article:
            await query.edit_message_text("Article not found.")
            return
        text = format_article(article)
        url = article.get("url", "")
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=article_keyboard(url, back_cb="back:news"),
        )

    elif parts[1] == "page":
        page = int(parts[2])
        articles = await get_latest_news(limit=50)
        page_articles, total_pages = _paginate(articles, page)
        await query.edit_message_reply_markup(
            reply_markup=news_list_keyboard(page_articles, page, total_pages, prefix="news")
        )


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data  # "cat:Anime"

    category = data.split(":", 1)[1]
    articles = await get_latest_news(category=category, limit=50)
    page_articles, total_pages = _paginate(articles, 1)

    if not page_articles:
        await query.edit_message_text(
            f"No news found for <b>{category}</b> yet.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="back:categories")]
            ]),
        )
        return

    # Store category in context for pagination
    context.user_data["browse_category"] = category

    await query.edit_message_text(
        f"<b>{category} News</b>  ({len(articles)} articles)",
        parse_mode="HTML",
        reply_markup=news_list_keyboard(
            page_articles, 1, total_pages, prefix=f"cat_{category}"
        ),
    )


async def cat_news_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles pagination inside a category."""
    query = update.callback_query
    await query.answer()
    data = query.data  # "cat_Anime:detail:5" or "cat_Anime:page:2"

    prefix, action, value = data.rsplit(":", 2)
    category = prefix.replace("cat_", "", 1)

    if action == "detail":
        article_id = int(value)
        articles = await get_latest_news(category=category, limit=200)
        article = next((a for a in articles if a["id"] == article_id), None)
        if not article:
            await query.edit_message_text("Article not found.")
            return
        text = format_article(article)
        url = article.get("url", "")
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=article_keyboard(url, back_cb=f"cat:{category}"),
        )

    elif action == "page":
        page = int(value)
        articles = await get_latest_news(category=category, limit=50)
        page_articles, total_pages = _paginate(articles, page)
        await query.edit_message_reply_markup(
            reply_markup=news_list_keyboard(page_articles, page, total_pages, prefix=prefix)
        )
