import pytest
from unittest.mock import MagicMock
from quads_client.commands.user import UserCommands


def test_register_new_user_success(mock_shell):
    """Test successful registration of a new user"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"
    mock_shell.connection.api.username = None
    mock_shell.connection.api.password = None

    # Mock successful registration (no "already exists" message)
    mock_shell.connection.api.register.return_value = {"status": "success", "message": "Welcome!"}

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("newuser@example.com password123")

    # Should save credentials for new user
    mock_shell.config.update_server_credentials.assert_called_once_with(
        "test_server", "newuser@example.com", "password123"
    )
    # Should attempt auto-login
    mock_shell.connection.disconnect.assert_called_once()
    mock_shell.connection.connect.assert_called_once_with("test_server")


def test_register_existing_user_no_save(mock_shell):
    """Test registration attempt with existing user - should NOT save credentials"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"
    mock_shell.connection.api.username = None
    mock_shell.connection.api.password = None

    # Mock registration response for existing user
    mock_shell.connection.api.register.return_value = {
        "status": "error",
        "message": "User already exists. Please Log in.",
    }

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("existing@example.com wrongpassword")

    # Should NOT save credentials
    mock_shell.config.update_server_credentials.assert_not_called()
    # Should NOT attempt auto-login
    mock_shell.connection.disconnect.assert_not_called()
    # Should show warning
    mock_shell.pwarning.assert_called()
    # Check for helpful error messages
    warning_calls = [call[0][0] for call in mock_shell.pwarning.call_args_list]
    assert any("already registered" in str(call).lower() for call in warning_calls)


def test_register_existing_user_case_insensitive(mock_shell):
    """Test that 'Already Exists' message is detected case-insensitively"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"

    # Test various case variations
    messages = [
        "User already exists. Please Log in.",
        "USER ALREADY EXISTS",
        "Email Already Exists",
        "Account already exists, please login",
    ]

    for message in messages:
        mock_shell.reset_mock()
        mock_shell.connection.api.register.return_value = {"status": "error", "message": message}

        user_cmd = UserCommands(mock_shell)
        user_cmd.cmd_register("test@example.com password")

        # Should NOT save credentials for any variation
        mock_shell.config.update_server_credentials.assert_not_called()


def test_register_no_args(mock_shell):
    """Test register command with no arguments"""
    mock_shell.connection.is_connected = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("")

    mock_shell.perror.assert_called_with("Usage: register <email> <password>")


def test_register_missing_password(mock_shell):
    """Test register command with missing password"""
    mock_shell.connection.is_connected = True

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("user@example.com")

    mock_shell.perror.assert_called_with("Usage: register <email> <password>")


def test_register_not_connected(mock_shell):
    """Test register command when not connected"""
    mock_shell.connection.is_connected = False

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("user@example.com password123")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_register_auto_login_failure(mock_shell):
    """Test registration with auto-login failure"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"
    mock_shell.connection.api.register.return_value = {"status": "success"}
    mock_shell.connection.connect.side_effect = Exception("Connection failed")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("newuser@example.com password123")

    # Should still save credentials
    mock_shell.config.update_server_credentials.assert_called_once()
    # Should warn about login failure
    mock_shell.pwarning.assert_called()


def test_register_save_credentials_failure(mock_shell):
    """Test registration when saving credentials fails"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.current_server = "test_server"
    mock_shell.connection.api.register.return_value = {"status": "success"}
    mock_shell.config.update_server_credentials.side_effect = Exception("Config write failed")

    user_cmd = UserCommands(mock_shell)
    user_cmd.cmd_register("newuser@example.com password123")

    # Should warn about save failure
    mock_shell.pwarning.assert_called()
    warning_calls = [call[0][0] for call in mock_shell.pwarning.call_args_list]
    assert any("save credentials" in str(call).lower() for call in warning_calls)
