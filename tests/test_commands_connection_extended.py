import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.connection import ConnectionCommands


@pytest.fixture
def connection_commands(mock_shell):
    return ConnectionCommands(mock_shell)


def test_connect_to_default_server(connection_commands, mock_shell, mock_config):
    """Test connecting to default server when no server name provided"""
    mock_shell.config = mock_config
    mock_shell.connection.is_connected = False
    mock_config.get_default_server.return_value = "test_server"

    connection_commands.cmd_connect("")

    mock_shell.connection.connect.assert_called_once_with("test_server")
    mock_shell.poutput.assert_any_call("Connecting to default server: test_server")


def test_connect_no_default_server(connection_commands, mock_shell, mock_config):
    """Test connect without args and no default server configured"""
    mock_shell.config = mock_config
    mock_shell.connection.is_connected = False
    mock_config.get_default_server.return_value = None
    mock_shell.connection.get_available_servers.return_value = ["server1", "server2"]

    connection_commands.cmd_connect("")

    mock_shell.poutput.assert_any_call("Available servers:")
    mock_shell.poutput.assert_any_call("\nUsage: connect <server_name>")
    mock_shell.connection.connect.assert_not_called()


def test_connect_with_server_name(connection_commands, mock_shell):
    """Test connecting to specific server"""
    mock_shell.connection.is_connected = False

    connection_commands.cmd_connect("server1")

    mock_shell.connection.connect.assert_called_once_with("server1")


def test_connect_error_handling(connection_commands, mock_shell):
    """Test connect command error handling"""
    from quads_client.connection import ConnectionError

    mock_shell.connection.is_connected = False
    mock_shell.connection.connect.side_effect = ConnectionError("Connection failed")

    connection_commands.cmd_connect("test_server")

    mock_shell.perror.assert_called_with("Connection failed")


def test_connect_no_connection_manager(connection_commands, mock_shell):
    """Test connect when connection manager not initialized"""
    mock_shell.connection = None

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
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"
    mock_shell.connection.username = "test@example.com"
    mock_shell.config = mock_config

    connection_commands.cmd_status("")

    assert mock_shell.poutput.call_count >= 3
    mock_shell.config.get_server_url.assert_called_once_with("test_server")


def test_status_disconnected(connection_commands, mock_shell):
    """Test status when disconnected"""
    mock_shell.connection.is_connected = False
    mock_shell.connection.get_available_servers.return_value = ["server1", "server2"]

    connection_commands.cmd_status("")

    mock_shell.poutput.assert_any_call("Not connected")
