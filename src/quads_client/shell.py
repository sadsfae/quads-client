import cmd2

from quads_client.commands.available import AvailableCommands
from quads_client.commands.cloud import CloudCommands
from quads_client.commands.connection import ConnectionCommands
from quads_client.commands.host import HostCommands
from quads_client.commands.schedule import ScheduleCommands
from quads_client.commands.server import ServerCommands
from quads_client.commands.ssm import SSMCommands
from quads_client.commands.version import VersionCommands
from quads_client.config import ConfigError, QuadsClientConfig
from quads_client.connection import ConnectionManager
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
        self.host_commands = HostCommands(self)
        self.schedule_commands = ScheduleCommands(self)
        self.available_commands = AvailableCommands(self)
        self.server_commands = ServerCommands(self)

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

    def complete_connect(self, text, line, begidx, endidx):
        """Autocomplete for connect command"""
        if self.connection:
            servers = self.connection.get_available_servers()
            if text:
                return [s for s in servers if s.startswith(text)]
            return servers
        return []

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

    def do_ssm_register(self, args):
        """Register a new user"""
        self.ssm_commands.cmd_ssm_register(args)

    def do_ssm_login(self, args):
        """Explicit login"""
        self.ssm_commands.cmd_ssm_login(args)

    def do_ssm_create(self, args):
        """Create a self-assignment"""
        self.ssm_commands.cmd_ssm_create(args)

    def do_ssm_status(self, args):
        """Show assignment details"""
        self.ssm_commands.cmd_ssm_status(args)

    def do_ssm_list(self, args):
        """List user's assignments"""
        self.ssm_commands.cmd_ssm_list(args)

    def do_ssm_terminate(self, args):
        """Terminate an assignment"""
        self.ssm_commands.cmd_ssm_terminate(args)

    def do_ssm_whoami(self, args):
        """Show current user information"""
        self.ssm_commands.cmd_ssm_whoami(args)

    def do_ssm_available(self, args):
        """Show available hosts for self-scheduling"""
        self.ssm_commands.cmd_ssm_available(args)

    def do_ssm_schedule(self, args):
        """Schedule a host for yourself"""
        self.ssm_commands.cmd_ssm_schedule(args)

    def do_ssm_my_hosts(self, args):
        """Show hosts scheduled by you"""
        self.ssm_commands.cmd_ssm_my_hosts(args)

    def do_ls_hosts(self, args):
        """List all hosts"""
        self.host_commands.cmd_ls_hosts(args)

    def do_mark_broken(self, args):
        """Mark a host as broken"""
        self.host_commands.cmd_mark_broken(args)

    def do_mark_repaired(self, args):
        """Mark a broken host as repaired"""
        self.host_commands.cmd_mark_repaired(args)

    def do_retire(self, args):
        """Mark a host as retired"""
        self.host_commands.cmd_retire(args)

    def do_unretire(self, args):
        """Mark a retired host as active"""
        self.host_commands.cmd_unretire(args)

    def do_ls_broken(self, args):
        """List all broken hosts"""
        self.host_commands.cmd_ls_broken(args)

    def do_ls_retired(self, args):
        """List all retired hosts"""
        self.host_commands.cmd_ls_retired(args)

    def do_ls_schedule(self, args):
        """List schedules"""
        self.schedule_commands.cmd_ls_schedule(args)

    def do_add_schedule(self, args):
        """Add a schedule"""
        self.schedule_commands.cmd_add_schedule(args)

    def do_mod_schedule(self, args):
        """Modify a schedule"""
        self.schedule_commands.cmd_mod_schedule(args)

    def do_rm_schedule(self, args):
        """Remove a schedule"""
        self.schedule_commands.cmd_rm_schedule(args)

    def do_extend(self, args):
        """Extend a schedule"""
        self.schedule_commands.cmd_extend(args)

    def do_shrink(self, args):
        """Shrink a schedule"""
        self.schedule_commands.cmd_shrink(args)

    def do_ls_available(self, args):
        """List available hosts"""
        self.available_commands.cmd_ls_available(args)

    def do_servers(self, args):
        """List all configured servers"""
        self.server_commands.cmd_servers(args)

    def do_add_server(self, args):
        """Add a new server to configuration"""
        self.server_commands.cmd_add_server(args)

    def do_edit_server(self, args):
        """Edit an existing server configuration"""
        self.server_commands.cmd_edit_server(args)

    def do_rm_server(self, args):
        """Remove a server from configuration"""
        self.server_commands.cmd_rm_server(args)

    def do_config_reload(self, args):
        """Reload configuration from file"""
        self.server_commands.cmd_config_reload(args)

    def do_mod_cloud(self, args):
        """Modify cloud attributes"""
        self.cloud_commands.cmd_mod_cloud(args)
