from db import Database
from ai_engine import GeminiAnalyst
from domain.post import Post
from heuristics import should_process_post

import asyncio
import time
from typing import List

RECENT_EVENT_DELTA = 24 * 60 * 60  # 24 hours in seconds

class PostProcessor:
    def __init__(self, db: Database, analyst: GeminiAnalyst, queue: asyncio.Queue[Post]) -> None:
        self.db = db
        self.analyst = analyst
        self.queue = queue
        self.buffer: List[Post] = []
        
    async def process_queue(self):
        while post := await self.queue.get():
            if should_process_post(post):
                self.buffer.append(post)
                
                if len(self.buffer) >= 10:
                    await self._process_buffer()
            
    async def _process_buffer(self):
        min_timestamp = int(time.time()) - RECENT_EVENT_DELTA
        current_events = self.db.get_recent_events(min_timestamp)[:10]
        
        analysis = await self.analyst.analyze_posts(current_events, self.buffer)
        if analysis is None: return
        
        for new_event in analysis.new_events:
            self.db.add_event(
                new_event.summary,
                new_event.signal,
                new_event.sources
            )
            print(f"[New Event] Signal: {new_event.signal}\nSummary: {new_event.summary}\nSources: {new_event.sources}")
            
        for updated_summary in analysis.updated_summaries:
            self.db.update_event_summary(
                updated_summary.id,
                updated_summary.summary
            )
            self.db.set_event_alerted(updated_summary.id, alerted=False)
            print(f"[Updated Summary] ID: {updated_summary.id}\nNew Summary: {updated_summary.summary}")
            
        for updated_sources in analysis.updated_sources:
            self.db.add_event_sources(
                updated_sources.id,
                updated_sources.sources
            )
            print(f"[Updated Sources] ID: {updated_sources.id}\nNew Sources: {updated_sources.sources}")
            
        self.buffer = []


async def main():
    database = Database()
    queue = asyncio.Queue()
    analyst = GeminiAnalyst()
    processor = PostProcessor(database, analyst, queue)
    
    await processor.process_queue()

if __name__ == "__main__":
    asyncio.run(main())
