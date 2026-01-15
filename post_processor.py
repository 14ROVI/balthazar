import time
from db import Database
from ai_engine import GeminiAnalyst
from domain.post import Post
from heuristics import should_process_post
from vectors import get_signal_probability

import re
import asyncio
import joblib
from numpy import float64
from numpy.typing import NDArray
from typing import List

RECENT_EVENT_DELTA = 24 * 60 * 60  # 24 hours in seconds

class PostProcessor:
    def __init__(self, db: Database, analyst: GeminiAnalyst, queue: asyncio.Queue[Post]) -> None:
        self.db = db
        self.analyst = analyst
        self.queue = queue
        self.buffer: List[Post] = []
        self.high_signal_anchors: List[NDArray[float64]] = joblib.load("high_signal_anchors.pkl")
        self.low_signal_anchors: List[NDArray[float64]] = joblib.load("low_signal_anchors.pkl")
        
    async def process_queue(self):
        while post := await self.queue.get():
            if should_process_post(post):
                await self._process_post(post)

    async def _process_post(self, post: Post):
        embedding = await self.analyst.get_embedding(post)

        # summary_res = await self.analyst.summarise_post(clean_content)
        # if summary_res is None or summary_res.summary == "": return
        # print("------------")
        # print(summary_res)
        
        if embedding is None: return

        self.db.add_intelligence(post.url, post.content, embedding)

        # signal = get_signal_probability(embedding, self.high_signal_anchors, self.low_signal_anchors)

        # if summary_res.signal >= 7:
        #     min_timestamp = time.time() - 60*60*24 # only within last day
        #     closest_intelligence = (self.db.get_closest_intelligence(embedding, 1, min_timestamp) or [None])[0]
        #     self.db.add_intelligence(post.url, summary_res.summary, embedding)

        #     if closest_intelligence is None or closest_intelligence[1] > 0.15:
        #         # far away, make a new event!
        #         # signal = int(round(((signal[0] - 0.8) * 2 + 0.6) * 10))
        #         print(f"Making new event of signal {summary_res.signal}")
        #         event = self.db.add_event(summary_res.summary, summary_res.signal, embedding)
        #         self.db.set_intelligence_event(post.url, event.id)
        #     else:
        #         # get event that that intelligence is a part of or if it doesnt have one, make one!
        #         if (event := closest_intelligence[0].event) is not None:
        #             print(f"hit event similar {event}")
        #             self.db.set_intelligence_event(post.url, event)
        #         else:
        #             print(f"Creating new event (signal {summary_res.signal}) with {closest_intelligence[0].url}")
        #             event = self.db.add_event(summary_res.summary, summary_res.signal, embedding)
        #             self.db.set_intelligence_event(post.url, event.id)
        #             self.db.set_intelligence_event(closest_intelligence[0].url, event.id)
                 
                
                





async def main():
    database = Database()
    queue = asyncio.Queue()
    analyst = GeminiAnalyst()
    processor = PostProcessor(database, analyst, queue)

    await queue.put(Post(
        "N/A",
        "N/A",
        "i want to do a furry meetup with all my buddies from the clash raid!",
        # "U.S. Forces Capture Maduro and Wife in Caracas Raid",
        []
    ))
    
    await processor.process_queue()

if __name__ == "__main__":
    asyncio.run(main())