from tabulate import tabulate
import yaml
from pathlib import Path

from quads_client.utils import get_ssl_status_text


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
            verify = server_config.get("verify", True)
            # Get both status/version and info in one call to avoid double connection overhead
            status, version, info = self._get_server_info_combined(name, url, server_config)

            is_default = "✓" if name == default else ""
            is_connected = "Connected" if name == current else status
            short_name = self._shorten_server_name(name)
            ssl_status = get_ssl_status_text(url, verify)

            table_data.append([i, short_name, ssl_status, version, info, is_connected, is_default])

        headers = ["#", "Server Name", "SSL", "Version", "Capacity", "Status", "Default"]
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

    def _get_server_info_combined(self, name, url, server_config):
        """Get server status, version, and capacity in one API connection to avoid double overhead"""
        try:
            from quads_lib import QuadsApi
            import urllib3

            username = server_config.get("username", "")
            password = server_config.get("password", "")
            verify = server_config.get("verify", True)

            if not username or not password:
                return "No credentials", "N/A", "N/A"

            # Suppress SSL warnings when certificate verification is disabled
            if not verify:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Single API connection for all info
            api = QuadsApi(base_url=url, username=username, password=password, verify=verify)

            # Login first
            try:
                login_result = api.login()
                if not login_result or login_result.get("status") == "failure":
                    return "Auth failed", "N/A", "N/A"
            except Exception:
                return "Offline", "N/A", "N/A"

            # Get version
            version = "unknown"
            try:
                version_info = api.get_version()

                if isinstance(version_info, dict):
                    version = version_info.get("version", "unknown")
                    if not version or version == "":
                        version = "unknown"
                elif isinstance(version_info, str):
                    # API returns string like "QUADS version 2.2.6 maximilian"
                    # Extract just the version number
                    import re

                    version_match = re.search(r"(\d+\.\d+\.\d+)", version_info)
                    if version_match:
                        version = version_match.group(1)
                    else:
                        # Couldn't parse version number, use full string
                        version = version_info if version_info else "unknown"
                else:
                    version = "unknown"
            except Exception:
                version = "unknown"

            # Get capacity info
            capacity = "N/A"
            try:
                all_hosts = api.get_hosts()
                total_hosts = sum(1 for h in all_hosts if not h.get("broken") and not h.get("retired"))

                if total_hosts > 0:
                    current_schedules = api.get_current_schedules({})
                    scheduled_hosts = len(
                        set(s.get("host", {}).get("name", "") for s in current_schedules if s.get("host"))
                    )
                    percent_used = int((scheduled_hosts / total_hosts) * 100)
                    free_hosts = total_hosts - scheduled_hosts
                    capacity = f"{percent_used}% ({free_hosts}/{total_hosts})"
                else:
                    capacity = "0% (0/0)"
            except Exception:
                # Capacity check failed, but we still have version
                capacity = "N/A"

            return "Online", version, capacity
        except Exception:
            return "Offline", "N/A", "N/A"

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
            # Login first to get authenticated
            try:
                login_result = api.login()
                if not login_result or login_result.get("status") == "failure":
                    return "Auth failed", "N/A"
            except Exception:
                # Login failed - server might be offline or credentials wrong
                return "Offline", "N/A"

            # Try to get version - if not implemented, still show as online
            try:
                version_info = api.get_version()

                if isinstance(version_info, dict):
                    version = version_info.get("version", "unknown")
                    # Handle case where version might be None or empty
                    if not version or version == "":
                        version = "unknown"
                elif isinstance(version_info, str):
                    # API returns string like "QUADS version 2.2.6 maximilian"
                    # Extract just the version number
                    import re

                    version_match = re.search(r"(\d+\.\d+\.\d+)", version_info)
                    if version_match:
                        version = version_match.group(1)
                    else:
                        # Couldn't parse version number, use full string
                        version = version_info if version_info else "unknown"
                else:
                    version = "unknown"
            except Exception:
                # Version endpoint not implemented or failed - but we're still online
                version = "unknown"

            return "Online", version
        except Exception:
            return "Offline", "N/A"

    def _get_server_info(self, name, url, server_config):
        """Get server capacity info (% utilization + free/total)"""
        try:
            from quads_lib import QuadsApi

            username = server_config.get("username", "")
            password = server_config.get("password", "")
            verify = server_config.get("verify", True)

            if not username or not password:
                return "N/A"

            api = QuadsApi(base_url=url, username=username, password=password, verify=verify)
            # Login first to get authenticated
            try:
                login_result = api.login()
                if not login_result or login_result.get("status") == "failure":
                    return "N/A"
            except Exception:
                return "N/A"

            # Get total hosts (excluding broken/retired)
            all_hosts = api.get_hosts()
            total_hosts = sum(1 for h in all_hosts if not h.get("broken") and not h.get("retired"))

            if total_hosts == 0:
                return "0% (0/0)"

            # Get currently scheduled hosts
            current_schedules = api.get_current_schedules({})
            scheduled_hosts = len(set(s.get("host", {}).get("name", "") for s in current_schedules if s.get("host")))

            # Calculate percentage and free hosts
            percent_used = int((scheduled_hosts / total_hosts) * 100)
            free_hosts = total_hosts - scheduled_hosts

            return f"{percent_used}% ({free_hosts}/{total_hosts})"
        except Exception:
            return "N/A"

    def cmd_add_quads_server(self, args):
        """Interactive command to add a new QUADS server to configuration"""
        if not self.shell.config:
            self.shell.perror("Configuration not loaded")
            return

        self.shell.poutput("\n=== Add New QUADS Server ===\n")

        # Prompt for server name
        server_name = input("Enter server name (e.g., quads1.example.com): ").strip()
        if not server_name:
            self.shell.perror("Server name cannot be empty")
            return

        # Check if server already exists
        config_path = Path(self.shell.config.config_path).expanduser()
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

            if "servers" not in config_data:
                config_data["servers"] = {}

            if server_name in config_data["servers"]:
                self.shell.perror(f"Server '{server_name}' already exists. Use edit-server to modify.")
                return
        except Exception as e:
            self.shell.perror(f"Failed to read configuration: {e}")
            return

        # Prompt for URL
        server_url = input("Enter server URL (e.g., https://quads1.example.com): ").strip()
        if not server_url:
            self.shell.perror("Server URL cannot be empty")
            return

        # Ensure URL starts with http:// or https://
        if not server_url.startswith(("http://", "https://")):
            self.shell.pwarning("URL should start with https:// (or http:// for testing)")
            server_url = f"https://{server_url}"
            self.shell.poutput(f"Using URL: {server_url}")

        # Ask about SSL verification
        verify_input = input("Enable SSL certificate verification? [Y/n]: ").strip().lower()
        verify = verify_input != "n"

        # Test connection (without credentials - just check if server is reachable)
        self.shell.poutput(f"\nTesting connection to {server_url}...")
        try:
            import requests
            import urllib3

            # Suppress SSL warnings when certificate verification is disabled
            if not verify:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            response = requests.get(f"{server_url}/api/v3/version", verify=verify, timeout=5)
            if response.status_code in [200, 401, 403]:
                # 200 = success, 401/403 = needs auth (but server is reachable)
                self.shell.poutput("Server is reachable")
            else:
                self.shell.pwarning(f"Server returned status code: {response.status_code}")
        except Exception as e:
            self.shell.pwarning(f"Could not connect to server: {e}")
            response = input("Add server anyway? [y/N]: ")
            if response.lower() != "y":
                self.shell.poutput("Server not added")
                return

        # Add server to config with empty credentials
        config_data["servers"][server_name] = {
            "url": server_url,
            "username": "",
            "password": "",
            "verify": verify,
        }

        try:
            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            if self.rich_console:
                self.rich_console.print_success(f"\nServer '{server_name}' added successfully!")
                self.rich_console.print_info("\nNext steps:")
                self.rich_console.print_info("  1. Reload configuration: config-reload")
                self.rich_console.print_info(f"  2. Connect to server: connect {server_name}")
                self.rich_console.print_info("  3. Register account: register <email> <password>")
            else:
                self.shell.poutput(f"\nOK: Server '{server_name}' added successfully!")
                self.shell.poutput("\nNext steps:")
                self.shell.poutput("  1. Reload configuration: config-reload")
                self.shell.poutput(f"  2. Connect to server: connect {server_name}")
                self.shell.poutput("  3. Register account: register <email> <password>")
        except Exception as e:
            self.shell.perror(f"Failed to save configuration: {e}")

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
                    self.rich_console.print_success(
                        f"Connected successfully (QUADS version: {version.get('version', 'unknown')})"
                    )
                else:
                    self.shell.poutput(
                        f"OK: Connected successfully (QUADS version: {version.get('version', 'unknown')})"
                    )
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
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            if self.rich_console:
                self.rich_console.print_success(f"Server '{name}' added successfully")
                self.rich_console.print_info("Reload configuration with: config-reload")
            else:
                self.shell.poutput(f"OK: Server '{name}' added successfully")
                self.shell.poutput("Reload configuration with: config-reload")

        except Exception as e:
            self.shell.perror(f"Failed to add server: {e}")

    def cmd_edit_server(self, args):
        """Edit an existing server.
        Usage: edit-server <name> [url URL] [username USER] [password PASS] [verify true|false]
        """
        parts = args.split()
        if len(parts) < 1:
            self.shell.perror(
                "Usage: edit-server <name> [url URL] [username USER] [password PASS] [verify true|false]"
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
                if parts[i] == "url" and i + 1 < len(parts):
                    updates["url"] = parts[i + 1]
                    i += 2
                elif parts[i] == "username" and i + 1 < len(parts):
                    updates["username"] = parts[i + 1]
                    i += 2
                elif parts[i] == "password" and i + 1 < len(parts):
                    updates["password"] = parts[i + 1]
                    i += 2
                elif parts[i] == "verify" and i + 1 < len(parts):
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
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            self.shell.poutput(f"OK: Server '{name}' updated successfully")
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
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            self.shell.poutput(f"OK: Server '{name}' removed successfully")
            self.shell.poutput("Reload configuration with: config-reload")

        except Exception as e:
            self.shell.perror(f"Failed to remove server: {e}")

    def cmd_config_reload(self, args):
        """Reload configuration from file"""
        try:
            from quads_client.config import QuadsClientConfig

            self.shell.config = QuadsClientConfig()

            # Update config for all sessions
            if self.shell.session_manager:
                self.shell.session_manager.config = self.shell.config
                for session in self.shell.session_manager.sessions.values():
                    session.connection.config = self.shell.config

            self.shell.poutput("OK: Configuration reloaded successfully")
        except Exception as e:
            self.shell.perror(f"Failed to reload configuration: {e}")
