from typing import List
import orjson
import sqlite3
import importlib.resources
import numpy as np
from numpy import float64
from numpy.typing import NDArray
import time
from env import DB_NAME, GEMINI_EMBEDDING_LENGTH
from dataclasses import dataclass


@dataclass
class RssRow:
    source: str
    id: str
    added: int

@dataclass
class IntelligenceRow:
    rowid: int
    url: str
    content: str
    embedding: NDArray[float64]
    event: int | None

@dataclass
class EventRow:
    id: int
    summary: str
    embedding: NDArray[float64]
    signal: int
    alerted: bool
    added: int
    last_updated: int


class Database:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row

        vector_ext_path = importlib.resources.files("sqlite_vector.binaries") / "vector"
        self.conn.enable_load_extension(True)
        self.conn.load_extension(str(vector_ext_path))
        self.conn.enable_load_extension(False)
        
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
            CREATE TABLE IF NOT EXISTS intelligence (
                url TEXT PRIMARY KEY,
                content TEXT,
                embedding BLOB,
                event INTEGER,
                added INTEGER DEFAULT (unixepoch()),
                last_updated DATETIME DEFAULT (unixepoch())
            )
        """)
        c.execute(f"SELECT vector_init('intelligence', 'embedding', 'dimension={GEMINI_EMBEDDING_LENGTH},type=FLOAT32,distance=cosine')")

        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                summary TEXT,
                embedding BLOB,
                signal INTEGER,
                alerted INTEGER DEFAULT FALSE,
                added INTEGER DEFAULT (unixepoch()),
                last_updated DATETIME DEFAULT (unixepoch())
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_alert ON events (signal, alerted)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_last_updated ON events (last_updated)")
        c.execute(f"SELECT vector_init('events', 'embedding', 'dimension={GEMINI_EMBEDDING_LENGTH},type=FLOAT32,distance=cosine')")

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
            "SELECT EXISTS(SELECT 1 FROM rss WHERE source = ? AND id = ? LIMIT 1)",
            (source, id)
        )
        return bool(c.fetchone()[0])
    

    ## RSS ITEMS

    def add_intelligence(self, url: str, content: str, embedding: NDArray[float64]):
        c = self.conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO intelligence (url, content, embedding)
            VALUES (?, ?, vector_as_f32(?))""",
            (url, content, embedding.astype('float32').tobytes())
        )
        self.conn.commit()

    def set_intelligence_event(self, url: str, event_id: int):
        c = self.conn.cursor()
        c.execute(
            "UPDATE intelligence SET event = ? WHERE url = ?",
            (event_id, url)
        )
        self.conn.commit()

    def get_event_intelligence(self, event_id: int) -> List[IntelligenceRow]:
        c = self.conn.cursor()
        c.execute(
            "SELECT rowid, * FROM intelligence WHERE event = ?",
            (event_id, )
        )
        
        return [_to_intelligence_row(row) for row in c.fetchall()]
        
    def get_all_embeddings(self) -> List[IntelligenceRow]:
        c = self.conn.cursor()
        c.execute("SELECT rowid, * FROM intelligence")
        return [_to_intelligence_row(row) for row in c.fetchall()]
    
    def get_closest_intelligence(self, embedding: NDArray[float64], amount: float, min_timestamp: int) -> List[tuple[IntelligenceRow, float]]:
        c = self.conn.cursor()
        c.execute("""
            SELECT
                intelligence.rowid,
                intelligence.*,
                v.distance
            FROM vector_full_scan('intelligence', 'embedding', vector_as_f32(?), ?) as v
            JOIN intelligence ON intelligence.rowid = v.rowid
            WHERE intelligence.last_updated > ?
            """,
            (embedding.astype('float32').tobytes(), amount, min_timestamp)
        )
        return [(_to_intelligence_row(row), row["distance"]) for row in c.fetchall()]

    
    ## EVENTS
        
    def add_event(self, summary: str, signal: int, embedding: NDArray[float64]):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO events (summary, signal, embedding) VALUES (?, ?, vector_as_f32(?)) RETURNING *",
            (summary, signal, embedding.astype('float32').tobytes())
        )
        row = _to_event_row(c.fetchone())
        self.conn.commit()
        return row
        
    def update_event_summary(self, id: int, summary: str):
        c = self.conn.cursor()
        c.execute(
            "UPDATE events SET summary = ? WHERE id = ?",
            (summary, id)
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
    
    def get_closest_events(self, embedding: NDArray[float64], amount: int) -> List[tuple[EventRow, float]]:
        c = self.conn.cursor()
        c.execute("""
            SELECT
                events.*,
                v.distance
            FROM vector_full_scan('events', 'embedding', vector_as_f32(?), ?) as v
            JOIN events ON events.rowid = v.rowid
            """,
            (embedding.astype('float32').tobytes(), amount)
        )

        return [(_to_event_row(row), row["distance"]) for row in c.fetchall()]
    
    def clear_events(self):
        c = self.conn.cursor()
        c.execute("DELETE FROM events WHERE 1=1")
        c.execute("UPDATE intelligence SET event = NULL WHERE 1=1")
        self.conn.commit()


def _to_intelligence_row(row: sqlite3.Row) -> IntelligenceRow:
    return IntelligenceRow(
        row["rowid"],
        row["url"],
        row["content"],
        np.frombuffer(row["embedding"], dtype=float64),
        row["event"]
    )
    
def _to_event_row(row: sqlite3.Row) -> EventRow:
    return EventRow(
        row["id"],
        row["summary"],
        np.frombuffer(row["embedding"], dtype=float64),
        row["signal"],
        row["alerted"],
        row["added"],
        row["last_updated"],
    )