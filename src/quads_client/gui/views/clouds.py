"""Clouds view - admin cloud management (refactored with DRY principles)"""

import tkinter as tk
from tkinter import ttk, messagebox

from quads_client.gui.widgets.base import BaseAdminView, ScrolledTreeview, FormDialog


class CloudsView(BaseAdminView):
    """View for managing clouds (admin only)"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Cloud Management", requires_admin=True)
        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        # Header with buttons
        self.create_header(
            [
                ("➕ Create Cloud", self._create_cloud),
                ("🔄 Refresh", self._load_clouds),
            ]
        )

        # Content frame with scrolled treeview
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("cloud", "assignment", "owner", "description", "vlan", "wipe")
        column_configs = {
            "cloud": ("Cloud", 100),
            "assignment": ("Assignment", 100),
            "owner": ("Owner", 120),
            "description": ("Description", 300),
            "vlan": ("VLAN", 80),
            "wipe": ("Wipe", 60),
        }

        self.tree = ScrolledTreeview(content_frame, columns, column_configs)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        self.create_action_bar(
            [
                ("View Details", self._view_details),
                ("Modify Cloud", self._modify_cloud),
                ("Delete Cloud", self._delete_cloud),
                ("Find Free Clouds", self._find_free),
            ]
        )

        # Status label
        self.create_status_label()

        # Initial load
        self._load_clouds()

    def _load_clouds(self):
        """Load clouds from server"""

        def load_data():
            return self.shell.connection.api.get_clouds()

        self.tree.clear()
        clouds = self.safe_load_data(load_data, success_message="Showing {count} cloud(s)")

        if not clouds:
            return

        for cloud in clouds:
            cloud_name = cloud.get("name", "")
            assignment_id = "-"
            owner = "-"
            description = "-"
            vlan = "-"
            wipe = "No"

            try:
                assignment = self.shell.connection.api.get_active_cloud_assignment(cloud_name)
                if assignment and isinstance(assignment, dict):
                    assignment_id = str(assignment.get("id", "-"))
                    owner = assignment.get("owner", "-") or "-"
                    desc_full = assignment.get("description", "-") or "-"
                    description = desc_full[:40] if len(desc_full) > 40 else desc_full
                    wipe = "Yes" if assignment.get("wipe", False) else "No"

                    vlan_obj = assignment.get("vlan")
                    if isinstance(vlan_obj, dict):
                        vlan = str(vlan_obj.get("vlan_id", "-"))
                    elif vlan_obj:
                        vlan = str(vlan_obj)
            except Exception:
                pass

            self.tree.insert(
                "",
                tk.END,
                values=(cloud_name, assignment_id, owner, description, vlan, wipe),
            )

    def _create_cloud(self):
        """Create a new cloud"""
        dialog = self.create_simple_dialog("Create Cloud", "400x150")

        ttk.Label(dialog, text="Cloud Name:").pack(pady=10, padx=20, anchor=tk.W)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(padx=20, fill=tk.X)
        name_entry.focus()

        def on_create():
            cloud_name = name_entry.get().strip()
            if not cloud_name:
                messagebox.showerror("Error", "Cloud name is required", parent=dialog)
                return

            self.safe_execute(
                lambda: self.shell.cloud_commands.cmd_cloud_create(cloud_name),
                f"Cloud '{cloud_name}' created",
                "Create Cloud Failed",
                self._load_clouds,
            )
            dialog.destroy()

        FormDialog.create_button_row(
            dialog,
            [
                ("Cancel", dialog.destroy),
                ("Create", on_create),
            ],
        )

    def _delete_cloud(self):
        """Delete selected cloud"""
        _, values = self.get_selected_item("Please select a cloud to delete")
        if not values:
            return

        cloud_name = values[0]
        if not self.confirm_action(
            "Confirm Deletion",
            f"Are you sure you want to delete cloud '{cloud_name}'?\n\n" "This action cannot be undone.",
        ):
            return

        self.safe_execute(
            lambda: self.shell.cloud_commands.cmd_cloud_delete(cloud_name),
            f"Cloud '{cloud_name}' deleted",
            "Delete Cloud Failed",
            self._load_clouds,
        )

    def _modify_cloud(self):
        """Modify selected cloud assignment"""
        _, values = self.get_selected_item("Please select a cloud to modify")
        if not values:
            return

        cloud_name = values[0]
        dialog = self.create_simple_dialog(f"Modify Cloud: {cloud_name}", "500x400")

        ttk.Label(
            dialog,
            text=f"Modify assignment attributes for {cloud_name}",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(pady=10, padx=20)

        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create form fields
        desc_entry = FormDialog.create_labeled_entry(form_frame, "Description:", 0, 40)
        owner_entry = FormDialog.create_labeled_entry(form_frame, "Cloud Owner:", 1, 40)
        ticket_entry = FormDialog.create_labeled_entry(form_frame, "Ticket ID:", 2, 40)
        cc_entry = FormDialog.create_labeled_entry(form_frame, "CC Users:", 3, 40)
        vlan_entry = FormDialog.create_labeled_entry(form_frame, "VLAN ID:", 4, 40)

        ttk.Label(form_frame, text="QinQ:").grid(row=5, column=0, sticky=tk.W, pady=5)
        qinq_combo = ttk.Combobox(form_frame, values=["0", "1"], width=37, state="readonly")
        qinq_combo.set("0")
        qinq_combo.grid(row=5, column=1, pady=5, sticky=tk.W)

        wipe_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_frame, text="Enable wipe", variable=wipe_var).grid(row=6, column=1, sticky=tk.W, pady=5)

        def on_modify():
            args = cloud_name

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
            if wipe_var.get():
                args += " wipe"

            if args == cloud_name:
                messagebox.showwarning("No Changes", "No modifications specified", parent=dialog)
                return

            self.safe_execute(
                lambda: self.shell.cloud_commands.cmd_mod_cloud(args),
                f"Cloud '{cloud_name}' modified",
                "Modify Cloud Failed",
                self._load_clouds,
            )
            dialog.destroy()

        FormDialog.create_button_row(
            dialog,
            [
                ("Cancel", dialog.destroy),
                ("Modify", on_modify),
            ],
        )

    def _view_details(self):
        """View detailed information for selected cloud"""
        _, values = self.get_selected_item("Please select a cloud to view")
        if not values:
            return

        cloud_name = values[0]
        self.safe_execute(
            lambda: self.shell.cloud_commands.cmd_cloud_list(f"cloud {cloud_name} detail"),
            "",  # No success message needed
            "View Details Failed",
        )

    def _find_free(self):
        """Find free clouds"""
        self.safe_execute(
            lambda: self.shell.cloud_commands.cmd_find_free_cloud(""),
            "",  # No success message needed
            "Find Free Clouds Failed",
        )

    def refresh(self):
        """Public method to refresh the view"""
        self._load_clouds()
