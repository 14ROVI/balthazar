from dataclasses import dataclass
from datetime import datetime

@dataclass
class Intelligence:
    url: str
    summary: str
    signal: int
    alerted: bool
    added: datetime | None
