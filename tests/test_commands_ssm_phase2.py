import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.ssm import SSMCommands


def test_ssm_register_success(mock_shell):
    """Test ssm-register command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.register.return_value = {"status": "success", "message": "User registered"}

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_register("user@example.com password123")

    mock_shell.connection.api.register.assert_called_once_with({"email": "user@example.com", "password": "password123"})
    assert mock_shell.poutput.call_count >= 1


def test_ssm_register_missing_args(mock_shell):
    """Test ssm-register with missing arguments"""
    mock_shell.connection.is_connected = True

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_register("user@example.com")

    mock_shell.perror.assert_called_with("Usage: ssm-register <email> <password>")


def test_ssm_register_not_connected(mock_shell):
    """Test ssm-register when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_register("user@example.com password123")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_register_api_error(mock_shell):
    """Test ssm-register with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.register.side_effect = Exception("Registration failed")

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_register("user@example.com password123")

    mock_shell.perror.assert_called_with("Failed to register user: Registration failed")


def test_ssm_login_success(mock_shell):
    """Test ssm-login command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.login.return_value = {"auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_login("")

    mock_shell.connection.api.login.assert_called_once()
    assert mock_shell.poutput.call_count >= 1


def test_ssm_login_no_token(mock_shell):
    """Test ssm-login without token in response"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.login.return_value = {"status": "success"}

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_login("")

    mock_shell.poutput.assert_called_with("✓ Logged in successfully")


def test_ssm_login_not_connected(mock_shell):
    """Test ssm-login when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_login("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_login_api_error(mock_shell):
    """Test ssm-login with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.login.side_effect = Exception("Login failed")

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_login("")

    mock_shell.perror.assert_called_with("Failed to login: Login failed")


def test_ssm_create_success(mock_shell):
    """Test ssm-create command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
        "owner": "user@example.com",
        "qinq": 1234,
    }

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_create("--description My test environment --wipe true --qinq 1234")

    mock_shell.connection.api.create_self_assignment.assert_called_once()
    assert mock_shell.poutput.call_count >= 4


def test_ssm_create_multiword_description(mock_shell):
    """Test ssm-create with multi-word description"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
        "owner": "user@example.com",
    }

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_create("--description CI/CD pipeline testing environment --wipe false")

    call_args = mock_shell.connection.api.create_self_assignment.call_args[0][0]
    assert call_args["description"] == "CI/CD pipeline testing environment"
    assert call_args["wipe"] is False


def test_ssm_create_missing_description(mock_shell):
    """Test ssm-create without description"""
    mock_shell.connection.is_connected = True

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_create("--wipe true")

    mock_shell.perror.assert_called()


def test_ssm_create_not_connected(mock_shell):
    """Test ssm-create when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_create("--description Test")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_create_api_error(mock_shell):
    """Test ssm-create with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.create_self_assignment.side_effect = Exception("Creation failed")

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_create("--description Test environment")

    mock_shell.perror.assert_called_with("Failed to create self-assignment: Creation failed")


def test_ssm_status_success(mock_shell):
    """Test ssm-status command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_assignments.return_value = [
        {
            "id": 42,
            "cloud": {"name": "cloud17"},
            "owner": "user@example.com",
            "description": "Test environment",
            "ticket": "JIRA-123",
            "qinq": 1234,
            "wipe": True,
            "validated": True,
            "active": True,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = [
        {
            "host": {"name": "host01.example.com", "model": "r640"},
            "start": "2026-04-30 08:00",
            "end": "2026-05-30 08:00",
        }
    ]

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_status("42")

    mock_shell.connection.api.filter_assignments.assert_called_once_with({"id": 42})
    mock_shell.connection.api.get_schedules.assert_called_once_with({"assignment_id": 42})
    assert mock_shell.poutput.call_count >= 10


def test_ssm_status_not_found(mock_shell):
    """Test ssm-status with non-existent assignment"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_assignments.return_value = []

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_status("99")

    mock_shell.perror.assert_called_with("Assignment 99 not found")


def test_ssm_status_no_hosts(mock_shell):
    """Test ssm-status with no assigned hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_assignments.return_value = [
        {
            "id": 42,
            "cloud": {"name": "cloud17"},
            "owner": "user@example.com",
            "description": "Test environment",
            "wipe": False,
            "validated": False,
            "active": True,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = []

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_status("42")

    assert "No hosts assigned" in str(mock_shell.poutput.call_args_list)


def test_ssm_status_missing_args(mock_shell):
    """Test ssm-status without assignment ID"""
    mock_shell.connection.is_connected = True

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_status("")

    mock_shell.perror.assert_called_with("Usage: ssm-status <assignment_id>")


def test_ssm_status_not_connected(mock_shell):
    """Test ssm-status when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_status("42")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_list_success(mock_shell):
    """Test ssm-list command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {
            "id": 42,
            "cloud": {"name": "cloud17"},
            "description": "Test environment",
            "validated": True,
            "active": True,
        },
        {
            "id": 43,
            "cloud": {"name": "cloud18"},
            "description": "Development environment",
            "validated": False,
            "active": True,
        },
    ]

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_list("")

    mock_shell.connection.api.filter_assignments.assert_called_once_with({"owner": "user@example.com"})
    assert mock_shell.poutput.call_count >= 2


def test_ssm_list_empty(mock_shell):
    """Test ssm-list with no assignments"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = []

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_list("")

    mock_shell.poutput.assert_called_with("No assignments found for user@example.com")


def test_ssm_list_long_description(mock_shell):
    """Test ssm-list truncates long descriptions"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {
            "id": 42,
            "cloud": {"name": "cloud17"},
            "description": "This is a very long description that should be truncated to fit in the table",
            "validated": True,
            "active": True,
        },
    ]

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_list("")

    # Should truncate to 40 chars
    assert mock_shell.poutput.call_count >= 2


def test_ssm_list_not_connected(mock_shell):
    """Test ssm-list when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_list("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_terminate_success(mock_shell):
    """Test ssm-terminate command with confirmation"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 42, "cloud": {"name": "cloud17"}, "owner": "user@example.com"}
    ]

    with patch("builtins.input", return_value="y"):
        ssm_cmd = SSMCommands(mock_shell)
        ssm_cmd.cmd_ssm_terminate("42")

        mock_shell.connection.api.terminate_assignment.assert_called_once_with(42)
        mock_shell.poutput.assert_called_with("✓ Assignment 42 terminated successfully")


def test_ssm_terminate_rejected(mock_shell):
    """Test ssm-terminate with user rejection"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 42, "cloud": {"name": "cloud17"}, "owner": "user@example.com"}
    ]

    with patch("builtins.input", return_value="n"):
        ssm_cmd = SSMCommands(mock_shell)
        ssm_cmd.cmd_ssm_terminate("42")

        mock_shell.connection.api.terminate_assignment.assert_not_called()
        mock_shell.poutput.assert_called_with("Assignment not terminated")


def test_ssm_terminate_not_found(mock_shell):
    """Test ssm-terminate with non-existent assignment"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_assignments.return_value = []

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_terminate("99")

    mock_shell.perror.assert_called_with("Assignment 99 not found")


def test_ssm_terminate_missing_args(mock_shell):
    """Test ssm-terminate without assignment ID"""
    mock_shell.connection.is_connected = True

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_terminate("")

    mock_shell.perror.assert_called_with("Usage: ssm-terminate <assignment_id>")


def test_ssm_terminate_not_connected(mock_shell):
    """Test ssm-terminate when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_terminate("42")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_ssm_terminate_api_error(mock_shell):
    """Test ssm-terminate with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 42, "cloud": {"name": "cloud17"}}
    ]
    mock_shell.connection.api.terminate_assignment.side_effect = Exception("Termination failed")

    with patch("builtins.input", return_value="y"):
        ssm_cmd = SSMCommands(mock_shell)
        ssm_cmd.cmd_ssm_terminate("42")

        mock_shell.perror.assert_called_with("Failed to terminate assignment: Termination failed")


