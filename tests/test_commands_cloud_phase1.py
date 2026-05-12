import pytest
from unittest.mock import MagicMock
from quads_client.commands.cloud import CloudCommands


def test_cloud_list_detail_success(mock_shell):
    """Test cloud-list --cloud <name> detail command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_clouds.return_value = [
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "Development CI/CD Pipeline",
            "ticket": "12345",
            "ccusers": ["bob@example.com", "charlie@example.com"],
            "vlan": {"vlan_id": 1117},
            "wipe": True,
            "validated": True,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = [
        {
            "host": {"name": "host01.example.com", "model": "r640"},
            "start": "2026-04-15 08:00",
            "end": "2026-05-15 08:00",
        },
        {
            "host": {"name": "host02.example.com", "model": "r640"},
            "start": "2026-04-15 08:00",
            "end": "2026-05-15 08:00",
        },
    ]

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("cloud cloud17 detail")

    mock_shell.connection.api.filter_clouds.assert_called_once_with({"name": "cloud17"})
    mock_shell.connection.api.get_schedules.assert_called_once_with({"cloud": "cloud17"})
    assert mock_shell.poutput.call_count >= 4


def test_cloud_list_detail_not_found(mock_shell):
    """Test cloud-list --cloud with non-existent cloud"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_clouds.return_value = []

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("cloud cloud99 detail")

    mock_shell.perror.assert_called_with("Cloud 'cloud99' not found")


def test_cloud_list_detail_no_hosts(mock_shell):
    """Test cloud-list detail with no assigned hosts"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_clouds.return_value = [
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "Test environment",
            "wipe": False,
            "validated": False,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = []

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("cloud cloud17 detail")

    assert "No hosts assigned" in str(mock_shell.poutput.call_args_list)


def test_cloud_list_detail_without_cloud_name(mock_shell):
    """Test detail flag without cloud name"""
    mock_shell.connection.is_connected = True

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("detail")

    mock_shell.perror.assert_called_with("detail requires cloud <name>")


def test_cloud_list_with_cloud_no_detail(mock_shell):
    """Test --cloud flag without detail shows detail view"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_clouds.return_value = [
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "Test environment",
            "wipe": True,
            "validated": True,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = []

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("cloud cloud17")

    # Should call filter_clouds for detail view
    mock_shell.connection.api.filter_clouds.assert_called_once_with({"name": "cloud17"})


def test_mod_cloud_success(mock_shell):
    """Test mod-cloud command"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice description Updated testing environment nowipe")

    mock_shell.connection.api.update_assignment.assert_called_once()
    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[0] == 42
    assert call_args[1]["owner"] == "alice"
    assert call_args[1]["description"] == "Updated testing environment"
    assert call_args[1]["wipe"] is False


def test_mod_cloud_multiword_description(mock_shell):
    """Test mod-cloud with multi-word description"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 description CI/CD pipeline testing environment")

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[1]["description"] == "CI/CD pipeline testing environment"


def test_mod_cloud_ticket(mock_shell):
    """Test mod-cloud with ticket"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-ticket 54321")

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[1]["ticket"] == "54321"


def test_mod_cloud_ccusers(mock_shell):
    """Test mod-cloud with cc-users"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cc-users bob@example.com,charlie@example.com")

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[1]["ccuser"] == "bob@example.com,charlie@example.com"


def test_mod_cloud_wipe_true(mock_shell):
    """Test mod-cloud wipe flag"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 wipe")

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[1]["wipe"] is True


def test_mod_cloud_wipe_false(mock_shell):
    """Test mod-cloud nowipe flag"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 nowipe")

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[1]["wipe"] is False


def test_mod_cloud_multiple_options(mock_shell):
    """Test mod-cloud with multiple options"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice wipe cloud-ticket 123")

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[1]["owner"] == "alice"
    assert call_args[1]["wipe"] is True
    assert call_args[1]["ticket"] == "123"


def test_mod_cloud_no_cloud_name(mock_shell):
    """Test mod-cloud without cloud name"""
    mock_shell.connection.is_connected = True

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("")

    mock_shell.perror.assert_called()


def test_mod_cloud_no_updates(mock_shell):
    """Test mod-cloud with no update flags"""
    mock_shell.connection.is_connected = True

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17")

    # Should call perror with both error messages
    assert mock_shell.perror.call_count == 2
    calls = [str(call) for call in mock_shell.perror.call_args_list]
    assert any("No updates specified" in str(call) for call in calls)
    assert any("mod-cloud ?" in str(call) for call in calls)


def test_mod_cloud_not_connected(mock_shell):
    """Test mod-cloud when not connected"""
    mock_shell.connection.is_connected = False

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.perror.assert_called_with("Not connected to any server")


def test_mod_cloud_forbidden(mock_shell):
    """Test mod-cloud with 403 Forbidden (non-admin)"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.side_effect = Exception("403 Forbidden")

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.perror.assert_called()
    error_msg = str(mock_shell.perror.call_args).lower()
    assert "permission" in error_msg or "admin" in error_msg or "403" in error_msg


def test_mod_cloud_api_error(mock_shell):
    """Test mod-cloud with generic API error"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.side_effect = Exception("Server error")

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.perror.assert_called()


def test_mod_cloud_no_active_assignment(mock_shell):
    """Test mod-cloud when cloud has no active assignment"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = None

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.perror.assert_called()
    error_msg = str(mock_shell.perror.call_args).lower()
    assert "no active assignment" in error_msg


