from enum import Enum
from domain.rss_item import RssItem
from domain.intelligence import Intelligence
from typing import List
import orjson
import sqlite3
import time
from env import DB_NAME
from dataclasses import dataclass


@dataclass
class RssRow:
    source: str
    id: str
    added: int

@dataclass
class EventRow:
    id: int
    summary: str
    signal: int
    alerted: bool
    sources: List[str]
    added: int
    last_updated: int


class Database:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS rss (
                source TEXT,
                id TEXT,
                added DATETIME DEFAULT (unixepoch()),
                PRIMARY KEY (source, id)
            );
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                summary TEXT,
                signal INTEGER,
                alerted INTEGER DEFAULT FALSE,
                sources TEXT,
                added INTEGER DEFAULT (unixepoch()),
                last_updated DATETIME DEFAULT (unixepoch())
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_alert ON events (signal, alerted)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_last_updated ON events (last_updated)")

        self.conn.commit()


    ## RSS ITEMS

    def add_rss_item(self, source: str, id: str):
        c = self.conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO rss (source, id)
            VALUES (?, ?)""",
            (source, id)
        )
        self.conn.commit()
        
    def has_rss_item(self, source: str, id: str) -> bool:
        c = self.conn.cursor()
        c.execute(
            "SELECT source, id FROM rss_items WHERE source = ? AND id = ?",
            (source, id)
        )
        return c.fetchone() is not None

    
    ## EVENTS
        
    def add_event(self, summary: str, signal: int, sources: List[str]):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO events (summary, signal, sources) VALUES (?, ?, ?)",
            (summary, signal, orjson.dumps(sources))
        )
        self.conn.commit()
        
    def update_event_summary(self, id: int, summary: str):
        c = self.conn.cursor()
        c.execute(
            "UPDATE events SET summary = ? WHERE id = ?",
            (summary, id)
        )
        self.conn.commit()
        
    def add_event_sources(self, id: int, sources: List[str]):
        c = self.conn.cursor()
        c.execute(
            "SELECT sources FROM events WHERE id = ?",
            (id, )
        )
        data = c.fetchone()
        if data is None: return
        
        new_sources = orjson.loads(data["sources"]) + sources
        
        c.execute(
            "UPDATE events SET sources = ?, last_updated = ? WHERE id = ?",
            (orjson.dumps(new_sources), int(time.time()), id)
        )
        
        self.conn.commit()
        
    def get_alertable_events(self, min_signal: int) -> List[EventRow]:
        c = self.conn.cursor()
        c.execute("""
            SELECT *
            FROM events
            WHERE signal > ? AND alerted = FALSE""",
            (min_signal, )
        )
        
        return [_to_event_row(row) for row in c.fetchall()]
        
    def set_event_alerted(self, id: int, alerted: bool = True):
        c = self.conn.cursor()
        c.execute(
            "UPDATE events SET alerted = ? WHERE id = ?",
            (alerted, id)
        )
        self.conn.commit()

    def get_recent_events(self, min_timestamp: int) -> List[EventRow]:
        c = self.conn.cursor()
        c.execute("""
            SELECT *
            FROM events
            WHERE last_updated > ?
            ORDER BY last_updated DESC""",
            (min_timestamp, )
        )
        
        return [_to_event_row(row) for row in c.fetchall()]

    
def _to_event_row(row: sqlite3.Row) -> EventRow:
    return EventRow(
        row["id"],
        row["summary"],
        row["signal"],
        row["alerted"],
        orjson.loads(row["sources"]),
        row["added"],
        row["last_updated"],
    )