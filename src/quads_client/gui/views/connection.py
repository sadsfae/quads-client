"""Connection and server management view"""

import tkinter as tk
from tkinter import ttk, messagebox

from quads_client.gui.widgets.dialogs import show_error_dialog


class ConnectionView(ttk.Frame):
    """View for managing servers and connections"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self.selected_server = None

        self._create_ui()
        self._refresh_server_list()

    def _create_ui(self):
        """Create the UI"""
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=20, pady=10)

        title_label = ttk.Label(
            title_frame,
            text="Servers & Connections",
            font=("TkDefaultFont", 14, "bold"),
        )
        title_label.pack(side=tk.LEFT)

        ttk.Button(title_frame, text="+ Add Server", command=self._add_server).pack(side=tk.RIGHT)

        ttk.Button(title_frame, text="🔄 Refresh", command=self._refresh_server_list).pack(side=tk.RIGHT, padx=5)

        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        ttk.Label(content_frame, text="Configured Servers:", font=("TkDefaultFont", 10)).pack(anchor=tk.W, pady=(0, 5))

        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.server_tree = ttk.Treeview(
            tree_frame,
            columns=("name", "url", "status"),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=8,
        )
        scrollbar.config(command=self.server_tree.yview)

        self.server_tree.heading("name", text="Name")
        self.server_tree.heading("url", text="URL")
        self.server_tree.heading("status", text="Status")

        self.server_tree.column("name", width=150)
        self.server_tree.column("url", width=300)
        self.server_tree.column("status", width=100)

        self.server_tree.pack(fill=tk.BOTH, expand=True)
        self.server_tree.bind("<<TreeviewSelect>>", self._on_server_selected)

        details_frame = ttk.LabelFrame(content_frame, text="Server Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(20, 10))

        self.details_text = tk.Text(details_frame, height=8, width=60, wrap=tk.WORD, state=tk.DISABLED, bg="white")
        self.details_text.pack(fill=tk.BOTH, expand=True)

        self.details_text.tag_config("connected", foreground="#4ec9b0")
        self.details_text.tag_config("disconnected", foreground="gray")

        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.connect_button = ttk.Button(button_frame, text="Connect", command=self._connect_server, state=tk.DISABLED)
        self.connect_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self._disconnect_server,
            state=tk.DISABLED,
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Edit", command=self._edit_server, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Remove", command=self._remove_server, state=tk.DISABLED).pack(
            side=tk.LEFT, padx=5
        )

        sessions_frame = ttk.LabelFrame(content_frame, text="Active Sessions", padding=10)
        sessions_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.sessions_tree = ttk.Treeview(
            sessions_frame,
            columns=("id", "server", "label", "status", "last_active"),
            show="headings",
            height=4,
        )

        self.sessions_tree.heading("id", text="ID")
        self.sessions_tree.heading("server", text="Server")
        self.sessions_tree.heading("label", text="Label")
        self.sessions_tree.heading("status", text="Status")
        self.sessions_tree.heading("last_active", text="Last Active")

        self.sessions_tree.column("id", width=50)
        self.sessions_tree.column("server", width=150)
        self.sessions_tree.column("label", width=100)
        self.sessions_tree.column("status", width=100)
        self.sessions_tree.column("last_active", width=100)

        self.sessions_tree.pack(fill=tk.BOTH, expand=True)

        session_button_frame = ttk.Frame(sessions_frame)
        session_button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(session_button_frame, text="Switch", command=self._switch_session).pack(side=tk.LEFT, padx=5)

        ttk.Button(session_button_frame, text="Close Session", command=self._close_session).pack(side=tk.LEFT, padx=5)

    def _refresh_server_list(self):
        """Refresh the server list"""
        for item in self.server_tree.get_children():
            self.server_tree.delete(item)

        if not self.shell.config:
            return

        servers = self.shell.config.get_all_servers()
        for name, server_config in servers.items():
            url = server_config.get("url", "")

            is_connected = False
            if self.shell.session_manager:
                for session in self.shell.session_manager.sessions.values():
                    if session.connection and session.connection.current_server == name:
                        is_connected = True
                        break

            status = "● Connected" if is_connected else "○ Disconnected"

            item_id = self.server_tree.insert("", tk.END, values=(name, url, status))

            if is_connected and self.shell.session_manager.active_session:
                if self.shell.session_manager.active_session.connection.current_server == name:
                    self.server_tree.item(item_id, tags=("active",))
                    self.server_tree.tag_configure("active", foreground="#4ec9b0", font=("TkDefaultFont", 9, "bold"))

        self._refresh_session_list()

    def _refresh_session_list(self):
        """Refresh the session list"""
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)

        if not self.shell.session_manager:
            return

        active_id = self.shell.session_manager.active_session_id if self.shell.session_manager.active_session else None

        for session_id, session in self.shell.session_manager.sessions.items():
            server_name = session.connection.current_server if session.connection else "N/A"
            label = session.label or "-"
            status = "Active" if session_id == active_id else "Inactive"
            last_active = "Just now" if session_id == active_id else "N/A"

            session_marker = f"{session_id} (*)" if session_id == active_id else str(session_id)

            item_id = self.sessions_tree.insert(
                "", tk.END, values=(session_marker, server_name, label, status, last_active)
            )

            if session_id == active_id:
                self.sessions_tree.item(item_id, tags=("active",))
                self.sessions_tree.tag_configure("active", foreground="#4ec9b0", font=("TkDefaultFont", 9, "bold"))

    def _on_server_selected(self, event):
        """Handle server selection"""
        selection = self.server_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.server_tree.item(item, "values")
        server_name = values[0]

        self.selected_server = server_name
        self._update_server_details()

    def _update_server_details(self):
        """Update server details display"""
        if not self.selected_server or not self.shell.config:
            return

        try:
            server_config = self.shell.config.get_server(self.selected_server)
        except Exception:
            server_config = {}

        url = server_config.get("url", "N/A")
        verify = server_config.get("verify", True)

        is_connected = False
        user = "N/A"
        role = "N/A"
        if self.shell.session_manager:
            for session in self.shell.session_manager.sessions.values():
                if session.connection and session.connection.current_server == self.selected_server:
                    is_connected = True
                    if session.connection.username:
                        user = session.connection.username
                    if session.connection.user_role:
                        role = session.connection.user_role.capitalize()
                    elif session.connection.is_authenticated:
                        role = "User"
                    break

        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)

        self.details_text.insert(tk.END, f"URL: {url}\n")
        self.details_text.insert(tk.END, f"SSL Verification: {'Enabled' if verify else 'Disabled'}\n")
        self.details_text.insert(tk.END, "Status: ")

        status_tag = "connected" if is_connected else "disconnected"
        status_text = "Connected" if is_connected else "Disconnected"
        self.details_text.insert(tk.END, status_text + "\n", status_tag)

        if is_connected:
            self.details_text.insert(tk.END, f"User: {user}\n")
            self.details_text.insert(tk.END, f"Role: {role}\n")

        self.details_text.config(state=tk.DISABLED)

        self.connect_button.config(state=tk.NORMAL if not is_connected else tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL if is_connected else tk.DISABLED)

    def _add_server(self):
        """Add a new server"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Server")
        dialog.geometry("450x380")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Apply theme colors to dialog
        if hasattr(self.shell, "gui_app") and hasattr(self.shell.gui_app, "theme_manager"):
            self.shell.gui_app.theme_manager.configure_toplevel(dialog)

        ttk.Label(dialog, text="Server Name:").grid(row=0, column=0, sticky=tk.W, padx=20, pady=8)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=20, pady=8)

        ttk.Label(dialog, text="Server URL:").grid(row=1, column=0, sticky=tk.W, padx=20, pady=8)
        url_entry = ttk.Entry(dialog, width=30)
        url_entry.grid(row=1, column=1, padx=20, pady=8)
        url_entry.insert(0, "https://")

        ttk.Label(dialog, text="Username:").grid(row=2, column=0, sticky=tk.W, padx=20, pady=8)
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.grid(row=2, column=1, padx=20, pady=8)

        ttk.Label(dialog, text="Password:").grid(row=3, column=0, sticky=tk.W, padx=20, pady=8)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.grid(row=3, column=1, padx=20, pady=8)

        verify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Verify SSL certificate", variable=verify_var).grid(
            row=4, column=1, sticky=tk.W, padx=20, pady=8
        )

        # Tip label
        tip_label = ttk.Label(
            dialog,
            text="💡 Username and password can be left blank.\nYou'll be prompted to login after connecting.",
            font=("TkDefaultFont", 8),
            foreground="gray",
            justify=tk.LEFT,
        )
        tip_label.grid(row=5, column=0, columnspan=2, padx=20, pady=(2, 8), sticky=tk.W)

        def save_server():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            username = username_entry.get().strip()
            password = password_entry.get()

            if not name or not url:
                messagebox.showerror("Error", "Name and URL are required")
                return

            # Use empty credentials if not provided (triggers registration mode)
            user = username if username else ""
            pwd = password if password else ""

            # Use programmatic server add method (DRY - reuses CLI logic)
            success, message, version_info = self.shell.server_commands.add_server_programmatic(
                name=name,
                url=url,
                username=user,
                password=pwd,
                verify=verify_var.get(),
                test_connection=True,  # Test before adding
            )

            if not success:
                # Connection test failed - ask if they want to add anyway
                if "Could not connect" in message or "returned status code" in message:
                    result = messagebox.askyesno(
                        "Connection Failed",
                        f"{message}\n\n"
                        f"Add server anyway?\n\n"
                        f"You can try connecting later with different credentials.",
                        icon="warning",
                    )
                    if result:
                        # Try again without connection test
                        success, message, version_info = self.shell.server_commands.add_server_programmatic(
                            name=name,
                            url=url,
                            username=user,
                            password=pwd,
                            verify=verify_var.get(),
                            test_connection=False,  # Skip test this time
                        )
                        if not success:
                            messagebox.showerror("Error", message)
                            return
                    else:
                        return
                else:
                    # Other error (e.g., server already exists)
                    messagebox.showerror("Error", message)
                    return

            self._refresh_server_list()
            dialog.destroy()

            if version_info:
                messagebox.showinfo(
                    "Success", f"Server '{name}' added successfully\n\n" f"QUADS version: {version_info}"
                )
            else:
                messagebox.showinfo(
                    "Server Added",
                    f"Server '{name}' added to configuration\n\n" f"You can now connect to this server.",
                )

        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 15))

        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add", command=save_server).pack(side=tk.LEFT, padx=5)

    def _connect_server(self):
        """Connect to selected server"""
        if not self.selected_server:
            return

        try:
            self.shell.connection_commands.cmd_connect(self.selected_server)
            self._refresh_server_list()
            self._update_server_details()
        except Exception as e:
            import traceback

            details = traceback.format_exc()
            show_error_dialog(self, "Connection Failed", str(e), details)

    def _disconnect_server(self):
        """Disconnect from selected server"""
        try:
            self.shell.connection_commands.cmd_disconnect("")
            self._refresh_server_list()
            self._update_server_details()
            self._on_server_selected(None)
        except Exception as e:
            import traceback

            details = traceback.format_exc()
            show_error_dialog(self, "Disconnect Failed", str(e), details)

    def _edit_server(self):
        """Edit selected server"""
        messagebox.showinfo("Not Implemented", "Edit server functionality coming soon")

    def _remove_server(self):
        """Remove selected server"""
        if not self.selected_server:
            return

        if messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to remove server '{self.selected_server}'?",
        ):
            try:
                self.shell.server_commands.cmd_rm_server(self.selected_server)
                self._refresh_server_list()
                self.selected_server = None
                messagebox.showinfo("Success", "Server removed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove server: {e}")

    def _switch_session(self):
        """Switch to selected session"""
        selection = self.sessions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a session to switch to")
            return

        item = selection[0]
        values = self.sessions_tree.item(item, "values")
        session_id_str = values[0].replace(" (*)", "").strip()

        try:
            session_id = int(session_id_str)
            self.shell.session_commands.cmd_session_switch(str(session_id))
            self._refresh_session_list()
            self._refresh_server_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to switch session: {e}")

    def _close_session(self):
        """Close selected session"""
        selection = self.sessions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a session to close")
            return

        item = selection[0]
        values = self.sessions_tree.item(item, "values")
        session_id_str = values[0].replace(" (*)", "").strip()

        if messagebox.askyesno("Confirm", f"Close session {session_id_str}?"):
            try:
                self.shell.session_commands.cmd_session_close(session_id_str)
                self._refresh_session_list()
                self._refresh_server_list()
            except Exception as e:
                import traceback

                details = traceback.format_exc()
                show_error_dialog(self, "Close Session Failed", str(e), details)

    def refresh(self):
        """Public method to refresh the view"""
        self._refresh_server_list()
