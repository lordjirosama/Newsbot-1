import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from database import search_news
from news.formatter import format_article
from utils.keyboards import article_keyboard, main_menu_keyboard

WAITING_QUERY = 1
PAGE_SIZE = 7


def _paginate(articles: list[dict], page: int) -> tuple[list[dict], int]:
    total_pages = max(1, math.ceil(len(articles) / PAGE_SIZE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    return articles[start : start + PAGE_SIZE], total_pages


def _results_keyboard(articles: list[dict], page: int, total_pages: int, query: str) -> InlineKeyboardMarkup:
    rows = []
    for a in articles:
        title = a["title"][:42] + ("..." if len(a["title"]) > 42 else "")
        rows.append([InlineKeyboardButton(title, callback_data=f"srch:detail:{a['id']}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("Prev", callback_data=f"srch:page:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next", callback_data=f"srch:page:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("New Search", callback_data="srch:new")])
    return InlineKeyboardMarkup(rows)


async def search_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Enter a keyword to search news.\n\nExample: <code>One Piece</code>",
        parse_mode="HTML",
    )
    return WAITING_QUERY


async def search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyword = update.message.text.strip()
    if len(keyword) < 2:
        await update.message.reply_text("Keyword too short. Try again:")
        return WAITING_QUERY

    articles = await search_news(keyword, limit=50)
    context.user_data["search_results"] = articles
    context.user_data["search_query"] = keyword

    if not articles:
        await update.message.reply_text(
            f"No results found for: <b>{keyword}</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    page_articles, total_pages = _paginate(articles, 1)
    await update.message.reply_text(
        f"<b>Search: {keyword}</b>  ({len(articles)} results)",
        parse_mode="HTML",
        reply_markup=_results_keyboard(page_articles, 1, total_pages, keyword),
    )
    return ConversationHandler.END


async def search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split(":", 2)
    action = parts[1]

    if action == "new":
        await query.edit_message_text(
            "Enter a new keyword to search:",
        )
        context.user_data["awaiting_search"] = True
        return

    articles = context.user_data.get("search_results", [])
    kw = context.user_data.get("search_query", "")

    if action == "detail":
        article_id = int(parts[2])
        article = next((a for a in articles if a["id"] == article_id), None)
        if not article:
            await query.edit_message_text("Article not found.")
            return
        text = format_article(article)
        url = article.get("url", "")
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=article_keyboard(url, back_cb="srch:back"),
        )

    elif action == "page":
        page = int(parts[2])
        page_articles, total_pages = _paginate(articles, page)
        await query.edit_message_reply_markup(
            reply_markup=_results_keyboard(page_articles, page, total_pages, kw)
        )

    elif action == "back":
        page_articles, total_pages = _paginate(articles, 1)
        await query.edit_message_text(
            f"<b>Search: {kw}</b>  ({len(articles)} results)",
            parse_mode="HTML",
            reply_markup=_results_keyboard(page_articles, 1, total_pages, kw),
        )


def get_search_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Search$"), search_prompt)],
        states={
            WAITING_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_execute)
            ]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        allow_reentry=True,
    )
