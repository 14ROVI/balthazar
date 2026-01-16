import asyncio
import os
import uvicorn
from api import app

from db import Database
from rss import RssFetcher
from trance import AntiBot
from ai_engine import GeminiAnalyst
from mastodon_listener import MastodonClient
from bluesky import BlueskyClient
from post_processor import PostProcessor
from market_data import MarketDataProvider
import anchors

FETCH_INTERVAL = 5 * 60

async def fetcher_loop(fetcher: RssFetcher):
    while True:
        try:
            await fetcher.fetch_updates()
        except Exception as e:
            print(f"[Fetcher Error]: {e}")    
        await asyncio.sleep(FETCH_INTERVAL)


async def main():
    async with AntiBot() as antibot:
        # --- Component Initialization ---
        queue = asyncio.Queue()
        database = Database()
        analyst = GeminiAnalyst()
        market_provider = MarketDataProvider()

        # --- Producer Initialization ---
        rss_client = RssFetcher(database, antibot, queue)
        mastodon_client = MastodonClient(queue)
        bluesky_client = BlueskyClient(queue)
    
        # --- Consumer/Processor Initialization ---
        processor = PostProcessor(database, analyst, market_provider, queue)

        # --- Uvicorn Server Setup ---
        config = uvicorn.Config(app=app, host="127.0.0.1", port=7777, log_level="info")
        server = uvicorn.Server(config)
    
        # --- Task Creation ---
        tasks = [
            asyncio.create_task(fetcher_loop(rss_client)),
            asyncio.create_task(bluesky_client.listen()),
            asyncio.create_task(processor.process_queue()),
            asyncio.to_thread(mastodon_client.listen),
            asyncio.create_task(server.serve()),
        ]
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    # To run this, execute `python main.py` in your terminal
    print("Starting Balthazar...")
    asyncio.run(main())