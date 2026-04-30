import pytest
from unittest.mock import MagicMock, patch
from quads_client.connection import ConnectionManager, ConnectionError


def test_user_role_property(mock_config):
    """Test user_role property"""
    conn = ConnectionManager(mock_config)
    conn._user_role = "admin"
    assert conn.user_role == "admin"


def test_decode_role_no_token(mock_config):
    """Test _decode_role_from_token when no token is set"""
    conn = ConnectionManager(mock_config)
    conn._token = None
    role = conn._decode_role_from_token()
    assert role is None


def test_decode_role_list_with_admin(mock_config):
    """Test _decode_role_from_token when roles is a list containing admin"""
    import jwt as pyjwt

    conn = ConnectionManager(mock_config)
    # Create a token with roles as a list containing 'admin'
    token_payload = {"roles": ["admin", "user"]}
    conn._token = pyjwt.encode(token_payload, "secret", algorithm="HS256")

    role = conn._decode_role_from_token()
    assert role == "admin"


def test_decode_role_list_without_admin(mock_config):
    """Test _decode_role_from_token when roles is a list without admin"""
    import jwt as pyjwt

    conn = ConnectionManager(mock_config)
    # Create a token with roles as a list not containing 'admin'
    token_payload = {"roles": ["user", "developer"]}
    conn._token = pyjwt.encode(token_payload, "secret", algorithm="HS256")

    role = conn._decode_role_from_token()
    assert role == "user"


def test_decode_role_invalid_token(mock_config):
    """Test _decode_role_from_token with invalid token"""
    conn = ConnectionManager(mock_config)
    conn._token = "invalid.token.here"

    role = conn._decode_role_from_token()
    assert role is None


def test_decode_role_alternative_field_names(mock_config):
    """Test _decode_role_from_token with different role field names"""
    import jwt as pyjwt

    conn = ConnectionManager(mock_config)

    # Test 'user_role' field
    token_payload = {"user_role": "admin"}
    conn._token = pyjwt.encode(token_payload, "secret", algorithm="HS256")
    assert conn._decode_role_from_token() == "admin"

    # Test 'role' field
    token_payload = {"role": "user"}
    conn._token = pyjwt.encode(token_payload, "secret", algorithm="HS256")
    assert conn._decode_role_from_token() == "user"


def test_get_available_servers(mock_config):
    """Test get_available_servers method"""
    mock_config.get_all_servers.return_value = {
        "server1": {"url": "https://server1.example.com"},
        "server2": {"url": "https://server2.example.com"},
    }

    conn = ConnectionManager(mock_config)
    servers = conn.get_available_servers()

    assert "server1" in servers
    assert "server2" in servers
    assert len(servers) == 2


def test_connect_registration_mode(mock_config):
    """Test connecting in registration mode (no credentials)"""
    mock_config.get_server_url.return_value = "https://test.example.com"
    mock_config.get_server_credentials.return_value = ("", "")
    mock_config.get_server_verify.return_value = True

    with patch("quads_client.connection.QuadsApi"):
        conn = ConnectionManager(mock_config)
        conn.connect("test_server", registration_mode=True)

        # Should connect without login in registration mode
        assert conn.is_connected
        assert conn._registration_mode is True
