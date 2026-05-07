"""Multi-server session management for QUADS Client"""

from datetime import datetime
from typing import Dict, Optional

from quads_client.connection import ConnectionManager
from quads_client.config import QuadsClientConfig


class Session:
    """Represents a server connection session"""

    def __init__(self, session_id: str, server_name: str, connection: ConnectionManager, label: str = None):
        self.id = session_id
        self.server_name = server_name
        self.connection = connection
        self.label = label or server_name
        self.created_at = datetime.now()
        self.last_active = datetime.now()

    def get_version(self) -> str:
        """Get QUADS server version from connection"""
        if not self.connection.is_connected:
            return "N/A"

        try:
            version_info = self.connection.api.get_version()

            if isinstance(version_info, dict):
                version = version_info.get("version", "N/A")
                return version if version else "N/A"
            elif isinstance(version_info, str):
                import re

                version_match = re.search(r"(\d+\.\d+\.\d+)", version_info)
                return version_match.group(1) if version_match else version_info
        except Exception:
            return "N/A"

        return "N/A"


class SessionManager:
    """Manages multiple server connection sessions"""

    def __init__(self, config: QuadsClientConfig):
        self.config = config
        self.sessions: Dict[str, Session] = {}
        self.active_session_id: Optional[str] = None
        self._previous_session_id: Optional[str] = None
        self._next_session_num = 1

    @property
    def active_connection(self) -> Optional[ConnectionManager]:
        """Returns ConnectionManager of active session (exposed as shell.connection)"""
        if self.active_session_id and self.active_session_id in self.sessions:
            return self.sessions[self.active_session_id].connection
        return None

    @property
    def active_session(self) -> Optional[Session]:
        """Returns the active Session object"""
        if self.active_session_id and self.active_session_id in self.sessions:
            return self.sessions[self.active_session_id]
        return None

    @property
    def previous_session_id(self) -> Optional[str]:
        """Returns the previous session ID for toggle functionality"""
        return self._previous_session_id

    def create_session(self, server_name: str, label: str = None) -> Session:
        """Create new session with connection to server"""
        session_id = str(self._next_session_num)
        self._next_session_num += 1

        connection = ConnectionManager(self.config)
        session = Session(session_id, server_name, connection, label)
        self.sessions[session_id] = session

        # Track previous session before switching
        self._previous_session_id = self.active_session_id
        self.active_session_id = session_id
        return session

    def switch_session(self, session_id: str):
        """Switch active session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        # Track previous session before switching
        self._previous_session_id = self.active_session_id
        self.active_session_id = session_id
        self.sessions[session_id].last_active = datetime.now()

    def close_session(self, session_id: str):
        """Close and remove session"""
        if session_id in self.sessions:
            self.sessions[session_id].connection.disconnect()
            del self.sessions[session_id]
            if self.active_session_id == session_id:
                # Switch to another session or None
                self.active_session_id = next(iter(self.sessions), None)

    def close_all_inactive(self):
        """Close all sessions except the active one"""
        if not self.active_session_id:
            return 0

        inactive_ids = [sid for sid in self.sessions.keys() if sid != self.active_session_id]
        for sid in inactive_ids:
            self.close_session(sid)
        return len(inactive_ids)

    def list_sessions(self) -> list[Session]:
        """Return list of all sessions ordered by ID"""
        return sorted(self.sessions.values(), key=lambda s: int(s.id))

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_session_by_label(self, label: str) -> Optional[Session]:
        """Get session by label"""
        for session in self.sessions.values():
            if session.label == label:
                return session
        return None
