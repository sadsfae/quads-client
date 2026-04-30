class SSMCommands:
    def __init__(self, shell):
        self.shell = shell

    def cmd_ssm_available(self, args):
        """Show available hosts for self-scheduling"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return

        try:
            # Get hosts in cloud01 that can be self-scheduled
            hosts = self.shell.connection.api.filter_hosts({"cloud": "cloud01", "retired": False, "broken": False})
            if not hosts:
                self.shell.poutput("No available hosts for self-scheduling")
                return

            # Filter by can_self_schedule flag
            ssm_hosts = [h for h in hosts if h.get("can_self_schedule")]
            if not ssm_hosts:
                self.shell.poutput("No available hosts for self-scheduling")
                return

            self.shell.poutput("Available hosts:")
            for host in ssm_hosts:
                self.shell.poutput(f"  {host['name']}")
        except Exception as e:
            self.shell.perror(f"Failed to get available hosts: {e}")

    def cmd_ssm_schedule(self, args):
        """Schedule a host for yourself. Usage: ssm-schedule <hostname> <cloud>"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return

        parts = args.strip().split()
        if len(parts) < 2:
            self.shell.perror("Usage: ssm-schedule <hostname> <cloud>")
            self.shell.perror("Example: ssm-schedule host01.example.com cloud02")
            return

        hostname, cloud = parts[0], parts[1]
        try:
            # Server handles SSM logic (auto-calculates dates if SSM cloud)
            self.shell.connection.api.create_schedule({"hostname": hostname, "cloud": cloud})
            self.shell.poutput(f"Host '{hostname}' scheduled on {cloud}")
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                self.shell.perror("Error: You don't have permission to schedule hosts")
            else:
                self.shell.perror(f"Failed to schedule host: {e}")

    def cmd_ssm_my_hosts(self, args):
        """Show hosts scheduled by you"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return

        try:
            username = self.shell.connection.username
            # Get assignments by owner
            assignments = self.shell.connection.api.filter_assignments({"owner": username})
            if not assignments:
                self.shell.poutput(f"No hosts scheduled by {username}")
                return

            self.shell.poutput(f"Hosts scheduled by {username}:")
            for assignment in assignments:
                # Get schedules for this assignment
                schedules = self.shell.connection.api.get_schedules({"assignment_id": assignment["id"]})
                for schedule in schedules:
                    host_name = schedule.get("host", {}).get("name", "Unknown")
                    start = schedule.get("start", "N/A")
                    end = schedule.get("end", "N/A")
                    self.shell.poutput(f"  {host_name} ({start} - {end})")
        except Exception as e:
            self.shell.perror(f"Failed to get schedules: {e}")
