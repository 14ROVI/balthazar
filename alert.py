import requests
from db import Database
from env import WEBHOOK_URL

class AlertSender:
    def __init__(self, db: Database) -> None:
        self.db = db
    
    def send_alerts(self):
        items = self.db.get_alertable_intelligence()
        for item in items:
            requests.post(
                WEBHOOK_URL,
                data = {
                    "content": f"<@195512978634833920> signal: {item['signal']} | id: {item['id']}\nsummary: {item['summary']}"
                }
            )
            self.db.set_intelligence_alerted(item["id"])
            print(f"Sent alert for: {item['id']}")


def main():
    database = Database()
    alert_sender = AlertSender(database)
    alert_sender.send_alerts()
    
if __name__ == "__main__":
    main()