import os
import hashlib
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional
from config import DATABASE_PATH, NEWS_RETENTION_DAYS
from utils.logger import logger


async def init_db() -> None:
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                joined_at   TEXT,
                last_active TEXT
            );

            CREATE TABLE IF NOT EXISTS news (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                description  TEXT,
                url          TEXT UNIQUE NOT NULL,
                image_url    TEXT,
                source_name  TEXT,
                category     TEXT,
                published_at TEXT,
                fetched_at   TEXT,
                url_hash     TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS channels (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id    TEXT UNIQUE NOT NULL,
                username   TEXT,
                title      TEXT,
                categories TEXT,
                enabled    INTEGER DEFAULT 1,
                added_by   INTEGER,
                added_at   TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);
            CREATE INDEX IF NOT EXISTS idx_news_fetched  ON news(fetched_at);
            CREATE INDEX IF NOT EXISTS idx_news_hash     ON news(url_hash);
        """)
        await db.commit()
    logger.info("Database initialized.")


# ── Users ────────────────────────────────────────────────────────────────────

async def upsert_user(user_id: int, username: str, first_name: str) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, joined_at, last_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username    = excluded.username,
                first_name  = excluded.first_name,
                last_active = excluded.last_active
        """, (user_id, username, first_name, now, now))
        await db.commit()


async def get_user_count() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ── News ─────────────────────────────────────────────────────────────────────

def _hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


async def is_duplicate(url: str) -> bool:
    h = _hash(url)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM news WHERE url_hash = ? OR url = ?", (h, url)
        ) as cur:
            return await cur.fetchone() is not None


async def save_article(
    title: str,
    description: str,
    url: str,
    image_url: Optional[str],
    source_name: str,
    category: str,
    published_at: Optional[str],
) -> bool:
    """Returns True if saved, False if duplicate."""
    if await is_duplicate(url):
        return False
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO news
                    (title, description, url, image_url, source_name,
                     category, published_at, fetched_at, url_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, description, url, image_url, source_name,
                category, published_at, now, _hash(url),
            ))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_latest_news(category: Optional[str] = None, limit: int = 10) -> list[dict]:
    query = "SELECT * FROM news"
    params: list = []
    if category:
        query += " WHERE category = ?"
        params.append(category)
    query += " ORDER BY fetched_at DESC LIMIT ?"
    params.append(limit)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def search_news(keyword: str, limit: int = 10) -> list[dict]:
    kw = f"%{keyword}%"
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM news
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY fetched_at DESC LIMIT ?
        """, (kw, kw, limit)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_news_count(today_only: bool = False) -> int:
    query = "SELECT COUNT(*) FROM news"
    params: list = []
    if today_only:
        today = datetime.utcnow().date().isoformat()
        query += " WHERE fetched_at >= ?"
        params.append(today)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(query, params) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def clean_old_news() -> int:
    cutoff = (datetime.utcnow() - timedelta(days=NEWS_RETENTION_DAYS)).isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("DELETE FROM news WHERE fetched_at < ?", (cutoff,))
        await db.commit()
        return cur.rowcount


# ── Channels ─────────────────────────────────────────────────────────────────

async def add_channel(
    chat_id: str,
    username: str,
    title: str,
    categories: list[str],
    added_by: int,
) -> bool:
    now = datetime.utcnow().isoformat()
    cats = ",".join(categories)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO channels (chat_id, username, title, categories, added_by, added_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chat_id, username, title, cats, added_by, now))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def remove_channel(chat_id: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        await db.commit()
        return cur.rowcount > 0


async def get_channels(enabled_only: bool = True) -> list[dict]:
    query = "SELECT * FROM channels"
    if enabled_only:
        query += " WHERE enabled = 1"
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_channel_by_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM channels WHERE added_by = ? LIMIT 1", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def toggle_channel(chat_id: str, enabled: bool) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE channels SET enabled = ? WHERE chat_id = ?",
            (1 if enabled else 0, chat_id),
        )
        await db.commit()


async def get_channel_count() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM channels WHERE enabled = 1") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0
