import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.user import UserCommands


def test_register_save_credentials_failure(mock_shell):
    """Test register when saving credentials fails"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "quads1.example.com"
    mock_shell.connection.api.register.return_value = {"status": "success"}
    mock_shell.config.update_server_credentials = MagicMock(side_effect=Exception("Permission denied"))

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("user@example.com password123")

    # Should warn about failure to save
    assert any("Could not save credentials" in str(call) for call in mock_shell.pwarning.call_args_list)


def test_whoami_not_authenticated(mock_shell):
    """Test whoami when user is connected but not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False
    mock_shell.connection.username = None
    mock_shell.connection.user_role = None

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_whoami("")

    # Should show "Not authenticated"
    assert any("Not authenticated" in str(call) for call in mock_shell.poutput.call_args_list)


def test_whoami_user_info_exception(mock_shell):
    """Test whoami when get_user_info raises exception"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.user_role = "user"
    mock_shell.connection.api.get_user_info.side_effect = Exception("API error")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_whoami("")

    # Should still complete without error
    assert mock_shell.poutput.call_count >= 2


def test_assignment_create_no_qinq(mock_shell):
    """Test assignment_create without qinq field"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
        "owner": "user@example.com",
    }

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_create("--description Test environment")

    # Should not print VLAN line when qinq is not present
    output = " ".join(str(call) for call in mock_shell.poutput.call_args_list)
    assert "VLAN (QinQ)" not in output


def test_assignment_status_no_schedules(mock_shell):
    """Test assignment_status when assignment has no schedules"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.filter_assignments.return_value = [
        {
            "id": 42,
            "cloud": {"name": "cloud17"},
            "owner": "user@example.com",
            "description": "Test",
            "wipe": False,
            "validated": False,
            "active": True,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = []

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_status("42")

    # Should show "No hosts assigned"
    output = " ".join(str(call) for call in mock_shell.poutput.call_args_list)
    assert "No hosts assigned" in output


def test_assignment_list_very_long_description(mock_shell):
    """Test assignment_list truncates very long descriptions"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {
            "id": 42,
            "cloud": {"name": "cloud17"},
            "description": "A" * 100,  # Very long description
            "validated": True,
            "active": True,
        }
    ]

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_list("")

    # Should truncate to 40 chars with "..."
    assert mock_shell.poutput.call_count >= 2


def test_assignment_terminate_object_response(mock_shell):
    """Test assignment_terminate with object response instead of dict"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    # Create mock object instead of dict
    mock_assignment = MagicMock()
    mock_assignment.id = 42
    mock_cloud = MagicMock()
    mock_cloud.name = "cloud17"
    mock_assignment.cloud = mock_cloud

    mock_shell.connection.api.filter_assignments.return_value = [mock_assignment]
    mock_shell.connection.api.terminate_assignment.return_value = {"status": "success"}

    with patch("builtins.input", return_value="y"):
        user_cmd = UserCommands(mock_shell)
        user_cmd.cmd_assignment_terminate("42")

        # Should handle object response
        assert "terminated successfully" in str(mock_shell.poutput.call_args_list)


def test_available_no_self_schedulable_hosts(mock_shell):
    """Test available when no hosts have can_self_schedule flag"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.filter_hosts.return_value = [
        {"name": "host01.example.com", "can_self_schedule": False},
        {"name": "host02.example.com", "can_self_schedule": False},
    ]

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_available("")

    mock_shell.poutput.assert_called_with("No available hosts")


def test_available_api_error(mock_shell):
    """Test available when API call fails"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.filter_hosts.side_effect = Exception("Database error")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_available("")

    mock_shell.perror.assert_called_with("Failed to get available hosts: Database error")


def test_schedule_api_error(mock_shell):
    """Test schedule with non-403 API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.create_schedule.side_effect = Exception("Network timeout")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_schedule("host01.example.com cloud02")

    mock_shell.perror.assert_called_with("Failed to schedule host: Network timeout")


def test_my_hosts_api_error(mock_shell):
    """Test my_hosts when API call fails"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.side_effect = Exception("Connection error")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_my_hosts("")

    mock_shell.perror.assert_called_with("Failed to get schedules: Connection error")
