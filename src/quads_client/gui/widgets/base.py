"""Base view class and helper widgets to reduce code duplication"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from quads_client.gui.widgets.dialogs import show_error_dialog


class ScrolledTreeview(ttk.Frame):
    """Treeview with vertical and horizontal scrollbars"""

    def __init__(self, parent, columns, column_configs=None, enable_copy=True, **tree_kwargs):
        """
        Create a treeview with scrollbars

        Args:
            parent: Parent widget
            columns: Tuple of column identifiers
            column_configs: Dict mapping column_id to (heading_text, width)
                           e.g., {"id": ("ID", 60), "name": ("Name", 200)}
            enable_copy: Enable Ctrl+C / Cmd+C to copy selected rows
            **tree_kwargs: Additional arguments passed to Treeview
        """
        super().__init__(parent)
        self.enable_copy = enable_copy

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(self)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            **tree_kwargs,
        )
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # Configure columns
        if column_configs:
            for col_id, (heading_text, width) in column_configs.items():
                self.tree.heading(col_id, text=heading_text)
                self.tree.column(col_id, width=width)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Setup clipboard if enabled
        if self.enable_copy:
            self._setup_clipboard()

    def _setup_clipboard(self):
        """Setup clipboard keyboard shortcuts"""
        self.tree.bind("<Control-c>", lambda e: self.copy_selected())
        self.tree.bind("<Command-c>", lambda e: self.copy_selected())

    def copy_selected(self):
        """Copy selected rows to clipboard"""
        selection = self.tree.selection()
        if not selection:
            return

        lines = []
        for item in selection:
            values = self.tree.item(item, "values")
            lines.append("\t".join(str(v) for v in values))

        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        return len(lines)

    def clear(self):
        """Clear all items from the tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert(self, *args, **kwargs):
        """Insert item into tree"""
        return self.tree.insert(*args, **kwargs)

    def selection(self):
        """Get selected items"""
        return self.tree.selection()

    def item(self, item_id, option=None, **kw):
        """Get or set item properties"""
        return self.tree.item(item_id, option, **kw)


