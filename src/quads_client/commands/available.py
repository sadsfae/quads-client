from tabulate import tabulate


class AvailableCommands:
    def __init__(self, shell):
        self.shell = shell

    def _require_connection(self):
        if not self.shell.connection or not self.shell.connection.is_connected:
            self.shell.perror("Not connected to any server")
            return False
        return True

    def cmd_ls_available(self, args):
        """List available hosts. Usage: ls-available [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--model MODEL]"""
        if not self._require_connection():
            return

        parts = args.split()
        filters = {}

        i = 0
        while i < len(parts):
            if parts[i] == "--start" and i + 1 < len(parts):
                filters["start"] = parts[i + 1]
                i += 2
            elif parts[i] == "--end" and i + 1 < len(parts):
                filters["end"] = parts[i + 1]
                i += 2
            elif parts[i] == "--model" and i + 1 < len(parts):
                filters["model"] = parts[i + 1]
                i += 2
            else:
                i += 1

        try:
            hosts = self.shell.connection.api.filter_available(filters)
            if not hosts:
                self.shell.poutput("No available hosts found")
                return

            table_data = []
            for host in hosts:
                table_data.append(
                    [
                        host.get("name", ""),
                        host.get("model", ""),
                        host.get("host_type", ""),
                        "Yes" if host.get("can_self_schedule", False) else "No",
                    ]
                )

            headers = ["Name", "Model", "Type", "Self-Schedule"]
            self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))

        except Exception as e:
            self.shell.perror(f"Failed to list available hosts: {e}")
