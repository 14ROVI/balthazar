from db import Database
from rss import RssFetcher
from trance import AntiBot
from alert import AlertSender
from ai_engine import GeminiAnalyst
from mastodon_listener import MastodonClient
from bluesky import BlueskyClient
from post_processor import PostProcessor
from process_rss import RssProcessor

from queue import SimpleQueue
import asyncio
import threading
import time
import sys

FETCH_INTERVAL = 5 * 60
ALERT_INTERVAL = 30

async def fetcher_loop(fetcher: RssFetcher):
    while True:
        try:
            await fetcher.fetch_updates()
        except Exception as e:
            print(f"[Fetcher Error]: {e}")    
        await asyncio.sleep(FETCH_INTERVAL)

async def alerter_loop(alert_sender: AlertSender):
    while True:
        try:
            await alert_sender.send_alerts()
        except Exception as e:
            print(f"[Alerter Error]: {e}")
        await asyncio.sleep(ALERT_INTERVAL)


async def main():
    async with AntiBot() as antibot:
        queue = asyncio.Queue()
        database = Database()
        analyst = GeminiAnalyst()
    
        rss_client = RssFetcher(database, antibot, analyst, queue)
        mastodon_client = MastodonClient(queue)
        bluesky_client = BlueskyClient(queue)
    
        processor = PostProcessor(database, analyst, queue)
        
        alerter = AlertSender(database)
    
        tasks = [
            asyncio.create_task(fetcher_loop(rss_client)),
            asyncio.create_task(bluesky_client.listen()),
            asyncio.create_task(processor.process_queue()),
            asyncio.create_task(alerter_loop(alerter)),
        ]
        
        mastodon_client.listen()
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())