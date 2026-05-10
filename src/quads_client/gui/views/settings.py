"""Settings view - application configuration"""

import tkinter as tk
from tkinter import ttk, messagebox


class SettingsView(ttk.Frame):
    """View for application settings"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self.parent = parent

        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        title_label = ttk.Label(
            header_frame, text="Settings", font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Content frame
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Appearance section
        appearance_frame = ttk.LabelFrame(content_frame, text="Appearance", padding=15)
        appearance_frame.pack(fill=tk.X, pady=(0, 15))

        # Theme toggle
        theme_row = ttk.Frame(appearance_frame)
        theme_row.pack(fill=tk.X, pady=5)

        ttk.Label(theme_row, text="Theme:").pack(side=tk.LEFT)

        current_theme = self.shell.gui_app.theme_manager.current_mode
        theme_label = ttk.Label(
            theme_row,
            text=f"{current_theme.capitalize()} Mode",
            font=("TkDefaultFont", 9, "bold")
        )
        theme_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(
            theme_row,
            text="Toggle Theme",
            command=self._toggle_theme
        ).pack(side=tk.LEFT, padx=5)

        # Auto-refresh settings
        refresh_frame = ttk.LabelFrame(content_frame, text="Auto-Refresh", padding=15)
        refresh_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            refresh_frame,
            text="Default auto-refresh is disabled.\n"
            "You can enable it per-view in 'My Hosts' view.",
            foreground="gray"
        ).pack(anchor=tk.W)

        # Connection settings
        conn_frame = ttk.LabelFrame(content_frame, text="Connection", padding=15)
        conn_frame.pack(fill=tk.X, pady=(0, 15))

        servers_row = ttk.Frame(conn_frame)
        servers_row.pack(fill=tk.X, pady=5)

        ttk.Label(servers_row, text="Configured Servers:").pack(side=tk.LEFT)

        server_count = 0
        if self.shell.config:
            servers = self.shell.config.get_all_servers()
            server_count = len(servers)

        ttk.Label(
            servers_row,
            text=str(server_count),
            font=("TkDefaultFont", 9, "bold")
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            servers_row,
            text="Manage Servers",
            command=self._manage_servers
        ).pack(side=tk.LEFT, padx=5)

        # Session info
        session_row = ttk.Frame(conn_frame)
        session_row.pack(fill=tk.X, pady=5)

        ttk.Label(session_row, text="Active Sessions:").pack(side=tk.LEFT)

        session_count = 0
        if self.shell.session_manager:
            session_count = len(self.shell.session_manager.sessions)

        ttk.Label(
            session_row,
            text=str(session_count),
            font=("TkDefaultFont", 9, "bold")
        ).pack(side=tk.LEFT, padx=10)

        # Keyboard shortcuts
        shortcuts_frame = ttk.LabelFrame(content_frame, text="Keyboard Shortcuts", padding=15)
        shortcuts_frame.pack(fill=tk.X, pady=(0, 15))

        import sys
        cmd_key = "Cmd" if sys.platform == "darwin" else "Ctrl"

        shortcuts_text = f"""
{cmd_key}+N     New Session
{cmd_key}+W     Close Session
{cmd_key}+Q     Quit Application
{cmd_key}+T     Toggle Theme
{cmd_key}+R     Refresh View
{cmd_key}+C     Copy to Clipboard
F1         Show Shortcuts Help
"""

        ttk.Label(
            shortcuts_frame,
            text=shortcuts_text.strip(),
            font=("TkMonospace", 9),
            justify=tk.LEFT
        ).pack(anchor=tk.W)

        # About section
        about_frame = ttk.LabelFrame(content_frame, text="About", padding=15)
        about_frame.pack(fill=tk.X, pady=(0, 15))

        from quads_client import __version__

        about_text = ttk.Label(
            about_frame,
            text=f"QUADS Client GUI v{__version__}\n\n"
            "A graphical interface for QUADS\n"
            "(QUADS Automated Deployment System)",
            justify=tk.CENTER
        )
        about_text.pack(pady=5)

        ttk.Button(
            about_frame,
            text="View Full About",
            command=self.shell.gui_app._show_about
        ).pack(pady=5)

        # Config file location
        config_frame = ttk.LabelFrame(content_frame, text="Configuration", padding=15)
        config_frame.pack(fill=tk.X, pady=(0, 15))

        if self.shell.config:
            config_path = self.shell.config.config_path
            ttk.Label(
                config_frame,
                text=f"Config file: {config_path}",
                font=("TkDefaultFont", 8),
                foreground="gray"
            ).pack(anchor=tk.W)

        # Status label
        self.status_label = ttk.Label(self, text="", font=("TkDefaultFont", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))

    def _toggle_theme(self):
        """Toggle theme"""
        new_mode = self.shell.gui_app.theme_manager.toggle_theme()
        self.shell.gui_app.theme_label.config(text=f"Theme: {self.shell.gui_app.theme_manager.get_theme_info()}")
        self.status_label.config(text=f"Theme switched to {new_mode} mode")

        # Refresh the settings view to show updated theme name
        self.refresh()

    def _manage_servers(self):
        """Switch to servers view"""
        self.shell.gui_app._show_servers_view()

    def refresh(self):
        """Public method to refresh the view"""
        # Recreate UI to show latest values
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()
