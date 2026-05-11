"""Main application window for QUADS Client GUI"""

import tkinter as tk
from tkinter import ttk
import webbrowser
import sys

from quads_client import __version__
from quads_client.gui.theme import ThemeManager
from quads_client.gui.controllers.gui_shell import GuiShell
from quads_client.gui.views.onboarding import OnboardingWizard
from quads_client.gui.views.connection import ConnectionView
from quads_client.gui.views.schedule import ScheduleView
from quads_client.gui.views.my_hosts import MyHostsView
from quads_client.gui.views.assignments import AssignmentsView
from quads_client.gui.views.clouds import CloudsView
from quads_client.gui.views.hosts import HostsView
from quads_client.gui.views.admin_schedule import AdminScheduleView
from quads_client.gui.views.available import AvailableView
from quads_client.gui.views.settings import SettingsView
from quads_client.gui.views.preferences import PreferencesDialog


class QuadsClientApp(tk.Tk):
    """Main QUADS Client GUI application"""

    def __init__(self):
        super().__init__()

        self.title(f"QUADS Client v{__version__}")

        self.is_macos = sys.platform == "darwin"

        # Set window icon
        self._set_window_icon()

        self.theme_manager = ThemeManager(self, initial_theme="dark")

        self.sidebar_visible = True

        self.shell = GuiShell(self)

        # Load preferences
        self.preferences = self._load_preferences()

        # Apply window size and position
        self._apply_window_preferences()

        # Apply font size from preferences
        self._apply_font_preferences()

        self._create_menu_bar()
        self._create_status_bar()
        self._create_main_layout()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._check_first_launch()

        # Auto-connect if enabled
        self.after(500, self._auto_connect_on_startup)

    def _create_menu_bar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        cmd_key = "Cmd" if self.is_macos else "Ctrl"

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self._new_session, accelerator=f"{cmd_key}+N")
        file_menu.add_command(label="Close Session", command=self._close_session, accelerator=f"{cmd_key}+W")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing, accelerator=f"{cmd_key}+Q")

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences", command=self._show_preferences)
        edit_menu.add_command(label="Toggle Theme", command=self._toggle_theme, accelerator=f"{cmd_key}+T")

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self._refresh_view, accelerator=f"{cmd_key}+R")
        view_menu.add_command(label="Toggle Sidebar", command=self._toggle_sidebar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Setup Wizard", command=self._show_onboarding)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._open_documentation)
        help_menu.add_command(label="Report Issue", command=self._report_issue)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts, accelerator="F1")

        self._bind_keyboard_shortcuts()

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts (cross-platform)"""
        modifier = "Command" if self.is_macos else "Control"

        self.bind(f"<{modifier}-n>", lambda e: self._new_session())
        self.bind(f"<{modifier}-w>", lambda e: self._close_session())
        self.bind(f"<{modifier}-q>", lambda e: self._on_closing())
        self.bind(f"<{modifier}-t>", lambda e: self._toggle_theme())
        self.bind(f"<{modifier}-r>", lambda e: self._refresh_view())
        self.bind("<F1>", lambda e: self._show_shortcuts())

    def _create_main_layout(self):
        """Create the main layout with sidebar and content area"""
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        self.sidebar_frame = ttk.Frame(main_container, width=200)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

        separator = ttk.Separator(main_container, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y)

        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._create_sidebar()
        self._create_content_area()
        self._create_views()

    def _create_sidebar(self):
        """Create navigation sidebar"""
        title_label = ttk.Label(
            self.sidebar_frame,
            text="QUADS Client",
            font=("TkDefaultFont", 12, "bold"),
        )
        title_label.pack(pady=10, padx=10)

        ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)

        # Store navigation items with admin flag
        nav_items = [
            ("📡 Servers", self._show_servers_view, False),
            ("📅 Schedule", self._show_schedule_view, False),
            ("📊 Available", self._show_available_view, False),
            ("💻 My Hosts", self._show_my_hosts_view, False),
            ("📋 Assignments", self._show_assignments_view, False),
            ("", None, False),  # Separator
            ("👑 Admin Schedule", self._show_admin_schedule_view, True),
            ("☁️  Clouds", self._show_clouds_view, True),
            ("🖥️  Hosts", self._show_hosts_view, True),
            ("", None, False),  # Separator
            ("⚙️  Settings", self._show_settings_view, False),
        ]

        self.nav_buttons = []
        for label, command, is_admin in nav_items:
            if label == "":  # Separator
                ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
                continue

            btn = ttk.Button(
                self.sidebar_frame,
                text=label,
                command=command,
                width=18,
            )
            btn.pack(pady=2, padx=10, fill=tk.X)
            self.nav_buttons.append((btn, is_admin))

    def _create_content_area(self):
        """Create main content area"""
        pass

    def _create_views(self):
        """Create all view instances"""
        self.views = {}
        self.current_view = None

        self.views["welcome"] = self._create_welcome_view()
        self.views["servers"] = ConnectionView(self.content_frame, self.shell)
        self.views["schedule"] = ScheduleView(self.content_frame, self.shell)
        self.views["available"] = AvailableView(self.content_frame, self.shell)
        self.views["my_hosts"] = MyHostsView(self.content_frame, self.shell)
        self.views["assignments"] = AssignmentsView(self.content_frame, self.shell)
        self.views["admin_schedule"] = AdminScheduleView(self.content_frame, self.shell)
        self.views["clouds"] = CloudsView(self.content_frame, self.shell)
        self.views["hosts"] = HostsView(self.content_frame, self.shell)
        self.views["settings"] = SettingsView(self.content_frame, self.shell)

        self._show_view("welcome")

    def _create_welcome_view(self):
        """Create welcome view with optional login button"""
        welcome_frame = ttk.Frame(self.content_frame)

        # Center container
        center_frame = ttk.Frame(welcome_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        welcome_label = ttk.Label(
            center_frame,
            text="Welcome to QUADS Client",
            font=("TkDefaultFont", 16),
        )
        welcome_label.pack(pady=(0, 30))

        # Check if we have servers configured but not logged in
        has_servers = False
        if self.shell.config:
            servers = self.shell.config.get_all_servers()
            has_servers = len(servers) > 0

        if has_servers and not self.shell.is_authenticated():
            # Show login button
            ttk.Label(
                center_frame, text="You have servers configured.\n\nClick below to login:", font=("TkDefaultFont", 11)
            ).pack(pady=(0, 20))

            ttk.Button(center_frame, text="Login", command=self._auto_login_from_welcome).pack()

        elif self.shell.is_authenticated():
            # Show logged in message
            server_name = ""
            if self.shell.connection:
                server_name = getattr(self.shell.connection, "server_name", "")
            username = self.shell.connection.username if self.shell.connection else ""

            info_text = f"Connected to {server_name}\nLogged in as {username}\n\n"
            info_text += "Select an item from the sidebar to get started.\n\nNew to QUADS? Check Help → Documentation"

            info_label = ttk.Label(center_frame, text=info_text, justify=tk.CENTER)
            info_label.pack(pady=10)

        else:
            # No servers configured - show setup message
            info_label = ttk.Label(
                center_frame,
                text="Select an item from the sidebar to get started.\n\n" "New to QUADS? Check Help → Documentation",
            )
            info_label.pack(pady=10)

        return welcome_frame

    def _auto_login_from_welcome(self):
        """Auto-login from welcome view"""
        from quads_client.gui.widgets.dialogs import show_error_dialog

        prefs = self.preferences
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
            self._show_servers_view()
            return

        if target_server:
            try:
                # Connect to the server
                self.shell.connection_commands.cmd_connect(target_server)
                # Update welcome view to remove login button
                self.views["welcome"].destroy()
                self.views["welcome"] = self._create_welcome_view()
                self._show_view("welcome")
            except Exception as e:
                show_error_dialog(self, "Login Failed", f"Failed to connect to {target_server}", str(e))
        else:
            # No servers configured - show servers view
            self._show_servers_view()

    def _create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Separator(self.status_bar, orient=tk.HORIZONTAL).pack(side=tk.TOP, fill=tk.X)

        status_content = ttk.Frame(self.status_bar)
        status_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Connection indicator (colored circle)
        self.connection_indicator = ttk.Label(
            status_content, text="●", foreground="#888888", font=("TkDefaultFont", 12)  # Grey when not connected
        )
        self.connection_indicator.pack(side=tk.LEFT, padx=(0, 5))

        self.status_label = ttk.Label(status_content, text="Not connected", wraplength=1100, justify=tk.LEFT)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
            self.sidebar_visible = False
        else:
            self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, before=self.content_frame)
            self.sidebar_visible = True

    def _toggle_theme(self):
        """Toggle between dark and light themes"""
        new_mode = self.theme_manager.toggle_theme()

        # Refresh theme-aware widgets in all views
        for view in self.views.values():
            if hasattr(view, "refresh_theme"):
                view.refresh_theme()

        self.update_status(f"Theme switched to {new_mode} mode")

    def _new_session(self):
        """Create new session (placeholder)"""
        self.update_status("New session - Not yet implemented")

    def _close_session(self):
        """Close current session (placeholder)"""
        self.update_status("Close session - Not yet implemented")

    def _show_preferences(self):
        """Show preferences dialog"""
        old_font_size = self.preferences.get("font_size", "medium")

        dialog = PreferencesDialog(self, self.shell.config, self.theme_manager)
        self.wait_window(dialog)

        result = dialog.get_result()
        if result:
            # Preferences were saved, reload them
            self.preferences = self._load_preferences()

            # Check if font size changed
            new_font_size = self.preferences.get("font_size", "medium")
            if new_font_size != old_font_size:
                # Apply font changes
                self._apply_font_preferences()
                self.update_status(f"Preferences saved - font size changed to {new_font_size}")
            else:
                self.update_status("Preferences saved successfully")

            # Apply any immediate changes (like auto-refresh in My Hosts view)
            if "my_hosts" in self.views and hasattr(self.views["my_hosts"], "apply_preferences"):
                self.views["my_hosts"].apply_preferences(self.preferences)

    def _refresh_view(self):
        """Refresh current view (placeholder)"""
        self.update_status("Refreshing view...")

    def _show_view(self, view_name):
        """Show a specific view"""
        if self.current_view:
            self.current_view.pack_forget()

        # Recreate welcome view to reflect current auth status
        if view_name == "welcome":
            self.views["welcome"].destroy()
            self.views["welcome"] = self._create_welcome_view()

        if view_name in self.views:
            self.views[view_name].pack(fill=tk.BOTH, expand=True)
            self.current_view = self.views[view_name]

            if hasattr(self.current_view, "refresh"):
                self.current_view.refresh()
        else:
            self.update_status(f"{view_name.title()} view - Not yet implemented")

    def _show_servers_view(self):
        """Show servers view"""
        self._show_view("servers")
        self.update_status("Servers & Connections")

    def _show_schedule_view(self):
        """Show schedule view"""
        self._show_view("schedule")
        self.update_status("Schedule Hosts")

    def _show_my_hosts_view(self):
        """Show my hosts view"""
        self._show_view("my_hosts")
        self.update_status("My Hosts")

    def _show_assignments_view(self):
        """Show assignments view"""
        self._show_view("assignments")
        self.update_status("My Assignments")

    def _show_admin_schedule_view(self):
        """Show admin schedule view"""
        if not self.shell.is_admin():
            self.update_status("Admin role required")
            return
        self._show_view("admin_schedule")
        self.update_status("Admin Schedule Management")

    def _show_clouds_view(self):
        """Show clouds view"""
        if not self.shell.is_admin():
            self.update_status("Admin role required")
            return
        self._show_view("clouds")
        self.update_status("Cloud Management")

    def _show_hosts_view(self):
        """Show hosts view"""
        if not self.shell.is_admin():
            self.update_status("Admin role required")
            return
        self._show_view("hosts")
        self.update_status("Host Management")

    def _show_available_view(self):
        """Show available hosts view"""
        self._show_view("available")
        self.update_status("Available Hosts")

    def _show_settings_view(self):
        """Show settings view"""
        self._show_view("settings")
        self.update_status("Settings")

    def _show_about(self):
        """Show About dialog"""
        about_window = tk.Toplevel(self)
        about_window.title("About QUADS Client")
        about_window.geometry("450x400")
        about_window.resizable(False, False)

        bg_color = self.theme_manager.get_color("bg")
        about_window.configure(bg=bg_color)

        title_label = ttk.Label(
            about_window,
            text=f"QUADS Client v{__version__}",
            font=("TkDefaultFont", 16, "bold"),
        )
        title_label.pack(pady=15)

        subtitle_label = ttk.Label(
            about_window,
            text="Graphical User Interface for QUADS",
        )
        subtitle_label.pack(pady=10)

        devs_label = ttk.Label(about_window, text="Core Developers:", font=("TkDefaultFont", 10, "bold"))
        devs_label.pack(pady=(20, 5))

        devs_frame = ttk.Frame(about_window)
        devs_frame.pack(pady=5)

        developers = ["Will Foster", "Gonza Rafuls", "Kambiz Aghaiepour"]
        for dev in developers:
            dev_label = ttk.Label(devs_frame, text=f"• {dev}")
            dev_label.pack()

        opensource_label = ttk.Label(
            about_window,
            text="QUADS is Open Source software crafted with love ❤️",
            font=("TkDefaultFont", 9),
        )
        opensource_label.pack(pady=(15, 5))

        license_link_frame = ttk.Frame(about_window)
        license_link_frame.pack(pady=5)

        ttk.Label(license_link_frame, text="Licensed under the", font=("TkDefaultFont", 8)).pack(side=tk.LEFT)

        license_button = ttk.Button(
            license_link_frame,
            text="GPLv3",
            command=lambda: webbrowser.open("https://github.com/quadsproject/quads-client/blob/main/LICENSE"),
        )
        license_button.pack(side=tk.LEFT, padx=3)

        website_button = ttk.Button(
            about_window,
            text="QUADS Website",
            command=lambda: webbrowser.open("https://quads.dev"),
        )
        website_button.pack(pady=10)

        close_button = ttk.Button(about_window, text="Close", command=about_window.destroy)
        close_button.pack(pady=15)

        about_window.transient(self)
        about_window.grab_set()

    def _open_documentation(self):
        """Open documentation in browser"""
        webbrowser.open("https://quads.dev")
        self.update_status("Opening documentation...")

    def _report_issue(self):
        """Open issue tracker in browser"""
        webbrowser.open("https://github.com/quadsproject/quads-client/issues")
        self.update_status("Opening issue tracker...")

    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_window = tk.Toplevel(self)
        shortcuts_window.title("Keyboard Shortcuts")
        shortcuts_window.geometry("400x350")
        shortcuts_window.resizable(False, False)

        bg_color = self.theme_manager.get_color("bg")
        shortcuts_window.configure(bg=bg_color)

        title_label = ttk.Label(
            shortcuts_window,
            text="Keyboard Shortcuts",
            font=("TkDefaultFont", 14, "bold"),
        )
        title_label.pack(pady=10)

        cmd_key = "Cmd" if self.is_macos else "Ctrl"

        shortcuts = [
            (f"{cmd_key}+N", "New Session"),
            (f"{cmd_key}+W", "Close Session"),
            (f"{cmd_key}+Q", "Quit Application"),
            (f"{cmd_key}+T", "Toggle Theme"),
            (f"{cmd_key}+R", "Refresh View"),
            ("F1", "Show Shortcuts"),
        ]

        frame = ttk.Frame(shortcuts_window)
        frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        for shortcut, description in shortcuts:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=5)

            key_label = ttk.Label(row, text=shortcut, font=("TkDefaultFont", 9, "bold"), width=12)
            key_label.pack(side=tk.LEFT)

            desc_label = ttk.Label(row, text=description)
            desc_label.pack(side=tk.LEFT, padx=10)

        close_button = ttk.Button(shortcuts_window, text="Close", command=shortcuts_window.destroy)
        close_button.pack(pady=15)

        shortcuts_window.transient(self)
        shortcuts_window.grab_set()

    def update_status(self, message):
        """Update status bar message"""
        if hasattr(self, "status_label") and self.status_label:
            self.status_label.config(text=message)
        self.update_connection_indicator()

    def update_connection_indicator(self):
        """Update connection indicator color based on connection status"""
        if not hasattr(self, "connection_indicator"):
            return

        is_connected = self.shell.is_authenticated() if self.shell else False

        if is_connected:
            # Green circle when connected
            self.connection_indicator.config(foreground="#4ec9b0")
        else:
            # Grey circle when disconnected
            self.connection_indicator.config(foreground="#888888")

    def update_role_visibility(self):
        """Update visibility of admin-only navigation items and visual indicators"""
        is_admin = self.shell.is_admin()
        is_authenticated = self.shell.is_authenticated()

        # Hide/show admin navigation buttons
        for btn, is_admin_only in self.nav_buttons:
            if is_admin_only:
                if is_admin:
                    btn.pack(pady=2, padx=10, fill=tk.X)
                else:
                    btn.pack_forget()

        # Update title bar with admin indicator
        base_title = f"QUADS Client v{__version__}"
        if is_admin and is_authenticated:
            username = getattr(self.shell.connection, "username", "")
            server = getattr(self.shell.connection, "current_server", "")
            self.title(f"{base_title} - 👑 ADMIN ({username}@{server})")
        elif is_authenticated:
            username = getattr(self.shell.connection, "username", "")
            server = getattr(self.shell.connection, "current_server", "")
            self.title(f"{base_title} - {username}@{server}")
        else:
            self.title(base_title)

        # Update status bar with admin mode indicator
        # Create admin indicator label if it doesn't exist
        if not hasattr(self, "admin_indicator_label"):
            status_content = self.status_bar.winfo_children()[1]
            self.admin_indicator_label = ttk.Label(
                status_content,
                text="",
                font=("TkDefaultFont", 9, "bold"),
                foreground="#ff9900",
            )

        if is_admin and is_authenticated:
            self.admin_indicator_label.config(text="👑 ADMIN MODE")
            self.admin_indicator_label.pack(side=tk.LEFT, padx=20)
        else:
            self.admin_indicator_label.pack_forget()

        # Update connection indicator
        self.update_connection_indicator()

    def show_message(self, message, level="info"):
        """
        Show message to user (called by gui_shell)

        Args:
            message: Message text
            level: Message level (info, warning, error, success)
        """
        if level == "error":
            self.update_status(f"ERROR: {message}")
        elif level == "warning":
            self.update_status(f"WARNING: {message}")
        elif level == "success":
            self.update_status(f"✓ {message}")
        else:
            self.update_status(message)

        # Update role visibility when connection changes
        self.update_role_visibility()

    def _load_preferences(self):
        """Load preferences from config"""
        defaults = {
            "auto_refresh_interval": 30,
            "auto_refresh_my_hosts": True,
            "confirm_terminate": True,
            "confirm_release": True,
            "confirm_exit": False,
            "remember_window": True,
            "auto_connect": False,
            "default_server": "",
            "font_size": "large",
            "window_geometry": "1200x800",
            "window_position": None,
        }

        if self.shell.config and hasattr(self.shell.config, "config_data"):
            gui_prefs = self.shell.config.config_data.get("gui_preferences", {})
            return {**defaults, **gui_prefs}

        return defaults

    def _apply_window_preferences(self):
        """Apply window size and position from preferences"""
        if self.preferences["remember_window"]:
            geometry = self.preferences.get("window_geometry", "1200x800")
            position = self.preferences.get("window_position")

            if position:
                # Apply both size and position
                self.geometry(f"{geometry}+{position}")
            else:
                # Just size, let OS decide position
                self.geometry(geometry)
        else:
            # Default size
            self.geometry("1200x800")

        self.minsize(1000, 600)

    def _set_window_icon(self):
        """Set window icon from desktop/icons/quads-client.png"""
        try:
            from pathlib import Path
            from tkinter import PhotoImage

            # Try to find icon in desktop/icons/ directory
            icon_paths = [
                # Repository structure
                Path(__file__).parent.parent.parent.parent / "desktop" / "icons" / "quads-client.png",
                # Installed structure (if running from installed package)
                Path("/usr/share/icons/hicolor/128x128/apps/quads-client.png"),
            ]

            for icon_path in icon_paths:
                if icon_path.exists():
                    icon = PhotoImage(file=str(icon_path))
                    self.iconphoto(True, icon)
                    break
        except Exception:
            # If icon loading fails, just continue without icon
            pass

    def _apply_font_preferences(self):
        """Apply font size from preferences"""
        font_size = self.preferences.get("font_size", "large")

        # Font size mappings
        size_map = {
            "small": {"default": 8, "heading": 10, "title": 12},
            "medium": {"default": 9, "heading": 12, "title": 14},
            "large": {"default": 11, "heading": 14, "title": 16},
            "extra_large": {"default": 13, "heading": 16, "title": 18},
        }

        sizes = size_map.get(font_size, size_map["large"])

        # Update default fonts for ttk widgets
        from tkinter import font as tkfont

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=sizes["default"])

        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(size=sizes["default"])

        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(size=sizes["heading"])

    def _auto_connect_on_startup(self):
        """Auto-connect to default server on startup if enabled"""
        if not self.preferences.get("auto_connect", False):
            return

        default_server = self.preferences.get("default_server", "")
        if not default_server:
            return

        # Check if server exists
        try:
            if self.shell.config:
                servers = self.shell.config.get_all_servers()
                if default_server in servers:
                    # Auto-connect
                    self.update_status(f"Auto-connecting to {default_server}...")
                    try:
                        self.shell.connection_commands.cmd_connect(default_server)
                        self.update_status(f"Connected to {default_server}")
                    except Exception as e:
                        self.update_status(f"Auto-connect failed: {e}")
        except Exception:
            pass

    def _save_window_preferences(self):
        """Save window size and position to preferences"""
        if not self.preferences.get("remember_window", True):
            return

        # Get current geometry
        geometry = self.geometry()

        # Split into size and position
        if "+" in geometry or "-" in geometry:
            # Has position (e.g., "1200x800+100+50")
            parts = geometry.replace("-", "+-").split("+")
            size = parts[0]
            if len(parts) >= 3:
                position = f"{parts[1]}+{parts[2]}"
            else:
                position = None
        else:
            # Just size
            size = geometry
            position = None

        # Save to config
        if self.shell.config and hasattr(self.shell.config, "config_data"):
            if "gui_preferences" not in self.shell.config.config_data:
                self.shell.config.config_data["gui_preferences"] = {}

            self.shell.config.config_data["gui_preferences"]["window_geometry"] = size
            if position:
                self.shell.config.config_data["gui_preferences"]["window_position"] = position

            try:
                self.shell.config.save_config()
            except Exception:
                pass

    def _check_first_launch(self):
        """Check if this is first launch and show onboarding"""
        if self.shell.config and self.shell.config.needs_initial_setup():
            self.after(500, self._show_onboarding)

        # Update role visibility on startup
        self.update_role_visibility()

    def _show_onboarding(self):
        """Show onboarding wizard"""
        OnboardingWizard(self, self.shell)

    def _on_closing(self):
        """Handle window closing"""
        from tkinter import messagebox

        # Check if we should confirm exit with active sessions
        if self.preferences.get("confirm_exit", False):
            session_count = 0
            if self.shell.session_manager:
                session_count = len(self.shell.session_manager.sessions)

            if session_count > 0:
                if not messagebox.askyesno(
                    "Confirm Exit", f"You have {session_count} active session(s). Are you sure you want to exit?"
                ):
                    return

        # Save window size/position
        self._save_window_preferences()

        self.destroy()


if __name__ == "__main__":
    app = QuadsClientApp()
    app.mainloop()
