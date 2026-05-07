"""Additional tests to boost schedule.py coverage"""

import pytest
from unittest.mock import MagicMock
from quads_client.commands.schedule import ScheduleCommands


class TestScheduleOptionalParameters:
    """Test optional assignment parameters"""

    def test_schedule_with_cc_users(self, mock_shell):
        """Test schedule with cc-users parameter"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.create_schedule.return_value = {"id": 1}

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123 '
            "cc-users bob@example.com,charlie@example.com"
        )

        # Verify cc_users was included in assignment data
        call_args = mock_shell.connection.api.create_assignment.call_args[0][0]
        assert "ccuser" in call_args
        assert call_args["ccuser"] == "bob@example.com,charlie@example.com"

    def test_schedule_with_vlan(self, mock_shell):
        """Test schedule with vlan parameter"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.create_schedule.return_value = {"id": 1}

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123 vlan 1234'
        )

        # Verify vlan was included in assignment data
        call_args = mock_shell.connection.api.create_assignment.call_args[0][0]
        assert "vlan" in call_args
        assert call_args["vlan"] == 1234

    def test_schedule_with_qinq(self, mock_shell):
        """Test schedule with qinq parameter"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.create_schedule.return_value = {"id": 1}

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123 qinq 1'
        )

        # Verify qinq was included in assignment data
        call_args = mock_shell.connection.api.create_assignment.call_args[0][0]
        assert "qinq" in call_args
        assert call_args["qinq"] == 1


class TestScheduleAssignmentErrors:
    """Test assignment creation error handling"""

    def test_assignment_returns_error_dict(self, mock_shell):
        """Test when assignment API returns error dict"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.return_value = {
            "error": True,
            "message": "Cloud already has an active assignment",
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show error and not proceed
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("Failed to create assignment" in call for call in error_calls)
        # Should not create schedules
        assert mock_shell.connection.api.create_schedule.call_count == 0

    def test_assignment_verification_not_active(self, mock_shell):
        """Test when assignment created but verification shows not active"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        # Verification returns None (not active)
        mock_shell.connection.api.get_active_cloud_assignment.return_value = None

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show timing error
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("Assignment created but not active" in call for call in error_calls)
        assert any("database timing issue" in call for call in error_calls)

    def test_assignment_verification_exception(self, mock_shell):
        """Test when assignment verification throws exception"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        # Verification throws exception but we proceed anyway
        mock_shell.connection.api.get_active_cloud_assignment.side_effect = Exception("Connection timeout")
        mock_shell.connection.api.create_schedule.return_value = {"id": 1}

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show warning but proceed
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("cannot verify it's active" in call for call in error_calls)
        assert any("Proceeding anyway" in call for call in error_calls)
        # Should still try to create schedules
        assert mock_shell.connection.api.create_schedule.call_count == 1

    def test_assignment_creation_exception(self, mock_shell):
        """Test when assignment creation throws exception"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.side_effect = Exception("Database error")

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show error
        mock_shell.perror.assert_called()
        # Should not create schedules
        assert mock_shell.connection.api.create_schedule.call_count == 0


class TestScheduleExistingAssignment:
    """Test using existing assignments"""

    def test_no_existing_assignment_error(self, mock_shell):
        """Test error when no assignment exists and no params provided"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.get_active_cloud_assignment.side_effect = Exception("No active assignment")

        schedule_cmd = ScheduleCommands(mock_shell)
        # No assignment params provided
        schedule_cmd.cmd_schedule_admin('cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should show helpful error
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("has no active assignment" in call for call in error_calls)
        assert any("Provide assignment parameters" in call for call in error_calls)
        # Should not create schedules
        assert mock_shell.connection.api.create_schedule.call_count == 0

    def test_existing_assignment_with_rich_console(self, mock_shell):
        """Test using existing assignment with rich console"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {
            "id": 50,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.create_schedule.return_value = {"id": 1}
        # Enable rich console
        mock_shell.rich_console = MagicMock()

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin('cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should show info via rich console
        mock_shell.rich_console.print_info.assert_called_with("Using existing assignment for cloud02")

    def test_new_assignment_with_rich_console(self, mock_shell):
        """Test creating assignment with rich console"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.create_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {
            "id": 150,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.create_schedule.return_value = {"id": 1}
        # Enable rich console
        mock_shell.rich_console = MagicMock()

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show success via rich console (called multiple times)
        assert mock_shell.rich_console.print_success.call_count >= 1
        # Check all calls for assignment creation message
        all_calls = [str(call) for call in mock_shell.rich_console.print_success.call_args_list]
        assert any("Assignment created" in call and "150" in call for call in all_calls)
