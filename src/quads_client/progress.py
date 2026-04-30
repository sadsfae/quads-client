from datetime import datetime
from typing import Any, Optional


class ProgressTracker:
    def __init__(self):
        self._active_moves: dict[str, dict[str, Any]] = {}

    def add_move(self, host: str, cloud: str, start_time: Optional[datetime] = None):
        if start_time is None:
            start_time = datetime.now()
        self._active_moves[host] = {
            "cloud": cloud,
            "start_time": start_time,
            "status": "pending",
            "progress": 0,
        }

    def update_progress(self, host: str, progress: int, status: str = "in_progress"):
        if host in self._active_moves:
            self._active_moves[host]["progress"] = min(100, max(0, progress))
            self._active_moves[host]["status"] = status

    def complete_move(self, host: str, success: bool = True):
        if host in self._active_moves:
            self._active_moves[host]["status"] = "completed" if success else "failed"
            self._active_moves[host]["progress"] = 100 if success else self._active_moves[host]["progress"]

    def remove_move(self, host: str):
        self._active_moves.pop(host, None)

    def get_move_status(self, host: str) -> Optional[dict[str, Any]]:
        return self._active_moves.get(host)

    def get_all_active_moves(self) -> dict[str, dict[str, Any]]:
        return self._active_moves.copy()

    def clear_completed(self):
        self._active_moves = {
            host: info for host, info in self._active_moves.items() if info["status"] not in ("completed", "failed")
        }

    def format_progress_bar(self, host: str, width: int = 40) -> str:
        if host not in self._active_moves:
            return ""

        progress = self._active_moves[host]["progress"]
        filled = int(width * progress / 100)
        bar = "#" * filled + "-" * (width - filled)
        return f"[{bar}] {progress}%"
