import pytest
from unittest.mock import MagicMock, patch
from quads_client.commands.schedule import ScheduleCommands


@pytest.fixture
def schedule_commands(mock_shell):
    return ScheduleCommands(mock_shell)


def test_ls_schedule_success(schedule_commands, mock_shell):
    """Test listing schedules successfully"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_schedules.return_value = [
        {
            "id": 1,
            "host": {"name": "host01.example.com"},
            "assignment": {
                "cloud": {"name": "cloud01"},
                "owner": "user@example.com",
            },
            "start": "2026-05-01 00:00",
            "end": "2026-05-15 00:00",
        },
    ]

    schedule_commands.cmd_ls_schedule("")

    mock_shell.connection.api.get_schedules.assert_called_once()
    mock_shell.poutput.assert_called()


def test_ls_schedule_with_filters(schedule_commands, mock_shell):
    """Test listing schedules with host filter"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_schedules.return_value = []

    schedule_commands.cmd_ls_schedule("host host01.example.com")

    mock_shell.connection.api.get_schedules.assert_called_once_with({"host": "host01.example.com"})


def test_ls_schedule_with_cloud_filter(schedule_commands, mock_shell):
    """Test listing schedules with cloud filter"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_schedules.return_value = []

    schedule_commands.cmd_ls_schedule("cloud cloud01")

    mock_shell.connection.api.get_schedules.assert_called_once_with({"cloud": "cloud01"})


def test_ls_schedule_empty(schedule_commands, mock_shell):
    """Test ls-schedule with no schedules"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.get_schedules.return_value = []

    schedule_commands.cmd_ls_schedule("")

    mock_shell.poutput.assert_called_with("No schedules found")


def test_add_schedule_success(schedule_commands, mock_shell):
    """Test adding a schedule successfully"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.api.create_schedule.return_value = {"id": 123}

    schedule_commands.cmd_add_schedule("host host01 cloud cloud01 start 2026-05-01 end 2026-05-15")

    expected_data = {
        "hostname": "host01",  # API expects "hostname" not "host"
        "cloud": "cloud01",
        "start": "2026-05-01",
        "end": "2026-05-15",
    }
    mock_shell.connection.api.create_schedule.assert_called_once_with(expected_data)
    mock_shell.poutput.assert_called_with("Schedule created successfully (ID: 123)")


def test_add_schedule_missing_args(schedule_commands, mock_shell):
    """Test add-schedule with missing arguments"""
    mock_shell.connection.is_connected = True

    schedule_commands.cmd_add_schedule("host host01")

    mock_shell.perror.assert_called()
    assert "Usage:" in mock_shell.perror.call_args[0][0]


def test_mod_schedule_success(schedule_commands, mock_shell):
    """Test modifying a schedule successfully"""
    mock_shell.connection.is_connected = True

    schedule_commands.cmd_mod_schedule("id 123 end 2026-06-01")

    mock_shell.connection.api.update_schedule.assert_called_once_with("123", {"end": "2026-06-01"})
    mock_shell.poutput.assert_called_with("Schedule 123 updated successfully")


def test_mod_schedule_no_id(schedule_commands, mock_shell):
    """Test mod-schedule without schedule ID"""
    mock_shell.connection.is_connected = True

    schedule_commands.cmd_mod_schedule("end 2026-06-01")

    mock_shell.perror.assert_called()
    assert "Usage:" in mock_shell.perror.call_args[0][0]


def test_mod_schedule_no_updates(schedule_commands, mock_shell):
    """Test mod-schedule with no updates specified"""
    mock_shell.connection.is_connected = True

    schedule_commands.cmd_mod_schedule("id 123")

    mock_shell.perror.assert_called_with("No updates specified")


def test_extend_success(schedule_commands, mock_shell):
    """Test extending a schedule successfully"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True
    mock_shell.connection.api.get_current_schedules.return_value = [
        {
            "id": 123,
            "host": {"name": "host01.example.com"},
            "end": "2026-05-15T00:00:00Z",
        }
    ]

    schedule_commands.cmd_extend("host01.example.com weeks 2")

    mock_shell.connection.api.get_current_schedules.assert_called_once_with({"host": "host01.example.com"})
    mock_shell.connection.api.update_schedule.assert_called_once()
    args = mock_shell.connection.api.update_schedule.call_args[0]
    assert args[0] == 123
    assert "2026-05-29" in args[1]["end"]
    mock_shell.poutput.assert_called()


