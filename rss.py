from db import Database
from trance import AntiBot
from ai_engine import GeminiAnalyst
from domain.post import Post

import asyncio
from asyncio import Queue
from html_to_markdown import convert
import feedparser
from feedparser import FeedParserDict
from abc import ABC, abstractmethod
from typing import Dict
import requests


class BaseRssAdapter(ABC):
    @abstractmethod
    async def get_rss_content(self, url: str) -> str | None:
        pass

class DefaultAdapter(BaseRssAdapter):
    def __init__(self, antibot: AntiBot) -> None:
        super().__init__()
        self.antibot = antibot

    async def get_rss_content(self, url: str) -> str | None:
        return await self.antibot.get_rss_content(url)

class SecAdapter(BaseRssAdapter):
    async def get_rss_content(self, url: str) -> str | None:
        try:
            r = requests.get(
                url, 
                headers={
                    "User-Agent": "Balthazar balthazar@gmail.com",
                    "Accept-Encoding": "gzip, deflate",
                    "Host": "www.sec.gov"
                }
            )
            return r.text
        except:
            return None


ADAPTERS: Dict[str, BaseRssAdapter] = {
    "https://www.sec.gov": SecAdapter()
}

RSS_FEEDS = [
    # congress.gov
    "https://www.congress.gov/rss/house-floor-today.xml",
    "https://www.congress.gov/rss/senate-floor-today.xml",
    "https://www.congress.gov/rss/presented-to-president.xml",
    
    # SEC
    "https://www.sec.gov/enforcement-litigation/litigation-releases/rss",
    "https://www.sec.gov/enforcement-litigation/administrative-proceedings/rss",
    "https://www.sec.gov/news/pressreleases.rss",
    "https://www.sec.gov/enforcement-litigation/trading-suspensions/rss",
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=40&output=atom",
    
    # State.gov
    "https://www.state.gov/rss-feed/press-releases/feed/",
    "https://www.state.gov/rss-feed/western-hemisphere/feed/",
    "https://www.state.gov/rss-feed/international-organizations/feed/",
    "https://www.state.gov/rss-feed/diplomatic-security/feed/",
    "https://www.state.gov/rss-feed/department-press-briefings/feed/",
    "https://www.state.gov/rss-feed/collected-department-releases/feed/",
    
    # hackernews
    "https://hnrss.org/newest",
    
    # cisa 
    "https://www.cisa.gov/uscert/ncas/alerts.xml",
    "https://www.cisa.gov/news.xml",
    
    # arxiv
    # "http://export.arxiv.org/rss/cs.AI",
    
    # department of justice
    "https://www.justice.gov/news/rss",
    
    # dowjones
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    
    # bloomberg
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.bloomberg.com/politics/news.rss",
    "https://feeds.bloomberg.com/technology/news.rss",
    "https://feeds.bloomberg.com/wealth/news.rss",
    
    # chief meta AI guy
    "https://yannlecum.com/feed/",
    
    # department of war
    "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=2&Site=945&max=10",
    "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?max=10&ContentType=1&Site=945",
    "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=9&Site=945&max=10",
    "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=400&Site=945&max=10",
    
    # gov uk
    "https://www.gov.uk/government/feed",
    "https://bills.parliament.uk/rss/allbills.rss",
    "https://www.ncsc.gov.uk/api/1/services/v1/news-rss-feed.xml",
    "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml",
    
    # donald trump truth social
    "https://trumpstruth.org/feed",
]

class RssFetcher:
    def __init__(self, db: Database, antibot: AntiBot, analyst: GeminiAnalyst, queue: Queue[Post]) -> None:
        self.db = db
        self.antibot = antibot
        self.analyst = analyst
        self.queue = queue

    async def fetch_updates(self):
        print("Starting fetch RSS")
        tasks = [self._process(url) for url in RSS_FEEDS]
        await asyncio.gather(*tasks)

    async def _process(self, source: str):

        rss_data = await self._get_adapter(source).get_rss_content(source)
        if rss_data is None: 
            print(f"Couldnt fetch {source}")
            return
        
        feed = feedparser.parse(rss_data)
        
        print(f"Found {len(feed.entries)} entries in {source}")

        for entry in feed.entries:
            entry_id: str = entry.id # type: ignore

            if self.db.has_rss_item(source, entry_id): continue

            links = [str(l.href) for l in entry.links]
            url = entry_id if entry_id.startswith("http") else (links[0] if links else "")
            string_content = await self.get_string_content(entry, url)

            await self.queue.put(Post(
                url,
                "N/A",
                string_content,
                links
            ))
            
            self.db.add_rss_item(source, entry_id)
    
    def _get_adapter(self, source: str) -> BaseRssAdapter:
        for host in ADAPTERS:
            if source.startswith(host):
                return ADAPTERS[host]
        return DefaultAdapter(self.antibot)

    async def get_string_content(self, entry: FeedParserDict, url: str) -> str:
        all_content = []
        
        if "summary" in entry:
            if entry.summary_detail.type == "text/html": # type: ignore
                all_content.append(convert(entry.summary_detail.value)) # type: ignore
            else:
                all_content.append(entry.summary_detail.value) # type: ignore
        
        if "content" in entry:
            for content_item in entry.content:
                if content_item.value != "" and content_item.value != entry.summary:
                    if content_item.type == "text/html":
                        all_content.append(convert(content_item.value)) # type: ignore
                    else:
                        all_content.append(content_item.value)

        page_content = await self.antibot.get_page(url)
        if page_content is not None:
            all_content.append(page_content)
        
        return "\n".join(all_content)
            
            
async def main():
    async with AntiBot() as antibot:
        database = Database()
        analyst = GeminiAnalyst()
        queue = Queue()
        rss_fetcher = RssFetcher(database, antibot, analyst, queue)
        await rss_fetcher.fetch_updates()

if __name__ == "__main__":
    asyncio.run(main())
