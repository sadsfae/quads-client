from tabulate import tabulate

from quads_client.arg_parser import parse_schedule_ssm_args
from quads_client.error_handler import auto_refresh_on_auth_error, handle_api_error, require_auth, require_connection


class UserCommands:
    def __init__(self, shell):
        self.shell = shell

    def _require_connection(self):
        """Check if connected to a server"""
        return require_connection(self.shell)

    def _require_auth(self):
        """Check if user is authenticated"""
        return require_auth(self.shell)

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
            # Set credentials on API instance for registration
            self.shell.connection.api.username = email
            self.shell.connection.api.password = password
            result = self.shell.connection.api.register()
            self.shell.poutput(f"OK: User registered successfully: {email}")
            if isinstance(result, dict) and result.get("message"):
                self.shell.poutput(f"  {result['message']}")

            # Save credentials to config file and auto-reconnect
            if self.shell.connection.current_server:
                try:
                    server_name = self.shell.connection.current_server
                    self.shell.config.update_server_credentials(server_name, email, password)
                    self.shell.poutput("OK: Credentials saved to configuration")

                    # Automatically reconnect with new credentials
                    try:
                        self.shell.poutput("OK: Logging in with new credentials...")
                        self.shell.connection.disconnect()
                        self.shell.connection.connect(server_name)
                        self.shell._update_prompt()
                        self.shell._update_visible_commands()
                        self.shell.poutput(f"OK: Logged in successfully as {email}")
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
                self.shell.poutput("OK: Logged in successfully")
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
                self.shell.poutput("OK: Logged in successfully")
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

            self.shell.poutput("OK: Assignment created successfully")
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
        """List user's assignments. Usage: assignment-list (deprecated, use my-assignments)"""
        self.cmd_my_assignments(args)

    def cmd_my_assignments(self, args):
        """List your active self-scheduled assignments. Usage: my-assignments"""
        if not self._require_auth():
            return

        try:
            username = self.shell.connection.username.split("@")[0]
            # Filter for active assignments only
            assignments = self.shell.connection.api.filter_assignments({"owner": username, "active": True})

            if not assignments:
                self.shell.poutput(f"No active assignments found for {username}")
                return

            self.shell.poutput(f"\nActive assignments for {username}:")
            self.shell.poutput("=" * 80)

            table_data = []
            for assignment in assignments:
                assignment_id = assignment.get("id", "N/A")
                cloud_name = assignment.get("cloud", {}).get("name", "N/A")
                description = assignment.get("description", "")
                if len(description) > 40:
                    description = description[:37] + "..."
                validated = "OK:" if assignment.get("validated") else "○"

                table_data.append([assignment_id, cloud_name, description, validated])

            headers = ["ID", "Cloud", "Description", "Validated"]
            self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))
        except Exception as e:
            handle_api_error(self.shell, e, "Listing assignments")

    def cmd_assignment_terminate(self, args):
        """Terminate an assignment. Usage: assignment-terminate <assignment_id> (deprecated, use release)"""
        self.cmd_release(args)

    def cmd_release(self, args):
        """
        Terminate assignment or release host. Usage: release <assignment_id> [hostname]

        Examples:
          release 42                    # Terminate entire assignment
          release 42 host03.example.com # Release specific host from assignment
        """
        if not self._require_auth():
            return

        parts = args.strip().split()
        if not parts:
            self.shell.perror("Usage: release <assignment_id> [hostname]")
            return

        assignment_id = parts[0]
        hostname = parts[1] if len(parts) > 1 else None

        try:
            # Get assignment details first
            assignments = self.shell.connection.api.filter_assignments({"id": int(assignment_id)})
            if not assignments:
                self.shell.perror(f"Assignment {assignment_id} not found")
                return

            assignment = assignments[0]

            # SSM users can only terminate their own assignments
            if not self.shell.connection.is_admin:
                owner = self.shell.connection.username.split("@")[0]

                # Handle both dict and object responses for owner
                if isinstance(assignment, dict):
                    assignment_owner = assignment.get("owner", "")
                else:
                    assignment_owner = getattr(assignment, "owner", "")

                if assignment_owner != owner:
                    self.shell.perror(f"Permission denied: You can only terminate your own assignments")
                    return

            # Handle both dict and object responses for cloud
            if isinstance(assignment, dict):
                cloud_name = assignment.get("cloud", {}).get("name", "N/A")
            else:
                cloud = getattr(assignment, "cloud", None)
                cloud_name = getattr(cloud, "name", "N/A") if cloud else "N/A"

            if hostname:
                # Release specific host
                response = input(f"Release {hostname} from assignment {assignment_id} (cloud: {cloud_name})? [y/N]: ")
                if response.lower() != "y":
                    self.shell.poutput("Host not released")
                    return

                schedules = self.shell.connection.api.get_schedules({"assignment_id": int(assignment_id), "host": hostname})
                if not schedules:
                    self.shell.perror(f"No schedule found for {hostname} in assignment {assignment_id}")
                    return

                self.shell.connection.api.remove_schedule(schedules[0]["id"])
                self.shell.poutput(f"OK: Released {hostname} from assignment #{assignment_id}")
            else:
                # Terminate entire assignment
                response = input(f"Terminate assignment {assignment_id} (cloud: {cloud_name})? [y/N]: ")
                if response.lower() != "y":
                    self.shell.poutput("Assignment not terminated")
                    return

                result = self.shell.connection.api.terminate_assignment(int(assignment_id))

                # Check if termination was successful
                if isinstance(result, dict):
                    if result.get("status") == "error" or result.get("error"):
                        self.shell.perror(
                            f"Failed to terminate: {result.get('message', result.get('error', 'Unknown error'))}"
                        )
                        return

                self.shell.poutput(f"OK: Terminated assignment #{assignment_id}")
                self.shell.poutput("  Note: It may take a few moments for the termination to complete")

        except Exception as e:
            handle_api_error(self.shell, e, "Release")

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
        """
        SSM Mode: Schedule hosts for self-service

        Syntax:
          schedule <NUMBER>                           description <desc> [options]
          schedule <hostname[,hostname,...]>          description <desc> [options]
          schedule host-list <file-path>              description <desc> [options]

        Options: nowipe vlan <id> qinq <0|1> model <name> ram <GB>

        Examples:
          schedule 3 description "Dev testing"                        # Count: QUADS picks 3 hosts
          schedule 5 description "Perf lab" model r640 ram 128        # Count with filters
          schedule host01.example.com,host02.example.com description "CI pipeline"
          schedule host-list ~/hosts.txt description "Batch test" vlan 1150 nowipe

        Note: SSM mode does NOT require tickets - the server automatically creates the assignment.
        """
        if not self._require_auth():
            return

        try:
            # Parse arguments
            parsed = parse_schedule_ssm_args(args)

            # Get host list (if count mode)
            host_list = parsed["host_list"]
            if host_list is None:
                # Count mode: query available hosts
                filters = {"can_self_schedule": True}
                if parsed["model"]:
                    filters["model"] = parsed["model"]
                if parsed["ram"]:
                    filters["memory__gte"] = parsed["ram"] * 1024

                available = auto_refresh_on_auth_error(
                    self.shell, self.shell.connection.api.filter_available, filters
                )

                if len(available) < parsed["count"]:
                    self.shell.perror(f"Not enough hosts available: found {len(available)}, requested {parsed['count']}")
                    self.shell.perror("Hint: Try removing filters or requesting fewer hosts")
                    return

                host_list = [h.get("name") for h in available[: parsed["count"]] if isinstance(h, dict)]

            # Create self-assignment (server auto-assigns cloud, handles ticketing)
            owner = self.shell.connection.username.split("@")[0]
            assignment_data = {
                "description": parsed["description"],
                "owner": owner,
                "wipe": parsed["wipe"],  # Default: True (wipe enabled)
            }
            # Optional fields - do NOT include cloud (let server auto-select)
            if parsed["qinq"]:
                assignment_data["qinq"] = parsed["qinq"]
            if parsed["vlan"]:
                assignment_data["vlan"] = parsed["vlan"]

            # Step 1: Create self-assignment (SSM endpoint auto-assigns cloud)
            assignment = auto_refresh_on_auth_error(
                self.shell, self.shell.connection.api.create_self_assignment, assignment_data
            )

            # Extract cloud name from response
            cloud = assignment.get("cloud", {})
            cloud_name = cloud.get("name") if isinstance(cloud, dict) else cloud
            assignment_id = assignment.get("id", "unknown")

            # Step 2: Create schedules for each host separately (per QUADS API spec)
            for hostname in host_list:
                schedule_data = {
                    "cloud": cloud_name,
                    "hostname": hostname,  # API expects "hostname" not "host"
                    # NO start/end - server controls duration via ssm_default_lifetime
                }
                auto_refresh_on_auth_error(
                    self.shell, self.shell.connection.api.create_schedule, schedule_data
                )

            self.shell.poutput(f"OK: Reserved {len(host_list)} host(s) - activated immediately")
            self.shell.poutput(f"  Cloud: {cloud_name}")
            self.shell.poutput(f"  Assignment: #{assignment_id}")
            self.shell.poutput(f"  Duration: Automatic (5 days or Sunday 21:00 UTC)")

        except ValueError as e:
            self.shell.perror(f"Invalid arguments: {e}")
            self.shell.perror("\nValid syntax:")
            self.shell.perror("  schedule <NUMBER> description \"...\"                    # Count mode")
            self.shell.perror("  schedule <hostname,hostname> description \"...\"         # Specific hosts")
            self.shell.perror("  schedule host-list <file> description \"...\"            # Host list file")
            self.shell.perror("\nExamples:")
            self.shell.perror("  schedule 3 description \"Dev testing\"")
            self.shell.perror("  schedule host01.example.com,host02.example.com description \"CI\"")
            self.shell.perror("  schedule host-list ~/hosts.txt description \"Batch\"")
        except ConnectionError:
            self.shell.perror("Connection failed: unable to reach QUADS server")
            self.shell.perror("Hint: Check 'status' or run 'connect <server>'")
        except Exception as e:
            handle_api_error(self.shell, e, "Scheduling")

    def cmd_my_hosts(self, args):
        """Show your currently scheduled hosts. Usage: my-hosts"""
        if not self._require_auth():
            return

        try:
            username = self.shell.connection.username.split("@")[0]
            # Get assignments by owner
            assignments = self.shell.connection.api.filter_assignments({"owner": username})
            if not assignments:
                self.shell.poutput(f"No hosts scheduled by {username}")
                return

            self.shell.poutput(f"\nHosts scheduled by {username}:")
            self.shell.poutput("=" * 80)

            for assignment in assignments:
                assignment_id = assignment.get("id")
                cloud_name = assignment.get("cloud", {}).get("name", "N/A")
                description = assignment.get("description", "")

                self.shell.poutput(f"\nAssignment #{assignment_id} - {description} ({cloud_name})")

                # Get schedules for this assignment
                schedules = self.shell.connection.api.get_schedules({"assignment_id": assignment_id})
                if schedules:
                    table_data = []
                    for schedule in schedules:
                        host_name = schedule.get("host", {}).get("name", "Unknown")
                        status = "Active"
                        end = schedule.get("end", "N/A")
                        table_data.append([host_name, status, f"Expires: {end}"])

                    headers = ["Host", "Status", "Schedule"]
                    self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))
                else:
                    self.shell.poutput("  No hosts assigned")

        except Exception as e:
            handle_api_error(self.shell, e, "Listing hosts")
