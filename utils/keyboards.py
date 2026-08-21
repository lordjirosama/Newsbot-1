from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import CATEGORIES, SUPPORT_CHANNEL, SUPPORT_GROUP


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["News", "Category"],
        ["Search", "Status"],
        ["Connect", "Disconnect"],
        ["Settings", "Help"],
        ["Support Channel", "Support Group"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def categories_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(CATEGORIES), 2):
        row = []
        for cat in CATEGORIES[i : i + 2]:
            row.append(InlineKeyboardButton(cat, callback_data=f"cat:{cat}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("Back", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


def news_list_keyboard(
    articles: list[dict],
    page: int,
    total_pages: int,
    prefix: str = "news",
) -> InlineKeyboardMarkup:
    rows = []
    for i, article in enumerate(articles):
        title = article["title"][:40] + ("..." if len(article["title"]) > 40 else "")
        rows.append([
            InlineKeyboardButton(title, callback_data=f"{prefix}:detail:{article['id']}")
        ])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("Prev", callback_data=f"{prefix}:page:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next", callback_data=f"{prefix}:page:{page + 1}"))

    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("Back", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


def article_keyboard(url: str, back_cb: str = "back:news") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Read Full Article", url=url)],
        [InlineKeyboardButton("Back", callback_data=back_cb)],
    ])


def channel_category_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(CATEGORIES), 2):
        row = []
        for cat in CATEGORIES[i : i + 2]:
            tick = "✓ " if cat in selected else ""
            row.append(InlineKeyboardButton(f"{tick}{cat}", callback_data=f"chcat:{cat}"))
        rows.append(row)
    rows.append([
        InlineKeyboardButton("Confirm", callback_data="chcat:confirm"),
        InlineKeyboardButton("Cancel", callback_data="chcat:cancel"),
    ])
    return InlineKeyboardMarkup(rows)


def support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Support Channel", url=SUPPORT_CHANNEL),
            InlineKeyboardButton("Support Group", url=SUPPORT_GROUP),
        ]
    ])
