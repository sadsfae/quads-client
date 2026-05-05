import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.user import UserCommands


def test_register_success(mock_shell):
    """Test register command with auto-login"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "quads1.example.com"
    mock_shell.connection.api.register.return_value = {"status": "success", "message": "User registered"}
    mock_shell.config.update_server_credentials = MagicMock()
    mock_shell.connection.disconnect = MagicMock()
    mock_shell.connection.connect = MagicMock()
    mock_shell._update_prompt = MagicMock()
    mock_shell._update_visible_commands = MagicMock()

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("user@example.com password123")

    # Should set credentials on API instance then call register()
    assert mock_shell.connection.api.username == "user@example.com"
    assert mock_shell.connection.api.password == "password123"
    mock_shell.connection.api.register.assert_called_once_with()
    mock_shell.config.update_server_credentials.assert_called_once_with(
        "quads1.example.com", "user@example.com", "password123"
    )
    # Should auto-reconnect after registration
    mock_shell.connection.disconnect.assert_called_once()
    mock_shell.connection.connect.assert_called_once_with("quads1.example.com")
    assert mock_shell.poutput.call_count >= 3


def test_register_missing_args(mock_shell):
    """Test register with missing arguments"""
    mock_shell.connection.is_connected = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("user@example.com")

    mock_shell.perror.assert_called_with("Usage: register <email> <password>")


def test_register_not_connected(mock_shell):
    """Test register when not connected"""
    mock_shell.connection.is_connected = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("user@example.com password123")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_register_api_error(mock_shell):
    """Test register with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.register.side_effect = Exception("Registration failed")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("user@example.com password123")

    mock_shell.perror.assert_called_with("Failed to register user: Registration failed")


def test_login_success(mock_shell):
    """Test login command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.login.return_value = {
        "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoidXNlciJ9.test"
    }
    mock_shell.connection._decode_role_from_token = MagicMock(return_value="user")
    mock_shell._update_visible_commands = MagicMock()

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_login("")

    mock_shell.connection.api.login.assert_called_once()
    mock_shell._update_visible_commands.assert_called_once()
    assert mock_shell.poutput.call_count >= 1


def test_login_no_token(mock_shell):
    """Test login without token in response"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.login.return_value = {"status": "success"}
    mock_shell._update_visible_commands = MagicMock()

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_login("")

    assert "Logged in successfully" in str(mock_shell.poutput.call_args_list)
    mock_shell._update_visible_commands.assert_called_once()


def test_login_not_connected(mock_shell):
    """Test login when not connected"""
    mock_shell.connection.is_connected = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_login("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_login_api_error(mock_shell):
    """Test login with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.login.side_effect = Exception("Login failed")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_login("")

    mock_shell.perror.assert_called_with("Failed to login: Login failed")


def test_assignment_create_success(mock_shell):
    """Test assignment_create command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
        "owner": "user@example.com",
        "qinq": 1234,
    }

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_create("--description My test environment --wipe true --qinq 1234")

    mock_shell.connection.api.create_self_assignment.assert_called_once()
    assert mock_shell.poutput.call_count >= 4


def test_assignment_create_multiword_description(mock_shell):
    """Test assignment_create with multi-word description"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.create_self_assignment.return_value = {
        "id": 42,
        "cloud": {"name": "cloud17"},
        "owner": "user@example.com",
    }

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_create("--description CI/CD pipeline testing environment --wipe false")

    call_args = mock_shell.connection.api.create_self_assignment.call_args[0][0]
    assert call_args["description"] == "CI/CD pipeline testing environment"
    assert call_args["wipe"] is False


def test_assignment_create_missing_description(mock_shell):
    """Test assignment_create without description"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_create("--wipe true")

    mock_shell.perror.assert_called()


def test_assignment_create_not_authenticated(mock_shell):
    """Test assignment_create when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_create("--description Test")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_assignment_create_api_error(mock_shell):
    """Test assignment_create with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.create_self_assignment.side_effect = Exception("Creation failed")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_create("--description Test environment")

    mock_shell.perror.assert_called_with("Failed to create assignment: Creation failed")


def test_assignment_status_success(mock_shell):
    """Test assignment_status command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
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

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_status("42")

    mock_shell.connection.api.filter_assignments.assert_called_once_with({"id": 42})
    mock_shell.connection.api.get_schedules.assert_called_once_with({"assignment_id": 42})
    assert mock_shell.poutput.call_count >= 10


def test_assignment_status_not_found(mock_shell):
    """Test assignment_status with non-existent assignment"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.api.filter_assignments.return_value = []

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_status("99")

    mock_shell.perror.assert_called_with("Assignment 99 not found")


def test_assignment_status_no_hosts(mock_shell):
    """Test assignment_status with no assigned hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
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

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_status("42")

    assert "No hosts assigned" in str(mock_shell.poutput.call_args_list)


def test_assignment_status_missing_args(mock_shell):
    """Test assignment_status without assignment ID"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_status("")

    mock_shell.perror.assert_called_with("Usage: assignment-status <assignment_id>")


def test_assignment_status_not_authenticated(mock_shell):
    """Test assignment_status when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_status("42")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_assignment_list_success(mock_shell):
    """Test assignment_list command (calls my_assignments, shows only active)"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
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

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_list("")

    mock_shell.connection.api.filter_assignments.assert_called_once_with({"owner": "user", "active": True})
    assert mock_shell.poutput.call_count >= 2


def test_assignment_list_empty(mock_shell):
    """Test assignment_list with no active assignments"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = []

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_list("")

    mock_shell.poutput.assert_called_with("No active assignments found for user")


def test_assignment_list_long_description(mock_shell):
    """Test assignment_list truncates long descriptions"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
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

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_list("")

    # Should truncate to 40 chars
    assert mock_shell.poutput.call_count >= 2


