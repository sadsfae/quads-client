"""QUADS Client GUI entry point"""

import sys


def main():
    """Main entry point for quads-client-gui"""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("ERROR: GUI dependencies not available.")
        print("\ntkinter is required for the GUI but is not installed.")
        print("\nOn Linux (Fedora/RHEL/CentOS):")
        print("  sudo dnf install python3-tkinter")
        print("\nOn Linux (Debian/Ubuntu):")
        print("  sudo apt install python3-tk")
        print("\nOn macOS:")
        print("  tkinter should be included with Python from python.org")
        print("  If missing, reinstall Python from https://www.python.org/downloads/")
        print("\nAlternatively, use the CLI instead: quads-client")
        return 1

    from quads_client.gui.main import QuadsClientApp

    try:
        app = QuadsClientApp()
        app.mainloop()
        return 0
    except Exception as e:
        print(f"ERROR: Failed to start GUI: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
