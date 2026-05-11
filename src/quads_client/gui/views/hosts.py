"""Hosts view - admin host management (refactored with DRY principles)"""

import tkinter as tk
from tkinter import ttk

from quads_client.gui.widgets.base import BaseAdminView, ScrolledTreeview


class HostsView(BaseAdminView):
    """View for managing hosts (admin only)"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Host Management", requires_admin=True)
        self.filter_mode = "active"  # Default to active (not broken, not retired)
        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        # Header with refresh button
        self.create_header([("🔄 Refresh", self._load_hosts)])

        # Filter buttons
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 10))

        for label, mode in [
            ("Active", "active"),
            ("All Hosts", "all"),
            ("Broken", "broken"),
            ("Retired", "retired"),
        ]:
            ttk.Button(filter_frame, text=label, command=lambda m=mode: self._set_filter(m)).pack(side=tk.LEFT, padx=2)

        # Content frame with scrolled treeview
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("name", "model", "default_cloud", "type", "broken", "retired")
        column_configs = {
            "name": ("Name", 200),
            "model": ("Model", 100),
            "default_cloud": ("Default Cloud", 120),
            "type": ("Type", 100),
            "broken": ("Broken", 80),
            "retired": ("Retired", 80),
        }

        self.tree = ScrolledTreeview(content_frame, columns, column_configs)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        self.create_action_bar(
            [
                ("Mark Broken", self._mark_broken),
                ("Mark Repaired", self._mark_repaired),
                ("Retire", self._retire),
                ("Un-retire", self._unretire),
            ]
        )

        # Status label
        self.create_status_label()

        # Initial load
        self._load_hosts()

    def _set_filter(self, mode):
        """Set filter mode and reload"""
        self.filter_mode = mode
        self._load_hosts()

    def _load_hosts(self):
        """Load hosts from server"""

        def load_data():
            if self.filter_mode == "active":
                # Default: show only active hosts (not broken, not retired)
                return self.shell.connection.api.filter_hosts({"broken": False, "retired": False})
            elif self.filter_mode == "all":
                return self.shell.connection.api.get_hosts()
            elif self.filter_mode == "broken":
                return self.shell.connection.api.filter_hosts({"broken": True})
            elif self.filter_mode == "retired":
                return self.shell.connection.api.filter_hosts({"retired": True})
            return []

        self.tree.clear()
        hosts = self.safe_load_data(load_data, success_message="Showing {count} host(s)")

        if not hosts:
            return

        for host in hosts:
            name = host.get("name", "")
            model = host.get("model", "")
            default_cloud = host.get("default_cloud", {})
            if isinstance(default_cloud, dict):
                default_cloud = default_cloud.get("name", "")
            host_type = host.get("host_type", "")
            broken = "Yes" if host.get("broken", False) else "No"
            retired = "Yes" if host.get("retired", False) else "No"

            item_id = self.tree.insert(
                "",
                tk.END,
                values=(name, model, default_cloud, host_type, broken, retired),
            )

            # Color code
            if host.get("broken", False):
                self.tree.tree.item(item_id, tags=("broken",))
                self.tree.tree.tag_configure(
                    "broken", foreground=self.shell.gui_app.theme_manager.get_color("error")
                )
            elif host.get("retired", False):
                self.tree.tree.item(item_id, tags=("retired",))
                self.tree.tree.tag_configure("retired", foreground="#999999")

        # Update status with filter info
        filter_text = f" ({self.filter_mode})" if self.filter_mode != "active" else ""
        self.update_status(f"Showing {len(hosts)} host(s){filter_text} | Last updated: Just now")

    def _mark_broken(self):
        """Mark selected host as broken"""
        _, values = self.get_selected_item("Please select a host to mark as broken")
        if not values:
            return

        hostname = values[0]
        if not self.confirm_action(
            "Confirm", f"Mark host '{hostname}' as broken?\n\n" "This will prevent it from being scheduled."
        ):
            return

        self.safe_execute(
            lambda: self.shell.host_commands.cmd_mark_broken(hostname),
            f"Host '{hostname}' marked as broken",
            "Mark Broken Failed",
            self._load_hosts,
        )

    def _mark_repaired(self):
        """Mark selected host as repaired"""
        _, values = self.get_selected_item("Please select a host to mark as repaired")
        if not values:
            return

        hostname = values[0]
        self.safe_execute(
            lambda: self.shell.host_commands.cmd_mark_repaired(hostname),
            f"Host '{hostname}' marked as repaired",
            "Mark Repaired Failed",
            self._load_hosts,
        )

    def _retire(self):
        """Mark selected host as retired"""
        _, values = self.get_selected_item("Please select a host to retire")
        if not values:
            return

        hostname = values[0]
        if not self.confirm_action(
            "Confirm", f"Retire host '{hostname}'?\n\n" "This will remove it from the active pool."
        ):
            return

        self.safe_execute(
            lambda: self.shell.host_commands.cmd_retire(hostname),
            f"Host '{hostname}' retired",
            "Retire Failed",
            self._load_hosts,
        )

    def _unretire(self):
        """Mark selected host as active"""
        _, values = self.get_selected_item("Please select a host to un-retire")
        if not values:
            return

        hostname = values[0]
        self.safe_execute(
            lambda: self.shell.host_commands.cmd_unretire(hostname),
            f"Host '{hostname}' is now active",
            "Un-retire Failed",
            self._load_hosts,
        )

    def refresh(self):
        """Public method to refresh the view"""
        self._load_hosts()