def test_assignment_list_not_authenticated(mock_shell):
    """Test assignment_list when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_assignment_list("")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_assignment_terminate_success(mock_shell):
    """Test release command (supersedes assignment_terminate) with confirmation"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 42, "cloud": {"name": "cloud17"}, "owner": "user"}
    ]
    mock_shell.connection.api.terminate_assignment.return_value = {"status": "success"}

    with patch("builtins.input", return_value="y"):
        user_cmd = UserCommands(mock_shell)
        user_cmd.cmd_release("42")

        mock_shell.connection.api.terminate_assignment.assert_called_once_with(42)
        assert "Terminated assignment" in str(mock_shell.poutput.call_args_list)


def test_assignment_terminate_rejected(mock_shell):
    """Test release command with user rejection"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 42, "cloud": {"name": "cloud17"}, "owner": "user"}
    ]

    with patch("builtins.input", return_value="n"):
        user_cmd = UserCommands(mock_shell)
        user_cmd.cmd_release("42")

        mock_shell.connection.api.terminate_assignment.assert_not_called()
        mock_shell.poutput.assert_called_with("Assignment not terminated")


def test_assignment_terminate_error_response(mock_shell):
    """Test release command with error in API response"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 42, "cloud": {"name": "cloud17"}, "owner": "user"}
    ]
    mock_shell.connection.api.terminate_assignment.return_value = {
        "status": "error",
        "message": "Assignment still has active hosts",
    }

    with patch("builtins.input", return_value="y"):
        user_cmd = UserCommands(mock_shell)
        user_cmd.cmd_release("42")

        mock_shell.perror.assert_called_with("Failed to terminate: Assignment still has active hosts")


def test_assignment_terminate_not_found(mock_shell):
    """Test release command with non-existent assignment"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = []

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_release("99")

    mock_shell.perror.assert_called_with("Assignment 99 not found")


def test_assignment_terminate_missing_args(mock_shell):
    """Test release command without assignment ID"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_release("")

    # Should show usage help
    assert any("Usage: release" in str(call) for call in mock_shell.poutput.call_args_list)


def test_assignment_terminate_help_question_mark(mock_shell):
    """Test release command with ? shows help"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_release("?")

    # Should show usage help
    assert any("Usage: release" in str(call) for call in mock_shell.poutput.call_args_list)
    assert any("Examples:" in str(call) for call in mock_shell.poutput.call_args_list)


def test_assignment_terminate_invalid_id(mock_shell):
    """Test release command with invalid assignment ID"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_release("abc")

    # Should error about invalid ID
    assert any("Invalid assignment ID" in str(call) for call in mock_shell.perror.call_args_list)


def test_assignment_terminate_not_authenticated(mock_shell):
    """Test release command when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_release("42")

    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_assignment_terminate_api_error(mock_shell):
    """Test release command with API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = False
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.api.filter_assignments.return_value = [
        {"id": 42, "cloud": {"name": "cloud17"}, "owner": "user"}
    ]
    mock_shell.connection.api.terminate_assignment.side_effect = Exception("Termination failed")

    with patch("builtins.input", return_value="y"):
        user_cmd = UserCommands(mock_shell)
        user_cmd.cmd_release("42")

        # Should handle error via error_handler
        mock_shell.perror.assert_called()


def test_whoami_success(mock_shell):
    """Test whoami command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.user_role = "user"

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_whoami("")

    assert mock_shell.poutput.call_count >= 3


def test_whoami_with_user_info(mock_shell):
    """Test whoami with user info API"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.user_role = "admin"
    mock_shell.connection.api.get_user_info.return_value = {
        "email": "user@example.com",
        "roles": ["admin", "developer"],
    }

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_whoami("")

    mock_shell.connection.api.get_user_info.assert_called_once()
    assert mock_shell.poutput.call_count >= 4


def test_whoami_no_user_info_api(mock_shell):
    """Test whoami when get_user_info not available"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.username = "user@example.com"
    mock_shell.connection.user_role = "user"
    mock_shell.connection.api.get_user_info = None

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_whoami("")

    # Should still show username
    assert mock_shell.poutput.call_count >= 3


def test_whoami_not_connected(mock_shell):
    """Test whoami when not connected"""
    mock_shell.connection.is_connected = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_whoami("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_require_connection_helper(mock_shell):
    """Test _require_connection helper method"""
    mock_shell.connection.is_connected = False

    user_cmd = UserCommands(mock_shell)
    result = user_cmd._require_connection()

    assert result is False
    mock_shell.perror.assert_called_with("Not connected to any server")


def test_require_connection_helper_connected(mock_shell):
    """Test _require_connection when connected"""
    mock_shell.connection.is_connected = True

    user_cmd = UserCommands(mock_shell)
    result = user_cmd._require_connection()

    assert result is True


def test_require_auth_helper_not_connected(mock_shell):
    """Test _require_auth when not connected"""
    mock_shell.connection.is_connected = False

    user_cmd = UserCommands(mock_shell)
    result = user_cmd._require_auth()

    assert result is False
    mock_shell.perror.assert_called_with("Not connected to any server")


def test_require_auth_helper_not_authenticated(mock_shell):
    """Test _require_auth when not authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = False

    user_cmd = UserCommands(mock_shell)
    result = user_cmd._require_auth()

    assert result is False
    mock_shell.perror.assert_called_with("Not authenticated. Use 'login' command first.")


def test_require_auth_helper_authenticated(mock_shell):
    """Test _require_auth when authenticated"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True

    user_cmd = UserCommands(mock_shell)
    result = user_cmd._require_auth()

    assert result is True
