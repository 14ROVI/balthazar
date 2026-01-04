import aiohttp
import asyncio

from db import Database
from env import WEBHOOK_URL

MIN_SIGNAL = 5

class AlertSender:
    def __init__(self, db: Database) -> None:
        self.db = db
    
    async def send_alerts(self):
        items = self.db.get_alertable_events(MIN_SIGNAL)
        async with aiohttp.ClientSession() as session:
            for item in items:
                await session.post(
                    WEBHOOK_URL,
                    data = {
                        "content": f"<@195512978634833920> signal: {item.signal} | id: {item.id}\nsummary: {item.summary}\nsources: {'\n'.join(item.sources)}"
                    }
                )
                self.db.set_event_alerted(item.id)
                print(f"Sent alert for: {item.id}")


async def main():
    database = Database()
    alert_sender = AlertSender(database)
    await alert_sender.send_alerts()
    
if __name__ == "__main__":
    asyncio.run(main())