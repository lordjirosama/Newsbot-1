from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from database import (
    add_channel, remove_channel, get_channel_by_user,
    toggle_channel,
)
from utils.keyboards import channel_category_keyboard, main_menu_keyboard
from utils.logger import logger

WAITING_CHANNEL_ID = 1
WAITING_CATEGORIES = 2


async def connect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    existing = await get_channel_by_user(user.id)
    if existing:
        await update.message.reply_text(
            f"You already have a connected channel: <b>{existing.get('title', existing['chat_id'])}</b>\n\n"
            "Use <b>Disconnect</b> to remove it first.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "<b>Connect Your Channel</b>\n\n"
        "Step 1: Add this bot as an <b>Admin</b> to your Telegram channel.\n\n"
        "Step 2: Forward any message from your channel here, "
        "or send the channel username (e.g. <code>@mychannel</code>).",
        parse_mode="HTML",
    )
    return WAITING_CHANNEL_ID


async def receive_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message

    # Forwarded message from a channel
    if msg.forward_origin and hasattr(msg.forward_origin, "chat"):
        chat = msg.forward_origin.chat
        context.user_data["connect_chat_id"] = str(chat.id)
        context.user_data["connect_title"] = chat.title or str(chat.id)
        context.user_data["connect_username"] = chat.username or ""
    else:
        text = msg.text.strip()
        if text.startswith("@"):
            context.user_data["connect_chat_id"] = text
            context.user_data["connect_title"] = text
            context.user_data["connect_username"] = text.lstrip("@")
        else:
            await msg.reply_text("Please forward a message from your channel or send the username.")
            return WAITING_CHANNEL_ID

    # Ask category selection
    context.user_data["connect_categories"] = []
    await msg.reply_text(
        "<b>Select categories</b> your channel should receive.\n"
        "Tap to toggle, then press Confirm.",
        parse_mode="HTML",
        reply_markup=channel_category_keyboard([]),
    )
    return WAITING_CATEGORIES


async def category_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data  # "chcat:Anime" or "chcat:confirm" or "chcat:cancel"

    action = data.split(":", 1)[1]

    if action == "confirm":
        cats = context.user_data.get("connect_categories", [])
        if not cats:
            await query.answer("Select at least one category.", show_alert=True)
            return

        chat_id = context.user_data.get("connect_chat_id", "")
        title = context.user_data.get("connect_title", "")
        username = context.user_data.get("connect_username", "")
        user = update.effective_user

        ok = await add_channel(chat_id, username, title, cats, user.id)
        if ok:
            cats_str = ", ".join(cats)
            await query.edit_message_text(
                f"Channel <b>{title}</b> connected.\n\n"
                f"Receiving: <b>{cats_str}</b>",
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text("This channel is already connected.")

    elif action == "cancel":
        await query.edit_message_text("Cancelled.")

    else:
        # Toggle category
        cats: list = context.user_data.get("connect_categories", [])
        if action in cats:
            cats.remove(action)
        else:
            cats.append(action)
        context.user_data["connect_categories"] = cats
        await query.edit_message_reply_markup(
            reply_markup=channel_category_keyboard(cats)
        )


async def disconnect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    existing = await get_channel_by_user(user.id)
    if not existing:
        await update.message.reply_text(
            "No channel connected.",
            reply_markup=main_menu_keyboard(),
        )
        return

    ok = await remove_channel(existing["chat_id"])
    if ok:
        await update.message.reply_text(
            f"Channel <b>{existing.get('title', existing['chat_id'])}</b> disconnected.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text("Could not disconnect. Try again.")


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    existing = await get_channel_by_user(user.id)
    if not existing:
        await update.message.reply_text(
            "No channel connected. Use <b>Connect</b> first.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    cats = existing.get("categories", "None")
    enabled = "Active" if existing.get("enabled") else "Paused"
    chat_id = existing.get("chat_id", "")

    await update.message.reply_text(
        f"<b>Channel Settings</b>\n\n"
        f"Channel  : {existing.get('title', chat_id)}\n"
        f"Status   : {enabled}\n"
        f"Categories: {cats}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Pause", callback_data=f"chset:pause:{chat_id}"),
                InlineKeyboardButton("Resume", callback_data=f"chset:resume:{chat_id}"),
            ],
            [InlineKeyboardButton("Disconnect", callback_data=f"chset:disconnect:{chat_id}")],
        ]),
    )


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, action, chat_id = query.data.split(":", 2)

    if action == "pause":
        await toggle_channel(chat_id, False)
        await query.edit_message_text("Channel posting paused.")
    elif action == "resume":
        await toggle_channel(chat_id, True)
        await query.edit_message_text("Channel posting resumed.")
    elif action == "disconnect":
        await remove_channel(chat_id)
        await query.edit_message_text("Channel disconnected.")


def get_connect_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Connect$"), connect_handler)],
        states={
            WAITING_CHANNEL_ID: [
                MessageHandler(filters.ALL & ~filters.COMMAND, receive_channel_id)
            ],
            WAITING_CATEGORIES: [],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        allow_reentry=True,
    )