def test_ssm_whoami_success(mock_shell):
    """Test ssm-whoami command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_whoami("")

    assert mock_shell.poutput.call_count >= 1


def test_ssm_whoami_with_user_info(mock_shell):
    """Test ssm-whoami with user info API"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.get_user_info.return_value = {
        "email": "user@example.com",
        "roles": ["user", "developer"],
    }

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_whoami("")

    mock_shell.connection.api.get_user_info.assert_called_once()
    assert mock_shell.poutput.call_count >= 1


def test_ssm_whoami_no_user_info_api(mock_shell):
    """Test ssm-whoami when get_user_info not available"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.get_user_info = None

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_whoami("")

    # Should still show username
    assert mock_shell.poutput.call_count >= 1


def test_ssm_whoami_not_connected(mock_shell):
    """Test ssm-whoami when not connected"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    ssm_cmd.cmd_ssm_whoami("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_require_connection_helper(mock_shell):
    """Test _require_connection helper method"""
    mock_shell.connection.is_connected = False

    ssm_cmd = SSMCommands(mock_shell)
    result = ssm_cmd._require_connection()

    assert result is False
    mock_shell.perror.assert_called_with("Not connected to any server")


def test_require_connection_helper_connected(mock_shell):
    """Test _require_connection when connected"""
    mock_shell.connection.is_connected = True

    ssm_cmd = SSMCommands(mock_shell)
    result = ssm_cmd._require_connection()

    assert result is True
