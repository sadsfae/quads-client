import pytest
from unittest.mock import MagicMock
from quads_client.commands.user import UserCommands


def test_available_success(mock_shell):
    """Test available command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.filter_hosts.return_value = [
        {"name": "host01.example.com", "can_self_schedule": True},
        {"name": "host02.example.com", "can_self_schedule": True},
        {"name": "host03.example.com", "can_self_schedule": False},
    ]

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_available("")

    mock_shell.connection.api.filter_hosts.assert_called_once_with(
        {"cloud": "cloud01", "retired": False, "broken": False}
    )
    # Should only show hosts with can_self_schedule=True
    assert mock_shell.poutput.call_count >= 2


def test_available_no_hosts(mock_shell):
    """Test available with no available hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.filter_hosts.return_value = []

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_available("")

    mock_shell.poutput.assert_called_with("No available hosts")


def test_available_not_authenticated(mock_shell):
    """Test available when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_available("")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_schedule_success(mock_shell):
    """Test schedule command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.create_schedule.return_value = {"id": 1, "status": "success"}

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule("host01.example.com cloud02")

    mock_shell.connection.api.create_schedule.assert_called_once_with(
        {"hostname": "host01.example.com", "cloud": "cloud02"}
    )
    mock_shell.poutput.assert_called()


def test_schedule_missing_args(mock_shell):
    """Test schedule with missing arguments"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule("host01.example.com")

    mock_shell.perror.assert_any_call("Usage: schedule <hostname> <cloud>")


def test_schedule_forbidden(mock_shell):
    """Test schedule when user lacks permission"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.create_schedule.side_effect = Exception("403 Forbidden")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule("host01.example.com cloud02")

    mock_shell.perror.assert_called_with("Error: You don't have permission to schedule hosts")


def test_my_hosts_success(mock_shell):
    """Test my_hosts command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 1, "owner": "test@example.com", "cloud": "cloud02"}
    ]
    mock_shell.connection.api.get_schedules.return_value = [
        {"id": 1, "host": {"name": "host01.example.com"}, "start": "2026-05-01", "end": "2026-05-15"}
    ]

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    mock_shell.connection.api.filter_assignments.assert_called_once_with({"owner": "test@example.com"})
    mock_shell.connection.api.get_schedules.assert_called_once_with({"assignment_id": 1})
    assert mock_shell.poutput.call_count >= 2


def test_my_hosts_no_schedules(mock_shell):
    """Test my_hosts with no schedules"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_assignments.return_value = []

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    mock_shell.poutput.assert_called_with("No hosts scheduled by test@example.com")


def test_my_hosts_not_authenticated(mock_shell):
    """Test my_hosts when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_schedule_not_authenticated(mock_shell):
    """Test schedule when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule("host01.example.com cloud02")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")
