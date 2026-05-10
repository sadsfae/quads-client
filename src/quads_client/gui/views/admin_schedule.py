"""Admin schedule view - for schedule management with explicit dates (refactored)"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from quads_client.gui.widgets.base import BaseAdminView, ScrolledTreeview, FormDialog


class AdminScheduleView(BaseAdminView):
    """View for admin schedule management"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Schedule Management (Admin)", requires_admin=True)
        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        # Header with buttons
        self.create_header([
            ("➕ New Schedule", self._create_schedule),
            ("🔄 Refresh", self._load_schedules),
        ])

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter by Cloud:").pack(side=tk.LEFT, padx=(0, 5))
        self.cloud_filter = ttk.Entry(filter_frame, width=20)
        self.cloud_filter.pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Host:").pack(side=tk.LEFT, padx=(20, 5))
        self.host_filter = ttk.Entry(filter_frame, width=20)
        self.host_filter.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="Apply", command=self._load_schedules).pack(
            side=tk.LEFT, padx=10
        )

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
        self.create_action_bar([
            ("Extend", self._extend_schedule),
            ("Shrink", self._shrink_schedule),
            ("Delete", self._delete_schedule),
        ])

        # Status label
        self.create_status_label()

        # Initial load
        self._load_schedules()

    def _load_schedules(self):
        """Load schedules from server"""
        def load_data():
            filters = {}
            if self.cloud_filter.get().strip():
                filters["cloud"] = self.cloud_filter.get().strip()
            if self.host_filter.get().strip():
                filters["host"] = self.host_filter.get().strip()
            return self.shell.connection.api.get_schedules(filters)

        self.tree.clear()
        schedules = self.safe_load_data(
            load_data,
            success_message="Showing {count} schedule(s)"
        )

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

    def _create_schedule(self):
        """Create new schedule with admin parameters"""
        dialog = self.create_simple_dialog("Create Schedule (Admin)", "600x550")

        ttk.Label(
            dialog,
            text="Create Schedule with Explicit Dates",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(pady=10, padx=20)

        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Cloud
        cloud_entry = FormDialog.create_labeled_entry(form_frame, "Cloud:", 0, 30)

        # Hosts selection mode
        ttk.Label(form_frame, text="Hosts:").grid(row=1, column=0, sticky=tk.W, pady=5)
        mode_var = tk.StringVar(value="list")

        mode_frame = ttk.Frame(form_frame)
        mode_frame.grid(row=1, column=1, pady=5, sticky=tk.W)

        ttk.Radiobutton(mode_frame, text="Comma-separated", variable=mode_var, value="list").pack(
            anchor=tk.W
        )
        hosts_entry = ttk.Entry(mode_frame, width=40)
        hosts_entry.pack(fill=tk.X, pady=2)

        ttk.Radiobutton(mode_frame, text="From file", variable=mode_var, value="file").pack(
            anchor=tk.W, pady=(5, 0)
        )
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

        # Dates
        ttk.Label(form_frame, text="Start Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        start_frame = ttk.Frame(form_frame)
        start_frame.grid(row=2, column=1, pady=5, sticky=tk.W)
        start_entry = ttk.Entry(start_frame, width=30)
        start_entry.pack(side=tk.LEFT)
        start_entry.insert(0, "YYYY-MM-DD HH:MM or 'now'")
        ttk.Label(start_frame, text="(UTC)", font=("TkDefaultFont", 8)).pack(side=tk.LEFT, padx=5)

        ttk.Label(form_frame, text="End Date:").grid(row=3, column=0, sticky=tk.W, pady=5)
        end_frame = ttk.Frame(form_frame)
        end_frame.grid(row=3, column=1, pady=5, sticky=tk.W)
        end_entry = ttk.Entry(end_frame, width=30)
        end_entry.pack(side=tk.LEFT)
        end_entry.insert(0, "YYYY-MM-DD HH:MM")
        ttk.Label(end_frame, text="(UTC)", font=("TkDefaultFont", 8)).pack(side=tk.LEFT, padx=5)

        # Assignment parameters
        desc_entry = FormDialog.create_labeled_entry(form_frame, "Description:", 4, 40)
        owner_entry = FormDialog.create_labeled_entry(form_frame, "Cloud Owner:", 5, 30)
        ticket_entry = FormDialog.create_labeled_entry(form_frame, "Ticket ID:", 6, 30)
        cc_entry = FormDialog.create_labeled_entry(form_frame, "CC Users:", 7, 40)
        vlan_entry = FormDialog.create_labeled_entry(form_frame, "VLAN:", 8, 20)

        ttk.Label(form_frame, text="QinQ:").grid(row=9, column=0, sticky=tk.W, pady=5)
        qinq_combo = ttk.Combobox(form_frame, values=["0", "1"], width=17, state="readonly")
        qinq_combo.set("0")
        qinq_combo.grid(row=9, column=1, pady=5, sticky=tk.W)

        nowipe_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_frame, text="No wipe", variable=nowipe_var).grid(
            row=10, column=1, sticky=tk.W, pady=5
        )

        def on_create():
            cloud = cloud_entry.get().strip()
            start = start_entry.get().strip()
            end = end_entry.get().strip()

            if not cloud or not start or not end:
                messagebox.showerror(
                    "Error", "Cloud, start, and end dates are required", parent=dialog
                )
                return

            # Build host argument
            if mode_var.get() == "list":
                hosts = hosts_entry.get().strip()
                if not hosts:
                    messagebox.showerror("Error", "Host list is required", parent=dialog)
                    return
            else:
                hosts_file = file_entry.get().strip()
                if not hosts_file:
                    messagebox.showerror("Error", "Host file is required", parent=dialog)
                    return
                hosts = f"host-list {hosts_file}"

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
            if vlan_entry.get().strip():
                args += f" vlan {vlan_entry.get().strip()}"
            if qinq_combo.get():
                args += f" qinq {qinq_combo.get()}"
            if nowipe_var.get():
                args += " nowipe"

            self.safe_execute(
                lambda: self.shell.schedule_commands.cmd_schedule_admin(args),
                "Schedule created successfully",
                "Create Schedule Failed",
                self._load_schedules
            )
            dialog.destroy()

        FormDialog.create_button_row(dialog, [
            ("Cancel", dialog.destroy),
            ("Create", on_create),
        ])

    def _extend_schedule(self):
        """Extend selected schedule"""
        _, values = self.get_selected_item("Please select a schedule to extend")
        if not values:
            return

        schedule_id = values[0]
        current_end = values[5]

        dialog = self.create_simple_dialog(f"Extend Schedule #{schedule_id}", "400x200")

        ttk.Label(dialog, text=f"Extend schedule #{schedule_id}", font=("TkDefaultFont", 10, "bold")).pack(
            pady=10
        )
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
                self._load_schedules
            )
            dialog.destroy()

        FormDialog.create_button_row(dialog, [
            ("Cancel", dialog.destroy),
            ("Extend", on_extend),
        ])

    def _shrink_schedule(self):
        """Shrink selected schedule"""
        _, values = self.get_selected_item("Please select a schedule to shrink")
        if not values:
            return

        schedule_id = values[0]
        current_end = values[5]

        dialog = self.create_simple_dialog(f"Shrink Schedule #{schedule_id}", "400x200")

        ttk.Label(dialog, text=f"Shrink schedule #{schedule_id}", font=("TkDefaultFont", 10, "bold")).pack(
            pady=10
        )
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
                self._load_schedules
            )
            dialog.destroy()

        FormDialog.create_button_row(dialog, [
            ("Cancel", dialog.destroy),
            ("Shrink", on_shrink),
        ])

    def _delete_schedule(self):
        """Delete selected schedule"""
        _, values = self.get_selected_item("Please select a schedule to delete")
        if not values:
            return

        schedule_id = values[0]
        host_name = values[1]

        if not self.confirm_action(
            "Confirm Deletion",
            f"Delete schedule #{schedule_id} for {host_name}?\n\n"
            "This action cannot be undone."
        ):
            return

        self.safe_execute(
            lambda: self.shell.schedule_commands.cmd_rm_schedule(schedule_id),
            f"Schedule #{schedule_id} deleted",
            "Delete Failed",
            self._load_schedules
        )

    def refresh(self):
        """Public method to refresh the view"""
        self._load_schedules()
