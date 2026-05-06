"""Comprehensive tests for session_manager.py"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from quads_client.session_manager import Session, SessionManager


class TestSession:
    """Test Session class"""

    def test_session_initialization(self, mock_config):
        """Test Session object initialization"""
        from quads_client.connection import ConnectionManager

        conn = MagicMock(spec=ConnectionManager)
        session = Session("1", "test_server", conn, "dev")

        assert session.id == "1"
        assert session.server_name == "test_server"
        assert session.connection == conn
        assert session.label == "dev"
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_active, datetime)

    def test_session_default_label(self, mock_config):
        """Test Session uses server_name as default label"""
        conn = MagicMock()
        session = Session("1", "test_server", conn)

        assert session.label == "test_server"

    def test_get_version_connected(self, mock_config):
        """Test get_version when connected with dict response"""
        conn = MagicMock()
        conn.is_connected = True
        conn.api.get_version.return_value = {"version": "2.2.6"}

        session = Session("1", "test_server", conn)
        version = session.get_version()

        assert version == "2.2.6"

    def test_get_version_string_response(self, mock_config):
        """Test get_version with string response containing version"""
        conn = MagicMock()
        conn.is_connected = True
        conn.api.get_version.return_value = "QUADS version 2.2.6"

        session = Session("1", "test_server", conn)
        version = session.get_version()

        assert version == "2.2.6"

    def test_get_version_string_response_no_match(self, mock_config):
        """Test get_version with string that has no version pattern"""
        conn = MagicMock()
        conn.is_connected = True
        conn.api.get_version.return_value = "invalid response"

        session = Session("1", "test_server", conn)
        version = session.get_version()

        assert version == "invalid response"

    def test_get_version_dict_no_version_key(self, mock_config):
        """Test get_version with dict but no version key"""
        conn = MagicMock()
        conn.is_connected = True
        conn.api.get_version.return_value = {"other": "data"}

        session = Session("1", "test_server", conn)
        version = session.get_version()

        assert version == "N/A"

    def test_get_version_dict_empty_version(self, mock_config):
        """Test get_version with empty version value"""
        conn = MagicMock()
        conn.is_connected = True
        conn.api.get_version.return_value = {"version": ""}

        session = Session("1", "test_server", conn)
        version = session.get_version()

        assert version == "N/A"

    def test_get_version_not_connected(self, mock_config):
        """Test get_version when not connected"""
        conn = MagicMock()
        conn.is_connected = False

        session = Session("1", "test_server", conn)
        version = session.get_version()

        assert version == "N/A"

    def test_get_version_api_exception(self, mock_config):
        """Test get_version when API throws exception"""
        conn = MagicMock()
        conn.is_connected = True
        conn.api.get_version.side_effect = Exception("API error")

        session = Session("1", "test_server", conn)
        version = session.get_version()

        assert version == "N/A"


class TestSessionManager:
    """Test SessionManager class"""

    def test_initialization(self, mock_config):
        """Test SessionManager initialization"""
        manager = SessionManager(mock_config)

        assert manager.config == mock_config
        assert manager.sessions == {}
        assert manager.active_session_id is None
        assert manager._next_session_num == 1

    def test_active_connection_none(self, mock_config):
        """Test active_connection property when no active session"""
        manager = SessionManager(mock_config)

        assert manager.active_connection is None

    def test_active_connection_returns_connection(self, mock_config):
        """Test active_connection property returns connection"""
        manager = SessionManager(mock_config)
        mock_conn = MagicMock()
        session = Session("1", "test_server", mock_conn)
        manager.sessions = {"1": session}
        manager.active_session_id = "1"

        assert manager.active_connection == mock_conn

    def test_active_session_none(self, mock_config):
        """Test active_session property when no active session"""
        manager = SessionManager(mock_config)

        assert manager.active_session is None

    def test_active_session_returns_session(self, mock_config):
        """Test active_session property returns session object"""
        manager = SessionManager(mock_config)
        mock_conn = MagicMock()
        session = Session("1", "test_server", mock_conn)
        manager.sessions = {"1": session}
        manager.active_session_id = "1"

        assert manager.active_session == session

    def test_create_session_no_label(self, mock_config):
        """Test create_session without label"""
        with patch("quads_client.session_manager.ConnectionManager") as mock_cm:
            manager = SessionManager(mock_config)
            session = manager.create_session("test_server")

            assert session.id == "1"
            assert session.server_name == "test_server"
            assert session.label == "test_server"
            assert manager.active_session_id == "1"
            assert "1" in manager.sessions
            mock_cm.assert_called_once_with(mock_config)

    def test_create_session_with_label(self, mock_config):
        """Test create_session with custom label"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session = manager.create_session("test_server", "dev")

            assert session.label == "dev"

    def test_create_session_increments_counter(self, mock_config):
        """Test create_session increments session counter"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1")
            session2 = manager.create_session("server2")

            assert session1.id == "1"
            assert session2.id == "2"
            assert manager._next_session_num == 3

    def test_create_session_sets_active(self, mock_config):
        """Test create_session sets new session as active"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1")
            assert manager.active_session_id == "1"

            session2 = manager.create_session("server2")
            assert manager.active_session_id == "2"

    def test_switch_session_success(self, mock_config):
        """Test switch_session to existing session"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1")
            session2 = manager.create_session("server2")

            # Switch back to session 1
            manager.switch_session("1")

            assert manager.active_session_id == "1"
            # last_active should be updated
            assert session1.last_active > session1.created_at

    def test_switch_session_not_found(self, mock_config):
        """Test switch_session with invalid session ID"""
        manager = SessionManager(mock_config)

        with pytest.raises(ValueError, match="Session 999 not found"):
            manager.switch_session("999")

    def test_close_session_exists(self, mock_config):
        """Test close_session removes session"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session = manager.create_session("test_server")

            manager.close_session("1")

            assert "1" not in manager.sessions
            assert manager.active_session_id is None

    def test_close_session_not_exists(self, mock_config):
        """Test close_session with non-existent session (no error)"""
        manager = SessionManager(mock_config)

        # Should not raise exception
        manager.close_session("999")

    def test_close_session_disconnects(self, mock_config):
        """Test close_session calls disconnect on connection"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session = manager.create_session("test_server")
            mock_disconnect = MagicMock()
            session.connection.disconnect = mock_disconnect

            manager.close_session("1")

            mock_disconnect.assert_called_once()

    def test_close_session_switches_to_next(self, mock_config):
        """Test close_session switches to another session when closing active"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1")
            session2 = manager.create_session("server2")

            # Active is session 2, close it
            manager.close_session("2")

            # Should switch to session 1
            assert manager.active_session_id == "1"
            assert "2" not in manager.sessions

    def test_close_all_inactive_no_active(self, mock_config):
        """Test close_all_inactive with no active session"""
        manager = SessionManager(mock_config)

        count = manager.close_all_inactive()

        assert count == 0

    def test_close_all_inactive_closes_others(self, mock_config):
        """Test close_all_inactive closes non-active sessions"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1")
            session2 = manager.create_session("server2")
            session3 = manager.create_session("server3")

            # Active is session 3
            count = manager.close_all_inactive()

            assert count == 2
            assert "1" not in manager.sessions
            assert "2" not in manager.sessions
            assert "3" in manager.sessions

    def test_close_all_inactive_only_active_exists(self, mock_config):
        """Test close_all_inactive when only active session exists"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1")

            count = manager.close_all_inactive()

            assert count == 0
            assert "1" in manager.sessions

    def test_list_sessions_empty(self, mock_config):
        """Test list_sessions with no sessions"""
        manager = SessionManager(mock_config)

        sessions = manager.list_sessions()

        assert sessions == []

    def test_list_sessions_ordered_by_id(self, mock_config):
        """Test list_sessions returns sessions ordered by ID"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1")
            session2 = manager.create_session("server2")
            session3 = manager.create_session("server3")

            sessions = manager.list_sessions()

            assert len(sessions) == 3
            assert sessions[0].id == "1"
            assert sessions[1].id == "2"
            assert sessions[2].id == "3"

    def test_get_session_exists(self, mock_config):
        """Test get_session returns session by ID"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session = manager.create_session("test_server")

            result = manager.get_session("1")

            assert result == session

    def test_get_session_not_exists(self, mock_config):
        """Test get_session returns None for non-existent ID"""
        manager = SessionManager(mock_config)

        result = manager.get_session("999")

        assert result is None

    def test_get_session_by_label_exists(self, mock_config):
        """Test get_session_by_label returns session"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session = manager.create_session("test_server", "dev")

            result = manager.get_session_by_label("dev")

            assert result == session

    def test_get_session_by_label_not_exists(self, mock_config):
        """Test get_session_by_label returns None when not found"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session = manager.create_session("test_server", "dev")

            result = manager.get_session_by_label("prod")

            assert result is None

    def test_get_session_by_label_multiple_sessions(self, mock_config):
        """Test get_session_by_label with multiple sessions"""
        with patch("quads_client.session_manager.ConnectionManager"):
            manager = SessionManager(mock_config)
            session1 = manager.create_session("server1", "dev")
            session2 = manager.create_session("server2", "prod")
            session3 = manager.create_session("server3", "stage")

            result = manager.get_session_by_label("prod")

            assert result == session2
