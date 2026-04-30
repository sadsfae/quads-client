class ConnectionCommands:
    def __init__(self, shell):
        self.shell = shell

    def cmd_connect(self, args):
        """Connect to a QUADS server. Usage: connect [server_name]"""
        if not self.shell.connection:
            self.shell.perror("Configuration not loaded")
            return

        if not args.strip():
            default = self.shell.config.get_default_server() if self.shell.config else None
            if default:
                server_name = default
                self.shell.poutput(f"Connecting to default server: {default}")
            else:
                servers = self.shell.connection.get_available_servers()
                self.shell.poutput("Available servers:")
                for server in servers:
                    self.shell.poutput(f"  {server}")
                self.shell.poutput("\nUsage: connect <server_name>")
                return
        else:
            server_name = args.strip()
        try:
            from quads_client.connection import ConnectionError

            self.shell.connection.connect(server_name)

            username = self.shell.connection.username

            self.shell._update_prompt()
            self.shell.poutput(f"Connected to {server_name} as {username}")
        except ConnectionError as e:
            self.shell.perror(str(e))

    def cmd_disconnect(self, args):
        """Disconnect from current QUADS server"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.pwarning("Not connected to any server")
            return

        server = self.shell.connection.current_server
        self.shell.connection.disconnect()
        self.shell._update_prompt()
        self.shell.poutput(f"Disconnected from {server}")

    def cmd_status(self, args):
        """Show current connection status"""
        if not self.shell.connection:
            self.shell.perror("Configuration not loaded")
            return

        if self.shell.connection.is_connected:
            server = self.shell.connection.current_server
            url = self.shell.config.get_server_url(server)
            username = self.shell.connection.username
            self.shell.poutput(f"Connected to: {server}")
            self.shell.poutput(f"URL: {url}")
            self.shell.poutput(f"User: {username}")
        else:
            self.shell.poutput("Not connected")
            servers = self.shell.connection.get_available_servers()
            self.shell.poutput(f"\nAvailable servers: {', '.join(servers)}")
