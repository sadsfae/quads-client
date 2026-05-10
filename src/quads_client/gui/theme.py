"""Theme manager for QUADS Client GUI with dark/light mode support"""

import tkinter as tk
from tkinter import ttk


class ThemeManager:
    """Manages themes and color schemes for the GUI"""

    DARK_THEME = {
        "bg": "#1e1e1e",
        "fg": "#d4d4d4",
        "accent": "#007acc",
        "success": "#4ec9b0",
        "warning": "#dcdcaa",
        "error": "#f48771",
        "panel_bg": "#252526",
        "border": "#3e3e42",
        "button_bg": "#0e639c",
        "button_fg": "#ffffff",
        "entry_bg": "#3c3c3c",
        "entry_fg": "#cccccc",
    }

    LIGHT_THEME = {
        "bg": "#ffffff",
        "fg": "#000000",
        "accent": "#0066cc",
        "success": "#16825d",
        "warning": "#bf8803",
        "error": "#cd3131",
        "panel_bg": "#f3f3f3",
        "border": "#cccccc",
        "button_bg": "#0066cc",
        "button_fg": "#ffffff",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
    }

    def __init__(self, root, initial_theme="dark"):
        self.root = root
        self.style = ttk.Style(root)
        self.current_theme_mode = initial_theme
        self.has_sv_ttk = False
        self.has_ttkthemes = False

        self._detect_available_themes()
        self.apply_theme(initial_theme)

    def _detect_available_themes(self):
        """Detect which theme packages are available"""
        try:
            import sv_ttk

            self.has_sv_ttk = True
        except ImportError:
            pass

        try:
            import ttkthemes

            self.has_ttkthemes = True
        except ImportError:
            pass

    def apply_theme(self, mode="dark"):
        """Apply theme based on mode (dark or light)"""
        self.current_theme_mode = mode

        if self.has_sv_ttk:
            self._apply_sv_ttk_theme(mode)
        elif self.has_ttkthemes:
            self._apply_ttkthemes_theme(mode)
        else:
            self._apply_builtin_theme(mode)

    def _apply_sv_ttk_theme(self, mode):
        """Apply Sun Valley theme (modern Windows 11-like)"""
        try:
            import sv_ttk

            if mode == "dark":
                sv_ttk.set_theme("dark")
            else:
                sv_ttk.set_theme("light")

            self._apply_custom_colors(mode)
        except Exception as e:
            print(f"Warning: Failed to apply sv_ttk theme: {e}")
            self._apply_builtin_theme(mode)

    def _apply_ttkthemes_theme(self, mode):
        """Apply ttkthemes (arc, adapta, breeze, etc.)"""
        try:
            if mode == "dark":
                self.style.theme_use("arc")
            else:
                self.style.theme_use("breeze")

            self._apply_custom_colors(mode)
        except Exception as e:
            print(f"Warning: Failed to apply ttkthemes: {e}")
            self._apply_builtin_theme(mode)

    def _apply_builtin_theme(self, mode):
        """Fallback to built-in 'clam' theme with custom colors"""
        try:
            self.style.theme_use("clam")
            self._apply_custom_colors(mode)
        except Exception as e:
            print(f"Warning: Failed to apply built-in theme: {e}")
            self.style.theme_use("default")

    def _apply_custom_colors(self, mode):
        """Apply custom color scheme to current theme"""
        colors = self.DARK_THEME if mode == "dark" else self.LIGHT_THEME

        self.root.configure(bg=colors["bg"])

        self.style.configure(".", background=colors["bg"], foreground=colors["fg"])

        self.style.configure(
            "TFrame", background=colors["bg"], bordercolor=colors["border"]
        )

        self.style.configure(
            "TLabel", background=colors["bg"], foreground=colors["fg"]
        )

        self.style.configure(
            "TButton",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            bordercolor=colors["border"],
            focuscolor=colors["accent"],
        )

        self.style.map(
            "TButton",
            background=[("active", colors["accent"]), ("pressed", colors["accent"])],
        )

        self.style.configure(
            "TEntry",
            fieldbackground=colors["entry_bg"],
            foreground=colors["entry_fg"],
            bordercolor=colors["border"],
        )

        self.style.configure(
            "Treeview",
            background=colors["bg"],
            foreground=colors["fg"],
            fieldbackground=colors["bg"],
            bordercolor=colors["border"],
        )

        self.style.configure(
            "Treeview.Heading",
            background=colors["panel_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
        )

        self.style.configure(
            "TNotebook", background=colors["bg"], bordercolor=colors["border"]
        )

        self.style.configure(
            "TNotebook.Tab",
            background=colors["panel_bg"],
            foreground=colors["fg"],
            padding=[10, 5],
        )

        self.style.map(
            "TNotebook.Tab",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["button_fg"])],
        )

        self.style.configure("TMenubutton", background=colors["panel_bg"])

        self.style.configure(
            "Success.TLabel", foreground=colors["success"], background=colors["bg"]
        )

        self.style.configure(
            "Warning.TLabel", foreground=colors["warning"], background=colors["bg"]
        )

        self.style.configure(
            "Error.TLabel", foreground=colors["error"], background=colors["bg"]
        )

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        new_mode = "light" if self.current_theme_mode == "dark" else "dark"
        self.apply_theme(new_mode)
        return new_mode

    def get_color(self, color_name):
        """Get a color from the current theme"""
        colors = (
            self.DARK_THEME if self.current_theme_mode == "dark" else self.LIGHT_THEME
        )
        return colors.get(color_name, "#000000")

    def get_theme_info(self):
        """Get information about active theme backend"""
        if self.has_sv_ttk:
            return "Sun Valley (sv-ttk)"
        elif self.has_ttkthemes:
            return "ttkthemes"
        else:
            return "Built-in (clam)"

    def configure_toplevel(self, toplevel):
        """Configure a Toplevel dialog with current theme colors"""
        colors = (
            self.DARK_THEME if self.current_theme_mode == "dark" else self.LIGHT_THEME
        )
        toplevel.configure(bg=colors["bg"])

    @property
    def current_mode(self):
        """Get current theme mode"""
        return self.current_theme_mode
