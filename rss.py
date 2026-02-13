import os
import sys
import feedparser
from sql import db
from dotenv import load_dotenv
from pyrogram import Client
from pyrogram.errors import FloodWait
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

if os.path.exists("config.env"):
    load_dotenv("config.env")

try:
    api_id = int(os.environ.get("API_ID"))
    api_hash = os.environ.get("API_HASH")
    feed_urls = list(set(os.environ.get("FEED_URLS").split("|")))
    bot_token = os.environ.get("BOT_TOKEN")
    log_channel = int(os.environ.get("LOG_CHANNEL"))
    check_interval = int(os.environ.get("INTERVAL", 10))
    max_instances = int(os.environ.get("MAX_INSTANCES", 3))
except Exception as e:
    print(e)
    print("One or more variables missing. Exiting !")
    sys.exit(1)

for feed_url in feed_urls:
    if db.get_link(feed_url) is None:
        db.update_link(feed_url, "*")

app = Client("rss_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


async def check_feed(feed_url):
    FEED = feedparser.parse(feed_url)
    entry = FEED.entries[0]

    if entry.id != db.get_link(feed_url).link:
        message = f"**{entry.title}**\n```{entry.link}```"
        try:
            await app.send_message(log_channel, message)
            db.update_link(feed_url, entry.id)
        except FloodWait as e:
            print(f"FloodWait: {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(e)
    else:
        print(f"Checked RSS FEED: {entry.id}")


async def main():
    scheduler = AsyncIOScheduler()
    for feed_url in feed_urls:
        scheduler.add_job(
            check_feed,
            "interval",
            seconds=check_interval,
            max_instances=max_instances,
            args=[feed_url],
        )
    scheduler.start()
    await app.start()
    print("Bot Started...")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
