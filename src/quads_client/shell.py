import cmd2

from quads_client.commands.cloud import CloudCommands
from quads_client.commands.connection import ConnectionCommands
from quads_client.commands.ssm import SSMCommands
from quads_client.commands.version import VersionCommands
from quads_client.config import ConfigError, QuadsClientConfig
from quads_client.connection import ConnectionError, ConnectionManager
from quads_client.history import CommandHistory


class QuadsClientShell(cmd2.Cmd):
    intro = r"""
================================================================================
  ___  _   _   _    ____  ____       ____ _ _            _
 / _ \| | | | / \  |  _ \/ ___|     / ___| (_) ___ _ __ | |_
| | | | | | |/ _ \ | | | \___ \ ___| |   | | |/ _ \ '_ \| __|
| |_| | |_| / ___ \| |_| |___) |___| |___| | |  __/ | | | |_
 \__\_\\___/_/   \_\____/|____/     \____|_|_|\___|_| |_|\__|

================================================================================
QUADS Client v1.0.0 - Interactive TUI Shell
https://quads.dev

Type 'help' for available commands
Type 'connect' to choose a server
Type 'ssm setup' for self-scheduling mode

Configuration: ~/.config/quads/quads-client.yml
History: ~/.config/quads/.quads-client-history.db
================================================================================
    """

    def __init__(self):
        super().__init__(
            multiline_commands=[],
            persistent_history_file="~/.config/quads/.quads-client_readline_history",
            persistent_history_length=1000,
        )
        self.config = None
        self.connection = None
        self.command_history = CommandHistory()

        try:
            self.config = QuadsClientConfig()
            self.connection = ConnectionManager(self.config)
        except ConfigError as e:
            self.pwarning(f"Configuration error: {e}")
            self.pwarning("Please create ~/.config/quads/quads-client.yml")

        self.connection_commands = ConnectionCommands(self)
        self.version_commands = VersionCommands(self)
        self.cloud_commands = CloudCommands(self)
        self.ssm_commands = SSMCommands(self)

        self._update_prompt()

    def _update_prompt(self):
        if self.connection and self.connection.is_connected:
            server = self.connection.current_server
            self.prompt = f"\033[1;32m({server})\033[0m > "
        else:
            self.prompt = "\033[1;31m(disconnected)\033[0m > "

    def do_version(self, args):
        """Display QUADS Client version"""
        self.version_commands.cmd_version(args)

    def do_connect(self, args):
        """Connect to a QUADS server. Usage: connect [server_name]"""
        self.connection_commands.cmd_connect(args)

    def do_disconnect(self, args):
        """Disconnect from current QUADS server"""
        self.connection_commands.cmd_disconnect(args)

    def do_status(self, args):
        """Show current connection status"""
        self.connection_commands.cmd_status(args)

    def do_cloud_list(self, args):
        """List all clouds (admin only)"""
        self.cloud_commands.cmd_cloud_list(args)

    def do_cloud_create(self, args):
        """Create a new cloud (admin only)"""
        self.cloud_commands.cmd_cloud_create(args)

    def do_cloud_delete(self, args):
        """Delete a cloud (admin only)"""
        self.cloud_commands.cmd_cloud_delete(args)

    def do_ssm_available(self, args):
        """Show available hosts for self-scheduling"""
        self.ssm_commands.cmd_ssm_available(args)

    def do_ssm_schedule(self, args):
        """Schedule a host for yourself"""
        self.ssm_commands.cmd_ssm_schedule(args)

    def do_ssm_my_hosts(self, args):
        """Show hosts scheduled by you"""
        self.ssm_commands.cmd_ssm_my_hosts(args)
