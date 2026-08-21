import os
from dotenv import load_dotenv

load_dotenv()

# Core
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))

# Database
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/autonews.db")

# Fetcher
AUTO_FETCH_INTERVAL: int = int(os.getenv("AUTO_FETCH_INTERVAL", "300"))
MAX_POSTS_PER_CYCLE: int = int(os.getenv("MAX_POSTS_PER_CYCLE", "5"))
NEWS_RETENTION_DAYS: int = int(os.getenv("NEWS_RETENTION_DAYS", "7"))

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Bot identity
BOT_NAME = "Auto News Bot"
BOT_VERSION = "1.0.0"
SUPPORT_CHANNEL = "https://t.me/your_support_channel"
SUPPORT_GROUP = "https://t.me/your_support_group"

# Categories supported
CATEGORIES = [
    "Anime",
    "Movies",
    "Gaming",
    "Web Series",
    "K-Drama",
]

# RSS Sources per category
# Add/remove sources here — no code changes needed elsewhere
RSS_SOURCES = [
    # Anime
    {
        "name": "Anime News Network",
        "url": "https://www.animenewsnetwork.com/news/rss.xml",
        "category": "Anime",
        "enabled": True,
    },
    {
        "name": "Crunchyroll News",
        "url": "https://www.crunchyroll.com/feed",
        "category": "Anime",
        "enabled": True,
    },
    # Movies
    {
        "name": "Deadline Hollywood",
        "url": "https://deadline.com/feed/",
        "category": "Movies",
        "enabled": True,
    },
    {
        "name": "The Hollywood Reporter",
        "url": "https://www.hollywoodreporter.com/feed/",
        "category": "Movies",
        "enabled": True,
    },
    # Gaming
    {
        "name": "IGN",
        "url": "https://feeds.feedburner.com/ign/all",
        "category": "Gaming",
        "enabled": True,
    },
    {
        "name": "GameSpot News",
        "url": "https://www.gamespot.com/feeds/news/",
        "category": "Gaming",
        "enabled": True,
    },
    # Web Series
    {
        "name": "What's on Netflix",
        "url": "https://www.whats-on-netflix.com/feed/",
        "category": "Web Series",
        "enabled": True,
    },
    # K-Drama
    {
        "name": "Soompi",
        "url": "https://www.soompi.com/feed",
        "category": "K-Drama",
        "enabled": True,
    },
    {
        "name": "Dramabeans",
        "url": "https://www.dramabeans.com/feed/",
        "category": "K-Drama",
        "enabled": True,
    },
]

# Validate on startup
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")
if not OWNER_ID:
    raise ValueError("OWNER_ID is not set in .env")
