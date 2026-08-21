from telegram import Update
from telegram.ext import ContextTypes
from config import BOT_NAME, BOT_VERSION, SUPPORT_CHANNEL, SUPPORT_GROUP
from database import upsert_user
from utils.keyboards import main_menu_keyboard, support_keyboard


WELCOME_TEXT = (
    f"<b>{BOT_NAME}</b>  v{BOT_VERSION}\n\n"
    "Automatically delivers the latest news in:\n"
    "  Anime · Movies · Gaming · Web Series · K-Drama\n\n"
    "Browse news, search by keyword, or connect your channel\n"
    "to receive automatic updates.\n\n"
    "Use the menu below to get started."
)

HELP_TEXT = (
    f"<b>{BOT_NAME} — Commands</b>\n\n"
    "<b>News</b>       — Show latest news\n"
    "<b>Category</b>   — Browse by category\n"
    "<b>Search</b>     — Search news by keyword\n"
    "<b>Status</b>     — Bot and database status\n"
    "<b>Connect</b>    — Connect your Telegram channel\n"
    "<b>Disconnect</b> — Remove connected channel\n"
    "<b>Settings</b>   — Manage your channel settings\n"
    "<b>Help</b>       — Show this message\n\n"
    f"Support: {SUPPORT_CHANNEL}"
)

ABOUT_TEXT = (
    f"<b>{BOT_NAME}</b>\n"
    f"Version : {BOT_VERSION}\n\n"
    "An automatic news bot delivering entertainment news\n"
    "to Telegram channels and users.\n\n"
    f"Channel : {SUPPORT_CHANNEL}\n"
    f"Group   : {SUPPORT_GROUP}"
)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        await upsert_user(user.id, user.username or "", user.first_name or "")

    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=support_keyboard(),
    )


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(ABOUT_TEXT, parse_mode="HTML")
