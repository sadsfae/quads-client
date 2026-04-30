from datetime import datetime, timedelta
from tabulate import tabulate


class ScheduleCommands:
    def __init__(self, shell):
        self.shell = shell

    def _require_connection(self):
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return False
        return True

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
            self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))

        except Exception as e:
            self.shell.perror(f"Failed to list schedules: {e}")

    def cmd_add_schedule(self, args):
        """Add a schedule. Usage: add-schedule --host <hostname> --cloud <cloudname> --start <YYYY-MM-DD> --end <YYYY-MM-DD>"""
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
            self.shell.perror(f"Failed to create schedule: {e}")

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
        """Extend a schedule. Usage: extend --host <hostname> --weeks <number>"""
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
            self.shell.perror("Usage: extend --host <hostname> --weeks <number>")
            return

        try:
            schedules = self.shell.connection.api.get_current_schedules({"host": hostname})
            if not schedules:
                self.shell.perror(f"No current schedule found for {hostname}")
                return

            current = schedules[0]
            current_end = datetime.strptime(current["end"], "%Y-%m-%d %H:%M")
            new_end = current_end + timedelta(weeks=weeks)
            new_end_str = new_end.strftime("%Y-%m-%d %H:%M")

            self.shell.connection.api.update_schedule(current["id"], {"end": new_end_str})
            self.shell.poutput(f"Extended schedule for {hostname} by {weeks} weeks to {new_end_str}")

        except Exception as e:
            self.shell.perror(f"Failed to extend schedule: {e}")

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
