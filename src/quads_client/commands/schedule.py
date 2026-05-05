from datetime import datetime, timedelta
from tabulate import tabulate

from quads_client.arg_parser import parse_extend_args, parse_schedule_admin_args
from quads_client.error_handler import handle_api_error, require_admin, require_connection


class ScheduleCommands:
    def __init__(self, shell):
        self.shell = shell
        self.rich_console = shell.rich_console if hasattr(shell, "rich_console") else None

    def _require_connection(self):
        return require_connection(self.shell)

    def cmd_ls_schedule(self, args):
        """List schedules. Usage: ls-schedule [--host hostname] [--cloud cloudname]"""
        if not self._require_connection():
            return

        parts = args.split()
        filters = {}

        i = 0
        while i < len(parts):
            if parts[i] == "--host" and i + 1 < len(parts):
                filters["host"] = parts[i + 1]
                i += 2
            elif parts[i] == "--cloud" and i + 1 < len(parts):
                filters["cloud"] = parts[i + 1]
                i += 2
            else:
                i += 1

        try:
            schedules = self.shell.connection.api.get_schedules(filters)
            if not schedules:
                self.shell.poutput("No schedules found")
                return

            table_data = []
            for sched in schedules:
                host_name = sched.get("host", {}).get("name", "")
                assignment = sched.get("assignment", {})
                cloud_name = assignment.get("cloud", {}).get("name", "")
                owner = assignment.get("owner", "")

                table_data.append(
                    [
                        sched.get("id", ""),
                        host_name,
                        cloud_name,
                        owner,
                        sched.get("start", ""),
                        sched.get("end", ""),
                    ]
                )

            headers = ["ID", "Host", "Cloud", "Owner", "Start", "End"]
            if self.rich_console:
                self.rich_console.print_table(headers, table_data, title="Schedules")
            else:
                self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))

        except Exception as e:
            self.shell.perror(f"Failed to list schedules: {e}")

    def cmd_schedule_admin(self, args):
        """
        Admin Mode: Schedule hosts with explicit dates
        Usage: schedule <cloud> <hosts|host-list path> <start> <end>

        Examples:
          schedule cloud02 host01,host02,host03 2026-05-11 2026-06-11
          schedule cloud17 host-list ~/hosts.txt now 2026-07-01
        """
        if not require_admin(self.shell):
            return

        try:
            # Parse arguments
            parsed = parse_schedule_admin_args(args)

            # Verify cloud exists
            clouds = self.shell.connection.api.filter_clouds({"name": parsed["cloud"]})
            if not clouds:
                self.shell.perror(f"Cloud '{parsed['cloud']}' not found")
                return

            # Create schedules for each host
            created_count = 0
            for hostname in parsed["host_list"]:
                schedule_data = {
                    "cloud": parsed["cloud"],
                    "host": hostname,
                    "start": None if parsed["start"] == "now" else parsed["start"],
                    "end": parsed["end"],
                }
                self.shell.connection.api.create_schedule(schedule_data)
                created_count += 1

            if self.rich_console:
                self.rich_console.print_success(f"Created {created_count} schedule(s)")
            else:
                self.shell.poutput(f"✓ Created {created_count} schedule(s)")

        except ValueError as e:
            self.shell.perror(f"Invalid arguments: {e}")
            self.shell.perror("Usage: schedule <cloud> <hosts|host-list path> <start> <end>")
        except ConnectionError:
            self.shell.perror("Connection failed: unable to reach QUADS server")
            self.shell.perror("Hint: Check 'status' or run 'connect <server>'")
        except Exception as e:
            handle_api_error(self.shell, e, "Scheduling")

    def cmd_add_schedule(self, args):
        """Add a schedule. (deprecated, use schedule command)
        Usage: add-schedule --host <hostname> --cloud <cloudname> --start <YYYY-MM-DD> --end <YYYY-MM-DD>
        """
        if not self._require_connection():
            return

        parts = args.split()
        data = {}

        i = 0
        while i < len(parts):
            if parts[i] == "--host" and i + 1 < len(parts):
                data["host"] = parts[i + 1]
                i += 2
            elif parts[i] == "--cloud" and i + 1 < len(parts):
                data["cloud"] = parts[i + 1]
                i += 2
            elif parts[i] == "--start" and i + 1 < len(parts):
                data["start"] = parts[i + 1]
                i += 2
            elif parts[i] == "--end" and i + 1 < len(parts):
                data["end"] = parts[i + 1]
                i += 2
            else:
                i += 1

        if not all(k in data for k in ["host", "cloud", "start", "end"]):
            self.shell.perror(
                "Usage: add-schedule --host <hostname> --cloud <cloudname> --start <YYYY-MM-DD> --end <YYYY-MM-DD>"
            )
            return

        try:
            result = self.shell.connection.api.create_schedule(data)
            schedule_id = result.get("id", "unknown")
            self.shell.poutput(f"Schedule created successfully (ID: {schedule_id})")
        except Exception as e:
            handle_api_error(self.shell, e, "Creating schedule")

    def cmd_mod_schedule(self, args):
        """Modify a schedule. Usage: mod-schedule --id <schedule_id> [--start <YYYY-MM-DD>] [--end <YYYY-MM-DD>]"""
        if not self._require_connection():
            return

        parts = args.split()
        schedule_id = None
        updates = {}

        i = 0
        while i < len(parts):
            if parts[i] == "--id" and i + 1 < len(parts):
                schedule_id = parts[i + 1]
                i += 2
            elif parts[i] == "--start" and i + 1 < len(parts):
                updates["start"] = parts[i + 1]
                i += 2
            elif parts[i] == "--end" and i + 1 < len(parts):
                updates["end"] = parts[i + 1]
                i += 2
            else:
                i += 1

        if not schedule_id:
            self.shell.perror("Usage: mod-schedule --id <schedule_id> [--start <YYYY-MM-DD>] [--end <YYYY-MM-DD>]")
            return

        if not updates:
            self.shell.perror("No updates specified")
            return

        try:
            self.shell.connection.api.update_schedule(schedule_id, updates)
            self.shell.poutput(f"Schedule {schedule_id} updated successfully")
        except Exception as e:
            self.shell.perror(f"Failed to update schedule: {e}")

    def cmd_rm_schedule(self, args):
        """Remove a schedule. Usage: rm-schedule <schedule_id>"""
        if not self._require_connection():
            return

        if not args.strip():
            self.shell.perror("Usage: rm-schedule <schedule_id>")
            return

        schedule_id = args.strip()
        try:
            self.shell.connection.api.remove_schedule(schedule_id)
            self.shell.poutput(f"Schedule {schedule_id} removed successfully")
        except Exception as e:
            self.shell.perror(f"Failed to remove schedule: {e}")

    def cmd_extend(self, args):
        """
        Extend cloud or host schedules (admin only - HIDDEN from SSM users)
        Usage: extend <cloud|hostname> weeks <N>
               extend <cloud|hostname> date <YYYY-MM-DD HH:MM>

        Examples:
          extend cloud02 weeks 2
          extend cloud02 date "2026-05-17 22:00"
          extend host01.example.com weeks 1
        """
        # Failsafe check (command should be hidden from SSM users via _update_visible_commands)
        if not require_admin(self.shell):
            return

        try:
            # Parse arguments
            parsed = parse_extend_args(args)

            # Determine if target is cloud or hostname
            if parsed["target"].startswith("cloud"):
                # Cloud mode: extend all current schedules in cloud
                schedules = self.shell.connection.api.get_current_schedules({"cloud": parsed["target"]})

                if not schedules:
                    if self.rich_console:
                        self.rich_console.print_error(f"No current schedules found for {parsed['target']}")
                    else:
                        self.shell.perror(f"No current schedules found for {parsed['target']}")
                    return

                if self.rich_console:
                    self.rich_console.print_info(f"Extending {len(schedules)} schedule(s) in {parsed['target']}...")
                else:
                    self.shell.poutput(f"Extending {len(schedules)} schedule(s) in {parsed['target']}...")

                for schedule in schedules:
                    if parsed["weeks"]:
                        current_end = datetime.fromisoformat(schedule["end"].replace("Z", "+00:00"))
                        end_date = current_end + timedelta(weeks=parsed["weeks"])
                    else:
                        end_date = datetime.strptime(parsed["date"], "%Y-%m-%d %H:%M")

                    self.shell.connection.api.update_schedule(schedule["id"], {"end": end_date.strftime("%Y-%m-%d %H:%M")})
                    if self.rich_console:
                        self.rich_console.print_success(schedule['host']['name'])
                    else:
                        self.shell.poutput(f"  ✓ {schedule['host']['name']}")

                if parsed["weeks"]:
                    if self.rich_console:
                        self.rich_console.print_success(f"Extended {parsed['target']} by {parsed['weeks']} week(s)")
                    else:
                        self.shell.poutput(f"✓ Extended {parsed['target']} by {parsed['weeks']} week(s)")
                else:
                    if self.rich_console:
                        self.rich_console.print_success(f"Extended {parsed['target']} to {parsed['date']}")
                    else:
                        self.shell.poutput(f"✓ Extended {parsed['target']} to {parsed['date']}")

            else:
                # Hostname mode: extend specific host's current schedule
                schedules = self.shell.connection.api.get_current_schedules({"host": parsed["target"]})

                if not schedules:
                    self.shell.perror(f"No current schedule found for {parsed['target']}")
                    return

                schedule = schedules[0]

                if parsed["weeks"]:
                    current_end = datetime.fromisoformat(schedule["end"].replace("Z", "+00:00"))
                    end_date = current_end + timedelta(weeks=parsed["weeks"])
                else:
                    end_date = datetime.strptime(parsed["date"], "%Y-%m-%d %H:%M")

                self.shell.connection.api.update_schedule(schedule["id"], {"end": end_date.strftime("%Y-%m-%d %H:%M")})

                if parsed["weeks"]:
                    self.shell.poutput(f"✓ Extended {parsed['target']} by {parsed['weeks']} week(s)")
                else:
                    self.shell.poutput(f"✓ Extended {parsed['target']} to {parsed['date']}")

        except ValueError as e:
            self.shell.perror(f"Invalid arguments: {e}")
            self.shell.perror("Usage: extend <cloud|hostname> weeks <N> OR extend <cloud|hostname> date <YYYY-MM-DD HH:MM>")
        except Exception as e:
            handle_api_error(self.shell, e, "Extending schedule")

    def cmd_shrink(self, args):
        """Shrink a schedule. Usage: shrink --host <hostname> --weeks <number>"""
        if not self._require_connection():
            return

        parts = args.split()
        hostname = None
        weeks = None

        i = 0
        while i < len(parts):
            if parts[i] == "--host" and i + 1 < len(parts):
                hostname = parts[i + 1]
                i += 2
            elif parts[i] == "--weeks" and i + 1 < len(parts):
                try:
                    weeks = int(parts[i + 1])
                except ValueError:
                    self.shell.perror("Invalid weeks value")
                    return
                i += 2
            else:
                i += 1

        if not hostname or weeks is None:
            self.shell.perror("Usage: shrink --host <hostname> --weeks <number>")
            return

        try:
            schedules = self.shell.connection.api.get_current_schedules({"host": hostname})
            if not schedules:
                self.shell.perror(f"No current schedule found for {hostname}")
                return

            current = schedules[0]
            current_end = datetime.strptime(current["end"], "%Y-%m-%d %H:%M")
            new_end = current_end - timedelta(weeks=weeks)
            new_end_str = new_end.strftime("%Y-%m-%d %H:%M")

            self.shell.connection.api.update_schedule(current["id"], {"end": new_end_str})
            self.shell.poutput(f"Shrunk schedule for {hostname} by {weeks} weeks to {new_end_str}")

        except Exception as e:
            self.shell.perror(f"Failed to shrink schedule: {e}")
