import pytest
from unittest.mock import MagicMock, patch, mock_open
from quads_client.commands.server import ServerCommands


def test_servers_success(mock_shell):
    """Test servers command shows server list"""
    mock_shell.config.get_all_servers.return_value = {
        "quads1": {"url": "https://quads1.example.com", "username": "admin", "password": "pass", "verify": True},
        "quads2": {"url": "https://quads2.example.com", "username": "admin", "password": "pass", "verify": True},
    }
    mock_shell.config.get_default_server.return_value = "quads1"
    mock_shell.connection.current_server = "quads2"

    with patch("quads_lib.QuadsApi") as mock_api:
        mock_api.return_value.get_version.return_value = {"version": "2.2.6"}
        mock_api.return_value.get_summary.return_value = [{"name": "cloud01"}, {"name": "cloud02"}]

        server_cmd = ServerCommands(mock_shell)
        server_cmd.cmd_servers("")

        assert mock_shell.poutput.call_count >= 2
        mock_shell.config.get_all_servers.assert_called_once()


def test_servers_no_config(mock_shell):
    """Test servers command with no config"""
    mock_shell.config = None

    server_cmd = ServerCommands(mock_shell)
    server_cmd.cmd_servers("")

    mock_shell.perror.assert_called_with("Configuration not loaded")


def test_servers_offline_status(mock_shell):
    """Test servers command shows offline status for unreachable servers"""
    mock_shell.config.get_all_servers.return_value = {
        "quads1": {"url": "https://quads1.example.com", "username": "admin", "password": "pass", "verify": True},
    }
    mock_shell.config.get_default_server.return_value = "quads1"
    mock_shell.connection.current_server = None

    with patch("quads_lib.QuadsApi") as mock_api:
        mock_api.return_value.get_version.side_effect = Exception("Connection failed")

        server_cmd = ServerCommands(mock_shell)
        server_cmd.cmd_servers("")

        assert mock_shell.poutput.call_count >= 1


