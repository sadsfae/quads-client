import sys
import pytest
from unittest.mock import MagicMock, Mock

# Mock quads_lib before any imports
sys.modules["quads_lib"] = MagicMock()
sys.modules["quads_lib.quads"] = MagicMock()


@pytest.fixture
def mock_config():
    """Mock QuadsClientConfig"""
    config = MagicMock()
    config.get_all_servers.return_value = {"test_server": {"url": "https://test.example.com", "username": "test@example.com"}}
    config.get_server_url.return_value = "https://test.example.com"
    config.get_server_credentials.return_value = ("test@example.com", "testpass")
    config.get_default_server.return_value = "test_server"
    config.get_server_verify.return_value = True
    return config


@pytest.fixture
def mock_api():
    """Mock QuadsApi"""
    api = MagicMock()
    api.login.return_value = {"status": "success", "auth_token": "test_token_123"}
    api.token = "test_token_123"
    api.get_clouds.return_value = [{"name": "cloud01"}, {"name": "cloud02"}]
    api.create_cloud.return_value = {"status": "success"}
    api.remove_cloud.return_value = {"status": "success"}
    api.filter_hosts.return_value = [
        {"name": "host01.example.com", "can_self_schedule": True},
        {"name": "host02.example.com", "can_self_schedule": True},
    ]
    api.create_schedule.return_value = {"id": 1, "status": "success"}
    api.filter_assignments.return_value = [{"id": 1, "owner": "test@example.com", "cloud": "cloud02"}]
    api.get_schedules.return_value = [
        {"id": 1, "host": {"name": "host01.example.com"}, "start": "2026-05-01", "end": "2026-05-15"}
    ]
    return api


@pytest.fixture
def mock_connection_manager(mock_config, mock_api):
    """Mock ConnectionManager with QuadsApi"""
    conn = MagicMock()
    conn.config = mock_config
    conn.is_connected = True
    conn.current_server = "test_server"
    conn.username = "test@example.com"
    conn.api = mock_api
    conn._token = "test_token_123"
    conn.get_available_servers.return_value = ["test_server"]
    conn.connect = MagicMock()
    conn.disconnect = MagicMock()
    return conn


@pytest.fixture
def mock_shell(mock_config, mock_connection_manager):
    """Mock QuadsClientShell"""
    shell = MagicMock()
    shell.config = mock_config
    shell.connection = mock_connection_manager
    shell.poutput = MagicMock()
    shell.perror = MagicMock()
    shell.pwarning = MagicMock()
    shell._update_prompt = MagicMock()
    return shell
