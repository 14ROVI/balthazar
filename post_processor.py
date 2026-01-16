from db import Database
from ai_engine import GeminiAnalyst
from domain.post import Post
from strategy import Strategy, Signal
from alert import AlertSender
from market_data import MarketDataProvider
import asyncio


class PostProcessor:
    def __init__(self, db: Database, analyst: GeminiAnalyst, market_provider: MarketDataProvider, queue: asyncio.Queue[Post]) -> None:
        self.db = db
        self.analyst = analyst
        self.queue = queue
        self.strategy = Strategy(market_provider=market_provider)
        self.alerter = AlertSender()
        
    async def process_queue(self):
        """
        Continuously processes posts from the queue, generates signals,
        logs them, and makes trading decisions.
        """
        while post := await self.queue.get():
            # 1. Generate embedding for the post content
            payload = f"Post by author {post.author_id}. Content: {post.content}"
            embedding = await self.analyst.get_embedding(payload)

            if embedding is None:
                continue

            # 2. Get the signal from the embedding
            initial_signal = self.analyst.get_signal_from_embedding(embedding)
            
            # 3. Log the signal to the database for future backtesting
            self.db.add_historical_signal(
                url=post.url,
                embedding=embedding,
                signal=initial_signal.name  # Store 'BUY', 'SELL', or 'HOLD'
            )

            # 4. Only consider BUY or SELL signals for the active strategy
            if initial_signal in [Signal.BUY, Signal.SELL]:
                print(f"Signal received: {initial_signal.name} | Post: {post.url}")

                self.strategy.add_signal(initial_signal, post)
                final_decision = self.strategy.decide()

                if final_decision != Signal.HOLD:
                    latest_post = self.strategy.recent_signals[-1]['post']
                    await self.alerter.send_decision_alert(final_decision, latest_post)
                    self.strategy.record_action(final_decision)