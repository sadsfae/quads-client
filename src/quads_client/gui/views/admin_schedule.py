"""Admin schedule view - for schedule management with explicit dates (refactored)"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from quads_client.gui.widgets.base import BaseAdminView, ScrolledTreeview, FormDialog
from quads_client.gui.widgets.date_picker import DatePickerDialog, get_next_sunday_22utc, get_two_weeks_sunday_22utc


class AdminScheduleView(BaseAdminView):
    """View for admin schedule management"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Schedule Management (Admin)", requires_admin=True)
        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        # Header with buttons
        self.create_header(
            [
                ("➕ New Schedule", self._create_schedule),
                ("🔄 Refresh", self._load_schedules),
            ]
        )

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter by Cloud:").pack(side=tk.LEFT, padx=(0, 5))
        self.cloud_filter = ttk.Entry(filter_frame, width=20)
        self.cloud_filter.pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Host:").pack(side=tk.LEFT, padx=(20, 5))
        self.host_filter = ttk.Entry(filter_frame, width=20)
        self.host_filter.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="Apply", command=self._load_schedules).pack(side=tk.LEFT, padx=10)

        # Content frame with scrolled treeview
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("id", "host", "cloud", "owner", "start", "end")
        column_configs = {
            "id": ("ID", 60),
            "host": ("Host", 200),
            "cloud": ("Cloud", 100),
            "owner": ("Owner", 150),
            "start": ("Start", 150),
            "end": ("End", 150),
        }

        self.tree = ScrolledTreeview(content_frame, columns, column_configs)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        self.create_action_bar(
            [
                ("Extend", self._extend_schedule),
                ("Shrink", self._shrink_schedule),
                ("Delete", self._delete_schedule),
            ]
        )

        # Status label
        self.create_status_label()

        # Initial load
        self._load_schedules()

    def _get_free_clouds(self):
        """Get list of free clouds (no active assignments)"""
        try:
            # Get all clouds
            clouds = self.shell.connection.api.get_clouds()
            if not clouds:
                return []

            free_clouds = []

            for cloud in clouds:
                cloud_name = cloud.get("name")

                # Skip cloud01 (spare pool)
                if cloud_name == "cloud01":
                    continue

                # Check if cloud has current schedules
                current_schedules = self.shell.connection.api.get_current_schedules({"cloud": cloud_name})

                # If no current schedules, cloud is free
                if not current_schedules:
                    free_clouds.append(cloud_name)

            return sorted(free_clouds)

        except Exception as e:
            self.update_status(f"Error getting free clouds: {e}")
            return []

    def _load_schedules(self):
        """Load schedules from server"""

        def load_data():
            filters = {}
            if self.cloud_filter.get().strip():
                filters["cloud"] = self.cloud_filter.get().strip()
            if self.host_filter.get().strip():
                filters["host"] = self.host_filter.get().strip()
            # Use get_current_schedules to get only active schedules
            return self.shell.connection.api.get_current_schedules(filters)

        self.tree.clear()
        schedules = self.safe_load_data(load_data, success_message="Showing {count} schedule(s)")

        if not schedules:
            return

        for sched in schedules:
            schedule_id = sched.get("id", "")
            host = sched.get("host", {})
            host_name = host.get("name", "") if isinstance(host, dict) else str(host)

            assignment = sched.get("assignment", {})
            cloud = assignment.get("cloud", {})
            cloud_name = cloud.get("name", "") if isinstance(cloud, dict) else str(cloud)
            owner = assignment.get("owner", "")

            start = sched.get("start", "")
            end = sched.get("end", "")

            self.tree.insert(
                "",
                tk.END,
                values=(schedule_id, host_name, cloud_name, owner, start, end),
            )

    def _validate_hosts_availability(self, hostnames, start_date, end_date):
        """Validate hosts are available for the specified date range

        Uses is_available() API which checks:
        - Host exists
        - Host is not broken or retired
        - No schedule conflicts in the date range

        Args:
            hostnames: List of hostname strings
            start_date: Start date string (YYYY-MM-DD HH:MM)
            end_date: End date string (YYYY-MM-DD HH:MM)

        Returns:
            tuple: (is_valid, error_list) where error_list contains hostname:reason pairs
        """
        errors = []

        for hostname in hostnames:
            hostname = hostname.strip()
            if not hostname:
                continue

            try:
                # is_available() handles all validation (exists, not broken/retired, schedule conflicts)
                is_available = self.shell.connection.api.is_available(hostname, {"start": start_date, "end": end_date})

                if not is_available:
                    errors.append(f"{hostname}: Not available for {start_date} to {end_date}")

            except Exception as e:
                errors.append(f"{hostname}: Error checking availability ({str(e)})")

        return (len(errors) == 0, errors)

    def _create_schedule(self, prefill_hosts=None):
        """Create new schedule with admin parameters

        Args:
            prefill_hosts: Optional comma-separated string of hostnames to pre-fill
        """
        dialog = self.create_simple_dialog("Create Schedule (Admin)", "650x700")
        dialog.resizable(True, True)  # Make it resizable so users can adjust if needed

        ttk.Label(
            dialog,
            text="Create Schedule with Explicit Dates",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(pady=10, padx=20)

        # Create scrollable container for form
        # Get background color from ttk style to match theme
        style = ttk.Style()
        bg_color = style.lookup("TFrame", "background")

        canvas = tk.Canvas(dialog, highlightthickness=0, background=bg_color, borderwidth=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/MacOS
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux

        form_frame = ttk.Frame(scrollable_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Load admin preferences
        prefs = {}
        if self.shell.config and hasattr(self.shell.config, "config_data"):
            prefs = self.shell.config.config_data.get("gui_preferences", {})

        cadence = prefs.get("admin_schedule_cadence", "2 weeks")
        start_hour = prefs.get("admin_schedule_start_hour", 22)
        end_hour = prefs.get("admin_schedule_end_hour", 22)

        # Cloud - populate with free clouds
        ttk.Label(form_frame, text="Cloud:").grid(row=0, column=0, sticky=tk.W, pady=5)
        cloud_frame = ttk.Frame(form_frame)
        cloud_frame.grid(row=0, column=1, pady=5, sticky=tk.W)

        free_clouds = self._get_free_clouds()
        cloud_var = tk.StringVar()
        cloud_combo = ttk.Combobox(cloud_frame, textvariable=cloud_var, values=free_clouds, width=27, state="readonly")
        cloud_combo.pack(side=tk.LEFT)

        if free_clouds:
            cloud_combo.current(0)  # Select first free cloud by default

        ttk.Label(cloud_frame, text=f"({len(free_clouds)} free)", font=("TkDefaultFont", 8), foreground="gray").pack(
            side=tk.LEFT, padx=5
        )

        # Hosts selection mode
        ttk.Label(form_frame, text="Hosts:").grid(row=1, column=0, sticky=tk.W, pady=5)
        mode_var = tk.StringVar(value="list")

        mode_frame = ttk.Frame(form_frame)
        mode_frame.grid(row=1, column=1, pady=5, sticky=tk.W)

        ttk.Radiobutton(mode_frame, text="Comma-separated", variable=mode_var, value="list").pack(anchor=tk.W)
        hosts_entry = ttk.Entry(mode_frame, width=40)
        hosts_entry.pack(fill=tk.X, pady=2)

        # Pre-fill hosts if provided
        if prefill_hosts:
            hosts_entry.insert(0, prefill_hosts)

        ttk.Radiobutton(mode_frame, text="From file", variable=mode_var, value="file").pack(anchor=tk.W, pady=(5, 0))
        file_frame = ttk.Frame(mode_frame)
        file_frame.pack(fill=tk.X, pady=2)
        file_entry = ttk.Entry(file_frame, width=30)
        file_entry.pack(side=tk.LEFT)

        def browse_file():
            filename = filedialog.askopenfilename(parent=dialog)
            if filename:
                file_entry.delete(0, tk.END)
                file_entry.insert(0, filename)

        ttk.Button(file_frame, text="Browse", command=browse_file).pack(side=tk.LEFT, padx=5)

        # Dates with smart defaults (using admin preferences)
        default_start = get_next_sunday_22utc(start_hour)
        default_end = get_two_weeks_sunday_22utc(default_start, cadence, end_hour)

        ttk.Label(form_frame, text="Start Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        start_frame = ttk.Frame(form_frame)
        start_frame.grid(row=2, column=1, pady=5, sticky=tk.W)
        start_entry = ttk.Entry(start_frame, width=25)
        start_entry.pack(side=tk.LEFT)
        start_entry.insert(0, default_start.strftime("%Y-%m-%d %H:%M"))

        def pick_start_date():
            # Pass end date as range_end to show the selection range
            picker = DatePickerDialog(
                dialog,
                "Select Start Date",
                start_entry.get(),
                range_start=start_entry.get(),
                range_end=end_entry.get(),
            )
            dialog.wait_window(picker)
            result = picker.get_result()
            if result:
                start_entry.delete(0, tk.END)
                start_entry.insert(0, result)
                # Update end date using admin preferences
                new_end = get_two_weeks_sunday_22utc(result, cadence, end_hour)
                end_entry.delete(0, tk.END)
                end_entry.insert(0, new_end.strftime("%Y-%m-%d %H:%M"))

        def set_start_now():
            now = datetime.utcnow()
            start_entry.delete(0, tk.END)
            start_entry.insert(0, now.strftime("%Y-%m-%d %H:%M"))
            # Also update end date using admin preferences
            new_end = get_two_weeks_sunday_22utc(now, cadence, end_hour)
            end_entry.delete(0, tk.END)
            end_entry.insert(0, new_end.strftime("%Y-%m-%d %H:%M"))

        ttk.Button(start_frame, text="📅", command=pick_start_date, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(start_frame, text="Now", command=set_start_now, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(start_frame, text="(UTC)", font=("TkDefaultFont", 8)).pack(side=tk.LEFT, padx=5)

        ttk.Label(form_frame, text="End Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
        end_frame = ttk.Frame(form_frame)
        end_frame.grid(row=3, column=1, pady=5, sticky=tk.W)
        end_entry = ttk.Entry(end_frame, width=25)
        end_entry.pack(side=tk.LEFT)
        end_entry.insert(0, default_end.strftime("%Y-%m-%d %H:%M"))

        def pick_end_date():
            # Pass start date as range_start to show the selection range
            picker = DatePickerDialog(
                dialog, "Select End Date", end_entry.get(), range_start=start_entry.get(), range_end=end_entry.get()
            )
            dialog.wait_window(picker)
            result = picker.get_result()
            if result:
                end_entry.delete(0, tk.END)
                end_entry.insert(0, result)

        ttk.Button(end_frame, text="📅", command=pick_end_date, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Label(end_frame, text="(UTC)", font=("TkDefaultFont", 8)).pack(side=tk.LEFT, padx=5)

        # Assignment parameters
        desc_entry = FormDialog.create_labeled_entry(form_frame, "Description:", 4, 40)
        owner_entry = FormDialog.create_labeled_entry(form_frame, "Cloud Owner:", 5, 30)
        ticket_entry = FormDialog.create_labeled_entry(form_frame, "Ticket ID:", 6, 30)
        cc_entry = FormDialog.create_labeled_entry(form_frame, "CC Users:", 7, 40)

        # VLAN dropdown - populate with free VLANs only
        ttk.Label(form_frame, text="VLAN:").grid(row=8, column=0, sticky=tk.W, pady=5)
        free_vlans = self.shell.get_available_vlans()
        if free_vlans:
            vlan_values = ["Select VLAN..."] + free_vlans
            vlan_combo = ttk.Combobox(form_frame, values=vlan_values, width=17, state="readonly")
            vlan_combo.set("Select VLAN...")
        else:
            vlan_combo = ttk.Combobox(form_frame, values=["No free VLANs available"], width=17, state="readonly")
            vlan_combo.set("No free VLANs available")
        vlan_combo.grid(row=8, column=1, pady=5, sticky=tk.W)

        ttk.Label(form_frame, text="QinQ:").grid(row=9, column=0, sticky=tk.W, pady=5)
        qinq_combo = ttk.Combobox(form_frame, values=["0", "1"], width=17, state="readonly")
        qinq_combo.set("0")
        qinq_combo.grid(row=9, column=1, pady=5, sticky=tk.W)

        nowipe_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_frame, text="No wipe", variable=nowipe_var).grid(row=10, column=1, sticky=tk.W, pady=5)

        def on_create():
            cloud = cloud_var.get().strip()
            start = start_entry.get().strip()
            end = end_entry.get().strip()

            if not cloud or not start or not end:
                messagebox.showerror("Error", "Cloud, start, and end dates are required", parent=dialog)
                return

            # Build host argument and validate
            hostname_list = []
            if mode_var.get() == "list":
                hosts = hosts_entry.get().strip()
                if not hosts:
                    messagebox.showerror("Error", "Host list is required", parent=dialog)
                    return

                # Parse comma-separated hostnames
                hostname_list = [h.strip() for h in hosts.split(",") if h.strip()]

            else:
                hosts_file = file_entry.get().strip()
                if not hosts_file:
                    messagebox.showerror("Error", "Host file is required", parent=dialog)
                    return

                # Read hostnames from file
                try:
                    with open(hosts_file, "r") as f:
                        hostname_list = [line.strip() for line in f if line.strip()]

                    if not hostname_list:
                        messagebox.showerror("Error", f"No hostnames found in file: {hosts_file}", parent=dialog)
                        return

                except FileNotFoundError:
                    messagebox.showerror("Error", f"File not found: {hosts_file}", parent=dialog)
                    return
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to read file: {e}", parent=dialog)
                    return

                hosts = f"host-list {hosts_file}"

            # Validate hostnames before scheduling
            is_valid, errors = self._validate_hosts_availability(hostname_list, start, end)

            if not is_valid:
                error_msg = "The following hosts are invalid or unavailable:\n\n"
                error_msg += "\n".join(f"  • {err}" for err in errors)
                error_msg += "\n\nPlease fix these issues before scheduling."
                messagebox.showerror("Invalid Hostnames", error_msg, parent=dialog)
                return

            # Build host argument for CLI
            if mode_var.get() == "list":
                hosts = hosts_entry.get().strip()
            else:
                hosts = f"host-list {file_entry.get().strip()}"

            # Build args string
            args = f"{cloud} {hosts} {start} {end}"

            if desc_entry.get().strip():
                args += f' description "{desc_entry.get().strip()}"'
            if owner_entry.get().strip():
                args += f" cloud-owner {owner_entry.get().strip()}"
            if ticket_entry.get().strip():
                args += f" cloud-ticket {ticket_entry.get().strip()}"
            if cc_entry.get().strip():
                args += f' cc-users "{cc_entry.get().strip()}"'
            # Only add VLAN if a valid one is selected
            vlan = vlan_combo.get()
            if vlan and vlan != "Select VLAN..." and vlan != "No free VLANs available":
                args += f" vlan {vlan}"
            if qinq_combo.get():
                args += f" qinq {qinq_combo.get()}"
            if nowipe_var.get():
                args += " nowipe"

            self.safe_execute(
                lambda: self.shell.schedule_commands.cmd_schedule_admin(args),
                "Schedule created successfully",
                "Create Schedule Failed",
                self._load_schedules,
            )
            dialog.destroy()

        # Button row inside scrollable frame
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create", command=on_create).pack(side=tk.LEFT, padx=5)

    def _extend_schedule(self):
        """Extend selected schedule"""
        _, values = self.get_selected_item("Please select a schedule to extend")
        if not values:
            return

        schedule_id = values[0]
        current_end = values[5]

        dialog = self.create_simple_dialog(f"Extend Schedule #{schedule_id}", "400x200")

        ttk.Label(dialog, text=f"Extend schedule #{schedule_id}", font=("TkDefaultFont", 10, "bold")).pack(pady=10)
        ttk.Label(dialog, text=f"Current end: {current_end}").pack(pady=5)

        ttk.Label(dialog, text="New end date (YYYY-MM-DD HH:MM):").pack(pady=10)
        date_entry = ttk.Entry(dialog, width=30)
        date_entry.pack()

        def on_extend():
            new_date = date_entry.get().strip()
            if not new_date:
                messagebox.showerror("Error", "Date is required", parent=dialog)
                return

            args = f"{schedule_id} {new_date}"
            self.safe_execute(
                lambda: self.shell.schedule_commands.cmd_extend(args),
                f"Schedule #{schedule_id} extended",
                "Extend Failed",
                self._load_schedules,
            )
            dialog.destroy()

        FormDialog.create_button_row(
            dialog,
            [
                ("Cancel", dialog.destroy),
                ("Extend", on_extend),
            ],
        )

    def _shrink_schedule(self):
        """Shrink selected schedule"""
        _, values = self.get_selected_item("Please select a schedule to shrink")
        if not values:
            return

        schedule_id = values[0]
        current_end = values[5]

        dialog = self.create_simple_dialog(f"Shrink Schedule #{schedule_id}", "400x200")

        ttk.Label(dialog, text=f"Shrink schedule #{schedule_id}", font=("TkDefaultFont", 10, "bold")).pack(pady=10)
        ttk.Label(dialog, text=f"Current end: {current_end}").pack(pady=5)

        ttk.Label(dialog, text="New end date (YYYY-MM-DD HH:MM):").pack(pady=10)
        date_entry = ttk.Entry(dialog, width=30)
        date_entry.pack()

        def on_shrink():
            new_date = date_entry.get().strip()
            if not new_date:
                messagebox.showerror("Error", "Date is required", parent=dialog)
                return

            args = f"{schedule_id} {new_date}"
            self.safe_execute(
                lambda: self.shell.schedule_commands.cmd_shrink(args),
                f"Schedule #{schedule_id} shrunk",
                "Shrink Failed",
                self._load_schedules,
            )
            dialog.destroy()

        FormDialog.create_button_row(
            dialog,
            [
                ("Cancel", dialog.destroy),
                ("Shrink", on_shrink),
            ],
        )

    def _delete_schedule(self):
        """Delete selected schedule"""
        _, values = self.get_selected_item("Please select a schedule to delete")
        if not values:
            return

        schedule_id = values[0]
        host_name = values[1]

        if not self.confirm_action(
            "Confirm Deletion", f"Delete schedule #{schedule_id} for {host_name}?\n\n" "This action cannot be undone."
        ):
            return

        self.safe_execute(
            lambda: self.shell.schedule_commands.cmd_rm_schedule(schedule_id),
            f"Schedule #{schedule_id} deleted",
            "Delete Failed",
            self._load_schedules,
        )

    def refresh(self):
        """Public method to refresh the view"""
        self._load_schedules()
