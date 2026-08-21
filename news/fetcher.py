import asyncio
import feedparser
import aiohttp
from datetime import datetime
from typing import Optional
from config import RSS_SOURCES
from database import save_article
from utils.logger import logger

# feedparser is sync — run in executor to avoid blocking
_loop_executor = None


def _parse_feed(url: str) -> feedparser.FeedParserDict:
    return feedparser.parse(url)


def _entry_to_article(entry: dict, source: dict) -> Optional[dict]:
    url = entry.get("link", "").strip()
    title = entry.get("title", "").strip()
    if not url or not title:
        return None

    # Description — try multiple fields
    description = (
        entry.get("summary")
        or entry.get("description")
        or ""
    ).strip()
    # Strip basic HTML tags from description
    import re
    description = re.sub(r"<[^>]+>", "", description).strip()

    # Image — try media_content, enclosures
    image_url: Optional[str] = None
    if "media_content" in entry and entry["media_content"]:
        image_url = entry["media_content"][0].get("url")
    elif "enclosures" in entry and entry["enclosures"]:
        enc = entry["enclosures"][0]
        if enc.get("type", "").startswith("image"):
            image_url = enc.get("href") or enc.get("url")

    # Published date
    published_at: Optional[str] = None
    if hasattr(entry, "published_parsed") and entry.get("published_parsed"):
        try:
            published_at = datetime(*entry.published_parsed[:6]).isoformat()
        except Exception:
            pass

    return {
        "title": title,
        "description": description[:500],
        "url": url,
        "image_url": image_url,
        "source_name": source["name"],
        "category": source["category"],
        "published_at": published_at,
    }


async def fetch_source(source: dict) -> int:
    """Fetches one RSS source. Returns count of new articles saved."""
    if not source.get("enabled", True):
        return 0

    url = source["url"]
    try:
        loop = asyncio.get_event_loop()
        feed = await asyncio.wait_for(
            loop.run_in_executor(None, _parse_feed, url),
            timeout=20,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching source: {source['name']}")
        return 0
    except Exception as e:
        logger.error(f"Error fetching {source['name']}: {e}")
        return 0

    if feed.bozo and not feed.entries:
        logger.warning(f"Invalid feed: {source['name']} — {feed.bozo_exception}")
        return 0

    saved = 0
    for entry in feed.entries[:10]:  # max 10 per fetch cycle
        article = _entry_to_article(entry, source)
        if not article:
            continue
        try:
            if await save_article(**article):
                saved += 1
        except Exception as e:
            logger.error(f"Error saving article from {source['name']}: {e}")

    logger.info(f"[{source['name']}] {saved} new articles.")
    return saved


async def fetch_all_sources() -> int:
    """Fetches all enabled sources concurrently. Returns total new articles."""
    tasks = [fetch_source(s) for s in RSS_SOURCES if s.get("enabled", True)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total = sum(r for r in results if isinstance(r, int))
    logger.info(f"Fetch complete. Total new articles: {total}")
    return total
