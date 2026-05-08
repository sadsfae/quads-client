"""Tests for admin schedule command enhancements (pre-flight checks, orphaned cleanup)"""

import pytest
from unittest.mock import MagicMock
from quads_client.commands.schedule import ScheduleCommands


class TestSchedulePreFlightChecks:
    """Test pre-flight availability checking"""

    def test_schedule_admin_pre_flight_all_available(self, mock_shell):
        """Test schedule with all hosts available"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 50}
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 50,
            "schedules_created": 2,
            "hostnames": ["host01", "host02"],
            "jira_updated": False,
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin('cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should use batch endpoint
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert batch_data["cloud"] == "cloud02"
        assert batch_data["hostnames"] == ["host01", "host02"]

    def test_schedule_admin_pre_flight_some_unavailable(self, mock_shell):
        """Test schedule with some hosts unavailable"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 50}
        # Batch endpoint returns error for unavailable hosts
        mock_shell.connection.api.create_schedules_batch.side_effect = Exception("Some hosts are unavailable")

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin('cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should show error about unavailable hosts
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("unavailable" in call.lower() for call in error_calls)

    def test_schedule_admin_pre_flight_now_skips_check(self, mock_shell):
        """Test schedule with 'now' passes to batch endpoint"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 2,
            "hostnames": ["host01", "host02"],
            "jira_updated": True,
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02 now "2026-06-11 22:00" description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should use batch endpoint with "now"
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert batch_data["start"] == "now"
        assert batch_data["description"] == "Test"
        assert batch_data["owner"] == "alice"
        assert batch_data["ticket"] == "JIRA-123"


class TestScheduleOrphanedCleanup:
    """Test orphaned assignment cleanup when all schedules fail"""

    def test_orphaned_assignment_cleanup_on_all_failures(self, mock_shell):
        """Test error handling when batch endpoint fails"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        # Batch endpoint fails
        mock_shell.connection.api.create_schedules_batch.side_effect = Exception("Some schedules failed to create")

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00" description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should show error from batch endpoint
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("failed" in call.lower() for call in error_calls)

    def test_no_cleanup_when_some_schedules_succeed(self, mock_shell):
        """Test batch endpoint success"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.create_schedules_batch.return_value = {
            "assignment_id": 150,
            "schedules_created": 2,
            "hostnames": ["host01", "host02"],
            "jira_updated": False,
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Batch endpoint should succeed
        mock_shell.connection.api.create_schedules_batch.assert_called_once()

    def test_no_cleanup_when_using_existing_assignment(self, mock_shell):
        """Test using existing assignment with batch endpoint"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
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

        schedule_cmd = ScheduleCommands(mock_shell)
        # No assignment params provided - uses existing
        schedule_cmd.cmd_schedule_admin('cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should use batch endpoint without assignment params
        mock_shell.connection.api.create_schedules_batch.assert_called_once()
        batch_data = mock_shell.connection.api.create_schedules_batch.call_args[0][0]
        assert "description" not in batch_data  # No assignment params


class TestScheduleDateValidation:
    """Test date validation in schedule command"""

    def test_start_before_end_validation(self, mock_shell):
        """Test error when start date >= end date"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]

        schedule_cmd = ScheduleCommands(mock_shell)
        # End date before start date
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-06-11 22:00" "2026-05-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should error about date order
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("start date must be before end date" in call.lower() for call in error_calls)

    def test_invalid_date_format(self, mock_shell):
        """Test error on invalid date format"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]

        schedule_cmd = ScheduleCommands(mock_shell)
        # Invalid date format
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11" "2026-06-11" description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should error about format
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("invalid date format" in call.lower() for call in error_calls)


class TestScheduleRequiredFields:
    """Test required field validation for new assignments"""

    def test_missing_description_for_new_assignment(self, mock_shell):
        """Test error when description missing for new assignment"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True

        schedule_cmd = ScheduleCommands(mock_shell)
        # Has cloud-ticket but missing description
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should error about missing description
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("description is required" in call.lower() for call in error_calls)

    def test_missing_cloud_owner_for_new_assignment(self, mock_shell):
        """Test error when cloud-owner missing for new assignment"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True

        schedule_cmd = ScheduleCommands(mock_shell)
        # Has cloud-ticket but missing cloud-owner
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" description "Test" cloud-ticket JIRA-123'
        )

        # Should error about missing cloud-owner
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("cloud-owner is required" in call.lower() for call in error_calls)

    def test_missing_cloud_ticket_for_new_assignment(self, mock_shell):
        """Test error when cloud-ticket missing for new assignment"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True

        schedule_cmd = ScheduleCommands(mock_shell)
        # Has description and owner but missing ticket
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00" description "Test" cloud-owner alice'
        )

        # Should error about missing cloud-ticket
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("cloud-ticket is required" in call.lower() for call in error_calls)
