import asyncio
import orjson
import websockets

uri = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

LISTEN_TO = {
    "did:plc:6ofscwmf6hva6ega2a5jirq7", # hunterbrook media
    "did:plc:sb54dpdfefflykmf5bcfvr7t", # bellingcat
    "did:plc:oaektkwkglhxs2zlts4nzuvr", # shayan86.bsky.social
    "did:plc:c6hdm36q5qqcf5puaao3v33m", # acleddata.bsky.social
    "did:plc:uewxgchsjy4kmtu7dcxa77us", # bloomberg
    "did:plc:xraomsuf6pvh7r2cqtdwhkvm", # swiftonsecurity.com
    "did:plc:anssft5emdfb2sjnjyeqnprh", # alisonkilling.bsky.social
    "did:plc:73234535z57357466535", # FT
    "did:plc:idwhjzs5boatwv4zxwwcjk5i", # malwaretech.com
}

async def listen_to_websocket():
  async with websockets.connect(uri) as websocket:
      async for message in websocket:
        message = await websocket.recv()
        data = orjson.loads(message)
            
        if data["did"] in LISTEN_TO:
            print(data)

if __name__ == "__main__":
    asyncio.run(listen_to_websocket())
