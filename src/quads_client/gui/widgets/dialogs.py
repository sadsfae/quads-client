"""Reusable dialog widgets"""

import tkinter as tk
from tkinter import ttk


def show_error_dialog(parent, title, message, details=None):
    """
    Show an error dialog with copyable text

    Args:
        parent: Parent window
        title: Dialog title
        message: Main error message
        details: Optional detailed error text (e.g., traceback)
    """
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    size = "500x350" if details else "450x200"
    dialog.geometry(size)
    try:
        w, h = (int(v) for v in size.split("x"))
        dialog.minsize(w, h)
    except (ValueError, AttributeError):
        pass
    dialog.transient(parent)
    dialog.grab_set()

    # Apply theme if available
    _apply_theme_to_dialog(parent, dialog)

    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        main_frame,
        text="❌ " + title,
        font=("TkDefaultFont", 11, "bold"),
        foreground="red",
    ).pack(pady=(0, 10))

    text_frame = ttk.Frame(main_frame)
    text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    scrollbar = ttk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget = tk.Text(
        text_frame,
        wrap=tk.WORD,
        height=10 if details else 3,
        yscrollcommand=scrollbar.set,
    )
    scrollbar.config(command=text_widget.yview)

    text_widget.insert("1.0", message)
    if details:
        text_widget.insert(tk.END, "\n\nDetails:\n")
        text_widget.insert(tk.END, details)

    text_widget.pack(fill=tk.BOTH, expand=True)

    hint_label = ttk.Label(
        main_frame,
        text="💡 You can select and copy this text",
        font=("TkDefaultFont", 8),
        foreground="gray",
    )
    hint_label.pack(pady=(0, 10))

    button_frame = ttk.Frame(main_frame)
    button_frame.pack()

    ttk.Button(
        button_frame,
        text="Copy to Clipboard",
        command=lambda: _copy_to_clipboard(dialog, text_widget),
    ).pack(side=tk.LEFT, padx=5)

    ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)


def _copy_to_clipboard(window, text_widget):
    """Copy text widget contents to clipboard"""
    text = text_widget.get("1.0", tk.END).strip()
    window.clipboard_clear()
    window.clipboard_append(text)
    window.update()


def _apply_theme_to_dialog(parent, dialog):
    """Apply theme colors to dialog window"""
    # Try to find theme manager from parent window hierarchy
    theme_manager = None

    # Check if parent has theme_manager
    if hasattr(parent, "theme_manager"):
        theme_manager = parent.theme_manager
    # Check if parent has shell.gui_app.theme_manager
    elif hasattr(parent, "shell") and hasattr(parent.shell, "gui_app"):
        if hasattr(parent.shell.gui_app, "theme_manager"):
            theme_manager = parent.shell.gui_app.theme_manager
    # Check toplevel window
    else:
        try:
            toplevel = parent.winfo_toplevel()
            if hasattr(toplevel, "theme_manager"):
                theme_manager = toplevel.theme_manager
        except Exception:
            pass

    # Apply theme if found
    if theme_manager:
        theme_manager.configure_toplevel(dialog)


def show_info_dialog(parent, title, message):
    """Show an info dialog"""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("450x220")
    dialog.minsize(450, 220)
    dialog.transient(parent)
    dialog.grab_set()

    # Apply theme if available
    _apply_theme_to_dialog(parent, dialog)

    main_frame = ttk.Frame(dialog, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="ℹ️ " + title, font=("TkDefaultFont", 11, "bold")).pack(pady=(0, 10))

    ttk.Label(main_frame, text=message, wraplength=350).pack(pady=10)

    ttk.Button(main_frame, text="OK", command=dialog.destroy).pack(pady=(10, 0))
