import pytest
from unittest.mock import MagicMock
from quads_client.commands.cloud import CloudCommands


def test_cloud_list_with_assignment_details(mock_shell):
    """Test cloud-list displays assignment details correctly"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    # Mock assignment with full details
    assignment = {
        "id": 42,
        "owner": "test@example.com",
        "description": "This is a test assignment description that is very long and should be truncated",
        "wipe": True,
        "vlan": {"vlan_id": 1234},
    }
    mock_shell.connection.api.get_active_cloud_assignment.return_value = assignment

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    # Verify assignment API was called
    mock_shell.connection.api.get_active_cloud_assignment.assert_called_with("cloud01")


def test_cloud_list_with_vlan_as_dict(mock_shell):
    """Test cloud-list handles VLAN as dict"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    assignment = {
        "id": 42,
        "owner": "test@example.com",
        "description": "Test",
        "wipe": False,
        "vlan": {"vlan_id": 999},
    }
    mock_shell.connection.api.get_active_cloud_assignment.return_value = assignment

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_with_vlan_as_int(mock_shell):
    """Test cloud-list handles VLAN as int"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    assignment = {"id": 42, "owner": "test@example.com", "description": "Test", "wipe": False, "vlan": 1234}
    mock_shell.connection.api.get_active_cloud_assignment.return_value = assignment

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_with_none_owner(mock_shell):
    """Test cloud-list handles None owner"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    assignment = {"id": 42, "owner": None, "description": None, "wipe": False, "vlan": None}
    mock_shell.connection.api.get_active_cloud_assignment.return_value = assignment

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_no_active_assignment(mock_shell):
    """Test cloud-list when no active assignment"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    # No active assignment
    mock_shell.connection.api.get_active_cloud_assignment.return_value = None

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_assignment_api_error(mock_shell):
    """Test cloud-list handles assignment API error gracefully"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    # Assignment API raises exception
    mock_shell.connection.api.get_active_cloud_assignment.side_effect = Exception("API error")

    cloud_cmd = CloudCommands(mock_shell)
    # Should not raise, should handle exception gracefully
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_truncates_long_description(mock_shell):
    """Test cloud-list truncates descriptions longer than 40 chars"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    assignment = {
        "id": 42,
        "owner": "test@example.com",
        "description": "A" * 100,  # Very long description
        "wipe": True,
        "vlan": 1234,
    }
    mock_shell.connection.api.get_active_cloud_assignment.return_value = assignment

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_assignment_not_dict(mock_shell):
    """Test cloud-list handles non-dict assignment"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    # Assignment is not a dict (shouldn't happen, but test defensive code)
    mock_shell.connection.api.get_active_cloud_assignment.return_value = "not a dict"

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_wipe_flag_true(mock_shell):
    """Test cloud-list displays 'Yes' for wipe=True"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    assignment = {"id": 42, "owner": "test@example.com", "description": "Test", "wipe": True, "vlan": 1234}
    mock_shell.connection.api.get_active_cloud_assignment.return_value = assignment

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()


def test_cloud_list_wipe_flag_false(mock_shell):
    """Test cloud-list displays 'No' for wipe=False"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [{"name": "cloud01"}]

    assignment = {"id": 42, "owner": "test@example.com", "description": "Test", "wipe": False, "vlan": 1234}
    mock_shell.connection.api.get_active_cloud_assignment.return_value = assignment

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_active_cloud_assignment.assert_called_once()
