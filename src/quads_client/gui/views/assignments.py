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

        # Action button
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
            # Use short username (without @domain.com) and filter for active assignments
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

    def refresh(self):
        """Public method to refresh the view"""
        self._load_assignments()
