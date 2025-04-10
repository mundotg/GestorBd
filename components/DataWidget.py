import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkcalendar import DateEntry
import datetime
from typing import Optional, Callable, Dict, Any


class DatabaseDateWidget:
    """
    A Tkinter widget for date and time selection optimized for database operations.
    Supports multiple database formats and provides SQL filter generation.
    """

    DB_DATE_FORMATS = {
        'sqlite': '%Y-%m-%d %H:%M',
        'mysql': '%Y-%m-%d %H:%M',
        'postgresql': '%Y-%m-%d %H:%M',
        'oracle': '%d-%b-%Y %H:%M',
        'mssql': '%Y-%m-%d %H:%M',
        'oracle-timestamp-tz': '%Y-%m-%d %H:%M:%S %z',
        'mssql-datetimeoffset': '%Y-%m-%d %H:%M:%S %z',
        'postgresql-timestamptz': '%Y-%m-%d %H:%M:%S %z',
        'oracle-timestamp-local': '%Y-%m-%d %H:%M:%S'
    }

    SQL_DATE_FUNCTIONS = {
        'sqlite': lambda field: f"{field} = ?",
        'mysql': lambda field: f"{field} = %s",
        'postgresql': lambda field: f"{field} = %s",
        'oracle': lambda field: f"{field} = TO_DATE(?, 'DD-MON-YYYY HH24:MI')",
        'mssql': lambda field: f"{field} = ?",
        'oracle-timestamp-tz': lambda field: f"{field} = TO_TIMESTAMP_TZ(?, 'YYYY-MM-DD HH24:MI:SS TZH:TZM')",
        'mssql-datetimeoffset': lambda field: f"{field} = ?",
        'postgresql-timestamptz': lambda field: f"{field} = ?::TIMESTAMPTZ",
        'oracle-timestamp-local': lambda field: f"{field} = TO_TIMESTAMP(?, 'YYYY-MM-DD HH24:MI:SS')"
    }

    TIMEZONE_SUPPORT = {
        'sqlite': False,
        'mysql': False,
        'postgresql': False,
        'oracle': False,
        'mssql': False,
        'oracle-timestamp-tz': True,
        'mssql-datetimeoffset': True,
        'postgresql-timestamptz': True,
        'oracle-timestamp-local': False
    }

    def __init__(self, 
                 master: tk.Widget, 
                 db_type: str = 'sqlite', 
                 field_name: str = '',
                 on_change: Optional[Callable] = None, 
                 label_text: str = "Date and Time:",
                 default_date: Optional[str] = None,
                 timezone: Optional[str] = None,
                 **widget_options):
        """
        Initialize the database date widget.
        
        Args:
            master: Parent Tkinter widget
            db_type: Database type (sqlite, mysql, postgresql, oracle, mssql, etc.)
            field_name: Database field name for SQL filter generation
            on_change: Callback function when date/time is changed
            label_text: Text label for the widget
            default_date: Default date in 'YYYY-MM-DD HH:MM' format
            timezone: Timezone string (for timezone-aware database types)
            **widget_options: Additional widget options
        """
        self.master = master
        self.db_type = db_type.lower() if db_type in self.DB_DATE_FORMATS else 'sqlite'
        self.field_name = field_name
        self.on_change = on_change
        self.timezone = timezone

        # Create main frame
        self.frame = ttk.Frame(master)

        # Create and pack label
        self.label = ttk.Label(self.frame, text=label_text)
        self.label.pack(side=tk.LEFT, padx=5)

        # Get date format for selected database type
        self.date_format = self.DB_DATE_FORMATS[self.db_type]

        # Create date variable and set default value
        self.date_var = tk.StringVar()
        self.current_date = self._get_default_date(default_date)

        # Set the formatted date in the widget
        if pd.isna(self.current_date):
            self.current_date = pd.to_datetime("2025-03-23 00:00:00")  # Set a default date if NaT is encountered
        
        # Format the date if it is a valid datetime object
        try:
            formatted_date = self.current_date.strftime(self.date_format.split()[0]) if not pd.isna(self.current_date) else "No Date"
        except ValueError as e:
            formatted_date = "Invalid Date"
            print(f"Error formatting date: {e}")
           # print(self, f"Error formatting date: {e}", level="ERROR")
        self.date_var.set(formatted_date)

        # Date entry field (read-only)
        self.date_entry = ttk.Entry(self.frame, textvariable=self.date_var, width=16)
        self.date_entry.pack(side=tk.LEFT)

        # Calendar button with better icon handling
        self.calendar_button = ttk.Button(self.frame, 
                                          text="Calendar", 
                                          width=8, 
                                          command=self.open_calendar)
        self.calendar_button.pack(side=tk.LEFT, padx=5)

        # Time variable and entry
        self.time_var = tk.StringVar(value=self.current_date.strftime("%H:%M"))
        self.time_entry = ttk.Entry(self.frame, textvariable=self.time_var, width=5)
        self.time_entry.pack(side=tk.LEFT, padx=5)

        # Add timezone support for compatible database types
        if self.TIMEZONE_SUPPORT.get(self.db_type, False) and timezone:
            self.tz_var = tk.StringVar(value=timezone)
            self.tz_label = ttk.Label(self.frame, text="TZ:")
            self.tz_label.pack(side=tk.LEFT, padx=(10, 2))
            self.tz_entry = ttk.Entry(self.frame, textvariable=self.tz_var, width=6)
            self.tz_entry.pack(side=tk.LEFT)

        # Bind events
        self.time_entry.bind("<FocusOut>", self.validate_time)
        self.date_var.trace_add("write", self._on_date_change)
        self.time_var.trace_add("write", self._on_date_change)

        # Apply widget options
        for option, value in widget_options.items():
            if hasattr(self.frame, option):
                setattr(self.frame, option, value)

    def _get_default_date(self, default_date: Optional[str]) -> datetime.datetime:
        """
        Get the default date based on the input or use the current date.
        Args:
            default_date: Default date in string format 'YYYY-MM-DD HH:MM'
        Returns:
            datetime.datetime object
        """
        now = datetime.datetime.now()
        if default_date:
            try:
                return datetime.datetime.strptime(default_date, self.date_format)
            except ValueError:
                print(f"Invalid date format: {default_date}. Using current date.")
        return now

    def _on_date_change(self, *args) -> None:
        """Handle date or time change."""
        if self.on_change:
            self.on_change(self.get())

    def validate_time(self, event: tk.Event) -> None:
        """Validate the time input format."""
        time_str = self.time_var.get()
        try:
            datetime.datetime.strptime(time_str, "%H:%M")
        except ValueError:
            print("Invalid time format. Reverting to default.")
            self.time_var.set(self.current_date.strftime("%H:%M"))

    def open_calendar(self) -> None:
        """Open the calendar popup for date selection."""
        self.calendar_window = tk.Toplevel(self.master)
        self.calendar_window.title("Select Date and Time")
        self.calendar_window.transient(self.master)
        self.calendar_window.attributes("-topmost", True)

        # Position window near the button
        x = self.master.winfo_rootx() + self.calendar_button.winfo_x()
        y = self.master.winfo_rooty() + self.calendar_button.winfo_y() + self.calendar_button.winfo_height()
        self.calendar_window.geometry(f"+{x}+{y}")

        # Date picker widget
        current_date = datetime.datetime.strptime(self.date_var.get(), '%Y-%m-%d')
        self.date_picker = DateEntry(
            self.calendar_window, 
            width=12, 
            background='darkblue', 
            foreground='white',
            borderwidth=2, 
            date_pattern='yyyy-mm-dd',
            year=current_date.year,
            month=current_date.month,
            day=current_date.day
        )
        self.date_picker.pack(padx=10, pady=5)

        # Time selection frame
        time_frame = ttk.Frame(self.calendar_window)
        time_frame.pack(pady=5)

        # Current time values
        current_time = self.time_var.get().split(':')
        current_hour = int(current_time[0]) if current_time[0].isdigit() else 0
        current_minute = int(current_time[1]) if current_time[1].isdigit() else 0

        # Time selection widgets
        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT, padx=5)

        self.hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=2)
        self.hour_spinbox.set(current_hour)
        self.hour_spinbox.pack(side=tk.LEFT)

        self.minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=2)
        self.minute_spinbox.set(current_minute)
        self.minute_spinbox.pack(side=tk.LEFT)

        # Confirm button
        confirm_button = ttk.Button(self.calendar_window, text="Confirm", command=self.update_from_calendar)
        confirm_button.pack(pady=10)

    def update_from_calendar(self) -> None:
        """Update the date and time fields from calendar selection."""
        selected_date = self.date_picker.get_date()
        selected_time = f"{self.hour_spinbox.get()}:{self.minute_spinbox.get()}"
        datetime_str = f"{selected_date} {selected_time}"
        self.date_var.set(datetime_str.split()[0])
        self.time_var.set(datetime_str.split()[1])
        print(self.date_var.get(), self.time_var.get())
        # Update current date and time to new value
        self.current_date = datetime.datetime.strptime(datetime_str, self.date_format)
        self.frame.update_idletasks()
        self.calendar_window.destroy()

    def get(self) -> Dict[str, Any]:
        """
        Returns the selected date and time as a dictionary.

        Returns:
            Dict: Contains 'date', 'time', and optionally 'timezone'.
        """
        result = {
            'date': self.date_var.get(),
            'time': self.time_var.get(),
        }
        if self.TIMEZONE_SUPPORT.get(self.db_type, False):
            result['timezone'] = self.tz_var.get() if hasattr(self, 'tz_var') else None
        return result

    def set(self, date: str, time: str, timezone: Optional[str] = None) -> None:
        """
        Set the date, time, and timezone (if supported).
        
        Args:
            date: The date in the format 'YYYY-MM-DD'
            time: The time in the format 'HH:MM'
            timezone: Optional timezone string
        """
        datetime_str = f"{date} {time}"
        self.date_var.set(date)
        self.time_var.set(time)
        self.current_date = datetime.datetime.strptime(datetime_str, self.date_format)
        if self.TIMEZONE_SUPPORT.get(self.db_type, False) and timezone:
            if not hasattr(self, 'tz_var'):
                self.tz_var = tk.StringVar()
            self.tz_var.set(timezone)



