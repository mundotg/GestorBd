import sys
import tkinter as tk
import traceback
from DatabaseConnectorGUI import DatabaseConnectorGUI
from utils.logger import log_message

def main():
    try:
        # Create the main window
        root = tk.Tk()
        root.title("Database Connector")
        
        # Set window icon (optional)
        # root.iconbitmap("database_icon.ico")  # Uncomment if you have an icon file
        
        # Set minimum window size
        root.minsize(800, 600)
        
        # Center window on screen
        window_width = 1000
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Initialize application
        log_message(root,"Starting Database Connector Application","info")
        app = DatabaseConnectorGUI(root)
        
        # Start the main event loop
        root.mainloop()
        
    except Exception as e:
        log_message(root,f"Application crashed: {e} ({type(e).__name__})\n{traceback.format_exc()}", "error")
        # messagebox.showerror("Critical Error", 
        #                     f"An unexpected error occurred:\n{e}\n\nPlease check the log file for details.")
        sys.exit(1)


main()