import pytest
from unittest.mock import MagicMock, patch
from quads_client.connection import ConnectionManager, ConnectionError


def test_connection_initial_state(mock_config):
    """Test ConnectionManager initial state"""
    conn = ConnectionManager(mock_config)
    assert not conn.is_connected
    assert conn.current_server is None
    assert conn.username is None


def test_connection_connect_success(mock_config, mock_api):
    """Test successful connection to server"""
    with patch("quads_client.connection.QuadsApi", return_value=mock_api):
        conn = ConnectionManager(mock_config)
        conn.connect("test_server")

        assert conn.is_connected
        assert conn.current_server == "test_server"
        assert conn.username == "test@example.com"
        assert conn._token == "test_token_123"
        mock_api.login.assert_called_once()


def test_connection_connect_invalid_server(mock_config):
    """Test connecting to unknown server"""
    conn = ConnectionManager(mock_config)
    with pytest.raises(ConnectionError, match="Unknown server"):
        conn.connect("nonexistent_server")


def test_connection_connect_missing_credentials(mock_config):
    """Test connecting with missing credentials"""
    mock_config.get_server_credentials.return_value = (None, None)
    conn = ConnectionManager(mock_config)

    with pytest.raises(ConnectionError, match="missing credentials"):
        conn.connect("test_server")


def test_connection_connect_login_failure(mock_config, mock_api):
    """Test connection when login fails"""
    mock_api.login.return_value = {"status": "failure"}

    with patch("quads_client.connection.QuadsApi", return_value=mock_api):
        conn = ConnectionManager(mock_config)
        with pytest.raises(ConnectionError, match="Login failed"):
            conn.connect("test_server")


def test_connection_api_property_when_disconnected(mock_config):
    """Test accessing API property when not connected"""
    conn = ConnectionManager(mock_config)
    with pytest.raises(ConnectionError, match="Not connected"):
        _ = conn.api


def test_connection_api_property_when_connected(mock_config, mock_api):
    """Test accessing API property when connected"""
    with patch("quads_client.connection.QuadsApi", return_value=mock_api):
        conn = ConnectionManager(mock_config)
        conn.connect("test_server")
        assert conn.api == mock_api


def test_connection_disconnect(mock_config, mock_api):
    """Test disconnecting from server"""
    with patch("quads_client.connection.QuadsApi", return_value=mock_api):
        conn = ConnectionManager(mock_config)
        conn.connect("test_server")
        assert conn.is_connected

        conn.disconnect()
        assert not conn.is_connected
        assert conn.current_server is None
        assert conn.username is None
        assert conn._token is None


def test_connection_get_available_servers(mock_config):
    """Test retrieving list of available servers"""
    conn = ConnectionManager(mock_config)
    servers = conn.get_available_servers()
    assert "test_server" in servers


def test_connection_uses_ssl_verification(mock_config, mock_api):
    """Test that connection uses SSL verification from config"""
    mock_config.get_server_verify.return_value = True

    with patch("quads_client.connection.QuadsApi") as mock_quads_api:
        mock_quads_api.return_value = mock_api
        conn = ConnectionManager(mock_config)
        conn.connect("test_server")

        mock_quads_api.assert_called_once()
        call_kwargs = mock_quads_api.call_args[1]
        assert call_kwargs["verify"] is True


def test_connection_ssl_verification_disabled(mock_config, mock_api):
    """Test connection with SSL verification disabled"""
    mock_config.get_server_verify.return_value = False

    with patch("quads_client.connection.QuadsApi") as mock_quads_api:
        mock_quads_api.return_value = mock_api
        conn = ConnectionManager(mock_config)
        conn.connect("test_server")

        mock_quads_api.assert_called_once()
        call_kwargs = mock_quads_api.call_args[1]
        assert call_kwargs["verify"] is False




def test_connection_uses_base_url_parameter(mock_config, mock_api):
    """Test that connection uses base_url parameter (not url)"""
    with patch("quads_client.connection.QuadsApi") as mock_quads_api:
        mock_quads_api.return_value = mock_api
        conn = ConnectionManager(mock_config)
        conn.connect("test_server")

        mock_quads_api.assert_called_once()
        call_kwargs = mock_quads_api.call_args[1]
        assert "base_url" in call_kwargs
        assert "url" not in call_kwargs
