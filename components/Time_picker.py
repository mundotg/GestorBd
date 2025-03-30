import tkinter as tk
from tkinter import ttk

class TimePicker(ttk.Frame):
    def __init__(self, parent, default_time="00:00:00"):
        super().__init__(parent)

        # Verifica se o formato da hora inclui segundos
        time_parts = default_time.split(":")
        if len(time_parts) == 2:
            default_hour, default_minute = map(int, time_parts)
            default_second = 0
        elif len(time_parts) == 3:
            default_hour, default_minute, default_second = map(int, time_parts)
        else:
            raise ValueError("Formato de hora inválido. Use HH:MM ou HH:MM:SS")

        # Spinbox para horas (0 a 23)
        self.hour_spinbox = ttk.Spinbox(self, from_=0, to=23, width=3, format="%02.0f")
        self.hour_spinbox.set(f"{default_hour:02d}")
        self.hour_spinbox.grid(row=0, column=0, padx=2, pady=5)

        # Separador ":"
        ttk.Label(self, text=":").grid(row=0, column=1)

        # Spinbox para minutos (0 a 59)
        self.minute_spinbox = ttk.Spinbox(self, from_=0, to=59, width=3, format="%02.0f", increment=1)
        self.minute_spinbox.set(f"{default_minute:02d}")
        self.minute_spinbox.grid(row=0, column=2, padx=2, pady=5)

        # Separador ":" (opcional para segundos)
        self.second_label = ttk.Label(self, text=":")
        self.second_label.grid(row=0, column=3)
        self.second_label.grid_remove()  # Oculto por padrão

        # Spinbox para segundos (0 a 59)
        self.second_spinbox = ttk.Spinbox(self, from_=0, to=59, width=3, format="%02.0f", increment=1)
        self.second_spinbox.set(f"{default_second:02d}")
        self.second_spinbox.grid(row=0, column=4, padx=2, pady=5)
        self.second_spinbox.grid_remove()  # Oculto por padrão

        # Mostra ou oculta os segundos dependendo do formato
        if len(time_parts) == 3:
            self.show_seconds()

    def show_seconds(self):
        """Mostra o campo de segundos se estiver oculto"""
        self.second_label.grid()
        self.second_spinbox.grid()

    def hide_seconds(self):
        """Oculta o campo de segundos"""
        self.second_label.grid_remove()
        self.second_spinbox.grid_remove()

    def change_event(self, function_):
        """Adiciona eventos para detectar mudanças no tempo."""
        for spinbox in [self.hour_spinbox, self.minute_spinbox, self.second_spinbox]:
            spinbox.bind("<FocusOut>", lambda e: function_())
            spinbox.bind("<ButtonRelease>", lambda e: function_())

    def get_time(self):
        """Retorna o horário selecionado no formato HH:MM ou HH:MM:SS"""
        if self.second_spinbox.winfo_ismapped():
            return f"{self.hour_spinbox.get()}:{self.minute_spinbox.get()}:{self.second_spinbox.get()}"
        return f"{self.hour_spinbox.get()}:{self.minute_spinbox.get()}"

    def set_time(self, time_str):
        """Define um novo horário, aceitando HH:MM ou HH:MM:SS"""
        try:
            time_parts = time_str.split(":")
            if len(time_parts) == 2:
                hour, minute = map(int, time_parts)
                second = 0
                self.hide_seconds()
            elif len(time_parts) == 3:
                hour, minute, second = map(int, time_parts)
                self.show_seconds()
            else:
                raise ValueError("Formato inválido. Use HH:MM ou HH:MM:SS")

            # Validação dos valores
            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                self.hour_spinbox.set(f"{hour:02d}")
                self.minute_spinbox.set(f"{minute:02d}")
                self.second_spinbox.set(f"{second:02d}")
            else:
                print(f"Erro: Valores fora do intervalo permitido ({time_str}).")
        except ValueError:
            print(f"Erro: Formato de hora inválido ({time_str}). Use HH:MM ou HH:MM:SS.")

# Exemplo de uso do componente
if __name__ == "__main__":
    root = tk.Tk()
    root.title("TimePicker com HH:MM e HH:MM:SS")

    time_picker = TimePicker(root, default_time="14:30")  # Aceita "14:30" ou "14:30:45"
    time_picker.pack(padx=10, pady=10)

    def mostrar_horario():
        print("Hora selecionada:", time_picker.get_time())

    btn = ttk.Button(root, text="Obter Hora", command=mostrar_horario)
    btn.pack(pady=5)

    root.mainloop()