def test_mod_cloud_assignment_missing_id(mock_shell):
    """Test mod-cloud when assignment has no id field"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"description": "test"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.perror.assert_called()
    error_msg = str(mock_shell.perror.call_args).lower()
    assert "could not determine assignment id" in error_msg


def test_mod_cloud_rich_console_success(mock_shell):
    """Test mod-cloud success output via rich_console"""
    mock_shell.connection.is_connected = True
    mock_shell.rich_console = MagicMock()
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.rich_console.print_success.assert_called_once()
    mock_shell.rich_console.print_property.assert_called_once_with("owner", "alice")


def test_mod_cloud_rich_console_no_assignment(mock_shell):
    """Test mod-cloud no-assignment error via rich_console"""
    mock_shell.connection.is_connected = True
    mock_shell.rich_console = MagicMock()
    mock_shell.connection.api.get_active_cloud_assignment.return_value = None

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.rich_console.print_error.assert_called_once()
    assert "no active assignment" in str(mock_shell.rich_console.print_error.call_args).lower()


def test_mod_cloud_rich_console_missing_id(mock_shell):
    """Test mod-cloud missing-id error via rich_console"""
    mock_shell.connection.is_connected = True
    mock_shell.rich_console = MagicMock()
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"description": "test"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.rich_console.print_error.assert_called_once()
    assert "could not determine" in str(mock_shell.rich_console.print_error.call_args).lower()


def test_mod_cloud_rich_console_forbidden(mock_shell):
    """Test mod-cloud forbidden error via rich_console"""
    mock_shell.connection.is_connected = True
    mock_shell.rich_console = MagicMock()
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.side_effect = Exception("403 Forbidden")

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.rich_console.print_error.assert_called_once()
    assert "admin" in str(mock_shell.rich_console.print_error.call_args).lower()


def test_mod_cloud_rich_console_api_error(mock_shell):
    """Test mod-cloud generic error via rich_console"""
    mock_shell.connection.is_connected = True
    mock_shell.rich_console = MagicMock()
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.side_effect = Exception("Server error")

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud("cloud17 cloud-owner alice")

    mock_shell.rich_console.print_error.assert_called_once()
    assert "failed to modify" in str(mock_shell.rich_console.print_error.call_args).lower()


def test_mod_cloud_quoted_description(mock_shell):
    """Test mod-cloud with quoted description via shlex"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud('cloud17 description "admin test 15"')

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert call_args[1]["description"] == "admin test 15"


def test_mod_cloud_shlex_fallback(mock_shell):
    """Test mod-cloud falls back to split on malformed quotes"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 42}
    mock_shell.connection.api.update_assignment.return_value = {"status": "success"}

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_mod_cloud('cloud17 description "unclosed quote')

    call_args = mock_shell.connection.api.update_assignment.call_args[0]
    assert "unclosed" in call_args[1]["description"]


def test_cloud_list_enhanced_table_format(mock_shell):
    """Test enhanced cloud-list table format"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [
        {
            "name": "cloud01",
            "owner": None,
            "description": "Spare Pool (Available)",
            "vlan": None,
            "wipe": False,
        },
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "Development CI/CD Pipeline",
            "vlan": {"vlan_id": 1117},
            "wipe": True,
        },
    ]

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    mock_shell.connection.api.get_clouds.assert_called_once()
    # Enhanced table uses tabulate, one poutput call
    assert mock_shell.poutput.call_count == 1


def test_cloud_list_truncates_long_description(mock_shell):
    """Test cloud-list truncates descriptions over 50 chars"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "This is a very long description that should be truncated to fit in the table nicely",
            "vlan": {"vlan_id": 1117},
            "wipe": True,
        },
    ]

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    # Should call poutput with truncated description
    assert mock_shell.poutput.call_count == 1


def test_cloud_list_vlan_dict_format(mock_shell):
    """Test cloud-list handles vlan as dict"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "Test",
            "vlan": {"vlan_id": 1234},
            "wipe": False,
        },
    ]

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    assert mock_shell.poutput.call_count == 1


def test_cloud_list_vlan_none(mock_shell):
    """Test cloud-list handles vlan as None"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_clouds.return_value = [
        {
            "name": "cloud01",
            "owner": None,
            "description": "Spare Pool",
            "vlan": None,
            "wipe": False,
        },
    ]

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("")

    assert mock_shell.poutput.call_count == 1


def test_cloud_detail_ccusers_list(mock_shell):
    """Test cloud detail view with ccusers as list"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_clouds.return_value = [
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "Test",
            "ccusers": ["bob@example.com", "charlie@example.com"],
            "wipe": True,
            "validated": True,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = []

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("cloud cloud17 detail")

    # Should join ccusers list with commas
    assert mock_shell.poutput.call_count >= 2


def test_cloud_detail_no_ticket(mock_shell):
    """Test cloud detail view with no ticket"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.filter_clouds.return_value = [
        {
            "name": "cloud17",
            "owner": "alice",
            "description": "Test",
            "ticket": None,
            "wipe": True,
            "validated": True,
        }
    ]
    mock_shell.connection.api.get_schedules.return_value = []

    cloud_cmd = CloudCommands(mock_shell)
    cloud_cmd.cmd_cloud_list("cloud cloud17 detail")

    assert mock_shell.poutput.call_count >= 2
