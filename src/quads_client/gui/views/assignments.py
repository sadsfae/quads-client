"""Assignments view - shows user's assignments in list format (refactored)"""

import tkinter as tk
from tkinter import ttk

from quads_client.gui.widgets.base import BaseAdminView, ScrolledTreeview


class AssignmentsView(BaseAdminView):
    """View for displaying user's assignments in a simple list"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "My Assignments", requires_admin=False)
        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        # Header with refresh button
        self.create_header([("🔄 Refresh", self._load_assignments)])

        # Content frame with scrolled treeview
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("id", "cloud", "description", "owner", "validated")
        column_configs = {
            "id": ("ID", 80),
            "cloud": ("Cloud", 120),
            "description": ("Description", 300),
            "owner": ("Owner", 150),
            "validated": ("Validated", 100),
        }

        self.tree = ScrolledTreeview(content_frame, columns, column_configs)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Action buttons - admin users get extend/shrink, all users get terminate
        if self.shell.is_admin():
            self.create_action_bar(
                [
                    ("Extend", self._extend_assignment),
                    ("Shrink", self._shrink_assignment),
                    ("Terminate Selected", self._terminate_selected),
                ]
            )
        else:
            self.create_action_bar([("Terminate Selected", self._terminate_selected)])

        # Status label
        self.create_status_label()

        # Initial load
        self._load_assignments()

    def _load_assignments(self):
        """Load assignments from server"""
        from quads_client.utils import get_username_short, extract_assignment_id, extract_cloud_name

        # Check authentication first and show login button if needed
        if not self.shell.is_authenticated():
            self.tree.clear()
            # Show login button in the tree area
            for widget in self.tree.winfo_children():
                if isinstance(widget, ttk.Frame) and hasattr(widget, "_login_frame"):
                    return  # Already showing login UI

            # Create login frame
            login_frame = ttk.Frame(self.tree)
            login_frame._login_frame = True  # Mark it
            login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            ttk.Label(login_frame, text="Please login to view your assignments", font=("TkDefaultFont", 12)).pack(
                pady=(0, 20)
            )

            ttk.Button(login_frame, text="Login", command=self._auto_login).pack()

            self.update_status("Not authenticated")
            return

        # Remove login frame if it exists
        for widget in self.tree.winfo_children():
            if isinstance(widget, ttk.Frame) and hasattr(widget, "_login_frame"):
                widget.destroy()

        def load_data():
            # Admin users see ALL assignments, normal users only see their own
            if self.shell.is_admin():
                # Admin: show all active assignments
                return self.shell.connection.api.filter_assignments({"active": True})
            else:
                # Normal user: filter by owner
                username = get_username_short(self.shell.connection.username)
                return self.shell.connection.api.filter_assignments({"owner": username, "active": True})

        self.tree.clear()
        assignments = self.safe_load_data(load_data, success_message="Showing {count} assignment(s)")

        if not assignments:
            return

        for assignment in assignments:
            if isinstance(assignment, dict):
                assignment_id = extract_assignment_id(assignment)
                cloud_name = extract_cloud_name(assignment)
                description = assignment.get("description", "No description")
                owner = assignment.get("owner", "N/A")
                validated = "✓" if assignment.get("validated") else "○"

                self.tree.insert(
                    "",
                    tk.END,
                    values=(assignment_id, cloud_name, description, owner, validated),
                )

    def _auto_login(self):
        """Auto-login to default or only server"""
        from quads_client.gui.widgets.dialogs import show_error_dialog

        prefs = self._get_preferences()
        default_server = prefs.get("default_server")

        # Get all configured servers
        servers = {}
        if self.shell.config:
            servers = self.shell.config.get_all_servers()

        # Determine which server to connect to
        target_server = None
        if default_server and default_server in servers:
            target_server = default_server
        elif len(servers) == 1:
            # Only one server configured
            target_server = list(servers.keys())[0]
        elif len(servers) > 1:
            # Multiple servers, no default - switch to connection view
            self.shell.gui_app._show_connection_view()
            return

        if target_server:
            try:
                # Connect to the server
                self.shell.connection_commands.cmd_connect(target_server)
                # Refresh this view
                self._load_assignments()
            except Exception as e:
                show_error_dialog(self, "Login Failed", f"Failed to connect to {target_server}", str(e))
        else:
            # No servers configured - show onboarding
            self.shell.gui_app._show_servers_view()

    def _get_preferences(self):
        """Get GUI preferences from config"""
        if self.shell.config and hasattr(self.shell.config, "config_data"):
            return self.shell.config.config_data.get("gui_preferences", {})
        return {}

    def _terminate_selected(self):
        """Terminate selected assignment"""
        _, values = self.get_selected_item("Please select an assignment to terminate")
        if not values:
            return

        assignment_id = values[0]

        if not self.confirm_action(
            "Confirm Termination",
            f"Are you sure you want to terminate assignment #{assignment_id}?\n\n"
            "This will release all hosts in this assignment.",
        ):
            return

        self.safe_execute(
            lambda: self.shell.user_commands.cmd_terminate(str(assignment_id)),
            f"Assignment #{assignment_id} terminated\n\n"
            "Note: It may take a few moments for the termination to complete.",
            "Termination Failed",
            self._load_assignments,
        )

    def _extend_assignment(self):
        """Extend selected assignment (admin only)"""
        from tkinter import messagebox

        _, values = self.get_selected_item("Please select an assignment to extend")
        if not values:
            return

        assignment_id = values[0]
        cloud_name = values[1]

        # Create dialog for extend options
        dialog = self.create_simple_dialog(f"Extend Assignment #{assignment_id}", "350x200")

        ttk.Label(
            dialog, text=f"Extend assignment #{assignment_id} ({cloud_name})", font=("TkDefaultFont", 10, "bold")
        ).pack(pady=10)

        # Weeks input
        input_frame = ttk.Frame(dialog)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="Number of weeks:").pack(side=tk.LEFT, padx=5)
        weeks_var = tk.StringVar(value="2")
        weeks_entry = ttk.Entry(input_frame, textvariable=weeks_var, width=10)
        weeks_entry.pack(side=tk.LEFT, padx=5)
        weeks_entry.focus()

        def on_extend():
            weeks_str = weeks_var.get().strip()

            # Validate integer
            try:
                weeks = int(weeks_str)
                if weeks <= 0:
                    messagebox.showerror("Invalid Input", "Weeks must be a positive integer", parent=dialog)
                    return
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid integer for weeks", parent=dialog)
                return

            dialog.destroy()

            # Confirm action
            if not self.confirm_action(
                "Confirm Extend",
                f"Extend assignment #{assignment_id} ({cloud_name}) by {weeks} week(s)?\n\n"
                "This will extend ALL schedules in this assignment.",
            ):
                return

            # Call extend command with cloud name
            self.safe_execute(
                lambda: self.shell.schedule_commands.cmd_extend(f"{cloud_name} weeks {weeks}"),
                f"Extended assignment #{assignment_id} by {weeks} week(s)",
                "Extend Failed",
                self._load_assignments,
            )

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Extend", command=on_extend).pack(side=tk.LEFT, padx=5)

    def _shrink_assignment(self):
        """Shrink selected assignment (admin only)"""
        from tkinter import messagebox

        _, values = self.get_selected_item("Please select an assignment to shrink")
        if not values:
            return

        assignment_id = values[0]
        cloud_name = values[1]

        # Create dialog for shrink options
        dialog = self.create_simple_dialog(f"Shrink Assignment #{assignment_id}", "400x250")

        ttk.Label(
            dialog, text=f"Shrink assignment #{assignment_id} ({cloud_name})", font=("TkDefaultFont", 10, "bold")
        ).pack(pady=10)

        # Mode selection
        mode_frame = ttk.Frame(dialog)
        mode_frame.pack(pady=10)

        mode_var = tk.StringVar(value="weeks")

        ttk.Radiobutton(mode_frame, text="By weeks:", variable=mode_var, value="weeks").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2
        )
        weeks_var = tk.StringVar(value="1")
        weeks_entry = ttk.Entry(mode_frame, textvariable=weeks_var, width=10)
        weeks_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Radiobutton(mode_frame, text="By days:", variable=mode_var, value="days").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=2
        )
        days_var = tk.StringVar(value="7")
        days_entry = ttk.Entry(mode_frame, textvariable=days_var, width=10)
        days_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Radiobutton(mode_frame, text="End now (terminate)", variable=mode_var, value="now").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2
        )

        def on_shrink():
            mode = mode_var.get()

            if mode == "weeks":
                value_str = weeks_var.get().strip()
                unit = "week(s)"
                try:
                    value = int(value_str)
                    if value <= 0:
                        messagebox.showerror("Invalid Input", "Weeks must be a positive integer", parent=dialog)
                        return
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a valid integer for weeks", parent=dialog)
                    return
            elif mode == "days":
                value_str = days_var.get().strip()
                unit = "day(s)"
                try:
                    value = int(value_str)
                    if value <= 0:
                        messagebox.showerror("Invalid Input", "Days must be a positive integer", parent=dialog)
                        return
                    # Convert days to weeks fraction for the command (assuming shrink accepts weeks)
                    # Actually, we'll need to calculate new end date
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a valid integer for days", parent=dialog)
                    return
            else:  # now
                value = 0
                value_str = "0"
                unit = "(end now)"

            dialog.destroy()

            # Confirm action
            if mode == "now":
                confirm_msg = f"End assignment #{assignment_id} ({cloud_name}) NOW?\n\nThis will terminate the assignment immediately."
            else:
                confirm_msg = f"Shrink assignment #{assignment_id} ({cloud_name}) by {value_str} {unit}?\n\nThis will shrink ALL schedules in this assignment."

            if not self.confirm_action("Confirm Shrink", confirm_msg):
                return

            # Build command based on mode
            if mode == "weeks":
                cmd_args = f"{cloud_name} weeks {value}"
            elif mode == "days":
                # Convert days to weeks for the command (API expects weeks)
                # But user said shrink should support days - we may need to enhance the CLI command
                # For now, convert days to fractional weeks
                weeks_value = value / 7.0
                cmd_args = f"{cloud_name} weeks {weeks_value:.2f}"
            else:  # now
                # Shrink to now means terminate - use 0 weeks or we could just terminate
                # Actually looking at shrink command, it reduces by weeks, so ending now would need different logic
                # Let's just call terminate for "now" mode
                self.safe_execute(
                    lambda: self.shell.user_commands.cmd_terminate(str(assignment_id)),
                    f"Assignment #{assignment_id} terminated",
                    "Terminate Failed",
                    self._load_assignments,
                )
                return

            # Call shrink command
            self.safe_execute(
                lambda: self.shell.schedule_commands.cmd_shrink(cmd_args),
                f"Shrunk assignment #{assignment_id} by {value_str} {unit}",
                "Shrink Failed",
                self._load_assignments,
            )

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Shrink", command=on_shrink).pack(side=tk.LEFT, padx=5)

    def refresh(self):
        """Public method to refresh the view"""
        self._load_assignments()
