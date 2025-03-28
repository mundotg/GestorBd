import tkinter as tk
from tkinter import ttk

class TimePicker(ttk.Frame):
    def __init__(self, parent, default_time="00:00"):
        super().__init__(parent)

        # Separando horas e minutos
        default_hour, default_minute = map(int, default_time.split(":"))

        # Spinbox para horas (0 a 23)
        self.hour_spinbox = ttk.Spinbox(self, from_=0, to=23, width=3, format="%02.0f")
        self.hour_spinbox.set(f"{default_hour:02d}")  # Define valor inicial
        self.hour_spinbox.grid(row=0, column=0, padx=2, pady=5)

        # Separador ":"
        ttk.Label(self, text=":").grid(row=0, column=1)

        # Spinbox para minutos (0 a 59)
        self.minute_spinbox = ttk.Spinbox(self, from_=0, to=59, width=3, format="%02.0f", increment=1)
        self.minute_spinbox.set(f"{default_minute:02d}")  # Define valor inicial
        self.minute_spinbox.grid(row=0, column=2, padx=2, pady=5)
    def change_event(self, function_: any):
        self.hour_spinbox.bind("<FocusOut>", lambda e: function_())
        self.minute_spinbox.bind("<FocusOut>", lambda e: function_())

        # OU, para capturar mudanças de valor imediatamente
        self.hour_spinbox.bind("<ButtonRelease>", lambda e: function_())
        self.minute_spinbox.bind("<ButtonRelease>", lambda e: function_())
        
    def get_time(self):
        """Retorna o horário selecionado no formato HH:MM"""
        return f"{self.hour_spinbox.get()}:{self.minute_spinbox.get()}"

    def set_time(self, time_str):
        """Define um novo horário no formato HH:MM"""
        try:
            hour, minute = map(int, time_str.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                self.hour_spinbox.set(f"{hour:02d}")
                self.minute_spinbox.set(f"{minute:02d}")
        except ValueError:
            print(f"Erro: Formato de hora inválido ({time_str}). Use HH:MM.")

# Exemplo de uso do componente
if __name__ == "__main__":
    root = tk.Tk()
    root.title("TimePicker com Spinbox")

    time_picker = TimePicker(root, default_time="14:30")
    time_picker.pack(padx=10, pady=10)

    def mostrar_horario():
        print("Hora selecionada:", time_picker.get_time())

    btn = ttk.Button(root, text="Obter Hora", command=mostrar_horario)
    btn.pack(pady=5)

    root.mainloop()
