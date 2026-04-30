import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.connection import ConnectionCommands
from quads_client.connection import ConnectionError


def test_connect_list_servers(mock_shell):
    """Test connect command without args and no default server lists servers"""
    mock_shell.connection.get_available_servers.return_value = ["server1", "server2"]
    mock_shell.config.get_default_server.return_value = None

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_connect("")

    assert mock_shell.poutput.call_count >= 2
    mock_shell.connection.get_available_servers.assert_called_once()
    mock_shell.connection.connect.assert_not_called()


def test_connect_success(mock_shell, mock_api):
    """Test successful connection"""
    mock_shell.connection.connect = MagicMock()
    mock_shell.connection.username = "test@example.com"
    mock_shell._update_prompt = MagicMock()

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_connect("test_server")

    mock_shell.connection.connect.assert_called_once_with("test_server")
    mock_shell._update_prompt.assert_called_once()
    mock_shell.poutput.assert_called()


def test_connect_failure(mock_shell):
    """Test connection failure"""
    mock_shell.connection.connect = MagicMock(side_effect=ConnectionError("Connection failed"))

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_connect("test_server")

    mock_shell.perror.assert_called_once()


def test_connect_no_config(mock_shell):
    """Test connect when config not loaded"""
    mock_shell.connection = None

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_connect("test_server")

    mock_shell.perror.assert_called_with("Configuration not loaded")


def test_disconnect_success(mock_shell):
    """Test successful disconnection"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"
    mock_shell.connection.disconnect = MagicMock()
    mock_shell._update_prompt = MagicMock()

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_disconnect("")

    mock_shell.connection.disconnect.assert_called_once()
    mock_shell._update_prompt.assert_called_once()
    mock_shell.poutput.assert_called()


def test_disconnect_not_connected(mock_shell):
    """Test disconnect when not connected"""
    mock_shell.connection.is_connected = False

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_disconnect("")

    mock_shell.pwarning.assert_called_with("Not connected to any server")


def test_status_connected(mock_shell):
    """Test status when connected"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"
    mock_shell.connection.username = "test@example.com"
    mock_shell.config.get_server_url.return_value = "https://test.example.com"

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_status("")

    assert mock_shell.poutput.call_count >= 3


def test_status_disconnected(mock_shell):
    """Test status when disconnected"""
    mock_shell.connection.is_connected = False
    mock_shell.connection.get_available_servers.return_value = ["server1", "server2"]

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_status("")

    mock_shell.poutput.assert_any_call("Not connected")


def test_status_no_config(mock_shell):
    """Test status when config not loaded"""
    mock_shell.connection = None

    conn_cmd = ConnectionCommands(mock_shell)
    conn_cmd.cmd_status("")

    mock_shell.perror.assert_called_with("Configuration not loaded")