def test_add_server_success(mock_shell):
    """Test add-server command"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {}}

    with patch("quads_lib.QuadsApi") as mock_api:
        mock_api.return_value.get_version.return_value = {"version": "2.2.6"}

        with patch("builtins.open", mock_open(read_data="servers: {}\n")):
            with patch("yaml.safe_load", return_value=yaml_content):
                with patch("yaml.dump") as mock_dump:
                    server_cmd = ServerCommands(mock_shell)
                    server_cmd.cmd_add_server("quads3 https://quads3.example.com admin pass")

                    mock_dump.assert_called_once()
                    assert mock_shell.poutput.call_count >= 2


def test_add_server_already_exists(mock_shell):
    """Test add-server with existing server name"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {"quads3": {"url": "https://quads3.example.com"}}}

    with patch("builtins.open", mock_open(read_data="servers:\n  quads3: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            server_cmd = ServerCommands(mock_shell)
            server_cmd.cmd_add_server("quads3 https://quads3.example.com admin pass")

            mock_shell.perror.assert_called_with("Server 'quads3' already exists. Use edit-server to modify.")


def test_add_server_connection_failed_reject(mock_shell):
    """Test add-server with connection test failure (user rejects)"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {}}

    with patch("quads_lib.QuadsApi") as mock_api:
        mock_api.return_value.get_version.side_effect = Exception("Connection failed")

        with patch("builtins.open", mock_open(read_data="servers: {}\n")):
            with patch("yaml.safe_load", return_value=yaml_content):
                with patch("builtins.input", return_value="n"):
                    server_cmd = ServerCommands(mock_shell)
                    server_cmd.cmd_add_server("quads3 https://quads3.example.com admin pass")

                    mock_shell.poutput.assert_called_with("Server not added")


def test_add_server_missing_args(mock_shell):
    """Test add-server with missing arguments"""
    server_cmd = ServerCommands(mock_shell)
    server_cmd.cmd_add_server("quads3")

    mock_shell.perror.assert_called_with("Usage: add-server <name> <url> <username> <password> [--no-verify]")


def test_add_server_no_verify_flag(mock_shell):
    """Test add-server with --no-verify flag"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {}}

    with patch("quads_lib.QuadsApi") as mock_api:
        mock_api.return_value.get_version.return_value = {"version": "2.2.6"}

        with patch("builtins.open", mock_open(read_data="servers: {}\n")):
            with patch("yaml.safe_load", return_value=yaml_content):
                with patch("yaml.dump") as mock_dump:
                    server_cmd = ServerCommands(mock_shell)
                    server_cmd.cmd_add_server("quads3 https://quads3.example.com admin pass --no-verify")

                    # Verify that verify was set to False
                    call_args = mock_dump.call_args[0][0]
                    assert call_args["servers"]["quads3"]["verify"] is False


def test_edit_server_success(mock_shell):
    """Test edit-server command"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {
        "servers": {"quads3": {"url": "https://quads3.example.com", "username": "admin", "password": "pass"}}
    }

    with patch("builtins.open", mock_open(read_data="servers:\n  quads3: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            with patch("quads_client.commands.server.yaml.dump") as mock_dump:
                server_cmd = ServerCommands(mock_shell)
                server_cmd.cmd_edit_server("quads3 --url https://new.example.com")

                mock_dump.assert_called_once()
                assert mock_shell.poutput.call_count >= 2


def test_edit_server_not_found(mock_shell):
    """Test edit-server with non-existent server"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {}}

    with patch("builtins.open", mock_open(read_data="servers: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            server_cmd = ServerCommands(mock_shell)
            server_cmd.cmd_edit_server("quads3 --url https://new.example.com")

            mock_shell.perror.assert_called_with("Server 'quads3' not found")


def test_edit_server_no_updates(mock_shell):
    """Test edit-server with no update flags"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {"quads3": {"url": "https://quads3.example.com"}}}

    with patch("builtins.open", mock_open(read_data="servers:\n  quads3: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            server_cmd = ServerCommands(mock_shell)
            server_cmd.cmd_edit_server("quads3")

            mock_shell.perror.assert_called_with("No updates specified")


def test_edit_server_missing_name(mock_shell):
    """Test edit-server with no server name"""
    server_cmd = ServerCommands(mock_shell)
    server_cmd.cmd_edit_server("")

    mock_shell.perror.assert_called()


def test_edit_server_verify_flag(mock_shell):
    """Test edit-server with --verify flag"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {"quads3": {"url": "https://quads3.example.com", "verify": True}}}

    with patch("builtins.open", mock_open(read_data="servers:\n  quads3: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            with patch("quads_client.commands.server.yaml.dump") as mock_dump:
                server_cmd = ServerCommands(mock_shell)
                server_cmd.cmd_edit_server("quads3 --verify false")

                call_args = mock_dump.call_args[0][0]
                assert call_args["servers"]["quads3"]["verify"] is False


def test_rm_server_success(mock_shell):
    """Test rm-server command with confirmation"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"
    mock_shell.connection.current_server = "quads1"

    yaml_content = {
        "servers": {"quads3": {"url": "https://quads3.example.com"}},
        "default_server": "quads1",
    }

    with patch("builtins.open", mock_open(read_data="servers:\n  quads3: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            with patch("quads_client.commands.server.yaml.dump") as mock_dump:
                with patch("builtins.input", return_value="y"):
                    server_cmd = ServerCommands(mock_shell)
                    server_cmd.cmd_rm_server("quads3")

                    mock_dump.assert_called_once()
                    assert mock_shell.poutput.call_count >= 2


def test_rm_server_reject(mock_shell):
    """Test rm-server command with rejection"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"
    mock_shell.connection.current_server = "quads1"

    yaml_content = {"servers": {"quads3": {"url": "https://quads3.example.com"}}}

    with patch("builtins.open", mock_open(read_data="servers:\n  quads3: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            with patch("builtins.input", return_value="n"):
                server_cmd = ServerCommands(mock_shell)
                server_cmd.cmd_rm_server("quads3")

                mock_shell.poutput.assert_called_with("Server not removed")


def test_rm_server_currently_connected(mock_shell):
    """Test rm-server prevents removing connected server"""
    mock_shell.connection.current_server = "quads3"

    server_cmd = ServerCommands(mock_shell)
    server_cmd.cmd_rm_server("quads3")

    mock_shell.perror.assert_called_with("Cannot remove 'quads3' - currently connected. Disconnect first.")


def test_rm_server_not_found(mock_shell):
    """Test rm-server with non-existent server"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"
    mock_shell.connection.current_server = "quads1"

    yaml_content = {"servers": {}}

    with patch("builtins.open", mock_open(read_data="servers: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            server_cmd = ServerCommands(mock_shell)
            server_cmd.cmd_rm_server("quads3")

            mock_shell.perror.assert_called_with("Server 'quads3' not found")


def test_rm_server_clears_default(mock_shell):
    """Test rm-server clears default_server if removing default"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"
    mock_shell.connection.current_server = "quads1"

    yaml_content = {
        "servers": {"quads3": {"url": "https://quads3.example.com"}},
        "default_server": "quads3",
    }

    with patch("builtins.open", mock_open(read_data="servers:\n  quads3: {}\n")):
        with patch("quads_client.commands.server.yaml.safe_load", return_value=yaml_content):
            with patch("quads_client.commands.server.yaml.dump") as mock_dump:
                with patch("builtins.input", return_value="y"):
                    server_cmd = ServerCommands(mock_shell)
                    server_cmd.cmd_rm_server("quads3")

                    call_args = mock_dump.call_args[0][0]
                    assert call_args["default_server"] is None


def test_rm_server_no_args(mock_shell):
    """Test rm-server with no arguments"""
    server_cmd = ServerCommands(mock_shell)
    server_cmd.cmd_rm_server("")

    mock_shell.perror.assert_called_with("Usage: rm-server <name>")


def test_config_reload_success(mock_shell):
    """Test config-reload command"""
    with patch("quads_client.config.QuadsClientConfig") as mock_config_class:
        with patch("quads_client.connection.ConnectionManager") as mock_conn_class:
            server_cmd = ServerCommands(mock_shell)
            server_cmd.cmd_config_reload("")

            mock_config_class.assert_called_once()
            mock_conn_class.assert_called_once()
            mock_shell.poutput.assert_called_with("OK: Configuration reloaded successfully")


def test_config_reload_failure(mock_shell):
    """Test config-reload with failure"""
    with patch("quads_client.config.QuadsClientConfig", side_effect=Exception("Config error")):
        server_cmd = ServerCommands(mock_shell)
        server_cmd.cmd_config_reload("")

        mock_shell.perror.assert_called_with("Failed to reload configuration: Config error")


def test_add_quads_server_success(mock_shell):
    """Test interactive add-quads-server command"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {}}

    with patch("builtins.input", side_effect=["quads3.example.com", "https://quads3.example.com", "y"]):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            with patch("builtins.open", mock_open(read_data="servers: {}\n")):
                with patch("yaml.safe_load", return_value=yaml_content):
                    with patch("yaml.dump") as mock_dump:
                        server_cmd = ServerCommands(mock_shell)
                        server_cmd.cmd_add_quads_server("")

                        mock_dump.assert_called_once()
                        # Verify empty credentials were set
                        call_args = mock_dump.call_args[0][0]
                        assert call_args["servers"]["quads3.example.com"]["username"] == ""
                        assert call_args["servers"]["quads3.example.com"]["password"] == ""
                        assert mock_shell.poutput.call_count >= 2


def test_add_quads_server_empty_name(mock_shell):
    """Test add-quads-server with empty server name"""
    with patch("builtins.input", return_value=""):
        server_cmd = ServerCommands(mock_shell)
        server_cmd.cmd_add_quads_server("")

        mock_shell.perror.assert_called_with("Server name cannot be empty")


def test_add_quads_server_already_exists(mock_shell):
    """Test add-quads-server with existing server name"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {"quads3.example.com": {"url": "https://quads3.example.com"}}}

    with patch("builtins.input", return_value="quads3.example.com"):
        with patch("builtins.open", mock_open(read_data="servers:\n  quads3.example.com: {}\n")):
            with patch("yaml.safe_load", return_value=yaml_content):
                server_cmd = ServerCommands(mock_shell)
                server_cmd.cmd_add_quads_server("")

                assert any(
                    "already exists" in str(call) for call in mock_shell.perror.call_args_list
                )


def test_add_quads_server_no_verify(mock_shell):
    """Test add-quads-server with SSL verification disabled"""
    mock_shell.config.config_path = "~/.config/quads/quads-client.yml"

    yaml_content = {"servers": {}}

    with patch("builtins.input", side_effect=["quads3.example.com", "https://quads3.example.com", "n"]):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            with patch("builtins.open", mock_open(read_data="servers: {}\n")):
                with patch("yaml.safe_load", return_value=yaml_content):
                    with patch("yaml.dump") as mock_dump:
                        server_cmd = ServerCommands(mock_shell)
                        server_cmd.cmd_add_quads_server("")

                        # Verify verify was set to False
                        call_args = mock_dump.call_args[0][0]
                        assert call_args["servers"]["quads3.example.com"]["verify"] is False


def test_server_info_no_credentials(mock_shell):
    """Test _get_server_info with missing credentials"""
    server_cmd = ServerCommands(mock_shell)
    server_config = {"url": "https://quads.example.com"}

    info = server_cmd._get_server_info("test", "https://quads.example.com", server_config)

    assert info == "N/A"


def test_server_status_no_credentials(mock_shell):
    """Test _get_server_status with missing credentials"""
    server_cmd = ServerCommands(mock_shell)
    server_config = {"url": "https://quads.example.com"}

    status, version = server_cmd._get_server_status("test", "https://quads.example.com", server_config)

    assert status == "No credentials"
    assert version == "N/A"
