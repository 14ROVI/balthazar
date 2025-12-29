from db import Database
from queue import SimpleQueue
from ai_engine import GeminiAnalyst
from domain.post import Post
from heuristics import should_process_post


class PostProcessor:
    def __init__(self, db: Database, analyst: GeminiAnalyst, queue: SimpleQueue[Post]) -> None:
        self.db = db
        self.analyst = analyst
        self.queue = queue
        
    def process_queue(self):
        while post := self.queue.get(block=True):
            if should_process_post(post):
                self._process_post(post)
            
    def _process_post(self, post: Post):
        analysis = self.analyst.analyze_post(post)
        if analysis is None: return
        
        self.db.save_intelligence(
            post.url,
            post.url,
            analysis.summary,
            analysis.signal,
            analysis.financial,
            analysis.alertable,
            False
        )
        
        print(f"signal: {analysis.signal}\n{analysis.summary}\n{post}\n-------------------")
        # print(f"{post.author_display_name}\n{post.author_id}\n{post.content}\n------------------------")


def main():
    database = Database()
    queue = SimpleQueue()
    analyst = GeminiAnalyst()
    processor = PostProcessor(database, analyst, queue)
    
    processor.process_queue()

if __name__ == "__main__":
    main()
