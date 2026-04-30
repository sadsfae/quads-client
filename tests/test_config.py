import pytest
import tempfile
import yaml
from pathlib import Path
from quads_client.config import QuadsClientConfig, ConfigError


def test_config_load_valid_yaml(tmp_path):
    """Test loading valid YAML configuration"""
    config_file = tmp_path / "quads-client.yml"
    config_data = {
        "servers": {
            "test_server": {"url": "https://test.example.com", "username": "test@example.com", "password": "testpass"}
        },
        "default_server": "test_server",
    }
    config_file.write_text(yaml.dump(config_data))

    config = QuadsClientConfig(config_path=str(config_file))
    assert config.get_default_server() == "test_server"
    assert config.get_server_url("test_server") == "https://test.example.com"
    username, password = config.get_server_credentials("test_server")
    assert username == "test@example.com"
    assert password == "testpass"


def test_config_missing_file():
    """Test handling of missing config file"""
    with pytest.raises(ConfigError, match="not found"):
        QuadsClientConfig(config_path="/nonexistent/path/config.yml")


def test_config_invalid_yaml(tmp_path):
    """Test handling of invalid YAML"""
    config_file = tmp_path / "quads-client.yml"
    config_file.write_text("invalid: yaml: content: {{")

    with pytest.raises(ConfigError):
        QuadsClientConfig(config_path=str(config_file))


def test_config_get_all_servers(tmp_path):
    """Test retrieving all server configurations"""
    config_file = tmp_path / "quads-client.yml"
    config_data = {
        "servers": {
            "server1": {"url": "https://server1.example.com", "username": "user1", "password": "pass1"},
            "server2": {"url": "https://server2.example.com", "username": "user2", "password": "pass2"},
        }
    }
    config_file.write_text(yaml.dump(config_data))

    config = QuadsClientConfig(config_path=str(config_file))
    servers = config.get_all_servers()
    assert "server1" in servers
    assert "server2" in servers
    assert len(servers) == 2


def test_config_unknown_server(tmp_path):
    """Test accessing unknown server"""
    config_file = tmp_path / "quads-client.yml"
    config_data = {"servers": {"test_server": {"url": "https://test.example.com"}}}
    config_file.write_text(yaml.dump(config_data))

    config = QuadsClientConfig(config_path=str(config_file))
    with pytest.raises(ConfigError, match="not found in configuration"):
        config.get_server_url("nonexistent_server")


def test_config_missing_credentials(tmp_path):
    """Test server with missing credentials"""
    config_file = tmp_path / "quads-client.yml"
    config_data = {"servers": {"test_server": {"url": "https://test.example.com"}}}
    config_file.write_text(yaml.dump(config_data))

    config = QuadsClientConfig(config_path=str(config_file))
    username, password = config.get_server_credentials("test_server")
    # Returns empty strings when credentials are missing
    assert username == ""
    assert password == ""
