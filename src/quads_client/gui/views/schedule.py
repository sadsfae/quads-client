"""Schedule view for self-service scheduling (SSM users)"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from quads_client.gui.widgets.dialogs import show_error_dialog


class ScheduleView(ttk.Frame):
    """View for scheduling hosts (SSM mode)"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell

        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        title_label = ttk.Label(
            self, text="Schedule Hosts", font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(pady=20, padx=20, anchor=tk.W)

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        ttk.Label(
            main_frame,
            text="How many hosts do you need?",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 10))

        self.mode_var = tk.StringVar(value="count")

        mode_frame = ttk.LabelFrame(main_frame, text="Selection Mode", padding=10)
        mode_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Radiobutton(
            mode_frame,
            text="Specific number of hosts",
            variable=self.mode_var,
            value="count",
            command=self._on_mode_changed,
        ).grid(row=0, column=0, sticky=tk.W, pady=5)

        count_frame = ttk.Frame(mode_frame)
        count_frame.grid(row=0, column=1, padx=20, sticky=tk.W)
        ttk.Label(count_frame, text="Count:").pack(side=tk.LEFT)
        self.count_spinbox = ttk.Spinbox(count_frame, from_=1, to=50, width=10)
        self.count_spinbox.set(3)
        self.count_spinbox.pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            mode_frame,
            text="Specific hostnames",
            variable=self.mode_var,
            value="hosts",
            command=self._on_mode_changed,
        ).grid(row=1, column=0, sticky=tk.W, pady=5)

        self.hosts_entry = ttk.Entry(mode_frame, width=40, state=tk.DISABLED)
        self.hosts_entry.grid(row=1, column=1, padx=20, sticky=tk.W)
        self.hosts_entry.insert(0, "host01.example.com,host02.example.com")

        ttk.Radiobutton(
            mode_frame,
            text="Host list from file",
            variable=self.mode_var,
            value="file",
            command=self._on_mode_changed,
        ).grid(row=2, column=0, sticky=tk.W, pady=5)

        file_frame = ttk.Frame(mode_frame)
        file_frame.grid(row=2, column=1, padx=20, sticky=tk.W)
        self.file_entry = ttk.Entry(file_frame, width=30, state=tk.DISABLED)
        self.file_entry.pack(side=tk.LEFT)
        self.browse_button = ttk.Button(
            file_frame, text="Browse...", command=self._browse_file, state=tk.DISABLED
        )
        self.browse_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(main_frame, text="Description:", font=("TkDefaultFont", 10)).pack(
            anchor=tk.W, pady=(10, 5)
        )
        self.description_entry = ttk.Entry(main_frame, width=50)
        self.description_entry.pack(fill=tk.X, pady=(0, 20))
        self.description_entry.insert(0, "Development testing environment")

        self.advanced_var = tk.BooleanVar(value=False)
        advanced_check = ttk.Checkbutton(
            main_frame,
            text="Show advanced options ▼",
            variable=self.advanced_var,
            command=self._toggle_advanced,
        )
        advanced_check.pack(anchor=tk.W, pady=(0, 10))

        self.advanced_frame = ttk.LabelFrame(
            main_frame, text="Advanced Options", padding=10
        )

        filters_frame = ttk.Frame(self.advanced_frame)
        filters_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(filters_frame, text="Model:").pack(side=tk.LEFT, padx=(0, 5))
        self.model_combo = ttk.Combobox(
            filters_frame, values=["All", "r640", "r650", "r750"], width=15, state="readonly"
        )
        self.model_combo.set("All")
        self.model_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(filters_frame, text="RAM (GB):").pack(side=tk.LEFT, padx=(20, 5))
        self.ram_combo = ttk.Combobox(
            filters_frame, values=["Any", "64", "128", "256", "512"], width=10, state="readonly"
        )
        self.ram_combo.set("Any")
        self.ram_combo.pack(side=tk.LEFT, padx=5)

        network_frame = ttk.Frame(self.advanced_frame)
        network_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=10)

        ttk.Label(network_frame, text="VLAN ID:").pack(side=tk.LEFT, padx=(0, 5))
        self.vlan_entry = ttk.Entry(network_frame, width=15)
        self.vlan_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(network_frame, text="QinQ:").pack(side=tk.LEFT, padx=(20, 5))
        self.qinq_combo = ttk.Combobox(
            network_frame, values=["Disabled", "0", "1"], width=10, state="readonly"
        )
        self.qinq_combo.set("Disabled")
        self.qinq_combo.pack(side=tk.LEFT, padx=5)

        self.nowipe_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.advanced_frame, text="No wipe (preserve existing data)", variable=self.nowipe_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.X, pady=(20, 20))

        self.preview_text = tk.Text(
            preview_frame, height=5, width=60, wrap=tk.WORD, state=tk.DISABLED
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        self._update_preview()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 20))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(
            button_frame, text="Schedule Now", command=self._schedule
        ).pack(side=tk.RIGHT, padx=5)

    def _on_mode_changed(self):
        """Handle mode change"""
        mode = self.mode_var.get()

        self.count_spinbox.config(state=tk.NORMAL if mode == "count" else tk.DISABLED)
        self.hosts_entry.config(state=tk.NORMAL if mode == "hosts" else tk.DISABLED)
        self.file_entry.config(state=tk.NORMAL if mode == "file" else tk.DISABLED)
        self.browse_button.config(state=tk.NORMAL if mode == "file" else tk.DISABLED)

        self._update_preview()

    def _toggle_advanced(self):
        """Toggle advanced options"""
        if self.advanced_var.get():
            self.advanced_frame.pack(fill=tk.X, pady=(0, 20))
        else:
            self.advanced_frame.pack_forget()

        self._update_preview()

    def _browse_file(self):
        """Browse for host list file"""
        filename = filedialog.askopenfilename(
            title="Select Host List File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            self._update_preview()

    def _update_preview(self):
        """Update preview text"""
        mode = self.mode_var.get()
        description = self.description_entry.get()

        preview = ""
        if mode == "count":
            count = self.count_spinbox.get()
            preview += f"• {count} hosts will be automatically selected\n"
        elif mode == "hosts":
            hosts = self.hosts_entry.get()
            host_list = [h.strip() for h in hosts.split(",") if h.strip()]
            preview += f"• {len(host_list)} specific hosts\n"
        elif mode == "file":
            file_path = self.file_entry.get()
            preview += f"• Hosts from file: {file_path or 'Not selected'}\n"

        preview += "• Cloud will be auto-assigned\n"
        preview += "• Duration: 5 days or until Sunday 21:00 UTC\n"
        preview += "• Assignment will be activated immediately\n"

        if self.advanced_var.get():
            if self.model_combo.get() != "All":
                preview += f"• Filter: Model {self.model_combo.get()}\n"
            if self.ram_combo.get() != "Any":
                preview += f"• Filter: RAM >= {self.ram_combo.get()} GB\n"
            if self.vlan_entry.get():
                preview += f"• VLAN: {self.vlan_entry.get()}\n"
            if self.qinq_combo.get() != "Disabled":
                preview += f"• QinQ: {self.qinq_combo.get()}\n"
            if self.nowipe_var.get():
                preview += "• No wipe (data will be preserved)\n"

        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", preview)
        self.preview_text.config(state=tk.DISABLED)

    def _schedule(self):
        """Perform the scheduling"""
        if not self.shell.is_authenticated():
            messagebox.showerror("Error", "You must be logged in to schedule hosts")
            return

        description = self.description_entry.get().strip()
        if not description:
            messagebox.showerror("Error", "Description is required")
            return

        mode = self.mode_var.get()
        args = ""

        if mode == "count":
            count = self.count_spinbox.get()
            args = f"{count}"
        elif mode == "hosts":
            hosts = self.hosts_entry.get().strip()
            if not hosts:
                messagebox.showerror("Error", "Hostnames are required")
                return
            args = hosts
        elif mode == "file":
            file_path = self.file_entry.get().strip()
            if not file_path:
                messagebox.showerror("Error", "Please select a host list file")
                return
            args = f"host-list {file_path}"

        args += f' description "{description}"'

        if self.advanced_var.get():
            if self.model_combo.get() != "All":
                args += f" model {self.model_combo.get()}"
            if self.ram_combo.get() != "Any":
                args += f" ram {self.ram_combo.get()}"
            if self.vlan_entry.get():
                args += f" vlan {self.vlan_entry.get()}"
            if self.qinq_combo.get() != "Disabled":
                args += f" qinq {self.qinq_combo.get()}"
            if self.nowipe_var.get():
                args += " nowipe"

        try:
            self.shell.user_commands.cmd_schedule(args)
            messagebox.showinfo(
                "Success",
                "Hosts scheduled successfully!\n\n"
                "View your assignments in the 'My Hosts' tab.",
            )
            self._reset_form()
        except Exception as e:
            import traceback
            details = traceback.format_exc()
            show_error_dialog(self, "Scheduling Failed", str(e), details)

    def _reset_form(self):
        """Reset the form to defaults"""
        self.mode_var.set("count")
        self.count_spinbox.set(3)
        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, "Development testing environment")
        self.model_combo.set("All")
        self.ram_combo.set("Any")
        self.vlan_entry.delete(0, tk.END)
        self.qinq_combo.set("Disabled")
        self.nowipe_var.set(False)
        self.advanced_var.set(False)
        self.advanced_frame.pack_forget()
        self._on_mode_changed()

    def _cancel(self):
        """Cancel scheduling"""
        self._reset_form()

    def refresh(self):
        """Public method to refresh the view"""
        self._update_preview()
