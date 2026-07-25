import sqlite3
import re
import time
from dataclasses import dataclass, field
from typing import Optional


WIKILINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")


@dataclass
class Note:
    id: Optional[int]
    title: str
    content: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 220.0
    height: float = 140.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class Database:
    def __init__(self, path: str = "notes.db"):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                x REAL NOT NULL DEFAULT 0,
                y REAL NOT NULL DEFAULT 0,
                width REAL NOT NULL DEFAULT 220,
                height REAL NOT NULL DEFAULT 140,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
                target_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
                created_at REAL NOT NULL,
                UNIQUE(source_id, target_id)
            );
            """
        )
        self.conn.commit()

                                             
    def create_note(self, title: str, content: str = "", x: float = 0, y: float = 0) -> Note:
        now = time.time()
        cur = self.conn.execute(
            "INSERT INTO notes (title, content, x, y, width, height, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 220, 140, ?, ?)",
            (title, content, x, y, now, now),
        )
        self.conn.commit()
        note = Note(id=cur.lastrowid, title=title, content=content, x=x, y=y,
                     created_at=now, updated_at=now)
        self.sync_links_for_note(note.id)
        return note

    def get_note(self, note_id: int) -> Optional[Note]:
        row = self.conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return self._row_to_note(row) if row else None

    def get_note_by_title(self, title: str) -> Optional[Note]:
        row = self.conn.execute(
            "SELECT * FROM notes WHERE title = ? COLLATE NOCASE", (title,)
        ).fetchone()
        return self._row_to_note(row) if row else None

    def all_notes(self) -> list[Note]:
        rows = self.conn.execute("SELECT * FROM notes ORDER BY id").fetchall()
        return [self._row_to_note(r) for r in rows]

    def update_note_content(self, note_id: int, title: str, content: str):
        now = time.time()
        self.conn.execute(
            "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
            (title, content, now, note_id),
        )
        self.conn.commit()
        self.sync_links_for_note(note_id)

    def update_note_position(self, note_id: int, x: float, y: float):
        self.conn.execute(
            "UPDATE notes SET x = ?, y = ?, updated_at = ? WHERE id = ?",
            (x, y, time.time(), note_id),
        )
        self.conn.commit()

    def update_note_size(self, note_id: int, width: float, height: float):
        self.conn.execute(
            "UPDATE notes SET width = ?, height = ? WHERE id = ?",
            (width, height, note_id),
        )
        self.conn.commit()

    def delete_note(self, note_id: int):
        self.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()

                                                         
    def sync_links_for_note(self, note_id: int):
        note = self.get_note(note_id)
        if note is None:
            return

        titles = WIKILINK_PATTERN.findall(note.content)
        target_ids = set()
        for t in titles:
            t = t.strip()
            if not t:
                continue
            target = self.get_note_by_title(t)
            if target is None:
                                                                                   
                target = self.create_note(t, "", x=note.x + 260, y=note.y)
            if target.id != note_id:
                target_ids.add(target.id)

        self.conn.execute("DELETE FROM links WHERE source_id = ?", (note_id,))
        now = time.time()
        for tid in target_ids:
            self.conn.execute(
                "INSERT OR IGNORE INTO links (source_id, target_id, created_at) VALUES (?, ?, ?)",
                (note_id, tid, now),
            )
        self.conn.commit()

    def outgoing_links(self, note_id: int) -> list[Note]:
        rows = self.conn.execute(
            "SELECT notes.* FROM links JOIN notes ON notes.id = links.target_id "
            "WHERE links.source_id = ?",
            (note_id,),
        ).fetchall()
        return [self._row_to_note(r) for r in rows]

    def backlinks(self, note_id: int) -> list[Note]:
        rows = self.conn.execute(
            "SELECT notes.* FROM links JOIN notes ON notes.id = links.source_id "
            "WHERE links.target_id = ?",
            (note_id,),
        ).fetchall()
        return [self._row_to_note(r) for r in rows]

    def all_links(self) -> list[tuple[int, int]]:
        rows = self.conn.execute("SELECT source_id, target_id FROM links").fetchall()
        return [(r["source_id"], r["target_id"]) for r in rows]

                                               
    @staticmethod
    def _row_to_note(row: sqlite3.Row) -> Note:
        return Note(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            x=row["x"],
            y=row["y"],
            width=row["width"],
            height=row["height"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def close(self):
        self.conn.close()
