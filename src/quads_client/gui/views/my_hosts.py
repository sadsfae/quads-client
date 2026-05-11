"""My Hosts view - shows user's active assignments and hosts"""

import tkinter as tk
from tkinter import ttk, messagebox

from quads_client.gui.widgets.dialogs import show_error_dialog


class MyHostsView(ttk.Frame):
    """View for displaying user's active hosts and assignments"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell

        # Load preferences
        prefs = self._get_preferences()
        self.auto_refresh_enabled = prefs.get("auto_refresh_my_hosts", True)
        self.refresh_interval = prefs.get("auto_refresh_interval", 30) * 1000  # Convert to ms

        self._create_ui()

    def _get_preferences(self):
        """Get GUI preferences from config"""
        if self.shell.config and hasattr(self.shell.config, "config_data"):
            return self.shell.config.config_data.get("gui_preferences", {})
        return {}

    def _auto_login(self):
        """Auto-login to default or only server"""
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

    def _create_ui(self):
        """Create the UI"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        title_label = ttk.Label(header_frame, text="My Hosts", font=("TkDefaultFont", 14, "bold"))
        title_label.pack(side=tk.LEFT)

        ttk.Button(header_frame, text="🔄 Refresh", command=self._manual_refresh).pack(side=tk.RIGHT)

        interval_sec = self.refresh_interval // 1000
        self.auto_refresh_var = tk.BooleanVar(value=self.auto_refresh_enabled)
        self.auto_refresh_check = ttk.Checkbutton(
            header_frame,
            text=f"Auto-refresh ({interval_sec}s)",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh,
        )
        self.auto_refresh_check.pack(side=tk.RIGHT, padx=10)

        # Start auto-refresh if enabled
        if self.auto_refresh_enabled:
            self.after(100, self._schedule_auto_refresh)

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.status_label = ttk.Label(self, text="Loading...", font=("TkDefaultFont", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))

        self._load_assignments()

    def _load_assignments(self):
        """Load user's assignments"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not self.shell.is_authenticated():
            # Not logged in - show message and login button
            message_frame = ttk.Frame(self.content_frame)
            message_frame.pack(pady=50)

            ttk.Label(
                message_frame,
                text="Please login to view your hosts",
                font=("TkDefaultFont", 12),
            ).pack(pady=(0, 20))

            ttk.Button(message_frame, text="Login", command=self._auto_login).pack()

            self.status_label.config(text="Not authenticated")
            return

        try:
            self.status_label.config(text="Loading assignments...")
            self.update()

            assignments_data = self._fetch_assignments()

            if not assignments_data:
                ttk.Label(
                    self.content_frame,
                    text="No active assignments\n\nGo to Schedule view to reserve hosts",
                    font=("TkDefaultFont", 12),
                    justify=tk.CENTER,
                ).pack(pady=50)
                self.status_label.config(text="No assignments found")
                return

            for assignment in assignments_data:
                self._create_assignment_panel(assignment)

            self.status_label.config(text=f"Showing {len(assignments_data)} assignment(s) | Last updated: Just now")

        except Exception as e:
            error_label = ttk.Label(
                self.content_frame,
                text=f"Error loading assignments:\n{str(e)}",
                foreground="red",
            )
            error_label.pack(pady=50)
            self.status_label.config(text="Error loading data")

    def _fetch_assignments(self):
        """Fetch assignments from the server via CLI command"""
        assignments_data = []

        try:
            user_assignments = self.shell.connection.api.filter_assignments({"owner": self.shell.connection.username})

            if not user_assignments:
                return []

            for assignment in user_assignments:
                if isinstance(assignment, dict):
                    assignment_id = assignment.get("_id") or assignment.get("id")
                    cloud = assignment.get("cloud", {})
                    cloud_name = cloud.get("name") if isinstance(cloud, dict) else str(cloud)
                    description = assignment.get("description", "No description")

                    # Fetch schedules by assignment_id (not cloud - API doesn't support that filter)
                    schedules = self.shell.connection.api.get_schedules({"assignment_id": int(assignment_id)})

                    hosts = []
                    for schedule in schedules if schedules else []:
                        if isinstance(schedule, dict):
                            hostname = schedule.get("host", {})
                            if isinstance(hostname, dict):
                                hostname = hostname.get("name", "")

                            # TODO: When QUADS server adds validation/provisioning status API,
                            # pull actual status instead of defaulting to "provisioning"
                            # For now, mark as provisioning with N/A progress until we have
                            # proper validation polling support
                            hosts.append({"name": str(hostname), "status": "provisioning", "progress": "N/A"})

                    assignments_data.append(
                        {
                            "id": assignment_id,
                            "cloud": cloud_name,
                            "description": description,
                            "created": "N/A",
                            "expires": "N/A",
                            "hosts": hosts,
                            "days_remaining": "N/A",
                        }
                    )

        except Exception as e:
            self.shell.perror(f"Failed to fetch assignments: {e}")

        return assignments_data

    def _create_assignment_panel(self, assignment):
        """Create a panel for one assignment"""
        panel = ttk.LabelFrame(
            self.content_frame,
            text=f"Assignment #{assignment['id']}: {assignment['description']}",
            padding=10,
        )
        panel.pack(fill=tk.X, pady=(0, 15))

        info_frame = ttk.Frame(panel)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_text = f"Cloud: {assignment['cloud']} | Created: {assignment['created']} | "
        info_text += f"Expires: {assignment['expires']} ({assignment['days_remaining']} days remaining)"

        ttk.Label(info_frame, text=info_text).pack(side=tk.LEFT)

        tree_frame = ttk.Frame(panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("host", "status", "progress")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=len(assignment["hosts"]))

        tree.heading("host", text="Host")
        tree.heading("status", text="Status")
        tree.heading("progress", text="Progress")

        tree.column("host", width=250)
        tree.column("status", width=120)
        tree.column("progress", width=150)

        for host in assignment["hosts"]:
            status_icon = self._get_status_icon(host["status"])
            progress_bar = self._get_progress_bar(host["progress"])

            item_id = tree.insert(
                "",
                tk.END,
                values=(host["name"], f"{status_icon} {host['status'].capitalize()}", progress_bar),
            )

            if host["status"] == "active":
                tree.item(item_id, tags=("active",))
                tree.tag_configure("active", foreground=self.shell.gui_app.theme_manager.get_color("success"))
            elif host["status"] == "provisioning":
                tree.item(item_id, tags=("provisioning",))
                tree.tag_configure(
                    "provisioning", foreground=self.shell.gui_app.theme_manager.get_color("provisioning")
                )
            elif host["status"] == "failed":
                tree.item(item_id, tags=("failed",))
                tree.tag_configure("failed", foreground=self.shell.gui_app.theme_manager.get_color("error"))

        tree.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(panel)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Terminate Assignment",
            command=lambda: self._terminate_assignment(assignment["id"]),
        ).pack(side=tk.LEFT)

    def _get_status_icon(self, status):
        """Get status icon for host"""
        icons = {
            "active": "✓",
            "provisioning": "⏳",
            "queued": "○",
            "failed": "✗",
        }
        return icons.get(status, "○")

    def _get_progress_bar(self, progress):
        """Get text progress bar"""
        if progress == "N/A":
            return "░" * 10 + " N/A"
        filled = int(progress / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty + f" {progress}%"

    def _terminate_assignment(self, assignment_id):
        """Terminate an assignment"""
        # Check if we should confirm
        prefs = self._get_preferences()
        if prefs.get("confirm_terminate", True):
            if not messagebox.askyesno(
                "Confirm Termination",
                f"Are you sure you want to terminate assignment #{assignment_id}?\n\n"
                "This will release all hosts in this assignment.",
            ):
                return

        try:
            # Set GUI mode to bypass terminal confirmation prompt
            old_gui_mode = getattr(self.shell, "gui_mode", False)
            self.shell.gui_mode = True

            try:
                self.shell.user_commands.cmd_terminate(str(assignment_id))
                messagebox.showinfo(
                    "Success",
                    f"Assignment #{assignment_id} terminated\n\n"
                    "Note: It may take a few moments for the termination to complete.",
                )
                self._load_assignments()
            finally:
                # Restore original gui_mode
                self.shell.gui_mode = old_gui_mode

        except Exception as e:
            import traceback

            details = traceback.format_exc()
            show_error_dialog(self, "Termination Failed", str(e), details)

    def _manual_refresh(self):
        """Manual refresh triggered by button"""
        self._load_assignments()

    def _toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        self.auto_refresh_enabled = self.auto_refresh_var.get()
        if self.auto_refresh_enabled:
            self._schedule_auto_refresh()

    def _schedule_auto_refresh(self):
        """Schedule automatic refresh"""
        if self.auto_refresh_enabled and self.winfo_exists():
            self._load_assignments()
            self.after(self.refresh_interval, self._schedule_auto_refresh)

    def refresh(self):
        """Public method to refresh the view"""
        self._load_assignments()

    def apply_preferences(self, preferences):
        """Apply updated preferences"""
        # Update interval
        new_interval = preferences.get("auto_refresh_interval", 30) * 1000
        if new_interval != self.refresh_interval:
            self.refresh_interval = new_interval
            interval_sec = self.refresh_interval // 1000
            self.auto_refresh_check.config(text=f"Auto-refresh ({interval_sec}s)")

        # Update enabled state
        new_enabled = preferences.get("auto_refresh_my_hosts", True)
        if new_enabled != self.auto_refresh_enabled:
            self.auto_refresh_enabled = new_enabled
            self.auto_refresh_var.set(new_enabled)
            if new_enabled:
                self._schedule_auto_refresh()
