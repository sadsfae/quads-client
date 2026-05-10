"""QUADS Client GUI entry point"""

import sys


def main():
    """Main entry point for quads-client-gui"""
    try:
        import tkinter
    except ImportError:
        print("ERROR: GUI dependencies not available.")
        print("\nPlease use the CLI instead: quads-client")
        print("Or install the GUI package: dnf install quads-client-gui")
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
