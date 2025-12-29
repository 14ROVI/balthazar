from mastodon import Mastodon, StreamListener
from queue import SimpleQueue
from domain.post import Post
from html_to_markdown import convert
import time
from bs4 import BeautifulSoup
from env import MASTODON_ACCESS_TOKEN


class MastodonClient:
    def __init__(self, queue: SimpleQueue[Post]) -> None:
        self.queue = queue
        self.client = Mastodon(
            access_token=MASTODON_ACCESS_TOKEN,
            api_base_url="https://mastodon.social"
        )
        
    def listen(self):
        print("Listening to mastodon")
        
        while True:
            try:
                self.client.stream_public(MastodonListener(self.queue))
            except Exception as e:
                print(f"Mastodon stream died: {e}. Restarting in 5s...")
                time.sleep(5)
        

class MastodonListener(StreamListener):
    def __init__(self, queue: SimpleQueue[Post]) -> None:
        super().__init__()
        self.queue = queue
        
    def on_update(self, status):
        content = status["content"]
        
        external_links = []
        soup = BeautifulSoup(content, "html.parser")
        for a in soup.find_all("a", href=True):
            classes = a.get("class") or []
            if "mention" not in classes and "hashtag" not in classes:
                link = a["href"]
                if link not in external_links:
                    external_links.append(link)
            
        post = Post(
            status.uri,
            status["account"]["acct"],
            status["account"]["display_name"],
            convert(content),
            external_links
        )
        # print(status["account"])
        self.queue.put(post)


def main():
    client = MastodonClient(SimpleQueue())
    client.listen()
    

if __name__ == "__main__":
    main()