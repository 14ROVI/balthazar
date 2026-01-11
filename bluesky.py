from domain.post import Post
from typing import List

import asyncio
import orjson
import websockets

BLUESKY_WEBSOCKET = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

def extract_links(data) -> List[str]:
    links = []
    
    try:
        facets = data["commit"]["record"]["facets"]
    except:
        return []
    
    for facet in facets:
        for feature in facet["features"]:
            if feature["$type"] == "app.bsky.richtext.facet#link":
                links.append(feature["uri"])
                
    return links

class BlueskyClient:
    def __init__(self, queue: asyncio.Queue[Post]) -> None:
        self.queue = queue
        
    async def listen(self):
        async with websockets.connect(BLUESKY_WEBSOCKET) as websocket:
            async for message in websocket:
                message = await websocket.recv()
                data = orjson.loads(message)
                
                links = extract_links(data)
                
                try:
                    if data["commit"]["operation"] != "create":
                        continue
                    if "reply" in data["commit"]["record"]:
                        continue
                    
                    did = data["did"]
                    rkey = data["commit"]["rkey"]
                    
                    post = Post(
                        f"https://bsky.app/profile/{did}/post/{rkey}",
                        did,
                        data["commit"]["record"]["text"],
                        links
                    )
                    
                    await self.queue.put(post)
                except:
                    continue
