"""Tests for programmatic command variants (GUI/scripting support)"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import yaml


class TestServerCommandsProgrammatic:
    """Test programmatic server management methods"""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell"""
        shell = MagicMock()
        shell.config = MagicMock()
        shell.config.config_path = "/tmp/test_config.yml"
        shell.config.get_all_servers.return_value = {}
        shell.poutput = MagicMock()
        shell.perror = MagicMock()
        shell.pwarning = MagicMock()
        return shell

    @pytest.fixture
    def server_commands(self, mock_shell):
        """Create ServerCommands instance"""
        from quads_client.commands.server import ServerCommands

        return ServerCommands(mock_shell)

    def test_add_server_programmatic_success(self, server_commands, mock_shell):
        """Test adding server programmatically succeeds"""
        # Mock config file operations
        mock_config_data = {"servers": {}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                with patch("yaml.dump") as mock_dump:
                    with patch("requests.get") as mock_get:
                        # Mock successful server connection
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"version": "2.2.6"}
                        mock_get.return_value = mock_response

                        success, message, version = server_commands.add_server_programmatic(
                            name="test-server",
                            url="https://test.example.com",
                            username="test@example.com",
                            password="testpass",
                            verify=True,
                            test_connection=True,
                        )

                        assert success is True
                        assert "successfully" in message.lower()
                        assert version == "2.2.6"

    def test_add_server_programmatic_connection_failure(self, server_commands):
        """Test adding server with connection failure"""
        with patch("builtins.open", mock_open(read_data=yaml.dump({"servers": {}}))):
            with patch("yaml.safe_load", return_value={"servers": {}}):
                with patch("requests.get") as mock_get:
                    # Mock connection failure
                    mock_get.side_effect = Exception("Connection timeout")

                    success, message, version = server_commands.add_server_programmatic(
                        name="test-server",
                        url="https://test.example.com",
                        username="",
                        password="",
                        verify=True,
                        test_connection=True,
                    )

                    assert success is False
                    assert "Could not connect" in message
                    assert version is None

    def test_add_server_programmatic_skip_connection_test(self, server_commands):
        """Test adding server without connection test"""
        mock_config_data = {"servers": {}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                with patch("yaml.dump"):
                    success, message, version = server_commands.add_server_programmatic(
                        name="test-server",
                        url="https://test.example.com",
                        username="",
                        password="",
                        verify=True,
                        test_connection=False,
                    )

                    assert success is True
                    assert version is None  # No connection test = no version

    def test_add_server_programmatic_duplicate(self, server_commands):
        """Test adding duplicate server"""
        mock_config_data = {
            "servers": {"test-server": {"url": "https://existing.example.com", "username": "", "password": ""}}
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config_data))):
            with patch("yaml.safe_load", return_value=mock_config_data):
                success, message, version = server_commands.add_server_programmatic(
                    name="test-server",
                    url="https://test.example.com",
                    username="",
                    password="",
                    verify=True,
                    test_connection=False,
                )

                assert success is False
                assert "already exists" in message.lower()


class TestUserCommandsProgrammatic:
    """Test programmatic user command methods"""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell with connection"""
        shell = MagicMock()
        shell.config = MagicMock()
        shell.config.config_path = "/tmp/test_config.yml"
        shell.config.get_server_url.return_value = "https://test.example.com"
        shell.config.get_server_verify.return_value = True

        # Mock connection
        mock_connection = MagicMock()
        mock_connection.is_connected = True
        mock_connection.is_authenticated = False
        mock_connection.current_server = "test-server"
        mock_connection.api = MagicMock()
        mock_connection._decode_role_from_token = MagicMock(return_value="user")

        shell.connection = mock_connection
        shell.session_manager = MagicMock()
        shell.session_manager.active_connection = mock_connection

        shell.poutput = MagicMock()
        shell.perror = MagicMock()
        shell.pwarning = MagicMock()
        shell._update_visible_commands = MagicMock()

        return shell

    @pytest.fixture
    def user_commands(self, mock_shell):
        """Create UserCommands instance"""
        from quads_client.commands.user import UserCommands

        return UserCommands(mock_shell)

    def test_login_programmatic_success(self, user_commands, mock_shell):
        """Test programmatic login succeeds"""
        with patch("quads_lib.QuadsApi") as mock_api_class:
            # Mock QuadsApi instance
            mock_api = MagicMock()
            mock_api.login.return_value = {"auth_token": "test_token_123", "status": "success"}
            mock_api.token = "test_token_123"
            mock_api_class.return_value = mock_api

            success, message, role = user_commands.login_programmatic(email="test@example.com", password="testpass")

            assert success is True
            assert "successfully" in message.lower()
            # Verify connection was updated
            assert mock_shell.connection._api == mock_api
            assert mock_shell.connection._token == "test_token_123"
            assert mock_shell.connection._username == "test@example.com"
            assert mock_shell.connection._registration_mode is False

    def test_login_programmatic_failure(self, user_commands, mock_shell):
        """Test programmatic login fails"""
        with patch("quads_lib.QuadsApi") as mock_api_class:
            # Mock failed login
            mock_api = MagicMock()
            mock_api.login.side_effect = Exception("Invalid credentials")
            mock_api_class.return_value = mock_api

            success, message, role = user_commands.login_programmatic(email="test@example.com", password="wrongpass")

            assert success is False
            assert "Failed to login" in message
            assert role is None

    def test_login_programmatic_not_connected(self, user_commands, mock_shell):
        """Test programmatic login when not connected"""
        mock_shell.connection = None

        success, message, role = user_commands.login_programmatic(email="test@example.com", password="testpass")

        assert success is False
        assert "Not connected" in message
        assert role is None

    def test_login_programmatic_updates_role(self, user_commands, mock_shell):
        """Test programmatic login updates user role"""
        with patch("quads_lib.QuadsApi") as mock_api_class:
            mock_api = MagicMock()
            mock_api.login.return_value = {"auth_token": "test_token_123", "status": "success"}
            mock_api.token = "test_token_123"
            mock_api_class.return_value = mock_api

            # Mock role detection
            mock_shell.connection._decode_role_from_token.return_value = "admin"

            success, message, role = user_commands.login_programmatic(email="admin@example.com", password="adminpass")

            assert success is True
            assert role == "admin"
            assert mock_shell.connection._user_role == "admin"
            mock_shell._update_visible_commands.assert_called_once()
