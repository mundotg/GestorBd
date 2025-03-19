import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar, DateEntry
import datetime
from typing import Optional, Callable, Dict, Any
import re

class DatabaseDateWidget:
    """
    A date picker widget that handles date formats for different database types.
    Supports SQLite, MySQL, PostgreSQL, Oracle, and MSSQL date formats.
    """
    
    # Date formats for different database types
    DB_DATE_FORMATS = {
        'sqlite': '%Y-%m-%d',
        'mysql': '%Y-%m-%d',
        'postgresql': '%Y-%m-%d',
        'oracle': 'YYYY-MM-DD',  # Oracle uses TO_DATE function
        'mssql': '%Y-%m-%d'      # MSSQL can use ISO format
    }
    
    # SQL conversion functions for different database types
    SQL_DATE_FUNCTIONS = {
        'sqlite': lambda field, value: f"{field} = '{value}'",
        'mysql': lambda field, value: f"{field} = '{value}'",
        'postgresql': lambda field, value: f"{field} = '{value}'",
        'oracle': lambda field, value: f"{field} = TO_DATE('{value}', 'YYYY-MM-DD')",
        'mssql': lambda field, value: f"{field} = CAST('{value}' AS DATE)"
    }
    
    def __init__(self, master: tk.Widget, db_type: str = 'sqlite', 
                 field_name: str = '', on_change: Optional[Callable] = None,
                 label_text: str = "Data:"):
        """
        Initialize the date picker widget.
        
        Args:
            master: Parent widget
            db_type: Database type ('sqlite', 'mysql', 'postgresql', 'oracle', 'mssql')
            field_name: Database field name this widget is associated with
            on_change: Callback function when date changes
            label_text: Label text for the widget
        """
        self.master = master
        self.db_type = db_type.lower()
        self.field_name = field_name
        self.on_change = on_change
        
        # Validate db_type and set default if invalid
        if self.db_type not in self.DB_DATE_FORMATS:
            print(f"Warning: Unknown database type '{db_type}'. Defaulting to SQLite format.")
            self.db_type = 'sqlite'
        
        # Create main frame
        self.frame = ttk.Frame(master)
        
        # Create label
        self.label = ttk.Label(self.frame, text=label_text)
        self.label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create date entry widget
        self.date_var = tk.StringVar()
        
        # Try to use tkcalendar if available
        try:
            self.date_entry = DateEntry(
                self.frame,
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                date_pattern='yyyy-mm-dd',
                textvariable=self.date_var
            )
        except Exception:
            # Fallback to a regular entry with validation
            self.date_var.set(datetime.date.today().strftime('%Y-%m-%d'))
            self.date_entry = ttk.Entry(self.frame, width=12, textvariable=self.date_var)
            self.date_entry.bind('<FocusOut>', self._validate_date)
            self.date_entry.bind('<Return>', self._validate_date)
        
        self.date_entry.pack(side=tk.LEFT)
        
        # Add a "clear" button
        self.clear_button = ttk.Button(self.frame, text="✕", width=2, 
                                      command=self.clear_date)
        self.clear_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Add "today" button
        self.today_button = ttk.Button(self.frame, text="Hoje", width=5,
                                      command=self.set_today)
        self.today_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Set up change callback
        self.date_var.trace_add("write", self._on_date_change)
    
    def pack(self, **kwargs):
        """Pack the frame with the provided options."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame with the provided options."""
        self.frame.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place the frame with the provided options."""
        self.frame.place(**kwargs)
    
    def get(self) -> str:
        """Get the date value in the format for the configured database type."""
        date_str = self.date_var.get()
        if not date_str:
            return ""
        
        try:
            # Parse the input date
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            # Return it in the appropriate format
            return date_obj.strftime(self.DB_DATE_FORMATS[self.db_type])
        except ValueError:
            return ""
    
    def get_sql_filter(self) -> str:
        """Get a SQL filter expression for the current date value."""
        date_str = self.get()
        if not date_str or not self.field_name:
            return ""
        
        return self.SQL_DATE_FUNCTIONS[self.db_type](self.field_name, date_str)
    
    def set(self, date_str: str) -> bool:
        """
        Set the date value.
        
        Args:
            date_str: Date string in ISO format (YYYY-MM-DD) or database-specific format
            
        Returns:
            bool: True if date was set successfully, False otherwise
        """
        if not date_str:
            self.clear_date()
            return True
        
        # Try to parse in ISO format first
        try:
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            self.date_var.set(date_obj.strftime('%Y-%m-%d'))
            return True
        except ValueError:
            # Try to parse in database-specific format
            try:
                date_obj = datetime.datetime.strptime(date_str, self.DB_DATE_FORMATS[self.db_type]).date()
                self.date_var.set(date_obj.strftime('%Y-%m-%d'))
                return True
            except ValueError:
                return False
    
    def clear_date(self):
        """Clear the date value."""
        self.date_var.set("")
        if self.on_change:
            self.on_change("")
    
    def set_today(self):
        """Set the date to today."""
        today = datetime.date.today()
        self.date_var.set(today.strftime('%Y-%m-%d'))
    
    def _validate_date(self, event=None):
        """Validate and format the date."""
        date_str = self.date_var.get()
        if not date_str:
            return
        
        # Try different common date formats
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y']
        date_obj = None
        
        for fmt in date_formats:
            try:
                date_obj = datetime.datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        
        # If no format matched, try to parse parts
        if date_obj is None:
            # Extract numbers from the string
            numbers = re.findall(r'\d+', date_str)
            if len(numbers) >= 3:
                day, month, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
                
                # Handle 2-digit years
                if year < 100:
                    year += 2000
                
                # Validate day, month, year
                try:
                    date_obj = datetime.date(year, month, day)
                except ValueError:
                    try:
                        # Try swapping day and month
                        date_obj = datetime.date(year, day, month)
                    except ValueError:
                        pass
        
        # Update the entry with the formatted date
        if date_obj:
            self.date_var.set(date_obj.strftime('%Y-%m-%d'))
        else:
            # Invalid date, reset to today
            self.date_var.set(datetime.date.today().strftime('%Y-%m-%d'))
    
    def _on_date_change(self, *args):
        """Handle date change event."""
        if self.on_change:
            self.on_change(self.get())


class DateRangeWidget:
    """
    A widget that provides a start and end date range for database queries.
    """
    
    def __init__(self, master: tk.Widget, db_type: str = 'sqlite',
                 start_field: str = '', end_field: str = '',
                 on_change: Optional[Callable] = None):
        """
        Initialize a date range widget with start and end dates.
        
        Args:
            master: Parent widget
            db_type: Database type ('sqlite', 'mysql', 'postgresql', 'oracle', 'mssql')
            start_field: Database field name for start date
            end_field: Database field name for end date (if different)
            on_change: Callback function when date range changes
        """
        self.master = master
        self.db_type = db_type
        self.start_field = start_field
        self.end_field = end_field or start_field
        self.on_change = on_change
        
        # Create frame
        self.frame = ttk.LabelFrame(master, text="Intervalo de Datas")
        
        # Create internal frame for dates
        date_frame = ttk.Frame(self.frame)
        date_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Start date
        self.start_date = DatabaseDateWidget(
            date_frame, 
            db_type=db_type,
            field_name=start_field,
            on_change=self._on_date_change,
            label_text="De:"
        )
        self.start_date.pack(side=tk.LEFT, padx=(0, 10))
        
        # End date
        self.end_date = DatabaseDateWidget(
            date_frame,
            db_type=db_type,
            field_name=end_field,
            on_change=self._on_date_change,
            label_text="Até:"
        )
        self.end_date.pack(side=tk.LEFT)
        
        # Quick buttons frame
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, expand=True, padx=5, pady=(0, 5))
        
        # Add quick selection buttons
        ttk.Button(button_frame, text="Hoje", 
                  command=self.set_today).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="Ontem", 
                  command=self.set_yesterday).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Esta Semana", 
                  command=self.set_this_week).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Este Mês", 
                  command=self.set_this_month).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Limpar", 
                  command=self.clear).pack(side=tk.LEFT, padx=5)
    
    def pack(self, **kwargs):
        """Pack the frame with the provided options."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame with the provided options."""
        self.frame.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place the frame with the provided options."""
        self.frame.place(**kwargs)
    
    def get(self) -> Dict[str, str]:
        """Get the start and end date values."""
        return {
            'start': self.start_date.get(),
            'end': self.end_date.get()
        }
    
    def get_sql_filter(self) -> str:
        """Get a SQL filter expression for the date range."""
        start_date = self.start_date.get()
        end_date = self.end_date.get()
        
        if not self.start_field or (not start_date and not end_date):
            return ""
        
        conditions = []
        
        # Add start date condition if provided
        if start_date:
            if self.db_type == 'oracle':
                conditions.append(f"{self.start_field} >= TO_DATE('{start_date}', 'YYYY-MM-DD')")
            elif self.db_type == 'mssql':
                conditions.append(f"{self.start_field} >= CAST('{start_date}' AS DATE)")
            else:
                conditions.append(f"{self.start_field} >= '{start_date}'")
        
        # Add end date condition if provided
        if end_date:
            if self.db_type == 'oracle':
                conditions.append(f"{self.end_field} <= TO_DATE('{end_date}', 'YYYY-MM-DD')")
            elif self.db_type == 'mssql':
                conditions.append(f"{self.end_field} <= CAST('{end_date}' AS DATE)")
            else:
                conditions.append(f"{self.end_field} <= '{end_date}'")
        
        return " AND ".join(conditions)
    
    def set(self, start_date: str = None, end_date: str = None) -> bool:
        """Set the start and end dates."""
        start_success = True
        end_success = True
        
        if start_date is not None:
            start_success = self.start_date.set(start_date)
        
        if end_date is not None:
            end_success = self.end_date.set(end_date)
            
        return start_success and end_success
    
    def clear(self):
        """Clear both dates."""
        self.start_date.clear_date()
        self.end_date.clear_date()
    
    def set_today(self):
        """Set the date range to today."""
        today = datetime.date.today().strftime('%Y-%m-%d')
        self.set(today, today)
    
    def set_yesterday(self):
        """Set the date range to yesterday."""
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        self.set(yesterday, yesterday)
    
    def set_this_week(self):
        """Set the date range to this week (Monday to Sunday)."""
        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
        sunday = monday + datetime.timedelta(days=6)
        self.set(monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d'))
    
    def set_this_month(self):
        """Set the date range to this month (1st to last day)."""
        today = datetime.date.today()
        first_day = today.replace(day=1)
        
        # Get last day of the month
        if today.month == 12:
            last_day = today.replace(day=31)
        else:
            last_day = today.replace(month=today.month+1, day=1) - datetime.timedelta(days=1)
        
        self.set(first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d'))
    
    def _on_date_change(self, value):
        """Handle date change event from either date widget."""
        if self.on_change:
            self.on_change(self.get())


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Database Date Widget Demo")
    root.geometry("600x400")
    
    # Example frame
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Label
    ttk.Label(frame, text="Database Date Widget Demo", font=("", 14, "bold")).pack(pady=(0, 20))
    
    # Demo for different database types
    db_types = ['SQLite', 'MySQL', 'PostgreSQL', 'Oracle', 'MSSQL']
    
    for i, db_type in enumerate(db_types):
        # Create frame for each db type
        db_frame = ttk.LabelFrame(frame, text=f"{db_type} Date")
        db_frame.pack(fill=tk.X, pady=5)
        
        # Create date widget
        date_widget = DatabaseDateWidget(
            db_frame, 
            db_type=db_type.lower(),
            field_name="created_at",
            label_text=f"{db_type} Date:"
        )
        date_widget.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Add a display label to show the SQL
        sql_var = tk.StringVar()
        
        def update_sql(db=db_type.lower(), widget=date_widget, var=sql_var):
            date_val = widget.get()
            if date_val:
                sql = widget.get_sql_filter()
                var.set(f"SQL: {sql}")
            else:
                var.set("SQL: (no date selected)")
        
        date_widget.on_change = update_sql
        update_sql()  # Initial update
        
        ttk.Label(db_frame, textvariable=sql_var).pack(side=tk.LEFT, padx=10)
    
    # Date range widget example
    ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)
    ttk.Label(frame, text="Date Range Example:", font=("", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
    
    date_range = DateRangeWidget(
        frame,
        db_type="mysql",
        start_field="created_at",
        end_field="created_at"
    )
    date_range.pack(fill=tk.X, pady=5)
    
    # Display the SQL for date range
    range_sql_var = tk.StringVar(value="SQL: ")
    
    def update_range_sql(value=None):
        sql = date_range.get_sql_filter()
        if sql:
            range_sql_var.set(f"SQL: WHERE {sql}")
        else:
            range_sql_var.set("SQL: (no date range selected)")
    
    date_range.on_change = update_range_sql
    update_range_sql()  # Initial update
    
    ttk.Label(frame, textvariable=range_sql_var).pack(anchor=tk.W, pady=5)
    
    root.mainloop()