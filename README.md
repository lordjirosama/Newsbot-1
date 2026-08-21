# Auto News Bot

A professional Telegram bot that automatically collects and publishes
entertainment news — Anime, Movies, Gaming, Web Series, K-Drama —
to channels and users.

---

## Requirements

- Python 3.11+
- pip
- A Telegram bot token from @BotFather
- Your Telegram user ID (from @userinfobot)

---

## Installation

```bash
git clone <repo>
cd AutoNewsBot

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
nano .env                       # Fill in BOT_TOKEN and OWNER_ID
```

---

## .env Configuration

```
BOT_TOKEN=your_bot_token
OWNER_ID=your_telegram_user_id
DATABASE_PATH=data/autonews.db
AUTO_FETCH_INTERVAL=300         # seconds between fetches (default: 5 min)
MAX_POSTS_PER_CYCLE=5           # max articles posted per cycle
NEWS_RETENTION_DAYS=7           # older articles auto-cleaned
LOG_LEVEL=INFO
```

---

## Running the Bot

```bash
python bot.py
```

To run in background (Linux):

```bash
nohup python bot.py > bot.log 2>&1 &
```

Or with screen:

```bash
screen -S autonewsbot
python bot.py
# Ctrl+A then D to detach
```

---

## Adding News Sources

Edit `config.py` — the `RSS_SOURCES` list.

Each source:

```python
{
    "name": "Source Display Name",
    "url":  "https://example.com/feed",
    "category": "Anime",        # Must match a name in CATEGORIES list
    "enabled": True,
}
```

---

## Configuring Channels

Users connect their own channels via the bot's Connect button.

As owner, use `/sources` to see source status and `/fetch` to trigger
an immediate fetch.

---

## Admin Commands

These are owner-only (OWNER_ID in .env):

| Command    | Action                              |
|------------|-------------------------------------|
| /fetch     | Immediately fetch all sources       |
| /cleandb   | Remove articles older than N days   |
| /sources   | List all configured sources         |
| /status    | Show stats (also available to users)|

---

## Project Structure

```
AutoNewsBot/
├── bot.py              Main entry point
├── config.py           All settings and RSS sources
├── database.py         SQLite async layer
├── requirements.txt
├── .env.example
│
├── handlers/
│   ├── start.py        /start, /help, /about
│   ├── news.py         News browsing and categories
│   ├── search.py       Keyword search
│   ├── channel.py      Connect/disconnect/settings
│   └── admin.py        Status, fetch, cleandb
│
├── news/
│   ├── fetcher.py      RSS fetch logic
│   ├── formatter.py    Post formatting
│   └── scheduler.py    Auto-fetch background loop
│
└── utils/
    ├── keyboards.py    All inline/reply keyboards
    └── logger.py       Logging setup
```

---

## Troubleshooting

**Bot not responding**
- Check BOT_TOKEN in .env
- Ensure bot is not already running elsewhere

**No news appearing**
- Send /fetch to trigger immediate fetch
- Check logs for source errors
- Some RSS feeds may block automated requests; replace with working ones

**Channel not receiving posts**
- Confirm bot is admin in the channel
- Use Connect button and verify categories match

**Database errors**
- Ensure `data/` directory exists (auto-created on first run)
