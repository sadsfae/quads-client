import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.connection import ConnectionCommands


@pytest.fixture
def connection_commands(mock_shell):
    return ConnectionCommands(mock_shell)


def test_connect_to_default_server(connection_commands, mock_shell, mock_config):
    """Test connecting to default server when no server name provided"""
    mock_shell.config = mock_config
    mock_config.get_default_server.return_value = "test_server"

    # Mock session creation
    mock_session = MagicMock()
    mock_session.id = "2"
    mock_session.connection = MagicMock()
    mock_session.connection.connect = MagicMock()
    mock_session.connection.username = "test@example.com"
    mock_session.connection._registration_mode = False
    mock_shell.session_manager.create_session.return_value = mock_session

    connection_commands.cmd_connect("")

    mock_shell.session_manager.create_session.assert_called_once_with("test_server", None)
    mock_session.connection.connect.assert_called_once_with("test_server")
    mock_shell.poutput.assert_any_call("Connecting to default server: test_server")


def test_connect_no_default_server(connection_commands, mock_shell, mock_config):
    """Test connect without args and no default server configured"""
    mock_shell.config = mock_config
    mock_config.get_default_server.return_value = None
    mock_config.get_all_servers.return_value = {"server1": {}, "server2": {}}

    connection_commands.cmd_connect("")

    mock_shell.poutput.assert_any_call("Available servers:")
    mock_shell.poutput.assert_any_call("\nUsage: connect <server_name|number> [--session <label>]")
    mock_shell.session_manager.create_session.assert_not_called()


def test_connect_with_server_name(connection_commands, mock_shell):
    """Test connecting to specific server"""
    # Mock session creation
    mock_session = MagicMock()
    mock_session.id = "2"
    mock_session.connection = MagicMock()
    mock_session.connection.connect = MagicMock()
    mock_session.connection.username = "test@example.com"
    mock_session.connection._registration_mode = False
    mock_shell.session_manager.create_session.return_value = mock_session

    connection_commands.cmd_connect("server1")

    mock_shell.session_manager.create_session.assert_called_once_with("server1", None)
    mock_session.connection.connect.assert_called_once_with("server1")


def test_connect_error_handling(connection_commands, mock_shell):
    """Test connect command error handling"""
    from quads_client.connection import ConnectionError

    # Mock session with failing connection
    mock_session = MagicMock()
    mock_session.connection.connect.side_effect = ConnectionError("Connection failed")
    mock_shell.session_manager.create_session.return_value = mock_session

    connection_commands.cmd_connect("test_server")

    mock_shell.perror.assert_called_with("Connection failed")


def test_connect_no_connection_manager(connection_commands, mock_shell):
    """Test connect when connection manager not initialized"""
    mock_shell.session_manager = None

    connection_commands.cmd_connect("test_server")

    mock_shell.perror.assert_called_with("Configuration not loaded")


def test_disconnect_success(connection_commands, mock_shell):
    """Test disconnecting from server"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"

    connection_commands.cmd_disconnect("")

    mock_shell.connection.disconnect.assert_called_once()
    mock_shell.poutput.assert_called_with("Disconnected from test_server")


def test_disconnect_not_connected(connection_commands, mock_shell):
    """Test disconnect when not connected"""
    mock_shell.connection.is_connected = False

    connection_commands.cmd_disconnect("")

    mock_shell.pwarning.assert_called_with("Not connected to any server")


def test_status_connected(connection_commands, mock_shell, mock_config):
    """Test status when connected"""
    # Mock active session
    mock_session = MagicMock()
    mock_session.id = "1"
    mock_session.label = "test_server"
    mock_session.connection.is_connected = True
    mock_session.connection.current_server = "test_server"
    mock_session.connection.username = "test@example.com"
    mock_session.get_version.return_value = "2.2.6"
    mock_shell.session_manager.active_session = mock_session
    mock_shell.session_manager.list_sessions.return_value = [mock_session]
    mock_shell.config = mock_config
    mock_shell.config.get_server_verify.return_value = True

    connection_commands.cmd_status("")

    assert mock_shell.poutput.call_count >= 3
    mock_shell.config.get_server_url.assert_called_once_with("test_server")


def test_status_disconnected(connection_commands, mock_shell):
    """Test status when disconnected"""
    mock_shell.session_manager.active_session = None
    mock_shell.session_manager.list_sessions.return_value = []

    connection_commands.cmd_status("")

    mock_shell.poutput.assert_any_call("Not connected")
