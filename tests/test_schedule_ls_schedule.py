"""Tests for ls-schedule command to boost coverage"""

import pytest
from unittest.mock import MagicMock
from quads_client.commands.schedule import ScheduleCommands


class TestLsScheduleSingleHost:
    """Test ls-schedule for single host with detail view"""

    def test_ls_schedule_single_host_with_current_schedule(self, mock_shell):
        """Test ls-schedule for single host showing current schedule"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-07T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}},
            },
            {
                "id": 2,
                "start": "2026-05-08T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud03"}},
            },
        ]
        mock_shell.connection.api.get_host.return_value = {
            "name": "host01.example.com",
            "default_cloud": {"name": "cloud01"},
            "cloud": {"name": "cloud02"},
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("host host01.example.com")

        # Should call get_schedules with host filter
        mock_shell.connection.api.get_schedules.assert_called_once_with({"host": "host01.example.com"})
        # Should call get_host for details
        mock_shell.connection.api.get_host.assert_called_once_with("host01.example.com")
        # Should show default cloud, current cloud, current schedule
        assert mock_shell.poutput.call_count >= 3

    def test_ls_schedule_single_host_no_current_schedule(self, mock_shell):
        """Test ls-schedule for single host with no current schedule"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}},
            },
        ]
        mock_shell.connection.api.get_host.return_value = {
            "name": "host01.example.com",
            "default_cloud": {"name": "cloud01"},
            "cloud": {"name": "cloud01"},
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("host host01.example.com")

        # Should show default/current cloud but not current schedule
        poutput_calls = [str(call) for call in mock_shell.poutput.call_args_list]
        assert any("Default cloud:" in call for call in poutput_calls)
        assert any("Current cloud:" in call for call in poutput_calls)

    def test_ls_schedule_single_host_with_rich_console(self, mock_shell):
        """Test ls-schedule single host with rich console"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}},
            },
        ]
        mock_shell.connection.api.get_host.return_value = {
            "name": "host01.example.com",
            "default_cloud": {"name": "cloud01"},
            "cloud": {"name": "cloud02"},
        }
        mock_shell.rich_console = MagicMock()

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("host host01.example.com")

        # Should use rich console for table
        mock_shell.rich_console.print_table.assert_called_once()
        call_args = mock_shell.rich_console.print_table.call_args
        assert "Schedule History for host01.example.com" in str(call_args)

    def test_ls_schedule_single_host_get_host_fails(self, mock_shell):
        """Test ls-schedule single host when get_host fails"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "host": {"name": "host01.example.com"},
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}, "owner": "alice"},
            },
        ]
        mock_shell.connection.api.get_host.side_effect = Exception("Host not found")

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("host host01.example.com")

        # Should show warning but fall through to regular table
        error_calls = [str(call) for call in mock_shell.perror.call_args_list]
        assert any("Warning: Could not fetch host details" in call for call in error_calls)
        # Should still show schedules in regular table format
        assert mock_shell.poutput.call_count >= 1


class TestLsScheduleRegularTable:
    """Test ls-schedule regular table format"""

    def test_ls_schedule_multiple_hosts(self, mock_shell):
        """Test ls-schedule without filters shows regular table"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "host": {"name": "host01.example.com"},
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}, "owner": "alice"},
            },
            {
                "id": 2,
                "host": {"name": "host02.example.com"},
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}, "owner": "alice"},
            },
        ]

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("")

        # Should show regular table
        assert mock_shell.poutput.call_count >= 1

    def test_ls_schedule_cloud_filter(self, mock_shell):
        """Test ls-schedule with cloud filter shows regular table"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "host": {"name": "host01.example.com"},
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}, "owner": "alice"},
            },
        ]

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("cloud cloud02")

        # Should call with cloud filter
        mock_shell.connection.api.get_schedules.assert_called_once_with({"cloud": "cloud02"})

    def test_ls_schedule_no_schedules(self, mock_shell):
        """Test ls-schedule when no schedules found"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = []

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("")

        # Should show "No schedules found"
        mock_shell.poutput.assert_called_with("No schedules found")

    def test_ls_schedule_host_and_cloud_filter(self, mock_shell):
        """Test ls-schedule with both host and cloud filter"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "host": {"name": "host01.example.com"},
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud02"}, "owner": "alice"},
            },
        ]

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("host host01.example.com cloud cloud02")

        # Should call with both filters and show regular table (not single host detail)
        mock_shell.connection.api.get_schedules.assert_called_once_with(
            {"host": "host01.example.com", "cloud": "cloud02"}
        )
        # Should not call get_host when cloud filter is present
        assert mock_shell.connection.api.get_host.call_count == 0


class TestLsScheduleDateParsing:
    """Test ls-schedule date parsing edge cases"""

    def test_ls_schedule_invalid_date_format(self, mock_shell):
        """Test ls-schedule with schedule containing invalid date format"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "start": "invalid-date",
                "end": "also-invalid",
                "assignment": {"cloud": {"name": "cloud02"}},
            },
            {
                "id": 2,
                "start": "2026-05-01T00:00:00Z",
                "end": "2026-05-15T23:59:59Z",
                "assignment": {"cloud": {"name": "cloud03"}},
            },
        ]
        mock_shell.connection.api.get_host.return_value = {
            "name": "host01.example.com",
            "default_cloud": {"name": "cloud01"},
            "cloud": {"name": "cloud02"},
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("host host01.example.com")

        # Should handle invalid dates gracefully (catch ValueError/AttributeError)
        # Should still show table
        assert mock_shell.poutput.call_count >= 1

    def test_ls_schedule_empty_date_fields(self, mock_shell):
        """Test ls-schedule with schedule containing empty date fields"""
        mock_shell.connection.is_connected = True
        mock_shell.connection.api.get_schedules.return_value = [
            {
                "id": 1,
                "start": "",
                "end": "",
                "assignment": {"cloud": {"name": "cloud02"}},
            },
        ]
        mock_shell.connection.api.get_host.return_value = {
            "name": "host01.example.com",
            "default_cloud": {"name": "cloud01"},
            "cloud": {"name": "cloud01"},
        }

        schedule_cmd = ScheduleCommands(mock_shell)
        schedule_cmd.cmd_ls_schedule("host host01.example.com")

        # Should handle empty dates gracefully
        assert mock_shell.poutput.call_count >= 1
