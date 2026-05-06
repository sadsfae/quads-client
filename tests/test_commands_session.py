"""Comprehensive tests for commands/session.py"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from quads_client.commands.session import SessionCommands


class TestSessionCreate:
    """Test session-create command"""

    def test_session_create_no_args(self, mock_shell):
        """Test session-create with no arguments"""
        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_create("")

        mock_shell.perror.assert_called_with("Usage: session-create <server_name> [label <name>]")

    def test_session_create_server_only(self, mock_shell):
        """Test session-create with server name only"""
        mock_session = MagicMock()
        mock_session.id = "2"
        mock_session.label = "test_server"
        mock_session.connection = MagicMock()
        mock_shell.session_manager.create_session.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_create("test_server")

        mock_shell.session_manager.create_session.assert_called_once_with("test_server", None)
        mock_session.connection.connect.assert_called_once_with("test_server")
        mock_shell._update_prompt.assert_called_once()
        mock_shell.poutput.assert_called_with("Created session 2 (test_server)")

    def test_session_create_with_label(self, mock_shell):
        """Test session-create with label flag"""
        mock_session = MagicMock()
        mock_session.id = "2"
        mock_session.label = "dev"
        mock_session.connection = MagicMock()
        mock_shell.session_manager.create_session.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_create("test_server label dev")

        mock_shell.session_manager.create_session.assert_called_once_with("test_server", "dev")
        mock_shell.poutput.assert_called_with("Created session 2 (dev)")

    def test_session_create_exception(self, mock_shell):
        """Test session-create when exception occurs"""
        mock_shell.session_manager.create_session.side_effect = Exception("Connection failed")

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_create("test_server")

        mock_shell.perror.assert_called_with("Failed to create session: Connection failed")


class TestSessionSwitch:
    """Test session-switch command"""

    def test_session_switch_no_args(self, mock_shell):
        """Test session-switch with no arguments"""
        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_switch("")

        mock_shell.perror.assert_called_with("Usage: session-switch <session_id>")

    def test_session_switch_success(self, mock_shell):
        """Test session-switch to existing session"""
        mock_session = MagicMock()
        mock_session.id = "2"
        mock_session.label = "prod"
        mock_shell.session_manager.get_session.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_switch("2")

        mock_shell.session_manager.switch_session.assert_called_once_with("2")
        mock_shell._update_prompt.assert_called_once()
        mock_shell._update_visible_commands.assert_called_once()
        mock_shell.poutput.assert_called_with("Switched to session 2 (prod)")

    def test_session_switch_invalid_id(self, mock_shell):
        """Test session-switch with invalid session ID"""
        mock_shell.session_manager.switch_session.side_effect = ValueError("Session 999 not found")

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_switch("999")

        mock_shell.perror.assert_called_with("Session 999 not found")

    def test_session_switch_already_active(self, mock_shell):
        """Test session-switch when already on target session"""
        mock_session = MagicMock()
        mock_session.id = "1"
        mock_session.label = "dev"
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.session_manager.get_session.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_switch("1")

        # Should not call switch_session
        mock_shell.session_manager.switch_session.assert_not_called()
        mock_shell.poutput.assert_called_with("Already on session 1 (dev)")
        mock_shell._update_prompt.assert_not_called()


class TestSessionQuickSwitch:
    """Test session (quick switch) command"""

    def test_session_no_args(self, mock_shell):
        """Test session with no arguments shows help"""
        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("")

        # Should show help, not error
        assert mock_shell.poutput.call_count >= 1
        assert any("Usage:" in str(call) for call in mock_shell.poutput.call_args_list)

    def test_session_by_id(self, mock_shell):
        """Test session quick switch by ID"""
        mock_session = MagicMock()
        mock_session.id = "2"
        mock_session.label = "prod"
        mock_shell.session_manager.get_session.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("2")

        mock_shell.session_manager.get_session.assert_called_once_with("2")
        mock_shell.session_manager.switch_session.assert_called_once_with("2")
        mock_shell.poutput.assert_called_with("Switched to session 2 (prod)")

    def test_session_by_label(self, mock_shell):
        """Test session quick switch by label"""
        mock_session = MagicMock()
        mock_session.id = "3"
        mock_session.label = "stage"
        mock_shell.session_manager.get_session.return_value = None
        mock_shell.session_manager.get_session_by_label.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("stage")

        mock_shell.session_manager.get_session.assert_called_once_with("stage")
        mock_shell.session_manager.get_session_by_label.assert_called_once_with("stage")
        mock_shell.session_manager.switch_session.assert_called_once_with("3")

    def test_session_not_found(self, mock_shell):
        """Test session with non-existent ID/label"""
        mock_shell.session_manager.get_session.return_value = None
        mock_shell.session_manager.get_session_by_label.return_value = None

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("999")

        mock_shell.perror.assert_called_with("Session not found: 999")

    def test_session_switch_exception(self, mock_shell):
        """Test session when switch raises exception"""
        mock_session = MagicMock()
        mock_session.id = "2"
        mock_shell.session_manager.get_session.return_value = mock_session
        mock_shell.session_manager.switch_session.side_effect = ValueError("Switch failed")

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("2")

        mock_shell.perror.assert_called_with("Switch failed")

    def test_session_help(self, mock_shell):
        """Test session ? shows help instead of error"""
        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("?")

        # Should show help, not error
        assert mock_shell.poutput.call_count >= 1
        assert any("Usage:" in str(call) for call in mock_shell.poutput.call_args_list)
        mock_shell.perror.assert_not_called()

    def test_session_already_active_by_id(self, mock_shell):
        """Test session when already on target session (by ID)"""
        mock_session = MagicMock()
        mock_session.id = "1"
        mock_session.label = "dev"
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.session_manager.get_session.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("1")

        # Should not call switch_session
        mock_shell.session_manager.switch_session.assert_not_called()
        mock_shell.poutput.assert_called_with("Already on session 1 (dev)")
        mock_shell._update_prompt.assert_not_called()

    def test_session_already_active_by_label(self, mock_shell):
        """Test session when already on target session (by label)"""
        mock_session = MagicMock()
        mock_session.id = "1"
        mock_session.label = "dev"
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.session_manager.get_session.return_value = None
        mock_shell.session_manager.get_session_by_label.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session("dev")

        # Should not call switch_session
        mock_shell.session_manager.switch_session.assert_not_called()
        mock_shell.poutput.assert_called_with("Already on session 1 (dev)")
        mock_shell._update_prompt.assert_not_called()


class TestSessionList:
    """Test session-list command"""

    def test_session_list_no_sessions(self, mock_shell):
        """Test session-list with no active sessions"""
        mock_shell.session_manager.list_sessions.return_value = []

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_list("")

        mock_shell.poutput.assert_called_with("No active sessions")

    def test_session_list_with_rich_console(self, mock_shell):
        """Test session-list with rich console"""
        mock_session1 = MagicMock()
        mock_session1.id = "1"
        mock_session1.server_name = "quads-dev.example.com"
        mock_session1.label = "dev"
        mock_session1.get_version.return_value = "2.2.6"
        mock_session1.connection.is_connected = True
        mock_session1.last_active = datetime.now()

        mock_session2 = MagicMock()
        mock_session2.id = "2"
        mock_session2.server_name = "quads-prod.example.com"
        mock_session2.label = "prod"
        mock_session2.get_version.return_value = "2.2.6"
        mock_session2.connection.is_connected = True
        mock_session2.last_active = datetime.now()

        mock_shell.session_manager.list_sessions.return_value = [mock_session1, mock_session2]
        mock_shell.session_manager.active_session_id = "2"
        mock_shell.rich_console = MagicMock()

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_list("")

        # Should use rich table
        assert mock_shell.rich_console.console.print.called

    def test_session_list_without_rich_console(self, mock_shell):
        """Test session-list without rich console (plain text)"""
        mock_session1 = MagicMock()
        mock_session1.id = "1"
        mock_session1.server_name = "quads-dev.example.com"
        mock_session1.label = "dev"
        mock_session1.get_version.return_value = "2.2.6"
        mock_session1.connection.is_connected = True
        mock_session1.last_active = datetime.now()

        mock_shell.session_manager.list_sessions.return_value = [mock_session1]
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.rich_console = None

        session_cmd = SessionCommands(mock_shell)

        with patch("tabulate.tabulate") as mock_tabulate:
            mock_tabulate.return_value = "table output"
            session_cmd.cmd_session_list("")

            mock_tabulate.assert_called_once()
            mock_shell.poutput.assert_called_with("table output")

    def test_session_list_status_indicators(self, mock_shell):
        """Test session-list shows correct status indicators"""
        # Active connected session
        mock_session1 = MagicMock()
        mock_session1.id = "1"
        mock_session1.server_name = "server1"
        mock_session1.label = "active"
        mock_session1.get_version.return_value = "2.2.6"
        mock_session1.connection.is_connected = True
        mock_session1.last_active = datetime.now()

        # Idle connected session
        mock_session2 = MagicMock()
        mock_session2.id = "2"
        mock_session2.server_name = "server2"
        mock_session2.label = "idle"
        mock_session2.get_version.return_value = "2.2.6"
        mock_session2.connection.is_connected = True
        mock_session2.last_active = datetime.now() - timedelta(minutes=5)

        # Offline session
        mock_session3 = MagicMock()
        mock_session3.id = "3"
        mock_session3.server_name = "server3"
        mock_session3.label = "offline"
        mock_session3.get_version.return_value = "N/A"
        mock_session3.connection.is_connected = False
        mock_session3.last_active = datetime.now() - timedelta(hours=2)

        mock_shell.session_manager.list_sessions.return_value = [
            mock_session1,
            mock_session2,
            mock_session3,
        ]
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.rich_console = MagicMock()

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_list("")

        # Verify rich table was called
        assert mock_shell.rich_console.console.print.called

    def test_session_list_time_formats(self, mock_shell):
        """Test session-list formats time correctly"""
        now = datetime.now()

        # Test "now" - less than 60 seconds
        mock_session1 = MagicMock()
        mock_session1.id = "1"
        mock_session1.server_name = "server1"
        mock_session1.label = "just_now"
        mock_session1.get_version.return_value = "2.2.6"
        mock_session1.connection.is_connected = True
        mock_session1.last_active = now - timedelta(seconds=30)

        # Test minutes ago - less than 1 hour
        mock_session2 = MagicMock()
        mock_session2.id = "2"
        mock_session2.server_name = "server2"
        mock_session2.label = "minutes"
        mock_session2.get_version.return_value = "2.2.6"
        mock_session2.connection.is_connected = True
        mock_session2.last_active = now - timedelta(minutes=15)

        # Test hours ago - less than 24 hours
        mock_session3 = MagicMock()
        mock_session3.id = "3"
        mock_session3.server_name = "server3"
        mock_session3.label = "hours"
        mock_session3.get_version.return_value = "2.2.6"
        mock_session3.connection.is_connected = True
        mock_session3.last_active = now - timedelta(hours=5)

        # Test days ago
        mock_session4 = MagicMock()
        mock_session4.id = "4"
        mock_session4.server_name = "server4"
        mock_session4.label = "days"
        mock_session4.get_version.return_value = "2.2.6"
        mock_session4.connection.is_connected = True
        mock_session4.last_active = now - timedelta(days=2)

        mock_shell.session_manager.list_sessions.return_value = [
            mock_session1,
            mock_session2,
            mock_session3,
            mock_session4,
        ]
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.rich_console = None

        session_cmd = SessionCommands(mock_shell)

        with patch("tabulate.tabulate") as mock_tabulate:
            session_cmd.cmd_session_list("")
            # Verify tabulate was called with data
            assert mock_tabulate.called

    def test_session_list_days_ago(self, mock_shell):
        """Test session-list shows days for old sessions"""
        mock_session = MagicMock()
        mock_session.id = "1"
        mock_session.server_name = "server1"
        mock_session.label = "old"
        mock_session.get_version.return_value = "2.2.6"
        mock_session.connection.is_connected = True
        mock_session.last_active = datetime.now() - timedelta(days=3)

        mock_shell.session_manager.list_sessions.return_value = [mock_session]
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.rich_console = MagicMock()

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_list("")

        # Should call rich print
        assert mock_shell.rich_console.console.print.called

    def test_session_list_plain_offline_session(self, mock_shell):
        """Test session-list plain text with offline session"""
        mock_session = MagicMock()
        mock_session.id = "1"
        mock_session.server_name = "server1"
        mock_session.label = "offline"
        mock_session.get_version.return_value = "N/A"
        mock_session.connection.is_connected = False
        mock_session.last_active = datetime.now()

        mock_shell.session_manager.list_sessions.return_value = [mock_session]
        mock_shell.session_manager.active_session_id = "1"
        mock_shell.rich_console = None

        session_cmd = SessionCommands(mock_shell)

        with patch("tabulate.tabulate") as mock_tabulate:
            session_cmd.cmd_session_list("")
            # Should call tabulate
            assert mock_tabulate.called


class TestSessionClose:
    """Test session-close command"""

    def test_session_close_no_args(self, mock_shell):
        """Test session-close with no arguments"""
        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_close("")

        mock_shell.perror.assert_called_with("Usage: session-close <session_id>")

    def test_session_close_success(self, mock_shell):
        """Test session-close removes session"""
        mock_session = MagicMock()
        mock_session.label = "dev"
        mock_shell.session_manager.get_session.return_value = mock_session

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_close("2")

        mock_shell.session_manager.get_session.assert_called_once_with("2")
        mock_shell.session_manager.close_session.assert_called_once_with("2")
        mock_shell._update_prompt.assert_called_once()
        mock_shell._update_visible_commands.assert_called_once()
        mock_shell.poutput.assert_called_with("Closed session 2 (dev)")

    def test_session_close_not_found(self, mock_shell):
        """Test session-close with non-existent session"""
        mock_shell.session_manager.get_session.return_value = None

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_close("999")

        mock_shell.perror.assert_called_with("Session not found: 999")


class TestSessionCloseAll:
    """Test session-close-all command"""

    def test_session_close_all_success(self, mock_shell):
        """Test session-close-all closes inactive sessions"""
        mock_shell.session_manager.close_all_inactive.return_value = 3

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_close_all("")

        mock_shell.session_manager.close_all_inactive.assert_called_once()
        mock_shell._update_prompt.assert_called_once()
        mock_shell._update_visible_commands.assert_called_once()
        mock_shell.poutput.assert_called_with("Closed 3 inactive sessions")

    def test_session_close_all_single_session(self, mock_shell):
        """Test session-close-all with one inactive session"""
        mock_shell.session_manager.close_all_inactive.return_value = 1

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_close_all("")

        mock_shell.poutput.assert_called_with("Closed 1 inactive session")

    def test_session_close_all_none(self, mock_shell):
        """Test session-close-all with no inactive sessions"""
        mock_shell.session_manager.close_all_inactive.return_value = 0

        session_cmd = SessionCommands(mock_shell)
        session_cmd.cmd_session_close_all("")

        mock_shell.poutput.assert_called_with("No inactive sessions to close")
