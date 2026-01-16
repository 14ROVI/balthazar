import aiohttp
import asyncio
import re

from domain.post import Post
from strategy import Signal
from env import WEBHOOK_URL

class AlertSender:
    def __init__(self) -> None:
        """
        Initializes the AlertSender.
        """
        self.session = aiohttp.ClientSession()

    async def send_decision_alert(self, decision: Signal, post: Post):
        """
        Sends an alert to the webhook with the trading decision and source post.

        :param decision: The BUY or SELL signal from the Strategy module.
        :param post: The Post object that was the source of the latest signal.
        """
        
        # Function to wrap URLs in angle brackets to prevent Discord auto-embedding
        def suppress_urls_in_content(text: str) -> str:
            # Regex to find URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            # Wrap found URLs in < >
            return re.sub(url_pattern, r'<\g<0>>', text)

        sanitized_content = suppress_urls_in_content(post.content[:1000])

        # Formatting for the alert message
        content = (
            f"======================================================\n"
            f"**TRADING SIGNAL: {decision.name}**\n"
            f"======================================================\n"
            f">>> **Source**: <{post.url}>\n"
            f"**Content**: {sanitized_content}"
        )

        try:
            await self.session.post(
                WEBHOOK_URL,
                data={"content": content}
            )
            print(f"Sent alert for decision: {decision.name}")
        except Exception as e:
            print(f"Error sending alert: {e}")

    async def close(self):
        """Closes the aiohttp client session."""
        await self.session.close()