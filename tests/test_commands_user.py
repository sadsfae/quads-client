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


def test_available_help(mock_shell):
    """Test available command help with ?"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_available("?")

    # Should print help, not call API
    assert any("Usage:" in str(call) for call in mock_shell.poutput.call_args_list)
    mock_shell.connection.api.filter_hosts.assert_not_called()


def test_available_help_dash_h(mock_shell):
    """Test available command help with -h"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_available("-h")

    # Should print help, not call API
    assert any("Usage:" in str(call) for call in mock_shell.poutput.call_args_list)
    mock_shell.connection.api.filter_hosts.assert_not_called()


def test_schedule_success(mock_shell):
    """Test schedule command success - superseded by test_commands_unified_schedule.py"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_available.return_value = [{"name": "host01.example.com"}]
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
    }
    mock_shell.connection.api.create_schedule.return_value = {"id": 1}

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule('host01.example.com description "Test"')

    mock_shell.poutput.assert_called()


def test_schedule_missing_args(mock_shell):
    """Test schedule with missing arguments - superseded by test_commands_unified_schedule.py"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule("host01.example.com")

    mock_shell.perror.assert_called()


def test_schedule_forbidden(mock_shell):
    """Test schedule when user lacks permission - superseded by test_commands_unified_schedule.py"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_available.return_value = [{"name": "host01.example.com"}]
    mock_shell.connection.api.create_self_assignment.side_effect = Exception("403 Forbidden")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule('host01.example.com description "Test"')

    mock_shell.perror.assert_called()


def test_my_hosts_success(mock_shell):
    """Test my_hosts command success - updated for unified schedule"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 1, "owner": "test", "cloud": {"name": "cloud02"}, "description": "Test assignment"}
    ]
    mock_shell.connection.api.get_current_schedules.return_value = [
        {"id": 1, "host": {"name": "host01.example.com"}, "start": "2026-05-01", "end": "2026-05-15"}
    ]

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    mock_shell.connection.api.filter_assignments.assert_called_once_with({"owner": "test", "active": True})
    mock_shell.connection.api.get_current_schedules.assert_called_once_with({"assignment_id": 1})
    assert mock_shell.poutput.call_count >= 2


def test_my_hosts_no_schedules(mock_shell):
    """Test my_hosts with no schedules"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "test@example.com"
    mock_shell.connection.api.filter_assignments.return_value = []

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    mock_shell.poutput.assert_called_with("No active hosts scheduled by test")


def test_my_hosts_not_authenticated(mock_shell):
    """Test my_hosts when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_my_hosts_duplicate_hosts_across_assignments(mock_shell):
    """Test my_hosts deduplicates hosts that appear in multiple assignments"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "test@example.com"

    # Three assignments with same 3 hosts in each (simulating the user's bug report)
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 138, "owner": "test", "cloud": {"name": "cloud02"}, "description": "SSM QUADS Client Test2"},
        {"id": 139, "owner": "test", "cloud": {"name": "cloud03"}, "description": "SSM QUADS Client Test3"},
        {"id": 140, "owner": "test", "cloud": {"name": "cloud04"}, "description": "SSM QUADS Client Test4"},
    ]

    # Each assignment has the same 3 hosts (simulating duplicate schedules)
    def mock_get_current_schedules(filters):
        return [
            {
                "id": 1,
                "host": {"name": "e28-h26-000-r650.stage.rdu2.scalelab.redhat.com"},
                "end": "Sun, 10 May 2026 21:00:00 GMT",
            },
            {
                "id": 2,
                "host": {"name": "f07-h36-000-1029u.stage.rdu2.scalelab.redhat.com"},
                "end": "Sun, 10 May 2026 21:00:00 GMT",
            },
            {
                "id": 3,
                "host": {"name": "f18-h29-000-1029p.stage.rdu2.scalelab.redhat.com"},
                "end": "Sun, 10 May 2026 21:00:00 GMT",
            },
        ]

    mock_shell.connection.api.get_current_schedules.side_effect = mock_get_current_schedules

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    # Verify we queried for assignments
    mock_shell.connection.api.filter_assignments.assert_called_once_with({"owner": "test", "active": True})

    # Verify poutput was called (for header, table, and total)
    assert mock_shell.poutput.call_count >= 3

    # Verify the last call shows "Total unique hosts: 3" (not 9)
    last_call = str(mock_shell.poutput.call_args_list[-1])
    assert "Total unique hosts: 3" in last_call


def test_schedule_not_authenticated(mock_shell):
    """Test schedule when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule("host01.example.com cloud02")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_schedule_count_with_dict_hosts(mock_shell):
    """Test schedule with count mode when API returns dicts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "test@example.com"

    # API returns list of dicts
    mock_shell.connection.api.filter_available.return_value = [
        {"name": "host01.example.com"},
        {"name": "host02.example.com"},
    ]
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
    }
    mock_shell.connection.api.create_schedule.return_value = {"id": 1}

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule('2 description "Test"')

    # Should create schedule for 2 hosts
    assert mock_shell.connection.api.create_schedule.call_count == 2


def test_schedule_count_with_object_hosts(mock_shell):
    """Test schedule with count mode when API returns objects"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "test@example.com"

    # API returns list of objects with name attribute
    class HostObj:
        def __init__(self, name):
            self.name = name

    mock_shell.connection.api.filter_available.return_value = [
        HostObj("host01.example.com"),
        HostObj("host02.example.com"),
    ]
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
    }
    mock_shell.connection.api.create_schedule.return_value = {"id": 1}

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule('2 description "Test"')

    # Should create schedule for 2 hosts
    assert mock_shell.connection.api.create_schedule.call_count == 2


def test_terminate_help(mock_shell):
    """Test terminate command with help flag"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_terminate("?")

    # Should print usage, not error
    assert any("Usage:" in str(call) for call in mock_shell.poutput.call_args_list)


def test_terminate_help_dash_h(mock_shell):
    """Test terminate command with -h flag"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_terminate("-h")

    # Should print usage, not error
    assert any("Usage:" in str(call) for call in mock_shell.poutput.call_args_list)


def test_terminate_help_help_flag(mock_shell):
    """Test terminate command with --help flag"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_terminate("--help")

    # Should print usage, not error
    assert any("Usage:" in str(call) for call in mock_shell.poutput.call_args_list)


def test_schedule_count_with_string_hosts(mock_shell):
    """Test schedule with count mode when API returns plain strings"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "test@example.com"

    # API returns list of plain hostname strings (new behavior)
    mock_shell.connection.api.filter_available.return_value = [
        "host01.example.com",
        "host02.example.com",
    ]
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
    }
    mock_shell.connection.api.create_schedule.return_value = {"id": 1}

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule('2 description "Test"')

    # Should create schedule for 2 hosts
    assert mock_shell.connection.api.create_schedule.call_count == 2
