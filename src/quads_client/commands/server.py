from tabulate import tabulate
import yaml
from pathlib import Path


class ServerCommands:
    def __init__(self, shell):
        self.shell = shell
        self.rich_console = shell.rich_console if hasattr(shell, "rich_console") else None

    def _shorten_server_name(self, name):
        """Shorten server name by stripping last 2 segments (e.g. quads2-dev.rdu2.scalelab)"""
        parts = name.split(".")
        if len(parts) > 3:
            return ".".join(parts[:-2])
        return name

    def cmd_servers(self, args):
        """List all configured servers with status"""
        if not self.shell.config:
            self.shell.perror("Configuration not loaded")
            return

        servers = self.shell.config.get_all_servers()
        default = self.shell.config.get_default_server()
        current = self.shell.connection.current_server if self.shell.connection else None

        table_data = []
        for i, (name, server_config) in enumerate(servers.items(), 1):
            url = server_config.get("url", "")
            status, version = self._get_server_status(name, url, server_config)
            info = self._get_server_info(name, url, server_config)

            is_default = "✓" if name == default else ""
            is_connected = "Connected" if name == current else status
            short_name = self._shorten_server_name(name)

            table_data.append([i, short_name, version, info, is_connected, is_default])

        headers = ["#", "Server Name", "Version", "Info", "Status", "Default"]
        if self.rich_console:
            self.rich_console.print_table(headers, table_data, title="Configured Servers")
            if current:
                short_current = self._shorten_server_name(current)
                self.rich_console.print_info(f"\n[bold cyan]Current connection:[/bold cyan] {short_current}")
        else:
            self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))
            if current:
                short_current = self._shorten_server_name(current)
                self.shell.poutput(f"\nCurrent connection: {short_current}")

    def _get_server_status(self, name, url, server_config):
        """Check if server is online and get version"""
        try:
            from quads_lib import QuadsApi

            username = server_config.get("username", "")
            password = server_config.get("password", "")
            verify = server_config.get("verify", True)

            if not username or not password:
                return "No credentials", "N/A"

            api = QuadsApi(base_url=url, username=username, password=password, verify=verify)
            version_info = api.get_version()
            version = version_info.get("version", "unknown") if isinstance(version_info, dict) else "unknown"
            return "Online", version
        except Exception:
            return "Offline", "N/A"

    def _get_server_info(self, name, url, server_config):
        """Get server summary info"""
        try:
            from quads_lib import QuadsApi

            username = server_config.get("username", "")
            password = server_config.get("password", "")
            verify = server_config.get("verify", True)

            if not username or not password:
                return "N/A"

            api = QuadsApi(base_url=url, username=username, password=password, verify=verify)
            summary = api.get_summary({})

            clouds = len(summary) if isinstance(summary, list) else 0
            return f"{clouds} clouds"
        except Exception:
            return "N/A"

    def cmd_add_server(self, args):
        """Add a new server to configuration. Usage: add-server <name> <url> <username> <password>"""
        parts = args.split()
        if len(parts) < 4:
            self.shell.perror("Usage: add-server <name> <url> <username> <password> [--no-verify]")
            return

        name = parts[0]
        url = parts[1]
        username = parts[2]
        password = parts[3]
        verify = "--no-verify" not in parts

        if not self.shell.config:
            self.shell.perror("Configuration not loaded")
            return

        config_path = Path(self.shell.config.config_path).expanduser()

        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

            if "servers" not in config_data:
                config_data["servers"] = {}

            if name in config_data["servers"]:
                self.shell.perror(f"Server '{name}' already exists. Use edit-server to modify.")
                return

            self.shell.poutput(f"Testing connection to {url}...")
            try:
                from quads_lib import QuadsApi

                api = QuadsApi(base_url=url, username=username, password=password, verify=verify)
                version = api.get_version()
                if self.rich_console:
                    self.rich_console.print_success(f"Connected successfully (QUADS version: {version.get('version', 'unknown')})")
                else:
                    self.shell.poutput(f"✓ Connected successfully (QUADS version: {version.get('version', 'unknown')})")
            except Exception as e:
                self.shell.pwarning(f"Warning: Could not connect to server: {e}")
                response = input("Add server anyway? [y/N]: ")
                if response.lower() != "y":
                    self.shell.poutput("Server not added")
                    return

            config_data["servers"][name] = {
                "url": url,
                "username": username,
                "password": password,
                "verify": verify,
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            if self.rich_console:
                self.rich_console.print_success(f"Server '{name}' added successfully")
                self.rich_console.print_info("Reload configuration with: config-reload")
            else:
                self.shell.poutput(f"✓ Server '{name}' added successfully")
                self.shell.poutput("Reload configuration with: config-reload")

        except Exception as e:
            self.shell.perror(f"Failed to add server: {e}")

    def cmd_edit_server(self, args):
        """Edit an existing server.
        Usage: edit-server <name> [--url URL] [--username USER] [--password PASS] [--verify true|false]
        """
        parts = args.split()
        if len(parts) < 1:
            self.shell.perror(
                "Usage: edit-server <name> [--url URL] [--username USER] [--password PASS] [--verify true|false]"
            )
            return

        name = parts[0]

        if not self.shell.config:
            self.shell.perror("Configuration not loaded")
            return

        config_path = Path(self.shell.config.config_path).expanduser()

        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

            if "servers" not in config_data or name not in config_data["servers"]:
                self.shell.perror(f"Server '{name}' not found")
                return

            server = config_data["servers"][name]
            updates = {}

            i = 1
            while i < len(parts):
                if parts[i] == "--url" and i + 1 < len(parts):
                    updates["url"] = parts[i + 1]
                    i += 2
                elif parts[i] == "--username" and i + 1 < len(parts):
                    updates["username"] = parts[i + 1]
                    i += 2
                elif parts[i] == "--password" and i + 1 < len(parts):
                    updates["password"] = parts[i + 1]
                    i += 2
                elif parts[i] == "--verify" and i + 1 < len(parts):
                    updates["verify"] = parts[i + 1].lower() == "true"
                    i += 2
                else:
                    i += 1

            if not updates:
                self.shell.perror("No updates specified")
                return

            server.update(updates)
            config_data["servers"][name] = server

            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            self.shell.poutput(f"✓ Server '{name}' updated successfully")
            self.shell.poutput("Reload configuration with: config-reload")

        except Exception as e:
            self.shell.perror(f"Failed to edit server: {e}")

    def cmd_rm_server(self, args):
        """Remove a server from configuration. Usage: rm-server <name>"""
        if not args.strip():
            self.shell.perror("Usage: rm-server <name>")
            return

        name = args.strip()

        if not self.shell.config:
            self.shell.perror("Configuration not loaded")
            return

        if self.shell.connection and self.shell.connection.current_server == name:
            self.shell.perror(f"Cannot remove '{name}' - currently connected. Disconnect first.")
            return

        config_path = Path(self.shell.config.config_path).expanduser()

        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

            if "servers" not in config_data or name not in config_data["servers"]:
                self.shell.perror(f"Server '{name}' not found")
                return

            response = input(f"Remove server '{name}'? [y/N]: ")
            if response.lower() != "y":
                self.shell.poutput("Server not removed")
                return

            del config_data["servers"][name]

            if config_data.get("default_server") == name:
                config_data["default_server"] = None

            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            self.shell.poutput(f"✓ Server '{name}' removed successfully")
            self.shell.poutput("Reload configuration with: config-reload")

        except Exception as e:
            self.shell.perror(f"Failed to remove server: {e}")

    def cmd_config_reload(self, args):
        """Reload configuration from file"""
        try:
            from quads_client.config import QuadsClientConfig
            from quads_client.connection import ConnectionManager

            self.shell.config = QuadsClientConfig()
            self.shell.connection = ConnectionManager(self.shell.config)
            self.shell.poutput("✓ Configuration reloaded successfully")
        except Exception as e:
            self.shell.perror(f"Failed to reload configuration: {e}")
