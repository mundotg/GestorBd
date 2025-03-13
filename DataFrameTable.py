import tkinter as tk
from tkinter import ttk
import pandas as pd

class DataFrameTable:
    def __init__(self, parent, df: pd.DataFrame, rows_per_page=10):
        self.parent = parent
        self.df = df
        self.rows_per_page = rows_per_page
        self.current_page = 0
        self.total_pages = (len(df) // rows_per_page) + (1 if len(df) % rows_per_page else 0)
        
        self.create_widgets()
        self.update_table()

    def create_widgets(self):
        self.tree = ttk.Treeview(self.parent, columns=list(self.df.columns), show='headings')
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(expand=True, fill='both')
        
        self.nav_frame = tk.Frame(self.parent)
        self.nav_frame.pack()
        
        self.prev_button = tk.Button(self.nav_frame, text='Anterior', command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT)
        
        self.page_label = tk.Label(self.nav_frame, text=f'Página {self.current_page + 1} de {self.total_pages}')
        self.page_label.pack(side=tk.LEFT)
        
        self.next_button = tk.Button(self.nav_frame, text='Próximo', command=self.next_page)
        self.next_button.pack(side=tk.LEFT)
    
    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        start = self.current_page * self.rows_per_page
        end = start + self.rows_per_page
        for _, row in self.df.iloc[start:end].iterrows():
            self.tree.insert('', tk.END, values=row.tolist())
        
        self.page_label.config(text=f'Página {self.current_page + 1} de {self.total_pages}')

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_table()

# Exemplo de uso:
if __name__ == '__main__':
    df = pd.DataFrame({
        'ID': range(1, 51),
        'Nome': [f'Item {i}' for i in range(1, 51)],
        'Valor': [round(i * 1.5, 2) for i in range(1, 51)]
    })

    root = tk.Tk()
    root.title("Tabela com Paginação")
    app = DataFrameTable(root, df)
    root.mainloop()
