"""My Hosts view - shows user's active assignments and hosts"""

import tkinter as tk
from tkinter import ttk, messagebox

from quads_client.gui.widgets.dialogs import show_error_dialog


class MyHostsView(ttk.Frame):
    """View for displaying user's active hosts and assignments"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self.auto_refresh_enabled = False
        self.refresh_interval = 30000

        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        title_label = ttk.Label(
            header_frame, text="My Hosts", font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)

        ttk.Button(
            header_frame, text="🔄 Refresh", command=self._manual_refresh
        ).pack(side=tk.RIGHT)

        self.auto_refresh_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            header_frame,
            text="Auto-refresh (30s)",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh,
        ).pack(side=tk.RIGHT, padx=10)

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.status_label = ttk.Label(
            self, text="Loading...", font=("TkDefaultFont", 9)
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))

        self._load_assignments()

    def _load_assignments(self):
        """Load user's assignments"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not self.shell.is_authenticated():
            ttk.Label(
                self.content_frame,
                text="Please login to view your hosts",
                font=("TkDefaultFont", 12),
            ).pack(pady=50)
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

            self.status_label.config(
                text=f"Showing {len(assignments_data)} assignment(s) | Last updated: Just now"
            )

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
            user_assignments = self.shell.connection.api.filter_assignments({
                "owner": self.shell.connection.username
            })

            if not user_assignments:
                return []

            for assignment in user_assignments:
                if isinstance(assignment, dict):
                    assignment_id = assignment.get("_id") or assignment.get("id")
                    cloud = assignment.get("cloud", {})
                    cloud_name = cloud.get("name") if isinstance(cloud, dict) else str(cloud)
                    description = assignment.get("description", "No description")

                    schedules = self.shell.connection.api.get_schedules({
                        "cloud": cloud_name
                    })

                    hosts = []
                    for schedule in schedules if schedules else []:
                        if isinstance(schedule, dict):
                            hostname = schedule.get("host", {})
                            if isinstance(hostname, dict):
                                hostname = hostname.get("name", "")

                            hosts.append({
                                "name": str(hostname),
                                "status": "active",
                                "progress": 100
                            })

                    assignments_data.append({
                        "id": assignment_id,
                        "cloud": cloud_name,
                        "description": description,
                        "created": "N/A",
                        "expires": "N/A",
                        "hosts": hosts,
                        "days_remaining": "N/A",
                    })

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
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=len(assignment['hosts']))

        tree.heading("host", text="Host")
        tree.heading("status", text="Status")
        tree.heading("progress", text="Progress")

        tree.column("host", width=250)
        tree.column("status", width=120)
        tree.column("progress", width=150)

        for host in assignment['hosts']:
            status_icon = self._get_status_icon(host['status'])
            progress_bar = self._get_progress_bar(host['progress'])

            item_id = tree.insert(
                "",
                tk.END,
                values=(host['name'], f"{status_icon} {host['status'].capitalize()}", progress_bar),
            )

            if host['status'] == "active":
                tree.item(item_id, tags=("active",))
                tree.tag_configure("active", foreground="#4ec9b0")
            elif host['status'] == "provisioning":
                tree.item(item_id, tags=("provisioning",))
                tree.tag_configure("provisioning", foreground="#dcdcaa")
            elif host['status'] == "failed":
                tree.item(item_id, tags=("failed",))
                tree.tag_configure("failed", foreground="#f48771")

        tree.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(panel)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Terminate Assignment",
            command=lambda: self._terminate_assignment(assignment['id']),
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
        filled = int(progress / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty + f" {progress}%"

    def _terminate_assignment(self, assignment_id):
        """Terminate an assignment"""
        if not messagebox.askyesno(
            "Confirm Termination",
            f"Are you sure you want to terminate assignment #{assignment_id}?\n\n"
            "This will release all hosts in this assignment.",
        ):
            return

        try:
            self.shell.user_commands.cmd_terminate(str(assignment_id))
            messagebox.showinfo(
                "Success",
                f"Assignment #{assignment_id} terminated\n\n"
                "Note: It may take a few moments for the termination to complete."
            )
            self._load_assignments()
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
