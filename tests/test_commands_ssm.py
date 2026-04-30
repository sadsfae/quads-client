import pytest
from unittest.mock import MagicMock
from quads_client.commands.ssm import SSMCommands


def test_ssm_available_success(mock_shell):
    """Test ssm-available command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_hosts.return_value = [
        {"name": "host01.example.com", "can_self_schedule": True},
        {"name": "host02.example.com", "can_self_schedule": True},
        {"name": "host03.example.com", "can_self_schedule": False},
    ]

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_available("")

    mock_shell.connection.api.filter_hosts.assert_called_once_with(
        {"cloud": "cloud01", "retired": False, "broken": False}
    )
    # Should only show hosts with can_self_schedule=True
    assert mock_shell.poutput.call_count >= 2


def test_ssm_available_no_hosts(mock_shell):
    """Test ssm-available with no available hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_hosts.return_value = []

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_available("")

    mock_shell.poutput.assert_called_with("No available hosts for self-scheduling")


def test_ssm_available_not_connected(mock_shell):
    """Test ssm-available when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_available("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_schedule_success(mock_shell):
    """Test ssm-schedule command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.create_schedule.return_value = {"id": 1, "status": "success"}

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_schedule("host01.example.com cloud02")

    mock_shell.connection.api.create_schedule.assert_called_once_with(
        {"hostname": "host01.example.com", "cloud": "cloud02"}
    )
    mock_shell.poutput.assert_called()


def test_ssm_schedule_missing_args(mock_shell):
    """Test ssm-schedule with missing arguments"""
    mock_shell.connection.is_connected = True

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_schedule("host01.example.com")

    mock_shell.perror.assert_any_call("Usage: ssm-schedule <hostname> <cloud>")


def test_ssm_schedule_forbidden(mock_shell):
    """Test ssm-schedule when user lacks permission"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.create_schedule.side_effect = Exception("403 Forbidden")

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_schedule("host01.example.com cloud02")

    mock_shell.perror.assert_called_with("Error: You don't have permission to schedule hosts")


def test_ssm_my_hosts_success(mock_shell):
    """Test ssm-my-hosts command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 1, "owner": "test@example.com", "cloud": "cloud02"}
    ]
    mock_shell.connection.api.get_schedules.return_value = [
        {"id": 1, "host": {"name": "host01.example.com"}, "start": "2026-05-01", "end": "2026-05-15"}
    ]

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_my_hosts("")

    mock_shell.connection.api.filter_assignments.assert_called_once_with({"owner": "test@example.com"})
    mock_shell.connection.api.get_schedules.assert_called_once_with({"assignment_id": 1})
    assert mock_shell.poutput.call_count >= 2


def test_ssm_my_hosts_no_schedules(mock_shell):
    """Test ssm-my-hosts with no schedules"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_assignments.return_value = []

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_my_hosts("")

    mock_shell.poutput.assert_called_with("No hosts scheduled by test@example.com")


def test_ssm_my_hosts_not_connected(mock_shell):
    """Test ssm-my-hosts when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_my_hosts("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_schedule_not_connected(mock_shell):
    """Test ssm-schedule when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_schedule("host01.example.com cloud02")

    mock_shell.perror.assert_called_with("Not connected to any server")
