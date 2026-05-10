"""Onboarding wizard for first-time setup"""

import tkinter as tk
from tkinter import ttk, messagebox


class OnboardingWizard(tk.Toplevel):
    """Multi-step onboarding wizard for new users"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.parent = parent
        self.shell = shell

        self.title("Welcome to QUADS Client")
        self.geometry("600x500")
        self.resizable(False, False)

        self.current_step = 0
        self.server_data = {}

        self.transient(parent)
        self.grab_set()

        self._create_ui()
        self._show_step(0)

    def _create_ui(self):
        """Create the wizard UI"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        self.back_button = ttk.Button(
            button_frame, text="Back", command=self._previous_step
        )
        self.back_button.pack(side=tk.LEFT)

        self.skip_button = ttk.Button(
            button_frame, text="Skip Setup", command=self._skip_setup
        )
        self.skip_button.pack(side=tk.LEFT, padx=10)

        self.next_button = ttk.Button(
            button_frame, text="Next", command=self._next_step
        )
        self.next_button.pack(side=tk.RIGHT)

    def _show_step(self, step):
        """Show a specific wizard step"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_step = step

        if step == 0:
            self._show_welcome()
        elif step == 1:
            self._show_add_server()
        elif step == 2:
            self._show_connect_register()
        elif step == 3:
            self._show_done()

        self.back_button.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        self.skip_button.config(state=tk.NORMAL if step < 3 else tk.DISABLED)

        if step == 3:
            self.next_button.config(text="Get Started", command=self._finish)
        else:
            self.next_button.config(text="Next", command=self._next_step)

    def _show_welcome(self):
        """Show welcome screen"""
        title = ttk.Label(
            self.content_frame,
            text="Welcome to QUADS Client!",
            font=("TkDefaultFont", 16, "bold"),
        )
        title.pack(pady=30)

        message = ttk.Label(
            self.content_frame,
            text="This wizard will help you set up your first QUADS server connection.\n\n"
            "You'll be able to:\n"
            "  • Add your QUADS server\n"
            "  • Connect and authenticate\n"
            "  • Start scheduling hosts\n\n"
            "Click Next to continue or Skip Setup to configure manually later.",
            justify=tk.CENTER,
        )
        message.pack(pady=20)

    def _show_add_server(self):
        """Show add server screen"""
        title = ttk.Label(
            self.content_frame,
            text="Add Your First Server",
            font=("TkDefaultFont", 14, "bold"),
        )
        title.pack(pady=20)

        form_frame = ttk.Frame(self.content_frame)
        form_frame.pack(pady=20, padx=40, fill=tk.BOTH)

        ttk.Label(form_frame, text="Server Name:").grid(
            row=0, column=0, sticky=tk.W, pady=10
        )
        self.server_name_entry = ttk.Entry(form_frame, width=30)
        self.server_name_entry.grid(row=0, column=1, pady=10, padx=10)
        self.server_name_entry.insert(0, "my-quads")

        ttk.Label(form_frame, text="Server URL:").grid(
            row=1, column=0, sticky=tk.W, pady=10
        )
        self.server_url_entry = ttk.Entry(form_frame, width=30)
        self.server_url_entry.grid(row=1, column=1, pady=10, padx=10)
        self.server_url_entry.insert(0, "https://")

        self.verify_ssl_var = tk.BooleanVar(value=True)
        ssl_check = ttk.Checkbutton(
            form_frame, text="Verify SSL certificate", variable=self.verify_ssl_var
        )
        ssl_check.grid(row=2, column=1, sticky=tk.W, pady=10)

        hint_label = ttk.Label(
            self.content_frame,
            text="Tip: You can add more servers later from the Servers view.",
            font=("TkDefaultFont", 8),
        )
        hint_label.pack(pady=10)

    def _show_connect_register(self):
        """Show connect/register screen"""
        title = ttk.Label(
            self.content_frame,
            text=f"Connect to {self.server_data.get('name', 'Server')}",
            font=("TkDefaultFont", 14, "bold"),
        )
        title.pack(pady=20)

        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        login_frame = ttk.Frame(notebook, padding=20)
        notebook.add(login_frame, text="Login")

        ttk.Label(login_frame, text="Email:").grid(
            row=0, column=0, sticky=tk.W, pady=10
        )
        self.login_email_entry = ttk.Entry(login_frame, width=30)
        self.login_email_entry.grid(row=0, column=1, pady=10, padx=10)

        ttk.Label(login_frame, text="Password:").grid(
            row=1, column=0, sticky=tk.W, pady=10
        )
        self.login_password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.login_password_entry.grid(row=1, column=1, pady=10, padx=10)

        ttk.Button(login_frame, text="Login", command=self._do_login).grid(
            row=2, column=1, pady=20, sticky=tk.E
        )

        register_frame = ttk.Frame(notebook, padding=20)
        notebook.add(register_frame, text="Register")

        ttk.Label(register_frame, text="Email:").grid(
            row=0, column=0, sticky=tk.W, pady=10
        )
        self.register_email_entry = ttk.Entry(register_frame, width=30)
        self.register_email_entry.grid(row=0, column=1, pady=10, padx=10)

        ttk.Label(register_frame, text="Password:").grid(
            row=1, column=0, sticky=tk.W, pady=10
        )
        self.register_password_entry = ttk.Entry(register_frame, width=30, show="*")
        self.register_password_entry.grid(row=1, column=1, pady=10, padx=10)

        ttk.Label(register_frame, text="Confirm:").grid(
            row=2, column=0, sticky=tk.W, pady=10
        )
        self.register_confirm_entry = ttk.Entry(register_frame, width=30, show="*")
        self.register_confirm_entry.grid(row=2, column=1, pady=10, padx=10)

        ttk.Button(register_frame, text="Register", command=self._do_register).grid(
            row=3, column=1, pady=20, sticky=tk.E
        )

        self.status_label = ttk.Label(
            self.content_frame, text="", foreground="blue"
        )
        self.status_label.pack(pady=10)

    def _show_done(self):
        """Show completion screen"""
        title = ttk.Label(
            self.content_frame,
            text="You're All Set!",
            font=("TkDefaultFont", 16, "bold"),
        )
        title.pack(pady=30)

        status = "✓ Server configured\n"
        if self.shell.is_authenticated():
            user = self.shell.connection.username if self.shell.connection else "user"
            status += f"✓ Logged in as {user}\n"
        else:
            status += "○ Not logged in (you can login later)\n"

        status_label = ttk.Label(
            self.content_frame,
            text=status,
            font=("TkDefaultFont", 12),
            justify=tk.CENTER,
        )
        status_label.pack(pady=20)

        message = ttk.Label(
            self.content_frame,
            text="You can now start scheduling hosts.\n"
            "Click 'Get Started' to begin using QUADS Client.",
            justify=tk.CENTER,
        )
        message.pack(pady=20)

    def _next_step(self):
        """Move to next step"""
        if self.current_step == 1:
            if not self._validate_server():
                return

        self._show_step(self.current_step + 1)

    def _previous_step(self):
        """Move to previous step"""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _validate_server(self):
        """Validate and save server data"""
        name = self.server_name_entry.get().strip()
        url = self.server_url_entry.get().strip()

        if not name:
            messagebox.showerror("Error", "Server name is required")
            return False

        if not url or not url.startswith("http"):
            messagebox.showerror("Error", "Valid server URL is required (must start with http:// or https://)")
            return False

        self.server_data = {
            "name": name,
            "url": url,
            "verify": self.verify_ssl_var.get(),
        }

        try:
            self.shell.server_commands.cmd_add_server(
                f"{name} {url} {'--verify' if self.verify_ssl_var.get() else '--no-verify'}"
            )
            self.shell.connection_commands.cmd_connect(name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add server: {e}")
            return False

        return True

    def _do_login(self):
        """Perform login"""
        email = self.login_email_entry.get().strip()
        password = self.login_password_entry.get()

        if not email or not password:
            self.status_label.config(text="Email and password required", foreground="red")
            return

        try:
            self.status_label.config(text="Logging in...", foreground="blue")
            self.update()

            self.shell.user_commands.cmd_login(f"{email} {password}")

            if self.shell.is_authenticated():
                self.status_label.config(text="✓ Login successful!", foreground="green")
                self.next_button.config(state=tk.NORMAL)
                self.after(1000, lambda: self._show_step(3))
            else:
                self.status_label.config(text="Login failed", foreground="red")
        except Exception as e:
            self.status_label.config(text=f"Login failed: {e}", foreground="red")

    def _do_register(self):
        """Perform registration"""
        email = self.register_email_entry.get().strip()
        password = self.register_password_entry.get()
        confirm = self.register_confirm_entry.get()

        if not email or not password:
            self.status_label.config(text="Email and password required", foreground="red")
            return

        if password != confirm:
            self.status_label.config(text="Passwords don't match", foreground="red")
            return

        try:
            self.status_label.config(text="Registering...", foreground="blue")
            self.update()

            self.shell.user_commands.cmd_register(f"{email} {password}")

            if self.shell.is_authenticated():
                self.status_label.config(text="✓ Registration successful!", foreground="green")
                self.next_button.config(state=tk.NORMAL)
                self.after(1000, lambda: self._show_step(3))
            else:
                self.status_label.config(text="Registration completed, please login", foreground="blue")
        except Exception as e:
            self.status_label.config(text=f"Registration failed: {e}", foreground="red")

    def _skip_setup(self):
        """Skip the setup wizard"""
        if messagebox.askyesno(
            "Skip Setup",
            "Are you sure you want to skip the setup wizard?\n\n"
            "You can configure servers later from the Servers view.",
        ):
            self.destroy()

    def _finish(self):
        """Finish the wizard"""
        self.destroy()
