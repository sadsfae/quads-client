import pytest
from unittest.mock import MagicMock, patch
from quads_client.shell import QuadsClientShell


def test_complete_connect_all_servers():
    """Test autocomplete for connect command shows all servers"""
    with patch("quads_client.shell.QuadsClientConfig"):
        shell = QuadsClientShell()
        shell.connection = MagicMock()
        shell.connection.get_available_servers.return_value = ["server1", "server2", "server3"]

        completions = shell.complete_connect("", "connect ", 8, 8)

        assert completions == ["server1", "server2", "server3"]


def test_complete_connect_filtered():
    """Test autocomplete for connect command filters by prefix"""
    with patch("quads_client.shell.QuadsClientConfig"):
        shell = QuadsClientShell()
        shell.connection = MagicMock()
        shell.connection.get_available_servers.return_value = ["server1", "server2", "staging"]

        completions = shell.complete_connect("ser", "connect ser", 8, 11)

        assert completions == ["server1", "server2"]


def test_complete_connect_no_connection():
    """Test autocomplete when not connected returns empty"""
    with patch("quads_client.shell.QuadsClientConfig"):
        shell = QuadsClientShell()
        shell.connection = None

        completions = shell.complete_connect("", "connect ", 8, 8)

        assert completions == []


def test_complete_connect_exact_match():
    """Test autocomplete with exact server prefix"""
    with patch("quads_client.shell.QuadsClientConfig"):
        shell = QuadsClientShell()
        shell.connection = MagicMock()
        shell.connection.get_available_servers.return_value = ["production", "prod-backup"]

        completions = shell.complete_connect("prod", "connect prod", 8, 12)

        assert "production" in completions
        assert "prod-backup" in completions


def test_complete_connect_no_match():
    """Test autocomplete with no matching servers"""
    with patch("quads_client.shell.QuadsClientConfig"):
        shell = QuadsClientShell()
        shell.connection = MagicMock()
        shell.connection.get_available_servers.return_value = ["server1", "server2"]

        completions = shell.complete_connect("xyz", "connect xyz", 8, 11)

        assert completions == []
