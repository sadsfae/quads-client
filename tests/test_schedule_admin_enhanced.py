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
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {"id": 50}
        mock_shell.connection.api.create_schedule.return_value = {"id": 1}

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin('cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should check availability for each host
        assert mock_shell.connection.api.is_available.call_count == 2
        # Should create schedules since all available
        assert mock_shell.connection.api.create_schedule.call_count == 2

    def test_schedule_admin_pre_flight_some_unavailable(self, mock_shell):
        """Test schedule with some hosts unavailable"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        # host01 available, host02 unavailable
        mock_shell.connection.api.is_available.side_effect = [True, False]

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin('cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should check availability
        assert mock_shell.connection.api.is_available.call_count == 2
        # Should NOT create any schedules (blocked by pre-flight)
        assert mock_shell.connection.api.create_schedule.call_count == 0
        # Should show error about unavailable host
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("unavailable" in call.lower() for call in error_calls)
        assert any("host02" in call for call in error_calls)

    def test_schedule_admin_pre_flight_now_skips_check(self, mock_shell):
        """Test schedule with 'now' skips pre-flight check"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
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
            'cloud02 host01,host02 now "2026-06-11 22:00" description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should NOT check availability when start is "now"
        assert mock_shell.connection.api.is_available.call_count == 0
        # Should create schedules with "now" as start value
        assert mock_shell.connection.api.create_schedule.call_count == 2
        # Verify "now" is passed to API (not None)
        first_call = mock_shell.connection.api.create_schedule.call_args_list[0][0][0]
        assert first_call["start"] == "now"


class TestScheduleOrphanedCleanup:
    """Test orphaned assignment cleanup when all schedules fail"""

    def test_orphaned_assignment_cleanup_on_all_failures(self, mock_shell):
        """Test cleanup when all schedules fail after assignment created"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
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
        # All schedule creations fail
        mock_shell.connection.api.create_schedule.side_effect = Exception("Host already scheduled")

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should create assignment
        mock_shell.connection.api.create_assignment.assert_called_once()
        # Should try to create schedules
        assert mock_shell.connection.api.create_schedule.call_count == 2
        # Should cleanup orphaned assignment
        mock_shell.connection.api.terminate_assignment.assert_called_once_with(150)

    def test_no_cleanup_when_some_schedules_succeed(self, mock_shell):
        """Test no cleanup when at least one schedule succeeds"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
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
        # First schedule succeeds, second fails
        mock_shell.connection.api.create_schedule.side_effect = [
            {"id": 1},
            Exception("Conflict"),
        ]

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_schedule_admin(
            'cloud02 host01,host02 "2026-05-11 22:00" "2026-06-11 22:00" '
            'description "Test" cloud-owner alice cloud-ticket JIRA-123'
        )

        # Should NOT cleanup assignment (at least one schedule succeeded)
        assert mock_shell.connection.api.terminate_assignment.call_count == 0

    def test_no_cleanup_when_using_existing_assignment(self, mock_shell):
        """Test no cleanup when using existing assignment"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.is_authenticated = True
        mock_shell.connection.is_admin = True
        mock_shell.connection.api.filter_clouds.return_value = [{"name": "cloud02"}]
        mock_shell.connection.api.is_available.return_value = True
        mock_shell.connection.api.get_active_cloud_assignment.return_value = {
            "id": 50,  # Existing assignment
            "cloud": {"name": "cloud02"},
        }
        # All schedule creations fail
        mock_shell.connection.api.create_schedule.side_effect = Exception("Error")

        schedule_cmd = ScheduleCommands(mock_shell)
        # No assignment params provided - uses existing
        schedule_cmd.cmd_schedule_admin('cloud02 host01 "2026-05-11 22:00" "2026-06-11 22:00"')

        # Should NOT cleanup (didn't create the assignment)
        assert mock_shell.connection.api.terminate_assignment.call_count == 0


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
