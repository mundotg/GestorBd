import tkinter as tk

from DatabaseConnectorGUI import DatabaseConnectorGUI


if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseConnectorGUI(root)
    root.mainloop()