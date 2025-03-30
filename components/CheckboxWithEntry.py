import tkinter as tk
from tkinter import ttk
from typing import Union


class CheckboxWithEntry(ttk.Frame):
    def __init__(
        self, 
        parent, 
        label_text: str = "", 
        entry_value: Union[str, bool] = False, 
        entry_width: int = 10,
    ):
        super().__init__(parent)
        
        # Tratamento de valores booleanos
        if isinstance(entry_value, str):
            default_value = entry_value.lower() in ["true", "1", "yes", "sim"]
        else:
            default_value = bool(entry_value)
        self.label_text = label_text
        # Variáveis de estado
        print(f"valor : {default_value}")
        self.var_checked = tk.BooleanVar(value=bool(default_value) )
        self.entry_var = tk.StringVar(value=str(default_value).lower())

        # Layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.style = ttk.Style()
        self.style.configure("Custom.TCheckbutton", foreground="blue", background="lightgray")

        # Checkbox
        self.checkbox = ttk.Checkbutton(
            self, 
            text=label_text, 
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

            # Alterna o valor do checkbox
            self.var_checked.set(not checked)

            # Atualiza o campo de entrada
            self.entry.config(state="normal")
            self.entry.delete(0, tk.END)
            self.entry.insert(0, "true" if self.var_checked.get() else "false")
            self.entry.config(state="readonly")  # Bloqueia edição manua
            # Log opcional
            print(f"{self.label_text} Checkbox {'marcado' if checked else 'desmarcado'} {new_value}")
        self.checkbox.bind("<Button-1>", on_check)

    

    def get_value(self) -> object:
        """Retorna o estado atual do widget."""
        return {
            'value': self.var_checked.get()
        }

# Criar a janela principal
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Checkbox com Entry")

    # Criar o componente personalizado
    checkbox = CheckboxWithEntry(root, "Ativar Opção")
    checkbox.pack(pady=10)

    # Botão para testar o valor do checkbox
    btn_get_value = ttk.Button(root, text="Obter Valor", command=lambda: print(checkbox.get_value()))
    btn_get_value.pack(pady=10)

    root.mainloop()
