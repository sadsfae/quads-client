import pytest
from unittest.mock import MagicMock, patch
from quads_client.error_handler import auto_refresh_on_auth_error, handle_api_error


def test_auto_refresh_on_auth_error_success():
    """Test auto_refresh wrapper when API call succeeds"""
    mock_shell = MagicMock()
    api_func = MagicMock(return_value={"status": "success"})

    result = auto_refresh_on_auth_error(mock_shell, api_func, "arg1", kwarg="value")

    assert result == {"status": "success"}
    api_func.assert_called_once_with("arg1", kwarg="value")
    # Should not attempt refresh
    mock_shell.connection.refresh_token.assert_not_called()


def test_auto_refresh_on_auth_error_401_error():
    """Test auto_refresh wrapper handles 401 error and retries"""
    mock_shell = MagicMock()
    mock_shell.connection.refresh_token.return_value = True

    # First call raises 401, second call succeeds
    api_func = MagicMock(side_effect=[Exception("401 Unauthorized"), {"status": "success"}])

    result = auto_refresh_on_auth_error(mock_shell, api_func)

    assert result == {"status": "success"}
    assert api_func.call_count == 2
    mock_shell.connection.refresh_token.assert_called_once()


def test_auto_refresh_on_auth_error_unauthorized_error():
    """Test auto_refresh wrapper handles unauthorized error"""
    mock_shell = MagicMock()
    mock_shell.connection.refresh_token.return_value = True

    api_func = MagicMock(side_effect=[Exception("Unauthorized access"), {"status": "success"}])

    result = auto_refresh_on_auth_error(mock_shell, api_func)

    assert result == {"status": "success"}
    assert api_func.call_count == 2
    mock_shell.connection.refresh_token.assert_called_once()


def test_auto_refresh_on_auth_error_token_expired():
    """Test auto_refresh wrapper handles token expired error"""
    mock_shell = MagicMock()
    mock_shell.connection.refresh_token.return_value = True

    api_func = MagicMock(side_effect=[Exception("Token has expired"), {"status": "success"}])

    result = auto_refresh_on_auth_error(mock_shell, api_func)

    assert result == {"status": "success"}
    assert api_func.call_count == 2
    mock_shell.connection.refresh_token.assert_called_once()


def test_auto_refresh_on_auth_error_refresh_failed():
    """Test auto_refresh wrapper when token refresh fails"""
    mock_shell = MagicMock()
    mock_shell.connection.refresh_token.return_value = False

    api_func = MagicMock(side_effect=Exception("401 Unauthorized"))

    with pytest.raises(Exception, match="401 Unauthorized"):
        auto_refresh_on_auth_error(mock_shell, api_func)

    api_func.assert_called_once()
    mock_shell.connection.refresh_token.assert_called_once()


def test_auto_refresh_on_auth_error_retry_failed():
    """Test auto_refresh wrapper when retry still fails after refresh"""
    mock_shell = MagicMock()
    mock_shell.connection.refresh_token.return_value = True

    # Both calls fail
    api_func = MagicMock(side_effect=[Exception("401 Unauthorized"), Exception("Still unauthorized")])

    with pytest.raises(Exception, match="Still unauthorized"):
        auto_refresh_on_auth_error(mock_shell, api_func)

    assert api_func.call_count == 2
    mock_shell.connection.refresh_token.assert_called_once()


def test_auto_refresh_on_auth_error_non_auth_error():
    """Test auto_refresh wrapper with non-authentication error"""
    mock_shell = MagicMock()

    api_func = MagicMock(side_effect=Exception("Network error"))

    with pytest.raises(Exception, match="Network error"):
        auto_refresh_on_auth_error(mock_shell, api_func)

    api_func.assert_called_once()
    # Should not attempt refresh for non-auth errors
    mock_shell.connection.refresh_token.assert_not_called()


def test_handle_api_error_host_limit():
    """Test handle_api_error for host limit errors"""
    mock_shell = MagicMock()
    error = Exception("host limit exceeded")

    handle_api_error(mock_shell, error, "Scheduling")

    assert mock_shell.perror.call_count >= 2
    calls = [str(call) for call in mock_shell.perror.call_args_list]
    assert any("Server limit" in str(call) for call in calls)


def test_handle_api_error_cloud_limit():
    """Test handle_api_error for cloud limit errors"""
    mock_shell = MagicMock()
    error = Exception("user cloud limit exceeded")

    handle_api_error(mock_shell, error, "Scheduling")

    assert mock_shell.perror.call_count >= 2
    calls = [str(call) for call in mock_shell.perror.call_args_list]
    assert any("Server limit" in str(call) for call in calls)


def test_handle_api_error_401():
    """Test handle_api_error for authentication errors"""
    mock_shell = MagicMock()
    error = Exception("401 Unauthorized")

    handle_api_error(mock_shell, error, "API call")

    assert mock_shell.perror.call_count >= 2
    calls = [str(call) for call in mock_shell.perror.call_args_list]
    assert any("Authentication failed" in str(call) for call in calls)


def test_handle_api_error_403():
    """Test handle_api_error for permission errors"""
    mock_shell = MagicMock()
    error = Exception("403 Forbidden")

    handle_api_error(mock_shell, error, "API call")

    mock_shell.perror.assert_called_once()
    call = str(mock_shell.perror.call_args)
    assert "Permission denied" in call


def test_handle_api_error_connection():
    """Test handle_api_error for connection errors"""
    mock_shell = MagicMock()
    error = Exception("connection timeout")

    handle_api_error(mock_shell, error, "API call")

    assert mock_shell.perror.call_count >= 2
    calls = [str(call) for call in mock_shell.perror.call_args_list]
    assert any("Connection failed" in str(call) for call in calls)