def test_database_date_widget():
    """
    Test function to validate the DatabaseDateWidget functionality.
    This function will create an instance of the widget and check if:
    - The widget is initialized correctly.
    - The date and time values can be set and retrieved.
    - The calendar popup works as expected.
    """
    
    def on_date_change(selected_data):
        """Simple callback to handle date changes."""
        print(f"Date changed: {selected_data}")

    # Create a Tkinter root window
    root = tk.Tk()
    root.geometry("400x200")  # Size of the window

    frame_principal = ttk.Frame(root, padding=10, relief="solid")
    frame_principal.pack(padx=20, pady=20, fill="both", expand=True)
    # Create an instance of the DatabaseDateWidget
    widget = DatabaseDateWidget(
        master=frame_principal, # You can try other DB types here (mysql, postgresql, etc.)
        field_name="event_date",
        on_change=on_date_change,
        label_text="Event Date and Time:",  # Default date and time
        timezone="UTC",  # Optional timezone for supported databases
    )

    # Pack the widget frame
    widget.frame.grid(padx=10, pady=10)

    # Set some initial date and time
    # widget.set(date="2025-03-23", time="14:00", timezone="UTC")
    
    # Retrieve the selected date and time
    selected_data = widget.get()
    print("Selected Data (get):", selected_data)

    # Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    test_database_date_widget()
