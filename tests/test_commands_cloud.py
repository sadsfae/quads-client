import pytest
from unittest.mock import MagicMock
from quads_client.commands.cloud import CloudCommands


def test_cloud_list_success(mock_shell):
    """Test cloud-list command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}, {"name": "cloud02"}]

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_clouds.assert_called_once()
    # Enhanced cloud-list now uses tabulate, so only one poutput call with the table
    assert mock_shell.poutput.call_count == 1


def test_cloud_list_no_clouds(mock_shell):
    """Test cloud-list with no clouds"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = []

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.poutput.assert_called_with("No clouds found")


def test_cloud_list_not_connected(mock_shell):
    """Test cloud-list when not connected"""
    mock_shell.connection.is_connected = False

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_cloud_create_success(mock_shell):
    """Test cloud-create command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.create_cloud.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_create("test_cloud")

    mock_shell.connection.api.create_cloud.assert_called_once_with({"cloud": "test_cloud"})
    mock_shell.poutput.assert_called()


def test_cloud_create_no_name(mock_shell):
    """Test cloud-create without providing name"""
    mock_shell.connection.is_connected = True

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_create("")

    mock_shell.perror.assert_called_with("Usage: cloud-create <name>")


def test_cloud_create_forbidden(mock_shell):
    """Test cloud-create when user lacks permission"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.create_cloud.side_effect = Exception("403 Forbidden")

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_create("test_cloud")

    mock_shell.perror.assert_called_with("Error: This command requires admin role")


def test_cloud_delete_success(mock_shell):
    """Test cloud-delete command success"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.remove_cloud.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_delete("test_cloud")

    mock_shell.connection.api.remove_cloud.assert_called_once_with("test_cloud")
    mock_shell.poutput.assert_called()


def test_cloud_delete_no_name(mock_shell):
    """Test cloud-delete without providing name"""
    mock_shell.connection.is_connected = True

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_delete("")

    mock_shell.perror.assert_called_with("Usage: cloud-delete <name>")


def test_cloud_delete_forbidden(mock_shell):
    """Test cloud-delete when user lacks permission"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.remove_cloud.side_effect = Exception("Forbidden")

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_delete("test_cloud")

    mock_shell.perror.assert_called_with("Error: This command requires admin role")


def test_cloud_delete_not_connected(mock_shell):
    """Test cloud-delete when not connected"""
    mock_shell.connection.is_connected = False

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_delete("test_cloud")

    mock_shell.perror.assert_called_with("Not connected to any server")
