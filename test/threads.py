import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime

class ThreadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Threads")
        
        self.running = False  # Flag para controle da thread
        
        # Botões
        self.start_button = tk.Button(root, text="Começar Threads", command=self.start_threads)
        self.start_button.pack(pady=5)
        
        self.stop_button = tk.Button(root, text="Parar", command=self.stop_threads)
        self.stop_button.pack(pady=5)
        
        # Criando a tabela
        self.tree = ttk.Treeview(root, columns=("#1", "#2", "#3"), show="headings")
        self.tree.heading("#1", text="Nº")
        self.tree.heading("#2", text="Descrição")
        self.tree.heading("#3", text="Data Criada")
        self.tree.column("#1", width=50)
        self.tree.column("#2", width=200)
        self.tree.column("#3", width=150)
        self.tree.pack(pady=10)
        
        self.counter = 1  # Contador para adicionar linhas
    
    def start_threads(self):
        if not self.running:  # Impede múltiplas threads
            self.running = True
            self.thread = threading.Thread(target=self.update_table, daemon=True)
            self.thread.start()
    
    def stop_threads(self):
        self.running = False
    
    def update_table(self):
        while self.running:
            time.sleep(1)  # Aguarda 1 segundo antes de adicionar nova linha
            data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.tree.insert("", "end", values=(self.counter, f"Linha {self.counter}", data))
            self.counter += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = ThreadApp(root)
    root.mainloop()
