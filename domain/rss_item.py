from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class RssItem:
    url: str
    title: str
    content: str
    links: List[str]
    added: datetime | None
    processed: datetime | None
