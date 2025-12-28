from db import Database
from rss import RssFetcher
from trance import AntiBot
from alert import AlertSender
from ai_engine import GeminiAnalyst
from process_rss import RssProcessor

import threading
import time
import sys

FETCH_INTERVAL = 5 * 60
PROCESS_INTERVAL = 30
ALERT_INTERVAL = 30

def fetcher_loop():
    db = Database()
    antibot = AntiBot()
    fetcher = RssFetcher(db, antibot)
    
    while True:
        try:
            fetcher.fetch_updates()
        except Exception as e:
            print(f"❌ [Fetcher Error]: {e}")
        
        time.sleep(FETCH_INTERVAL)
        
def processor_loop():
    database = Database()
    antibot = AntiBot()
    analyst = GeminiAnalyst()
    rss_processor = RssProcessor(database, antibot, analyst)
    
    while True:
        try:
            rss_processor.process()
        except Exception as e:
            print(f"❌ [Processor Error]: {e}")
        
        time.sleep(PROCESS_INTERVAL)
        
def alerter_loop():
    database = Database()
    alert_sender = AlertSender(database)
    
    while True:
        try:
            alert_sender.send_alerts()
        except Exception as e:
            print(f"❌ [Alerter Error]: {e}")
        
        time.sleep(ALERT_INTERVAL)

def main():
    t_fetch = threading.Thread(target=fetcher_loop, name="Fetcher", daemon=True)
    t_process = threading.Thread(target=processor_loop, name="Processor", daemon=True)
    t_alert = threading.Thread(target=alerter_loop, name="Alerter", daemon=True)

    t_fetch.start()
    t_process.start()
    t_alert.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down pipeline...")
        sys.exit(0)


if __name__ == "__main__":
    main()