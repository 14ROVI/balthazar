from enum import Enum
from typing import List
import orjson
import sqlite3
from env import DB_NAME

class Status(Enum):
    UNPROCESSED = 0
    PROCESSED = 1


class Database:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        
        c = self.conn.cursor()
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS rss_to_process (
                source TEXT,
                id TEXT,
                title TEXT,
                summary TEXT,
                links TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source, id)
            )
        """)
        
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS processed_rss (
                source TEXT,
                id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source, id)
            )
        """)
        
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS external_pages_to_process (
                url TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS intelligence (
                id TEXT PRIMARY KEY,
                url TEXT,
                summary TEXT,
                signal INTEGER,
                financial INTEGER,
                alertable INTEGER,
                alerted INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_rss_item(self, source: str, id: str, title: str, summary: str, links: List[str]):
        c = self.conn.cursor()
        c.execute("SELECT * FROM processed_rss WHERE source=? AND id=?", (source, id))
        processed = c.fetchone()
        if processed is not None:
            c.execute("""
                INSERT OR IGNORE INTO rss_to_process (source, id, title, summary, links)
                VALUES (?, ?, ?, ?, ?)""",
                (source, id, title, summary, orjson.dumps(links))
            )
        else:
            print(f"Skipped {source} {id}")
        self.conn.commit()
        
    def get_processable_rss(self):
        c = self.conn.cursor()
        c.execute("SELECT source, id, title, summary, links FROM rss_to_process WHERE (source, id) NOT IN (SELECT source, id FROM processed_rss)")
        data = c.fetchall()
        self.conn.commit()
        
        return data

    def set_rss_processed(self, source: str, id: str):
        c = self.conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO processed_rss (source, id) VALUES (?, ?)",
            (source, id)
        )
        self.conn.commit()
        
        
    def save_intelligence(self, id: str, url: str, summary: str, signal: int, financial: bool, alertable: bool, alerted: bool):
        c = self.conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO intelligence (id, url, summary, signal, financial, alertable, alerted)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (id, url, summary, signal, financial, alertable, alerted)
            )
        self.conn.commit()
        

    def get_alertable_intelligence(self):
        c = self.conn.cursor()
        c.execute("SELECT id, url, summary, signal FROM intelligence WHERE alertable = TRUE AND alerted = FALSE")
        data = c.fetchall()
        self.conn.commit()
        
        return data

    def set_intelligence_alerted(self, id: str):
        c = self.conn.cursor()
        c.execute(
            "UPDATE intelligence SET alerted = TRUE WHERE id = ?",
            (id, )
        )
        self.conn.commit()
        
