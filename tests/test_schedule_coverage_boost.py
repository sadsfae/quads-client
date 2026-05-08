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
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 1,
            "hostnames": ["host01"],
            "jira_updated": True,
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123 '
            "cc-users bob@example.com,charlie@example.com"
        )

        # Verify cc_users was included in batch data
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert "ccuser" in batch_data
        assert batch_data["ccuser"] == "bob@example.com,charlie@example.com"

    def test_schedule_with_vlan(self, mock_shell):
        """Test schedule with vlan parameter"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 1,
            "hostnames": ["host01"],
            "jira_updated": True,
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123 vlan 1234'
        )

        # Verify vlan was included in batch data
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert "vlan" in batch_data
        assert batch_data["vlan"] == 1234

    def test_schedule_with_qinq(self, mock_shell):
        """Test schedule with qinq parameter"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 1,
            "hostnames": ["host01"],
            "jira_updated": True,
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123 qinq 1'
        )

        # Verify qinq was included in batch data
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert "qinq" in batch_data
        assert batch_data["qinq"] == 1


class TestScheduleAssignmentErrors:
    """Test assignment creation error handling"""

    def test_assignment_returns_error_dict(self, mock_shell):
        """Test when batch endpoint fails with assignment error"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.side_effect = Exception(
            "Cloud already has an active assignment"
        )

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show error
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("failed" in call.lower() for call in error_calls)

    def test_batch_endpoint_partial_success(self, mock_shell):
        """Test when batch endpoint returns partial success"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 2,
            "hostnames": ["host01", "host02"],
            "jira_updated": False,  # JIRA update failed
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should succeed even if JIRA failed
        mock_shell.connection.api.create_schedules_batch.assert_called_once()

    def test_batch_endpoint_with_multiple_hosts(self, mock_shell):
        """Test batch endpoint with multiple hosts"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 3,
            "hostnames": ["host01", "host02", "host03"],
            "jira_updated": True,
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02,host03 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should call batch endpoint once with all hosts
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert len(batch_data["hostnames"]) == 3

    def test_assignment_creation_exception(self, mock_shell):
        """Test when batch endpoint throws exception"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.side_effect = Exception("Database error")

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show error
        mock_shell.perror.assert_called()
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("failed" in call.lower() for call in error_calls)


class TestScheduleExistingAssignment:
    """Test using existing assignments"""

    def test_no_existing_assignment_error(self, mock_shell):
        """Test error when no assignment exists and no params provided"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.side_effect = Exception("No active assignment for cloud02")

        schedule_cmd = ScheduleCommands(mock_shell)
        # No assignment params provided
        schedule_cmd.cmd_schedule_admin('cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should show error from batch endpoint
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("failed" in call.lower() for call in error_calls)

    def test_existing_assignment_with_rich_console(self, mock_shell):
        """Test using existing assignment with rich console"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {
            "id": 50,
            "cloud": {"name": "cloud02"},
        }
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 50,
            "schedules_created": 1,
            "hostnames": ["host01"],
            "jira_updated": False,
        }
        # Enable rich console
        mock_shell.rich_console = MagicMock()

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin('cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should call batch endpoint without assignment params
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert "description" not in batch_data  # No assignment params

    def test_new_assignment_with_rich_console(self, mock_shell):
        """Test creating assignment with rich console"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 1,
            "hostnames": ["host01"],
            "jira_updated": True,
        }
        # Enable rich console
        mock_shell.rich_console = MagicMock()

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should call batch endpoint with assignment params
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert batch_data["description"] == "Test"
        assert batch_data["owner"] == "alice"
        assert batch_data["ticket"] == "JIRA-123"
