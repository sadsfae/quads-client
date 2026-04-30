import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class CommandHistory:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = "~/.config/quads/.quads-client-history.db"
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    server TEXT,
                    command TEXT NOT NULL,
                    success INTEGER NOT NULL
                )
                """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON command_history(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server ON command_history(server)")
            conn.commit()

    def add_command(self, command: str, server: Optional[str] = None, success: bool = True):
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO command_history (timestamp, server, command, success) VALUES (?, ?, ?, ?)",
                (timestamp, server, command, 1 if success else 0),
            )
            conn.commit()

    def get_recent_commands(self, limit: int = 100, server: Optional[str] = None) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if server:
                cursor = conn.execute(
                    "SELECT * FROM command_history WHERE server = ? ORDER BY timestamp DESC LIMIT ?",
                    (server, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM command_history ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def clear_history(self, server: Optional[str] = None):
        with sqlite3.connect(self.db_path) as conn:
            if server:
                conn.execute("DELETE FROM command_history WHERE server = ?", (server,))
            else:
                conn.execute("DELETE FROM command_history")
            conn.commit()
