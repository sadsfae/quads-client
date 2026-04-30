import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.host import HostCommands


@pytest.fixture
def host_commands(mock_shell):
    return HostCommands(mock_shell)


def test_ls_hosts_success(host_commands, mock_shell):
    """Test listing hosts successfully"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_hosts.return_value = [
        {
            "name": "host01.example.com",
            "model": "R630",
            "default_cloud": {"name": "cloud01"},
            "host_type": "baremetal",
            "broken": False,
            "retired": False,
        },
        {
            "name": "host02.example.com",
            "model": "R640",
            "default_cloud": {"name": "cloud02"},
            "host_type": "baremetal",
            "broken": True,
            "retired": False,
        },
    ]

    host_commands.cmd_ls_hosts("")

    mock_shell.connection.api.get_hosts.assert_called_once()
    mock_shell.poutput.assert_called()


def test_ls_hosts_no_connection(host_commands, mock_shell):
    """Test ls-hosts when not connected"""
    mock_shell.connection.is_connected = False

    host_commands.cmd_ls_hosts("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ls_hosts_empty(host_commands, mock_shell):
    """Test ls-hosts with no hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_hosts.return_value = []

    host_commands.cmd_ls_hosts("")

    mock_shell.poutput.assert_called_with("No hosts found")


def test_mark_broken_success(host_commands, mock_shell):
    """Test marking a host as broken"""
    mock_shell.connection.is_connected = True

    host_commands.cmd_mark_broken("host01.example.com")

    mock_shell.connection.api.update_host.assert_called_once_with("host01.example.com", {"broken": True})
    mock_shell.poutput.assert_called_with("Marked host01.example.com as broken")


def test_mark_broken_no_args(host_commands, mock_shell):
    """Test mark-broken without hostname"""
    mock_shell.connection.is_connected = True

    host_commands.cmd_mark_broken("")

    mock_shell.perror.assert_called_with("Usage: mark-broken <hostname>")


def test_mark_repaired_success(host_commands, mock_shell):
    """Test marking a broken host as repaired"""
    mock_shell.connection.is_connected = True

    host_commands.cmd_mark_repaired("host01.example.com")

    mock_shell.connection.api.update_host.assert_called_once_with("host01.example.com", {"broken": False})
    mock_shell.poutput.assert_called_with("Marked host01.example.com as repaired")


def test_retire_success(host_commands, mock_shell):
    """Test retiring a host"""
    mock_shell.connection.is_connected = True

    host_commands.cmd_retire("host01.example.com")

    mock_shell.connection.api.update_host.assert_called_once_with("host01.example.com", {"retired": True})
    mock_shell.poutput.assert_called_with("Marked host01.example.com as retired")


def test_unretire_success(host_commands, mock_shell):
    """Test unretiring a host"""
    mock_shell.connection.is_connected = True

    host_commands.cmd_unretire("host01.example.com")

    mock_shell.connection.api.update_host.assert_called_once_with("host01.example.com", {"retired": False})
    mock_shell.poutput.assert_called_with("Marked host01.example.com as active")


def test_ls_broken_success(host_commands, mock_shell):
    """Test listing broken hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_hosts.return_value = [
        {"name": "host01.example.com", "model": "R630"},
        {"name": "host02.example.com", "model": "R640"},
    ]

    host_commands.cmd_ls_broken("")

    mock_shell.connection.api.filter_hosts.assert_called_once_with({"broken": True})
    mock_shell.poutput.assert_called()


def test_ls_broken_empty(host_commands, mock_shell):
    """Test ls-broken with no broken hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_hosts.return_value = []

    host_commands.cmd_ls_broken("")

    mock_shell.poutput.assert_called_with("No broken hosts found")


def test_ls_retired_success(host_commands, mock_shell):
    """Test listing retired hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_hosts.return_value = [
        {"name": "host01.example.com", "model": "R630"},
    ]

    host_commands.cmd_ls_retired("")

    mock_shell.connection.api.filter_hosts.assert_called_once_with({"retired": True})
    mock_shell.poutput.assert_called()


def test_mark_broken_api_error(host_commands, mock_shell):
    """Test mark-broken when API call fails"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.update_host.side_effect = Exception("API Error")

    host_commands.cmd_mark_broken("host01.example.com")

    mock_shell.perror.assert_called_with("Failed to mark host as broken: API Error")