def test_extend_no_schedule(schedule_commands, mock_shell):
    """Test extend with no current schedule"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True
    mock_shell.connection.api.get_current_schedules.return_value = []

    schedule_commands.cmd_extend("host01.example.com weeks 2")

    mock_shell.perror.assert_called_with("No current schedule found for host01.example.com")


def test_extend_missing_args(schedule_commands, mock_shell):
    """Test extend with missing arguments"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True

    schedule_commands.cmd_extend("host01")

    # Should error about invalid arguments
    mock_shell.perror.assert_called()
    assert "Usage:" in str(mock_shell.perror.call_args) or "Invalid arguments" in str(mock_shell.perror.call_args)


def test_shrink_success(schedule_commands, mock_shell):
    """Test shrinking a schedule by weeks"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True
    mock_shell.connection.api.get_current_schedules.return_value = [
        {
            "id": 123,
            "host": {"name": "host01.example.com"},
            "end": "2026-05-15 00:00",
        }
    ]

    schedule_commands.cmd_shrink("host01 weeks 1")

    mock_shell.connection.api.get_current_schedules.assert_called_once_with({"host": "host01"})
    mock_shell.connection.api.update_schedule.assert_called_once()
    args = mock_shell.connection.api.update_schedule.call_args[0]
    assert args[0] == 123
    assert "2026-05-08" in args[1]["end"]
    mock_shell.poutput.assert_called()


def test_shrink_by_days(schedule_commands, mock_shell):
    """Test shrinking a schedule by days"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True
    mock_shell.connection.api.get_current_schedules.return_value = [
        {
            "id": 123,
            "host": {"name": "host01.example.com"},
            "end": "2026-05-15 00:00",
        }
    ]

    schedule_commands.cmd_shrink("host01 days 3")

    mock_shell.connection.api.update_schedule.assert_called_once()
    args = mock_shell.connection.api.update_schedule.call_args[0]
    assert args[0] == 123
    assert "2026-05-12" in args[1]["end"]


def test_shrink_now(schedule_commands, mock_shell):
    """Test shrinking a schedule to now"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True
    mock_shell.connection.api.get_current_schedules.return_value = [
        {
            "id": 123,
            "host": {"name": "host01.example.com"},
            "end": "2026-05-15 00:00",
        }
    ]

    schedule_commands.cmd_shrink("host01 now")

    mock_shell.connection.api.update_schedule.assert_called_once()
    args = mock_shell.connection.api.update_schedule.call_args[0]
    assert args[0] == 123
    assert "end" in args[1]


def test_shrink_by_date(schedule_commands, mock_shell):
    """Test shrinking a schedule to a specific date"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True
    mock_shell.connection.api.get_current_schedules.return_value = [
        {
            "id": 123,
            "host": {"name": "host01.example.com"},
            "end": "2026-05-15 00:00",
        }
    ]

    schedule_commands.cmd_shrink('host01 date "2026-05-12 22:00"')

    mock_shell.connection.api.update_schedule.assert_called_once()
    args = mock_shell.connection.api.update_schedule.call_args[0]
    assert args[0] == 123
    assert "2026-05-12" in args[1]["end"]


def test_shrink_missing_args(schedule_commands, mock_shell):
    """Test shrink with missing arguments"""
    mock_shell.connection.is_connected = True
    mock_shell.connection.is_authenticated = True
    mock_shell.connection.is_admin = True

    schedule_commands.cmd_shrink("host01")

    mock_shell.perror.assert_called()


def test_schedule_not_connected(schedule_commands, mock_shell):
    """Test schedule commands when not connected"""
    mock_shell.connection.is_connected = False

    schedule_commands.cmd_ls_schedule("")

    mock_shell.perror.assert_called_with("Not connected to any server")
