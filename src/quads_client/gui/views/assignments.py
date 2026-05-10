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
