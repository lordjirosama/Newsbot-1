import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import BOT_TOKEN, BOT_NAME
from database import init_db
from utils.logger import logger

# Handlers
from handlers.start import start_handler, help_handler, about_handler
from handlers.news import (
    news_handler,
    category_handler,
    news_callback,
    category_callback,
    cat_news_callback,
)
from handlers.search import get_search_conversation, search_callback
from handlers.channel import (
    get_connect_conversation,
    disconnect_handler,
    settings_handler,
    settings_callback,
    category_toggle_callback,
)
from handlers.admin import (
    status_handler,
    fetch_now_handler,
    cleandb_handler,
    sources_list_handler,
)
from news.scheduler import scheduler_loop


async def back_callback(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()
    dest = query.data.split(":", 1)[1]

    if dest == "main":
        from utils.keyboards import main_menu_keyboard
        await query.edit_message_text(
            "Main menu — use the buttons below.",
            reply_markup=None,
        )
    elif dest == "categories":
        from utils.keyboards import categories_keyboard
        await query.edit_message_text(
            "<b>Select a Category</b>",
            parse_mode="HTML",
            reply_markup=categories_keyboard(),
        )
    elif dest == "news":
        from database import get_latest_news
        from utils.keyboards import news_list_keyboard
        import math
        articles = await get_latest_news(limit=50)
        page = 1
        page_size = 7
        total_pages = max(1, math.ceil(len(articles) / page_size))
        page_articles = articles[:page_size]
        await query.edit_message_text(
            f"<b>Latest News</b>  ({len(articles)} articles)",
            parse_mode="HTML",
            reply_markup=news_list_keyboard(page_articles, page, total_pages, prefix="news"),
        )


async def noop_callback(update: Update, context) -> None:
    await update.callback_query.answer()


async def post_init(application: Application) -> None:
    await init_db()
    logger.info(f"{BOT_NAME} database ready.")


async def main() -> None:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── Commands ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("about", about_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("fetch", fetch_now_handler))
    app.add_handler(CommandHandler("cleandb", cleandb_handler))
    app.add_handler(CommandHandler("sources", sources_list_handler))

    # ── Conversations (must come before generic text handler) ─────────────────
    app.add_handler(get_search_conversation())
    app.add_handler(get_connect_conversation())

    # ── Reply keyboard text buttons ───────────────────────────────────────────
    app.add_handler(MessageHandler(filters.Regex("^News$"), news_handler))
    app.add_handler(MessageHandler(filters.Regex("^Category$"), category_handler))
    app.add_handler(MessageHandler(filters.Regex("^Status$"), status_handler))
    app.add_handler(MessageHandler(filters.Regex("^Disconnect$"), disconnect_handler))
    app.add_handler(MessageHandler(filters.Regex("^Settings$"), settings_handler))
    app.add_handler(MessageHandler(filters.Regex("^Help$"), help_handler))
    app.add_handler(MessageHandler(filters.Regex("^(Support Channel|Support Group)$"), help_handler))

    # ── Inline callbacks ──────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))
    app.add_handler(CallbackQueryHandler(back_callback, pattern="^back:"))
    app.add_handler(CallbackQueryHandler(news_callback, pattern="^news:"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern="^cat:(?!confirm|cancel)"))
    app.add_handler(CallbackQueryHandler(cat_news_callback, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(search_callback, pattern="^srch:"))
    app.add_handler(CallbackQueryHandler(category_toggle_callback, pattern="^chcat:"))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^chset:"))

    # ── Start scheduler alongside bot ─────────────────────────────────────────
    async with app:
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        logger.info(f"{BOT_NAME} is running.")

        asyncio.create_task(scheduler_loop(app.bot))

        # Keep alive
        await asyncio.Event().wait()

        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
