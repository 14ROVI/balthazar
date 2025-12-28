import feedparser
from db import Database
from trance import AntiBot

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
    "http://export.arxiv.org/rss/cs.AI",
    
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
    def __init__(self, db: Database, antibot: AntiBot) -> None:
        self.db = db
        self.antibot = antibot

    def fetch_updates(self):
        for url in RSS_FEEDS:
            self._process(url)

    def _process(self, url: str):
        rss_data = self.antibot.get_rss_content(url)
        
        if rss_data is None: return
        
        feed = feedparser.parse(rss_data)
        
        print(f"Found {len(feed.entries)} entries in {url}:")
        
        for entry in feed.entries:
            links = [l.href for l in entry.links]
            self.db.add_rss_item(url, entry.id, entry.title, entry.summary, links) # type: ignore
            print(f"""id: {entry.id} link: {entry.link}\n{entry.title}\n{entry.summary}\n""")
            
        print("\n"*3)
        
            
def main():
    database = Database()
    antibot = AntiBot()
    rss_fetcher = RssFetcher(database, antibot)
    rss_fetcher.fetch_updates()

if __name__ == "__main__":
    main()
