class CloudCommands:
    def __init__(self, shell):
        self.shell = shell

    def cmd_cloud_list(self, args):
        """List all clouds"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return

        try:
            clouds = self.shell.connection.api.get_clouds()
            if not clouds:
                self.shell.poutput("No clouds found")
                return

            self.shell.poutput("Available clouds:")
            for cloud in clouds:
                self.shell.poutput(f"  {cloud['name']}")
        except Exception as e:
            self.shell.perror(f"Failed to list clouds: {e}")

    def cmd_cloud_create(self, args):
        """Create a new cloud (admin only). Usage: cloud-create <name>"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return

        if not args.strip():
            self.shell.perror("Usage: cloud-create <name>")
            return

        cloud_name = args.strip()
        try:
            result = self.shell.connection.api.create_cloud({"cloud": cloud_name})
            self.shell.poutput(f"Cloud '{cloud_name}' created successfully")
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                self.shell.perror("Error: This command requires admin role")
            else:
                self.shell.perror(f"Failed to create cloud: {e}")

    def cmd_cloud_delete(self, args):
        """Delete a cloud (admin only). Usage: cloud-delete <name>"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return

        if not args.strip():
            self.shell.perror("Usage: cloud-delete <name>")
            return

        cloud_name = args.strip()
        try:
            self.shell.connection.api.remove_cloud(cloud_name)
            self.shell.poutput(f"Cloud '{cloud_name}' deleted successfully")
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                self.shell.perror("Error: This command requires admin role")
            else:
                self.shell.perror(f"Failed to delete cloud: {e}")
