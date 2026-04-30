import pytest
from unittest.mock import MagicMock
from quads_client.commands.available import AvailableCommands


@pytest.fixture
def available_commands(mock_shell):
    return AvailableCommands(mock_shell)


def test_ls_available_success(available_commands, mock_shell):
    """Test listing available hosts successfully"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_available.return_value = [
        {
            "name": "host01.example.com",
            "model": "R630",
            "host_type": "baremetal",
            "can_self_schedule": True,
        },
        {
            "name": "host02.example.com",
            "model": "R640",
            "host_type": "baremetal",
            "can_self_schedule": False,
        },
    ]

    available_commands.cmd_ls_available("")

    mock_shell.connection.api.filter_available.assert_called_once_with({})
    mock_shell.poutput.assert_called()


def test_ls_available_with_filters(available_commands, mock_shell):
    """Test listing available hosts with filters"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_available.return_value = []

    available_commands.cmd_ls_available("--start 2026-05-01 --end 2026-05-15 --model R630")

    expected_filters = {
        "start": "2026-05-01",
        "end": "2026-05-15",
        "model": "R630",
    }
    mock_shell.connection.api.filter_available.assert_called_once_with(expected_filters)


def test_ls_available_empty(available_commands, mock_shell):
    """Test ls-available with no available hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_available.return_value = []

    available_commands.cmd_ls_available("")

    mock_shell.poutput.assert_called_with("No available hosts found")


def test_ls_available_not_connected(available_commands, mock_shell):
    """Test ls-available when not connected"""
    mock_shell.connection.is_connected = False

    available_commands.cmd_ls_available("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ls_available_api_error(available_commands, mock_shell):
    """Test ls-available when API call fails"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_available.side_effect = Exception("API Error")

    available_commands.cmd_ls_available("")

    mock_shell.perror.assert_called_with("Failed to list available hosts: API Error")


def test_ls_available_start_filter_only(available_commands, mock_shell):
    """Test ls-available with only start date filter"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_available.return_value = []

    available_commands.cmd_ls_available("--start 2026-05-01")

    mock_shell.connection.api.filter_available.assert_called_once_with({"start": "2026-05-01"})


def test_ls_available_end_filter_only(available_commands, mock_shell):
    """Test ls-available with only end date filter"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_available.return_value = []

    available_commands.cmd_ls_available("--end 2026-05-15")

    mock_shell.connection.api.filter_available.assert_called_once_with({"end": "2026-05-15"})


def test_ls_available_model_filter_only(available_commands, mock_shell):
    """Test ls-available with only model filter"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_available.return_value = []

    available_commands.cmd_ls_available("--model R630")

    mock_shell.connection.api.filter_available.assert_called_once_with({"model": "R630"})
