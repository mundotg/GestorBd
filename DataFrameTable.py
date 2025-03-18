
from tkinter import ttk
import pandas as pd
from typing import Callable,  Any, Optional
from components.treeview_frame import TreeViewFrame
from components.navigation_frame import NavigationFrame
from components.edit_modal import EditModal

class DataFrameTable(ttk.Frame):
    """
    A tkinter widget for displaying, editing, and paginating pandas DataFrames.
    """
    
    def __init__(
        self, 
        master: Any, 
        df: Optional[pd.DataFrame] = None,
        rows_per_page: int = 10,
        column_width: int = 100,
        on_data_change: Optional[Callable[[pd.DataFrame], None]] = None,
        edit_enabled: bool = True,
        delete_enabled: bool = True,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        # Configuration
        self.df = df.copy() if df is not None else pd.DataFrame()
        self.rows_per_page = rows_per_page
        self.column_width = column_width
        self.on_data_change = on_data_change
        self.edit_enabled = edit_enabled
        self.delete_enabled = delete_enabled
        
        # State variables
        self.current_page = 0
        self.total_pages = self._calculate_total_pages()
        self.selected_row_index = None
        
        # Setup the widget
        self._create_styles()
        self.treeview_frame = TreeViewFrame(self, self.df, self.column_width)
        self.navigation_frame = NavigationFrame(self, self.prev_page, self.next_page, self.update_table)
        self.update_table()
        
    def _calculate_total_pages(self) -> int:
        """Calculate the total number of pages based on the current DataFrame."""
        return max(1, (len(self.df) // self.rows_per_page) + (1 if len(self.df) % self.rows_per_page else 0))
        
    def _create_styles(self) -> None:
        """Create custom styles for the widget."""
        self.style = ttk.Style()
        self.style.configure(
            "DataTable.Treeview", 
            background="#f0f0f0",
            foreground="black",
            rowheight=25,
            fieldbackground="#f0f0f0"
        )
        self.style.map(
            'DataTable.Treeview', 
            background=[('selected', '#347083')],
            foreground=[('selected', 'white')]
        )

    def update_table(self) -> None:
        """Update the table with data from the current page."""
        self.treeview_frame.update_table(self.df, self.current_page, self.rows_per_page)
        self.navigation_frame.update_pagination(self.current_page, self.total_pages)

    def prev_page(self) -> None:
        """Go to the previous page if possible."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self) -> None:
        """Go to the next page if possible."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_table()

    def show_edit_modal(self):
        """Display a modal dialog for editing the selected row."""
        if self.selected_row_index is not None and self.selected_row_index < len(self.df):
            EditModal(self, self.df, self.selected_row_index, self.on_data_change)
