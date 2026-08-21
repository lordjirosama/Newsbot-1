from datetime import datetime
from config import BOT_NAME


def format_article(article: dict) -> str:
    """
    Returns a clean Telegram-ready message string.
    No emojis as per design spec — minimal, professional.
    """
    title = article.get("title", "No Title")
    description = article.get("description", "")
    category = article.get("category", "General")
    source = article.get("source_name", "Unknown Source")
    published_at = article.get("published_at", "")

    # Trim description
    if description and len(description) > 280:
        description = description[:277].rsplit(" ", 1)[0] + "..."

    # Format date
    date_str = ""
    if published_at:
        try:
            dt = datetime.fromisoformat(published_at)
            date_str = dt.strftime("%d %b %Y, %I:%M %p UTC")
        except ValueError:
            date_str = published_at

    lines = [
        f"<b>{title}</b>",
        "",
    ]
    if description:
        lines += [description, ""]

    lines += [
        f"Category : {category}",
        f"Source   : {source}",
    ]
    if date_str:
        lines.append(f"Published: {date_str}")

    lines += [
        "",
        f"— {BOT_NAME}",
    ]

    return "\n".join(lines)


def format_article_list(articles: list[dict], heading: str = "Latest News") -> str:
    if not articles:
        return f"<b>{heading}</b>\n\nNo articles found."
    lines = [f"<b>{heading}</b>", ""]
    for i, a in enumerate(articles, 1):
        title = a.get("title", "Untitled")[:60]
        category = a.get("category", "")
        lines.append(f"{i}. {title}  [{category}]")
    return "\n".join(lines)