class BaseAdminView(ttk.Frame):
    """Base class for admin views with common patterns"""

    def __init__(self, parent, shell, title, requires_admin=True):
        """
        Initialize base view

        Args:
            parent: Parent widget
            shell: GUI shell instance
            title: View title
            requires_admin: Whether this view requires admin role
        """
        super().__init__(parent)
        self.shell = shell
        self.title_text = title
        self.requires_admin = requires_admin
        self.tree = None
        self.status_label = None

    def create_header(self, buttons=None):
        """
        Create standard header with title and buttons

        Args:
            buttons: List of (text, command) tuples for header buttons

        Returns:
            Header frame
        """
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        title_label = ttk.Label(header_frame, text=self.title_text, font=("TkHeadingFont",))
        title_label.pack(side=tk.LEFT)

        if buttons:
            button_frame = ttk.Frame(header_frame)
            button_frame.pack(side=tk.RIGHT)

            for text, command in buttons:
                ttk.Button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)

        return header_frame

    def create_action_bar(self, buttons):
        """
        Create action button bar

        Args:
            buttons: List of (text, command) tuples

        Returns:
            Action frame
        """
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        for text, command in buttons:
            ttk.Button(action_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)

        return action_frame

    def create_status_label(self):
        """Create standard status label"""
        self.status_label = ttk.Label(self, text="", font=("TkDefaultFont", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))
        return self.status_label

    def update_status(self, message):
        """Update status label"""
        if self.status_label:
            self.status_label.config(text=message)
            self.update()

    def check_auth(self):
        """
        Check authentication and admin role

        Returns:
            True if authenticated (and admin if required), False otherwise
        """
        if not self.shell.is_authenticated():
            self.update_status("Not authenticated")
            return False

        if self.requires_admin and not self.shell.is_admin():
            self.update_status("Admin role required")
            return False

        return True

    def safe_load_data(self, load_func, success_message=None):
        """
        Safely load data with error handling

        Args:
            load_func: Function that loads and returns data
            success_message: Optional success message template (use {count} for item count)

        Returns:
            Data from load_func or None on error
        """
        if not self.check_auth():
            return None

        try:
            self.update_status("Loading...")
            data = load_func()

            if success_message and data:
                count = len(data) if isinstance(data, (list, tuple)) else 0
                msg = success_message.format(count=count)
                self.update_status(f"{msg} | Last updated: Just now")
            elif data:
                self.update_status("Loaded successfully")
            else:
                self.update_status("No items found")

            return data

        except Exception as e:
            self.update_status("Error loading data")
            import traceback

            details = traceback.format_exc()
            show_error_dialog(self, "Load Failed", str(e), details)
            return None

    def _run_in_thread(self, work_func, on_success, on_error=None):
        """Run work_func in a background thread, deliver result to main thread."""

        def _worker():
            try:
                result = work_func()
                self.after(0, lambda: on_success(result))
            except Exception as exc:
                if on_error:
                    self.after(0, lambda: on_error(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def safe_load_data_async(self, load_func, on_loaded, success_message=None, disable_widgets=None):
        """
        Async version of safe_load_data -- runs load_func in a background thread.

        Args:
            load_func: Function that loads and returns data (called in background)
            on_loaded: Function(data) called on main thread with the result
            success_message: Optional message template (use {count} for item count)
            disable_widgets: Optional list of widgets to disable during loading
        """
        if not self.check_auth():
            return

        self.update_status("Loading...")

        if disable_widgets:
            for w in disable_widgets:
                w.configure(state="disabled")

        def _restore_widgets():
            if disable_widgets:
                for w in disable_widgets:
                    try:
                        w.configure(state="normal")
                    except Exception:
                        pass

        def on_success(data):
            _restore_widgets()
            if success_message and data:
                count = len(data) if isinstance(data, (list, tuple)) else 0
                msg = success_message.format(count=count)
                self.update_status(f"{msg} | Last updated: Just now")
            elif data:
                self.update_status("Loaded successfully")
            else:
                self.update_status("No items found")
            on_loaded(data)

        def on_error(exc):
            _restore_widgets()
            self.update_status("Error loading data")
            import traceback

            details = traceback.format_exc()
            show_error_dialog(self, "Load Failed", str(exc), details)

        self._run_in_thread(load_func, on_success, on_error)

    def get_selected_item(self, warning_message="Please select an item"):
        """
        Get selected tree item with validation

        Args:
            warning_message: Message to show if no selection

        Returns:
            (item_id, values) tuple or (None, None) if no selection
        """
        if not self.tree:
            return None, None

        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", warning_message)
            return None, None

        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        return item_id, values

    def confirm_action(self, title, message):
        """
        Show confirmation dialog

        Args:
            title: Dialog title
            message: Confirmation message

        Returns:
            True if confirmed, False otherwise
        """
        return messagebox.askyesno(title, message)

    def create_simple_dialog(self, title, geometry="400x200"):
        """
        Create a simple dialog window

        Args:
            title: Dialog title
            geometry: Window geometry string

        Returns:
            Toplevel dialog window
        """
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry(geometry)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Apply theme colors
        try:
            # Try to get theme manager from shell's gui_app
            if hasattr(self.shell, "gui_app") and hasattr(self.shell.gui_app, "theme_manager"):
                self.shell.gui_app.theme_manager.configure_toplevel(dialog)
        except Exception:
            pass

        return dialog

    def safe_execute(self, command_func, success_message, error_title, refresh_func=None):
        """
        Safely execute a command with error handling

        Args:
            command_func: Function to execute (no arguments)
            success_message: Message to show on success
            error_title: Title for error dialog
            refresh_func: Optional function to call after success
        """
        try:
            # Capture shell output during command execution
            if hasattr(self.shell, "_capture_output"):
                self.shell._capture_output = True
                self.shell._captured_messages = []

            command_func()

            # Check for errors in captured output
            if hasattr(self.shell, "_captured_messages"):
                errors = [msg for level, msg in self.shell._captured_messages if level == "error"]

                if errors:
                    error_msg = "\n".join(errors)
                    messagebox.showerror(error_title, error_msg)
                    return

            messagebox.showinfo("Success", success_message)
            if refresh_func:
                refresh_func()
        except Exception as e:
            import traceback

            details = traceback.format_exc()
            show_error_dialog(self, error_title, str(e), details)
        finally:
            if hasattr(self.shell, "_capture_output"):
                self.shell._capture_output = False


class FormDialog:
    """Helper for creating form-based dialogs"""

    @staticmethod
    def create_labeled_entry(parent, label_text, row, entry_width=30, **entry_kwargs):
        """
        Create a labeled entry field

        Args:
            parent: Parent widget
            label_text: Label text
            row: Grid row number
            entry_width: Entry width
            **entry_kwargs: Additional Entry kwargs

        Returns:
            Entry widget
        """
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=5)
        entry = ttk.Entry(parent, width=entry_width, **entry_kwargs)
        entry.grid(row=row, column=1, pady=5, sticky=tk.W)
        return entry

    @staticmethod
    def create_button_row(parent, buttons):
        """
        Create a row of buttons

        Args:
            parent: Parent widget
            buttons: List of (text, command) tuples

        Returns:
            Button frame
        """
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)

        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)

        return button_frame
