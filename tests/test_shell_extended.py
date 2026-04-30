import pytest
from unittest.mock import MagicMock, patch
from quads_client.shell import QuadsClientShell
from quads_client.config import ConfigError


def test_shell_init_no_config():
    """Test shell initialization when config fails to load"""
    with patch("quads_client.shell.QuadsClientConfig", side_effect=ConfigError("Config not found")):
        shell = QuadsClientShell()
        # Should handle config error gracefully
        assert shell.config is None


def test_shell_shorten_server_name():
    """Test server name shortening"""
    with patch("quads_client.shell.QuadsClientConfig"):
        with patch("quads_client.shell.ConnectionManager"):
            shell = QuadsClientShell()

            # Test with long name (more than 3 segments)
            short = shell._shorten_server_name("quads2-dev.rdu2.scalelab.redhat.com")
            assert short == "quads2-dev.rdu2.scalelab"

            # Test with already short name
            short = shell._shorten_server_name("quads.example.com")
            assert short == "quads.example.com"


def test_shell_update_prompt_disconnected():
    """Test prompt update when disconnected"""
    with patch("quads_client.shell.QuadsClientConfig"):
        with patch("quads_client.shell.ConnectionManager") as mock_conn:
            shell = QuadsClientShell()
            shell.connection = mock_conn.return_value
            shell.connection.is_connected = False

            shell._update_prompt()
            assert "(disconnected)" in shell.prompt


def test_shell_update_prompt_connected():
    """Test prompt update when connected"""
    with patch("quads_client.shell.QuadsClientConfig"):
        with patch("quads_client.shell.ConnectionManager") as mock_conn:
            shell = QuadsClientShell()
            shell.connection = mock_conn.return_value
            shell.connection.is_connected = True
            shell.connection.current_server = "quads1.rdu2.scalelab.redhat.com"

            shell._update_prompt()
            assert "quads1.rdu2.scalelab" in shell.prompt


def test_shell_update_visible_commands_not_authenticated():
    """Test command visibility when not authenticated"""
    with patch("quads_client.shell.QuadsClientConfig"):
        with patch("quads_client.shell.ConnectionManager") as mock_conn:
            shell = QuadsClientShell()
            shell.connection = mock_conn.return_value
            shell.connection.is_authenticated = False
            shell.connection.is_admin = False

            shell._update_visible_commands()

            # Admin commands should be hidden
            assert "cloud_create" in shell.hidden_commands
            assert "login" in shell.hidden_commands


def test_shell_update_visible_commands_user():
    """Test command visibility for authenticated non-admin user"""
    with patch("quads_client.shell.QuadsClientConfig"):
        with patch("quads_client.shell.ConnectionManager") as mock_conn:
            shell = QuadsClientShell()
            shell.connection = mock_conn.return_value
            shell.connection.is_authenticated = True
            shell.connection.is_admin = False

            shell._update_visible_commands()

            # Admin commands should be hidden, but auth commands should be visible
            assert "cloud_create" in shell.hidden_commands
            assert "login" not in shell.hidden_commands


def test_shell_update_visible_commands_admin():
    """Test command visibility for admin user"""
    with patch("quads_client.shell.QuadsClientConfig"):
        with patch("quads_client.shell.ConnectionManager") as mock_conn:
            shell = QuadsClientShell()
            shell.connection = mock_conn.return_value
            shell.connection.is_authenticated = True
            shell.connection.is_admin = True

            shell._update_visible_commands()

            # No admin commands should be hidden for admin
            assert "cloud_create" not in shell.hidden_commands
