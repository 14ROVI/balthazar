from db import Database
from trance import AntiBot
from ai_engine import GeminiAnalyst
from heuristics import is_obvious_noise
import orjson
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
from domain.rss_item import RssItem
import asyncio

@dataclass
class ProcessableRssItem:
    rss_item: RssItem
    linked_content: List[str]

class RssProcessor:
    def __init__(self, db: Database, antibot: AntiBot, analyst: GeminiAnalyst) -> None:
        self.db = db
        self.antibot = antibot
        self.analyst = analyst

    async def start_process(self):
        unprocessed_rss_items = self.db.get_unprocessed_rss_items()
        
        rss_items_with_data = []
        for item in unprocessed_rss_items:
            try:
                rss_items_with_data.append(ProcessableRssItem(
                    item,
                    await self.get_rss_data(item)
                ))
            except Exception as e:
                print(f"Error processinng {item.url}: {e}")
                
        print(f"{len(rss_items_with_data)} items to batch process")
        
        # batch into < 20MB bundles
        batches = [[]]
        running_size = 0
        for item in rss_items_with_data:
            item_size = len(orjson.dumps(item))
            if item_size > 20 * 1000 * 1000:
                print(f"ITEM TOO LARGE {item['url']}")
                continue
            
            if running_size + item_size > 20 * 1000 * 1000:
                batches.append([])
            
            batches[-1].append(item)
                
        for batch in batches:
            print(f"batched {len(rss_items_with_data)} items")
            self.analyst.analyze_batch_rss(batch)
        
            
    async def get_rss_data(self, item: RssItem) -> List[str]:
        if is_obvious_noise(item.title, item.url):
            self.db.set_rss_item_processed(item.url)
            return []
        
        linked_content = []
        
        async with asyncio.TaskGroup() as tg:
            for link in item.links:
                if not is_obvious_noise(item.title, link):
                    tg.create_task(self._get_page_content(link, linked_content))
                
        return linked_content
        
    async def _get_page_content(self, link: str, linked_content: list):
        content = await self.antibot.get_page(link)
        if content is not None:
            linked_content.append((link, content))

    
        
def main():
    database = Database()
    antibot = AntiBot()
    analyst = GeminiAnalyst()
    rss_processor = RssProcessor(database, antibot, analyst)
    
    rss_processor.fetch_processed()

if __name__ == "__main__":
    main()