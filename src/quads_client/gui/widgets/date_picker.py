"""Date picker widget for GUI"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import calendar


def get_next_sunday_22utc(start_hour=22):
    """Get the next Sunday at specified hour (default 22:00 UTC)

    Args:
        start_hour: Hour of day (0-23), default 22
    """
    now = datetime.utcnow()
    # Days until Sunday (0=Monday, 6=Sunday)
    days_ahead = 6 - now.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    next_sunday = now + timedelta(days=days_ahead)
    # Set to specified hour
    return next_sunday.replace(hour=start_hour, minute=0, second=0, microsecond=0)


def get_two_weeks_sunday_22utc(start_date, cadence="2 weeks", end_hour=22):
    """Get N weeks ahead from start_date, on a Sunday at specified hour

    Args:
        start_date: Starting date (datetime or string)
        cadence: "1 week" or "2 weeks" (default "2 weeks")
        end_hour: Hour of day (0-23), default 22
    """
    if isinstance(start_date, str):
        # Parse the date string
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
        except ValueError:
            start_date = datetime.utcnow()

    # Determine number of days to add
    days_to_add = 14 if cadence == "2 weeks" else 7

    # Add days
    end_date = start_date + timedelta(days=days_to_add)
    # Find next Sunday from there
    days_ahead = 6 - end_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    elif days_ahead > 0:
        end_date += timedelta(days=days_ahead)

    # Set to specified hour
    return end_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)


class DatePickerDialog(tk.Toplevel):
    """Simple calendar date picker dialog"""

    def __init__(self, parent, title="Select Date", initial_date=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x400")
        self.resizable(False, False)
        self.result = None

        # Parse initial date or use today
        if initial_date:
            try:
                if isinstance(initial_date, str):
                    self.selected_date = datetime.strptime(initial_date.split()[0], "%Y-%m-%d")
                else:
                    self.selected_date = initial_date
            except (ValueError, IndexError):
                self.selected_date = datetime.utcnow()
        else:
            self.selected_date = datetime.utcnow()

        self.current_month = self.selected_date.month
        self.current_year = self.selected_date.year

        self._create_ui()

        # Center on parent
        self.transient(parent)
        self.grab_set()

    def _create_ui(self):
        """Create the calendar UI"""
        # Navigation frame
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(nav_frame, text="<", command=self._prev_month, width=3).pack(side=tk.LEFT)

        self.month_label = ttk.Label(
            nav_frame, text="", font=("TkDefaultFont", 12, "bold"), anchor=tk.CENTER, width=20
        )
        self.month_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Button(nav_frame, text=">", command=self._next_month, width=3).pack(side=tk.RIGHT)

        # Calendar frame
        cal_frame = ttk.Frame(self)
        cal_frame.pack(padx=10, pady=(0, 10))

        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(cal_frame, text=day, font=("TkDefaultFont", 9, "bold"), width=5).grid(row=0, column=i)

        # Day buttons (will be populated by _update_calendar)
        self.day_buttons = []
        for row in range(6):
            row_buttons = []
            for col in range(7):
                btn = ttk.Button(cal_frame, text="", width=5, command=lambda r=row, c=col: self._select_day(r, c))
                btn.grid(row=row + 1, column=col, padx=2, pady=2)
                row_buttons.append(btn)
            self.day_buttons.append(row_buttons)

        # Time selection
        time_frame = ttk.Frame(self)
        time_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(time_frame, text="Time (UTC):").pack(side=tk.LEFT, padx=5)

        self.hour_var = tk.StringVar(value=f"{self.selected_date.hour:02d}")
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=self.hour_var, format="%02.0f")
        hour_spin.pack(side=tk.LEFT, padx=5)

        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)

        self.minute_var = tk.StringVar(value=f"{self.selected_date.minute:02d}")
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=self.minute_var, format="%02.0f")
        minute_spin.pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side=tk.RIGHT, padx=5)

        self._update_calendar()

    def _update_calendar(self):
        """Update the calendar display"""
        # Update month/year label
        month_name = calendar.month_name[self.current_month]
        self.month_label.config(text=f"{month_name} {self.current_year}")

        # Get calendar for current month
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        # Update day buttons
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                btn = self.day_buttons[row_idx][col_idx]
                if day == 0:
                    btn.config(text="", state=tk.DISABLED)
                else:
                    btn.config(text=str(day), state=tk.NORMAL)

                    # Highlight selected date
                    if (
                        day == self.selected_date.day
                        and self.current_month == self.selected_date.month
                        and self.current_year == self.selected_date.year
                    ):
                        btn.config(style="Selected.TButton")
                    else:
                        btn.config(style="TButton")

        # Hide unused rows
        for row_idx in range(len(cal), 6):
            for col_idx in range(7):
                self.day_buttons[row_idx][col_idx].config(text="", state=tk.DISABLED)

    def _select_day(self, row, col):
        """Select a day"""
        btn = self.day_buttons[row][col]
        day_text = btn.cget("text")
        if day_text:
            day = int(day_text)
            self.selected_date = self.selected_date.replace(year=self.current_year, month=self.current_month, day=day)
            self._update_calendar()

    def _prev_month(self):
        """Go to previous month"""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self._update_calendar()

    def _next_month(self):
        """Go to next month"""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self._update_calendar()

    def _ok(self):
        """Confirm selection"""
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            self.selected_date = self.selected_date.replace(hour=hour, minute=minute)
            self.result = self.selected_date.strftime("%Y-%m-%d %H:%M")
            self.destroy()
        except ValueError:
            pass

    def _cancel(self):
        """Cancel selection"""
        self.result = None
        self.destroy()

    def get_result(self):
        """Get the selected date string"""
        return self.result
