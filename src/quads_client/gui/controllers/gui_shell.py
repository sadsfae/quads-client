"""GUI Shell Adapter - bridges GUI with existing command classes"""

from quads_client.commands.available import AvailableCommands
from quads_client.commands.cloud import CloudCommands
from quads_client.commands.connection import ConnectionCommands
from quads_client.commands.host import HostCommands
from quads_client.commands.schedule import ScheduleCommands
from quads_client.commands.server import ServerCommands
from quads_client.commands.session import SessionCommands
from quads_client.commands.user import UserCommands
from quads_client.commands.version import VersionCommands
from quads_client.config import ConfigError, QuadsClientConfig
from quads_client.history import CommandHistory
from quads_client.session_manager import SessionManager


class GuiShell:
    """
    Adapter that allows GUI to reuse command logic without cmd2 dependency.
    Mimics the QuadsClientShell interface that command classes expect.
    """

    def __init__(self, gui_app):
        """
        Initialize GUI shell adapter

        Args:
            gui_app: Reference to the main GUI application (QuadsClientApp)
        """
        self.gui_app = gui_app
        self.config = None
        self.session_manager = None
        self.command_history = CommandHistory()
        self.rich_console = None
        self.debug = False
        self.quiet = False
        self.gui_mode = True

        try:
            self.config = QuadsClientConfig()
            self.session_manager = SessionManager(self.config)
        except ConfigError as e:
            self.pwarning(f"Configuration error: {e}")

        self.connection_commands = ConnectionCommands(self)
        self.version_commands = VersionCommands(self)
        self.cloud_commands = CloudCommands(self)
        self.user_commands = UserCommands(self)
        self.host_commands = HostCommands(self)
        self.schedule_commands = ScheduleCommands(self)
        self.available_commands = AvailableCommands(self)
        self.server_commands = ServerCommands(self)
        self.session_commands = SessionCommands(self)

    @property
    def connection(self):
        """Active session's connection for backward compatibility"""
        if self.session_manager:
            return self.session_manager.active_connection
        return None

    def poutput(self, message):
        """Output message to GUI (info level)"""
        if self.gui_app:
            self.gui_app.show_message(message, level="info")
        else:
            print(message)

    def perror(self, message):
        """Error output to GUI"""
        if self.gui_app:
            self.gui_app.show_message(message, level="error")
        else:
            print(f"ERROR: {message}")

    def pwarning(self, message):
        """Warning output to GUI"""
        if self.gui_app:
            self.gui_app.show_message(message, level="warning")
        else:
            print(f"WARNING: {message}")

    def pfeedback(self, message):
        """Feedback output to GUI (same as poutput for GUI)"""
        self.poutput(message)

    def execute_command(self, command_name, args=""):
        """
        Execute a command by name with arguments

        Args:
            command_name: Name of the command (e.g., 'connect', 'schedule')
            args: Command arguments as string

        Returns:
            Command result (if any)
        """
        command_map = {
            "connect": self.connection_commands.cmd_connect,
            "disconnect": self.connection_commands.cmd_disconnect,
            "status": self.connection_commands.cmd_status,
            "login": self.user_commands.cmd_login,
            "logout": self.user_commands.cmd_logout,
            "register": self.user_commands.cmd_register,
            "whoami": self.user_commands.cmd_whoami,
            "schedule": self.user_commands.cmd_schedule,
            "my-hosts": self.user_commands.cmd_my_hosts,
            "my-assignments": self.user_commands.cmd_my_assignments,
            "terminate": self.user_commands.cmd_terminate,
            "cloud-list": self.cloud_commands.cmd_cloud_list,
            "ls-available": self.available_commands.cmd_ls_available,
            "ls-hosts": self.host_commands.cmd_ls_hosts,
            "version": self.version_commands.cmd_version,
            "servers": self.server_commands.cmd_servers,
            "add-server": self.server_commands.cmd_add_server,
            "session-list": self.session_commands.cmd_session_list,
            "session-create": self.session_commands.cmd_session_create,
            "session-switch": self.session_commands.cmd_session_switch,
            "session-close": self.session_commands.cmd_session_close,
        }

        command_func = command_map.get(command_name)
        if command_func:
            try:
                return command_func(args)
            except Exception as e:
                self.perror(f"Command failed: {e}")
                import traceback

                traceback.print_exc()
        else:
            self.perror(f"Unknown command: {command_name}")

    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.connection and self.connection.is_authenticated

    def is_admin(self):
        """Check if user has admin role"""
        return self.connection and self.connection.is_admin

    def _update_prompt(self):
        """Update prompt (no-op for GUI, used by CLI)"""
        pass

    def _update_visible_commands(self):
        """Update visible commands (no-op for GUI, used by CLI)"""
        pass
