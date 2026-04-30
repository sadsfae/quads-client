from tabulate import tabulate


class UserCommands:
    def __init__(self, shell):
        self.shell = shell

    def _require_connection(self):
        """Check if connected to a server"""
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return False
        return True

    def _require_auth(self):
        """Check if user is authenticated"""
        if not self._require_connection():
            return False
        if not self.shell.connection.is_authenticated:
            self.shell.perror("Not authenticated. Use 'login' command first.")
            return False
        return True

    def cmd_register(self, args):
        """Register a new user. Usage: register <email> <password>"""
        if not self._require_connection():
            return

        parts = args.strip().split()
        if len(parts) < 2:
            self.shell.perror("Usage: register <email> <password>")
            return

        email = parts[0]
        password = parts[1]

        try:
            result = self.shell.connection.api.register({"email": email, "password": password})
            self.shell.poutput(f"✓ User registered successfully: {email}")
            if isinstance(result, dict) and result.get("message"):
                self.shell.poutput(f"  {result['message']}")

            # Save credentials to config file and auto-reconnect
            if self.shell.connection.current_server:
                try:
                    server_name = self.shell.connection.current_server
                    self.shell.config.update_server_credentials(server_name, email, password)
                    self.shell.poutput("✓ Credentials saved to configuration")

                    # Automatically reconnect with new credentials
                    try:
                        self.shell.poutput("✓ Logging in with new credentials...")
                        self.shell.connection.disconnect()
                        self.shell.connection.connect(server_name)
                        self.shell._update_prompt()
                        self.shell._update_visible_commands()
                        self.shell.poutput(f"✓ Logged in successfully as {email}")
                    except Exception as login_error:
                        self.shell.pwarning(f"Warning: Auto-login failed: {login_error}")
                        self.shell.pwarning("Please use 'connect' command to login")
                except Exception as e:
                    self.shell.pwarning(f"Warning: Could not save credentials: {e}")
                    self.shell.pwarning("You will need to manually update your config file")
        except Exception as e:
            self.shell.perror(f"Failed to register user: {e}")

    def cmd_login(self, args):
        """Explicit login. Usage: login"""
        if not self._require_connection():
            return

        try:
            result = self.shell.connection.api.login()
            if isinstance(result, dict) and result.get("auth_token"):
                self.shell.poutput("✓ Logged in successfully")
                # Update connection token
                self.shell.connection._token = result["auth_token"]
                # Try to decode role
                role = self.shell.connection._decode_role_from_token()
                if role:
                    self.shell.connection._user_role = role
                    self.shell.poutput(f"  Role: {role}")
                # Update visible commands based on new authentication state
                self.shell._update_visible_commands()
            else:
                self.shell.poutput("✓ Logged in successfully")
                self.shell._update_visible_commands()
        except Exception as e:
            self.shell.perror(f"Failed to login: {e}")

    def cmd_whoami(self, args):
        """Show current user information. Usage: whoami"""
        if not self._require_connection():
            return

        try:
            username = self.shell.connection.username
            role = self.shell.connection.user_role
            is_auth = self.shell.connection.is_authenticated

            self.shell.poutput(f"\nCurrent user: {username or 'Not authenticated'}")
            if is_auth:
                self.shell.poutput("Authenticated: Yes")
                if role:
                    self.shell.poutput(f"Role: {role}")
            else:
                self.shell.poutput("Authenticated: No")

            # Try to get additional user info
            if is_auth:
                try:
                    user_info = self.shell.connection.api.get_user_info()
                    if user_info:
                        self.shell.poutput(f"Email: {user_info.get('email', 'N/A')}")
                except (AttributeError, Exception):
                    pass
        except Exception as e:
            self.shell.perror(f"Failed to get user info: {e}")

    def cmd_assignment_create(self, args):
        """Create an assignment. Usage: assignment-create --description <desc> [--wipe true|false] [--qinq <vlan>]"""
        if not self._require_auth():
            return

        parts = args.strip().split()
        if not parts or "--description" not in args:
            self.shell.perror("Usage: assignment-create --description <desc> [--wipe true|false] [--qinq <vlan>]")
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

            self.shell.poutput("✓ Assignment created successfully")
            self.shell.poutput(f"  Assignment ID: {assignment_id}")
            self.shell.poutput(f"  Cloud: {cloud_name}")
            self.shell.poutput(f"  Owner: {username}")
            if assignment.get("qinq"):
                self.shell.poutput(f"  VLAN (QinQ): {assignment['qinq']}")
        except Exception as e:
            self.shell.perror(f"Failed to create assignment: {e}")

    def cmd_assignment_status(self, args):
        """Show assignment details. Usage: assignment-status <assignment_id>"""
        if not self._require_auth():
            return

        assignment_id = args.strip()
        if not assignment_id:
            self.shell.perror("Usage: assignment-status <assignment_id>")
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

    def cmd_assignment_list(self, args):
        """List user's assignments. Usage: assignment-list"""
        if not self._require_auth():
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

    def cmd_assignment_terminate(self, args):
        """Terminate an assignment. Usage: assignment-terminate <assignment_id>"""
        if not self._require_auth():
            return

        assignment_id = args.strip()
        if not assignment_id:
            self.shell.perror("Usage: assignment-terminate <assignment_id>")
            return

        try:
            # Get assignment details first
            assignments = self.shell.connection.api.filter_assignments({"id": int(assignment_id)})
            if not assignments:
                self.shell.perror(f"Assignment {assignment_id} not found")
                return

            assignment = assignments[0]
            # Handle both dict and object responses
            if isinstance(assignment, dict):
                cloud_name = assignment.get("cloud", {}).get("name", "N/A")
            else:
                cloud = getattr(assignment, "cloud", None)
                cloud_name = getattr(cloud, "name", "N/A") if cloud else "N/A"

            response = input(f"Terminate assignment {assignment_id} (cloud: {cloud_name})? [y/N]: ")
            if response.lower() != "y":
                self.shell.poutput("Assignment not terminated")
                return

            # Call terminate and check response
            result = self.shell.connection.api.terminate_assignment(int(assignment_id))

            # Check if termination was successful
            if isinstance(result, dict):
                if result.get("status") == "error" or result.get("error"):
                    self.shell.perror(
                        f"Failed to terminate: {result.get('message', result.get('error', 'Unknown error'))}"
                    )
                    return

            self.shell.poutput(f"✓ Assignment {assignment_id} terminated successfully")
            self.shell.poutput("  Note: It may take a few moments for the termination to complete")
        except Exception as e:
            self.shell.perror(f"Failed to terminate assignment: {e}")

    def cmd_available(self, args):
        """Show available hosts. Usage: available"""
        if not self._require_auth():
            return

        try:
            # Get hosts that can be self-scheduled
            hosts = self.shell.connection.api.filter_hosts({"cloud": "cloud01", "retired": False, "broken": False})
            if not hosts:
                self.shell.poutput("No available hosts")
                return

            # Filter by can_self_schedule flag
            available_hosts = [h for h in hosts if h.get("can_self_schedule")]
            if not available_hosts:
                self.shell.poutput("No available hosts")
                return

            self.shell.poutput("Available hosts:")
            for host in available_hosts:
                self.shell.poutput(f"  {host['name']}")
        except Exception as e:
            self.shell.perror(f"Failed to get available hosts: {e}")

    def cmd_schedule(self, args):
        """Schedule a host. Usage: schedule <hostname> <cloud>"""
        if not self._require_auth():
            return

        parts = args.strip().split()
        if len(parts) < 2:
            self.shell.perror("Usage: schedule <hostname> <cloud>")
            self.shell.perror("Example: schedule host01.example.com cloud02")
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

    def cmd_my_hosts(self, args):
        """Show hosts scheduled by you. Usage: my-hosts"""
        if not self._require_auth():
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
