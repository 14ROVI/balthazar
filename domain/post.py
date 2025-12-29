from dataclasses import dataclass
from typing import List

@dataclass
class Post:
    url: str
    author_display_name: str
    author_id: str
    content: str
    links: List[str]
    