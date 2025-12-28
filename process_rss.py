from db import Database
from trance import AntiBot
from ai_engine import GeminiAnalyst
from heuristics import is_obvious_noise
import orjson

class RssProcessor:
    def __init__(self, db: Database, antibot: AntiBot, analyst: GeminiAnalyst) -> None:
        self.db = db
        self.antibot = antibot
        self.analyst = analyst

    def process(self):
        to_process = self.db.get_processable_rss()
        
        for item in to_process:
            self._process_item(item)
            
    def _process_item(self, item):
        try:
            print(f"Starting to process {item['id']}")
            
            links = orjson.loads(item["links"])
            url = item["id"] if item["id"].startswith("http") else links[0]
            
            if is_obvious_noise(item["title"], url):
                self.db.set_rss_processed(item["source"], item["id"])
                return
            
            linked_content = []
            for link in links:
                if not is_obvious_noise(item["title"], link):
                    linked_content.append(self.antibot.get_page(link))

            analysis = self.analyst.analyze(
                item["title"], 
                item["summary"], 
                "--- MORE LINKED CONTENT ---\n".join(linked_content)
            )
            
            if analysis is None:
                raise Exception("Analysis not found")
            
            self.db.set_rss_processed(item["source"], item["id"])
            self.db.save_intelligence(
                url,
                url,
                analysis.summary,
                analysis.signal,
                analysis.financial,
                analysis.alertable,
                False
            )
            
            print(f"Signal: {analysis.signal} | Financial: {analysis.financial} | Alertable: {analysis.alertable}")
            print(f"Summary: {analysis.summary}\n")
            
        except Exception as e:
            print(f"Failed to process {item['id']} with exception: {e}")
    
        
def main():
    database = Database()
    antibot = AntiBot()
    analyst = GeminiAnalyst()
    rss_processor = RssProcessor(database, antibot, analyst)
    
    rss_processor.process()

if __name__ == "__main__":
    main()