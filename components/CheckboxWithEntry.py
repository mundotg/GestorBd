import tkinter as tk
from tkinter import ttk
from typing import Union


class CheckboxWithEntry(ttk.Frame):
    def __init__(
        self, 
        parent, 
        label_text: str = "", 
        entry_value: Union[str, bool] = "", 
        entry_width: int = 10,
    ):
        super().__init__(parent)
        
        # Tratamento de valores booleanos
        if entry_value == "":
            default_value=False
            entry_value = ""
        elif isinstance(entry_value, str):
            default_value = entry_value.lower() in ["true", "1", "yes", "sim"]
            entry_value = default_value
        else:
            default_value = bool(entry_value)
            entry_value = default_value
        self.label_text = label_text
        # Variáveis de estado
        # print(f"valor : {default_value}")
        self.var_checked = tk.BooleanVar(value=bool(default_value) )
        self.entry_var = tk.StringVar(value=str(entry_value).lower())

        # Layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.style = ttk.Style()
        self.style.configure("Custom.TCheckbutton", foreground="blue", background="lightgray")
        self.func_on_check = None
        # Checkbox
        self.checkbox = ttk.Checkbutton(
            self, 
            text=self.label_text, 
            variable=self.var_checked,
            style="Custom.TCheckbutton"
        )
        self.checkbox.grid(row=0, column=0, sticky='w', padx=5)

        # Entry
        self.entry = ttk.Entry(
            self, 
            textvariable=self.entry_var, 
            width=entry_width,
            justify='center',
            state="readonly"
        )
        
        self.entry.grid(row=0, column=1, sticky='ew', padx=5)
        self.style.theme_use("clam")
        def on_check(event=None) -> None:
            """Manipula o estado do checkbox e entrada."""
            checked = self.var_checked.get()  # Obtém o valor atual
            
            # Atualiza o campo de entrada
            self.entry.config(state="normal")
            self.entry.delete(0, tk.END)
            self.entry.insert(0, "false" if checked else "true")
            self.entry.config(state="readonly")  # Bloqueia edição manual
            # self.update_idletasks()  # Atualiza o layout imediatamente

        self.checkbox.bind("<Button-1>", on_check)

    
    def set_on_check(self, func) -> None:
        """Define a função a ser chamada quando o checkbox for marcado/desmarcado."""
        self.checkbox.bind("<Button-1>", func)
    def get_value(self) -> object:
        """Retorna o estado atual do widget."""
        return {
            'value': self.var_checked.get()
        }
    def get_entry(self) -> str:
        """Retorna o valor do campo de entrada."""
        return self.entry.get()
    def set_value(self, value: bool) -> None:
        """Define o estado do checkbox."""
        valor = self.var_checked.get()
        self.var_checked.set(value)
        if valor:
            self.checkbox.state(["selected"])
        else:
            self.checkbox.state(["!selected"])
        # Atualiza o campo de entrada
        self.entry.config(state="normal")
        self.entry.delete(0, tk.END)
        self.entry.insert(0, "true" if value else "false")
        self.entry.config(state="readonly")
        # self.update_idletasks()  # Atualiza o layout imediatamente
    def set_entry(self, value: str) -> None:    
        """Define o valor do campo de entrada."""
        self.entry.config(state="normal")
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.entry.config(state="readonly")
        # self.update_idletasks()  # Atualiza o layout imediatamente

