from tabulate import tabulate

from quads_client.error_handler import require_connection


class CloudCommands:
    def __init__(self, shell):
        self.shell = shell
        self.rich_console = shell.rich_console if hasattr(shell, "rich_console") else None

    def _require_connection(self):
        return require_connection(self.shell)

    def cmd_cloud_list(self, args):
        """List all clouds. Usage: cloud-list [--cloud <name>] [--detail]"""
        if not self._require_connection():
            return

        parts = args.split()
        cloud_name = None
        show_detail = False

        i = 0
        while i < len(parts):
            if parts[i] == "--cloud" and i + 1 < len(parts):
                cloud_name = parts[i + 1]
                i += 2
            elif parts[i] == "--detail":
                show_detail = True
                i += 1
            else:
                i += 1

        try:
            if cloud_name:
                self._show_cloud_detail(cloud_name)
            elif show_detail and not cloud_name:
                self.shell.perror("--detail requires --cloud <name>")
            else:
                clouds = self.shell.connection.api.get_clouds()
                if not clouds:
                    self.shell.poutput("No clouds found")
                    return

                table_data = []
                for cloud in clouds:
                    owner = cloud.get("owner", "") or "-"
                    description = cloud.get("description", "") or "-"
                    wipe = "Yes" if cloud.get("wipe", False) else "No"
                    vlan = cloud.get("vlan", {}).get("vlan_id", "-") if isinstance(cloud.get("vlan"), dict) else "-"

                    table_data.append([cloud.get("name", ""), owner, description[:50], vlan, wipe])

                headers = ["Cloud", "Owner", "Description", "VLAN", "Wipe"]
                if self.rich_console:
                    self.rich_console.print_table(headers, table_data)
                else:
                    self.shell.poutput(tabulate(table_data, headers=headers, tablefmt="simple"))

        except Exception as e:
            self.shell.perror(f"Failed to list clouds: {e}")

    def _show_cloud_detail(self, cloud_name):
        """Show detailed information for a specific cloud"""
        try:
            clouds = self.shell.connection.api.filter_clouds({"name": cloud_name})
            if not clouds:
                if self.rich_console:
                    self.rich_console.print_error(f"Cloud '{cloud_name}' not found")
                else:
                    self.shell.perror(f"Cloud '{cloud_name}' not found")
                return

            cloud = clouds[0]

            if self.rich_console:
                self.rich_console.print_section(f"Cloud: {cloud_name}")

                properties = [
                    ["Name", cloud.get("name", "")],
                    ["Owner", cloud.get("owner", "") or "-"],
                    ["Description", cloud.get("description", "") or "-"],
                    ["Ticket", cloud.get("ticket", "") or "-"],
                    ["CC Users", cloud.get("ccusers", "") or "-"],
                    [
                        "VLAN (QinQ)",
                        cloud.get("vlan", {}).get("vlan_id", "-") if isinstance(cloud.get("vlan"), dict) else "-",
                    ],
                    ["Wipe", "Yes" if cloud.get("wipe", False) else "No"],
                    ["Validated", "Yes" if cloud.get("validated", False) else "No"],
                ]

                self.rich_console.print_table(["Property", "Value"], properties)

                schedules = self.shell.connection.api.get_schedules({"cloud": cloud_name})
                if schedules:
                    self.shell.poutput("")  # Blank line
                    host_data = []
                    for sched in schedules:
                        host = sched.get("host", {})
                        host_data.append(
                            [
                                host.get("name", ""),
                                host.get("model", ""),
                                sched.get("start", ""),
                                sched.get("end", ""),
                            ]
                        )

                    headers = ["Hostname", "Model", "Start", "End"]
                    self.rich_console.print_table(headers, host_data, title=f"Assigned Hosts ({len(schedules)})")
                else:
                    self.rich_console.print_info("\nNo hosts assigned to this cloud")
            else:
                self.shell.poutput(f"\nCloud: {cloud_name}")
                self.shell.poutput("=" * 80)

                properties = [
                    ["Name", cloud.get("name", "")],
                    ["Owner", cloud.get("owner", "") or "-"],
                    ["Description", cloud.get("description", "") or "-"],
                    ["Ticket", cloud.get("ticket", "") or "-"],
                    ["CC Users", cloud.get("ccusers", "") or "-"],
                    [
                        "VLAN (QinQ)",
                        cloud.get("vlan", {}).get("vlan_id", "-") if isinstance(cloud.get("vlan"), dict) else "-",
                    ],
                    ["Wipe", "Yes" if cloud.get("wipe", False) else "No"],
                    ["Validated", "Yes" if cloud.get("validated", False) else "No"],
                ]

                self.shell.poutput(tabulate(properties, tablefmt="simple"))

                schedules = self.shell.connection.api.get_schedules({"cloud": cloud_name})
                if schedules:
                    self.shell.poutput(f"\nAssigned Hosts ({len(schedules)}):")
                    self.shell.poutput("-" * 80)

                    host_data = []
                    for sched in schedules:
                        host = sched.get("host", {})
                        host_data.append(
                            [
                                host.get("name", ""),
                                host.get("model", ""),
                                sched.get("start", ""),
                                sched.get("end", ""),
                            ]
                        )

                    headers = ["Hostname", "Model", "Start", "End"]
                    self.shell.poutput(tabulate(host_data, headers=headers, tablefmt="simple"))
                else:
                    self.shell.poutput("\nNo hosts assigned to this cloud")

        except Exception as e:
            if self.rich_console:
                self.rich_console.print_error(f"Failed to get cloud details: {e}")
            else:
                self.shell.perror(f"Failed to get cloud details: {e}")

    def cmd_cloud_create(self, args):
        """Create a new cloud (admin only). Usage: cloud-create <name>"""
        if not self._require_connection():
            return

        if not args.strip():
            self.shell.perror("Usage: cloud-create <name>")
            return

        cloud_name = args.strip()
        try:
            self.shell.connection.api.create_cloud({"cloud": cloud_name})
            if self.rich_console:
                self.rich_console.print_success(f"Cloud '{cloud_name}' created successfully")
            else:
                self.shell.poutput(f"Cloud '{cloud_name}' created successfully")
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                if self.rich_console:
                    self.rich_console.print_error("This command requires admin role")
                else:
                    self.shell.perror("Error: This command requires admin role")
            else:
                if self.rich_console:
                    self.rich_console.print_error(f"Failed to create cloud: {e}")
                else:
                    self.shell.perror(f"Failed to create cloud: {e}")

    def cmd_cloud_delete(self, args):
        """Delete a cloud (admin only). Usage: cloud-delete <name>"""
        if not self._require_connection():
            return

        if not args.strip():
            self.shell.perror("Usage: cloud-delete <name>")
            return

        cloud_name = args.strip()
        try:
            self.shell.connection.api.remove_cloud(cloud_name)
            if self.rich_console:
                self.rich_console.print_success(f"Cloud '{cloud_name}' deleted successfully")
            else:
                self.shell.poutput(f"Cloud '{cloud_name}' deleted successfully")
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                if self.rich_console:
                    self.rich_console.print_error("This command requires admin role")
                else:
                    self.shell.perror("Error: This command requires admin role")
            else:
                if self.rich_console:
                    self.rich_console.print_error(f"Failed to delete cloud: {e}")
                else:
                    self.shell.perror(f"Failed to delete cloud: {e}")

    def cmd_mod_cloud(self, args):
        """Modify cloud attributes.
        Usage: mod-cloud <cloud_name> [--owner OWNER] [--description DESC] [--ticket TICKET] [--wipe true|false]
        """
        if not self._require_connection():
            return

        parts = args.split()
        if len(parts) < 1:
            self.shell.perror(
                "Usage: mod-cloud <cloud_name> [--owner OWNER] [--description DESC] "
                "[--ticket TICKET] [--wipe true|false] [--ccusers CCUSERS]"
            )
            return

        cloud_name = parts[0]
        updates = {}

        i = 1
        while i < len(parts):
            if parts[i] == "--owner" and i + 1 < len(parts):
                updates["owner"] = parts[i + 1]
                i += 2
            elif parts[i] == "--description" and i + 1 < len(parts):
                desc_parts = []
                i += 1
                while i < len(parts) and not parts[i].startswith("--"):
                    desc_parts.append(parts[i])
                    i += 1
                updates["description"] = " ".join(desc_parts)
            elif parts[i] == "--ticket" and i + 1 < len(parts):
                updates["ticket"] = parts[i + 1]
                i += 2
            elif parts[i] == "--wipe" and i + 1 < len(parts):
                updates["wipe"] = parts[i + 1].lower() == "true"
                i += 2
            elif parts[i] == "--ccusers" and i + 1 < len(parts):
                updates["ccusers"] = parts[i + 1]
                i += 2
            else:
                i += 1

        if not updates:
            self.shell.perror("No updates specified")
            return

        try:
            self.shell.connection.api.update_cloud(cloud_name, updates)
            if self.rich_console:
                self.rich_console.print_success(f"Cloud '{cloud_name}' updated successfully")
                for key, value in updates.items():
                    self.rich_console.print_property(key, value)
            else:
                self.shell.poutput(f"OK: Cloud '{cloud_name}' updated successfully")
                for key, value in updates.items():
                    self.shell.poutput(f"  {key}: {value}")

        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                if self.rich_console:
                    self.rich_console.print_error("This command requires admin role")
                else:
                    self.shell.perror("Error: This command requires admin role")
            else:
                if self.rich_console:
                    self.rich_console.print_error(f"Failed to modify cloud: {e}")
                else:
                    self.shell.perror(f"Failed to modify cloud: {e}")
