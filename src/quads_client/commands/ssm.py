from tabulate import tabulate


class SSMCommands:
    def __init__(self, shell):
        self.shell = shell

    def _require_connection(self):
        """Check if connected to a server"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return False
        return True

    def cmd_ssm_register(self, args):
        """Register a new user. Usage: ssm-register <email> <password>"""
        if not self._require_connection():
            return

        parts = args.strip().split()
        if len(parts) < 2:
            self.shell.perror("Usage: ssm-register <email> <password>")
            return

        email = parts[0]
        password = parts[1]

        try:
            result = self.shell.connection.api.register({"email": email, "password": password})
            self.shell.poutput(f"✓ User registered successfully: {email}")
            if result.get("message"):
                self.shell.poutput(f"  {result['message']}")
        except Exception as e:
            self.shell.perror(f"Failed to register user: {e}")

    def cmd_ssm_login(self, args):
        """Explicit login. Usage: ssm-login"""
        if not self._require_connection():
            return

        try:
            result = self.shell.connection.api.login()
            if result.get("auth_token"):
                self.shell.poutput("✓ Logged in successfully")
                self.shell.poutput(f"  Token: {result['auth_token'][:20]}...")
            else:
                self.shell.poutput("✓ Logged in successfully")
        except Exception as e:
            self.shell.perror(f"Failed to login: {e}")

    def cmd_ssm_create(self, args):
        """Create a self-assignment. Usage: ssm-create --description <desc> [--wipe true|false] [--qinq <vlan>]"""
        if not self._require_connection():
            return

        parts = args.strip().split()
        if not parts or "--description" not in args:
            self.shell.perror("Usage: ssm-create --description <desc> [--wipe true|false] [--qinq <vlan>]")
            return

        data = {}
        i = 0
        while i < len(parts):
            if parts[i] == "--description" and i + 1 < len(parts):
                # Handle multi-word descriptions
                desc_parts = []
                i += 1
                while i < len(parts) and not parts[i].startswith("--"):
                    desc_parts.append(parts[i])
                    i += 1
                data["description"] = " ".join(desc_parts)
            elif parts[i] == "--wipe" and i + 1 < len(parts):
                data["wipe"] = parts[i + 1].lower() == "true"
                i += 2
            elif parts[i] == "--qinq" and i + 1 < len(parts):
                data["qinq"] = int(parts[i + 1])
                i += 2
            else:
                i += 1

        try:
            username = self.shell.connection.username
            data["owner"] = username

            assignment = self.shell.connection.api.create_self_assignment(data)
            assignment_id = assignment.get("id", "unknown")
            cloud_name = assignment.get("cloud", {}).get("name", "unknown")

            self.shell.poutput("✓ Self-assignment created successfully")
            self.shell.poutput(f"  Assignment ID: {assignment_id}")
            self.shell.poutput(f"  Cloud: {cloud_name}")
            self.shell.poutput(f"  Owner: {username}")
            if assignment.get("qinq"):
                self.shell.poutput(f"  VLAN (QinQ): {assignment['qinq']}")
        except Exception as e:
            self.shell.perror(f"Failed to create self-assignment: {e}")

    def cmd_ssm_status(self, args):
        """Show assignment details. Usage: ssm-status <assignment_id>"""
        if not self._require_connection():
            return

        assignment_id = args.strip()
        if not assignment_id:
            self.shell.perror("Usage: ssm-status <assignment_id>")
            return

        try:
            assignments = self.shell.connection.api.filter_assignments({"id": int(assignment_id)})
            if not assignments:
                self.shell.perror(f"Assignment {assignment_id} not found")
                return

            assignment = assignments[0]
            cloud = assignment.get("cloud", {})

            self.shell.poutput(f"\nAssignment: {assignment.get('id')}")
            self.shell.poutput("=" * 80)
            self.shell.poutput(f"Cloud         {cloud.get('name', 'N/A')}")
            self.shell.poutput(f"Owner         {assignment.get('owner', 'N/A')}")
            self.shell.poutput(f"Description   {assignment.get('description', 'N/A')}")
            self.shell.poutput(f"Ticket        {assignment.get('ticket', 'N/A')}")
            self.shell.poutput(f"VLAN (QinQ)   {assignment.get('qinq', 'N/A')}")
            self.shell.poutput(f"Wipe          {'Yes' if assignment.get('wipe') else 'No'}")
            self.shell.poutput(f"Validated     {'Yes' if assignment.get('validated') else 'No'}")
            self.shell.poutput(f"Active        {'Yes' if assignment.get('active') else 'No'}")

            # Get schedules for this assignment
            schedules = self.shell.connection.api.get_schedules({"assignment_id": int(assignment_id)})
            if schedules:
                self.shell.poutput(f"\nAssigned Hosts ({len(schedules)}):")
                self.shell.poutput("-" * 80)
                table_data = []
                for schedule in schedules:
                    host = schedule.get("host", {})
                    hostname = host.get("name", "Unknown")
                    model = host.get("model", "N/A")
                    start = schedule.get("start", "N/A")
                    end = schedule.get("end", "N/A")
                    table_data.append([hostname, model, start, end])

                headers = ["Hostname", "Model", "Start", "End"]
                self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))
            else:
                self.shell.poutput("\nNo hosts assigned")
        except Exception as e:
            self.shell.perror(f"Failed to get assignment status: {e}")

    def cmd_ssm_list(self, args):
        """List user's assignments. Usage: ssm-list"""
        if not self._require_connection():
            return

        try:
            username = self.shell.connection.username
            assignments = self.shell.connection.api.filter_assignments({"owner": username})

            if not assignments:
                self.shell.poutput(f"No assignments found for {username}")
                return

            self.shell.poutput(f"\nAssignments for {username}:")
            self.shell.poutput("=" * 80)

            table_data = []
            for assignment in assignments:
                assignment_id = assignment.get("id", "N/A")
                cloud_name = assignment.get("cloud", {}).get("name", "N/A")
                description = assignment.get("description", "")
                if len(description) > 40:
                    description = description[:37] + "..."
                validated = "✓" if assignment.get("validated") else "○"
                active = "✓" if assignment.get("active") else "○"

                table_data.append([assignment_id, cloud_name, description, validated, active])

            headers = ["ID", "Cloud", "Description", "Validated", "Active"]
            self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))
        except Exception as e:
            self.shell.perror(f"Failed to list assignments: {e}")

    def cmd_ssm_terminate(self, args):
        """Terminate an assignment. Usage: ssm-terminate <assignment_id>"""
        if not self._require_connection():
            return

        assignment_id = args.strip()
        if not assignment_id:
            self.shell.perror("Usage: ssm-terminate <assignment_id>")
            return

        try:
            # Get assignment details first
            assignments = self.shell.connection.api.filter_assignments({"id": int(assignment_id)})
            if not assignments:
                self.shell.perror(f"Assignment {assignment_id} not found")
                return

            assignment = assignments[0]
            cloud_name = assignment.get("cloud", {}).get("name", "N/A")

            response = input(f"Terminate assignment {assignment_id} (cloud: {cloud_name})? [y/N]: ")
            if response.lower() != "y":
                self.shell.poutput("Assignment not terminated")
                return

            self.shell.connection.api.terminate_assignment(int(assignment_id))
            self.shell.poutput(f"✓ Assignment {assignment_id} terminated successfully")
        except Exception as e:
            self.shell.perror(f"Failed to terminate assignment: {e}")

    def cmd_ssm_whoami(self, args):
        """Show current user information. Usage: ssm-whoami"""
        if not self._require_connection():
            return

        try:
            username = self.shell.connection.username
            self.shell.poutput(f"\nCurrent user: {username}")

            # Try to get user roles if available
            try:
                # This may not be available in all python-quads-lib versions
                user_info = self.shell.connection.api.get_user_info()
                if user_info:
                    self.shell.poutput(f"Email: {user_info.get('email', 'N/A')}")
                    roles = user_info.get("roles", [])
                    if roles:
                        self.shell.poutput(f"Roles: {', '.join(roles)}")
            except AttributeError:
                # get_user_info() not available
                pass
        except Exception as e:
            self.shell.perror(f"Failed to get user info: {e}")

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
