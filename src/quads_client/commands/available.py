from tabulate import tabulate

from quads_client.error_handler import require_connection


class AvailableCommands:
    def __init__(self, shell):
        self.shell = shell

    def _require_connection(self):
        return require_connection(self.shell)

    def cmd_ls_available(self, args):
        """List available hosts.
        Usage: ls-available [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--model MODEL] [--ram GB]
                            [--gpu-vendor VENDOR] [--gpu-product PRODUCT]
                            [--disk-size GB] [--disk-type TYPE] [--disk-count N]
                            [--interfaces N]
        """
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
            elif parts[i] == "--ram" and i + 1 < len(parts):
                filters["memory__gte"] = int(parts[i + 1]) * 1024
                i += 2
            elif parts[i] == "--gpu-vendor" and i + 1 < len(parts):
                filters["processors.vendor"] = parts[i + 1]
                i += 2
            elif parts[i] == "--gpu-product" and i + 1 < len(parts):
                filters["processors.product"] = parts[i + 1]
                i += 2
            elif parts[i] == "--disk-size" and i + 1 < len(parts):
                filters["disks.size_gb__gte"] = int(parts[i + 1])
                i += 2
            elif parts[i] == "--disk-type" and i + 1 < len(parts):
                filters["disks.disk_type"] = parts[i + 1]
                i += 2
            elif parts[i] == "--disk-count" and i + 1 < len(parts):
                filters["disks.count__gte"] = int(parts[i + 1])
                i += 2
            elif parts[i] == "--interfaces" and i + 1 < len(parts):
                filters["interfaces.count__gte"] = int(parts[i + 1])
                i += 2
            else:
                i += 1

        try:
            hosts = self.shell.connection.api.filter_available(filters)

            # Check if API returned an error string instead of a list
            if isinstance(hosts, str):
                self.shell.perror(f"API error: {hosts}")
                return

            if not hosts:
                self.shell.poutput("No available hosts found")
                return

            # Ensure hosts is a list
            if not isinstance(hosts, list):
                self.shell.perror(f"Unexpected response type: {type(hosts)}")
                return

            table_data = []
            for host in hosts:
                # Handle both dict and object responses
                if isinstance(host, dict):
                    name = host.get("name", "")
                    model = host.get("model", "")
                    host_type = host.get("host_type", "")
                    can_self_schedule = host.get("can_self_schedule", False)
                else:
                    # If it's an object, try attribute access
                    name = getattr(host, "name", "")
                    model = getattr(host, "model", "")
                    host_type = getattr(host, "host_type", "")
                    can_self_schedule = getattr(host, "can_self_schedule", False)

                table_data.append([name, model, host_type, "Yes" if can_self_schedule else "No"])

            headers = ["Name", "Model", "Type", "Self-Schedule"]
            self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))

        except Exception as e:
            self.shell.perror(f"Failed to list available hosts: {e}")
