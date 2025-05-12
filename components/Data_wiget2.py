import tkinter as tk
from tkinter import ttk
import traceback
from tkcalendar import DateEntry
from datetime import datetime
from components.Time_picker import TimePicker
from utils.logger import log_message

# Formatos de data usando os tipos de dados das bases de dados
DATA_TYPE_FORMATS = {
    'datetime': '%Y-%m-%d %H:%M:%S',
    'timestamp': '%Y-%m-%d %H:%M:%S',
    'date': '%Y-%m-%d',
    'time': '%H:%M:%S'
}

def gerar_mensagem_tipo_dado(data_type):
    """
    Gera uma mensagem personalizada com base no tipo de dado.
    
    Args:
        data_type (str): Tipo de dado (por exemplo, 'datetime', 'date', 'time', 'timestamp', etc.).
    
    Returns:
        str: Mensagem personalizada com instruções sobre o formato do dado.
    """
    # Garantir que o tipo de dado esteja em minúsculas para facilitar a comparação
    data_type = data_type.lower()

    # Mensagens para diferentes tipos de dados
    if "datetime" in data_type:
        return "data formato: AAAA-MM-DD HH:MM:SS."
    elif "date" in data_type:
        return "data no formato: AAAA-MM-DD."
    elif "time" in data_type:
        return "data no formato: HH:MM:SS."
    elif "timestamp" in data_type:
        return "data no formato: AAAA-MM-DD HH:MM:SS."
    elif "year" in data_type:
        return "data no formato: AAAA."
    elif "month" in data_type:
        return "data no formato: MM."
    elif "day" in data_type:
        return "data no formato: DD."
    else:
        return "Formato de data desconhecido."

class DateTimeEntry(ttk.Frame):
    def __init__(self, parent, data_type="datetime"):
        super().__init__(parent)
        self.data_type = data_type.lower()
        text_label = gerar_mensagem_tipo_dado(data_type)
        
        self.frame_date = ttk.LabelFrame(self, text=text_label)
        width = 10 if data_type in "date" else 18
        self.entry = ttk.Entry(self.frame_date, width=width, state="normal")
        self.entry.grid(row=0, column=0, columnspan=1, padx=2, pady=5)
        
        self.date_entry = DateEntry(self.frame_date, width=1, background='darkblue', foreground='white', borderwidth=2)
        self.date_entry.grid(row=0, column=1, padx=1, pady=5)
        self.date_entry.lower(self.entry) 
        self.frame_date.grid(row=0, column=0, padx=5, pady=1, sticky="ew")
        # Criando um LabelFrame para agrupar o TimePicker
        self.frame_time = ttk.LabelFrame(self, text="Horário")
        # Centralizando o TimePicker dentro do LabelFrame
        self.time_entry = TimePicker(self.frame_time)
        self.time_entry.pack(padx=1, pady=1)
        # Adicionando o LabelFrame à interface
        self.frame_time.grid(row=0, column=3, padx=5, pady=1, sticky="ew")
        

        # Oculta ou destrói os elementos de acordo com o tipo de dado
        if self.data_type == "time":
            # Se for "time", remove o date_entry e o entry
            self.date_entry.grid_remove()
            self.entry.grid_remove()
        elif self.data_type == "date":
            # Se for "date", destrói o time_entry e remove o frame_time
            if hasattr(self, 'time_entry') and self.time_entry:
                self.time_entry.pack_forget()
            if hasattr(self, 'frame_time') and self.frame_time:
                self.frame_time.grid_remove()

        # Adiciona os eventos de atualização apenas se os widgets estiverem presentes
        if hasattr(self, 'date_entry') and self.date_entry:
            self.date_entry.bind("<<DateEntrySelected>>", self.update_entry)

        if hasattr(self, 'time_entry') and self.time_entry:
            if hasattr(self.time_entry, 'change_event'):
                self.time_entry.change_event(self.update_entry)

        # Inicializa com o valor padrão
        # self.update_entry()
        # self.after(100, self.hide_entry_field)
    

    def update_entry(self, event=None):
        """Atualiza o Entry com a data e hora formatadas corretamente."""
        date = ""
        if hasattr(self, 'date_entry') and self.date_entry is not None:
            date = self.date_entry.get().strip()  # Remove espaços extras
        time= ""
        if hasattr(self, 'time_entry') and self.time_entry is not None:
            time = self.time_entry.get_time().strip() if self.time_entry.get_time() else ""

        # Obtém o formato correto ou usa o padrão datetime
        date_format = DATA_TYPE_FORMATS.get(self.data_type, "%Y-%m-%d %H:%M:%S")

        formatted_date = None  # Inicializa para evitar erro de variável não definida

        try:
            if self.data_type == "date":
                if date:  # Só tenta converter se houver data
                    formatted_date = datetime.strptime(date, "%m/%d/%y").strftime(date_format)
                else:
                    formatted_date = ""  # Ou definir uma data padrão (ex: datetime.today().strftime(date_format))

            elif self.data_type == "time":
                if time:
                    formatted_date = datetime.strptime(time, "%H:%M").strftime(date_format)
                else:
                    formatted_date = ""  # Ou um horário padrão (ex: "00:00:00")

            else:  # Para datetime e timestamp
                if date and time:  
                    try:
                        formatted_date = datetime.strptime(f"{date} {time}", "%m/%d/%y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Caso a string não tenha segundos, tenta sem %S
                        formatted_date = datetime.strptime(f"{date} {time}", "%m/%d/%y %H:%M").strftime("%Y-%m-%d %H:%M")

                elif date:  # Se não houver tempo, assume "00:00"
                    formatted_date = datetime.strptime(f"{date} 00:00", "%m/%d/%y %H:%M").strftime(date_format)
                else:
                    formatted_date = ""  # Ou definir um valor padrão

        except ValueError as e:
            log_message(self,f"Erro ao formatar data/hora: {e} {traceback.format_exc()}","error")
            formatted_date = ""  # Define como vazio para evitar erro

        # Atualiza o Entry apenas se formatted_date estiver definido
        self.entry.delete(0, tk.END)
        self.entry.insert(0, formatted_date if formatted_date else "Erro no formato")


    def get_entry(self):
        """Retorna o valor atual do Entry formatado."""
        return self.entry.get()
    
    def set_default_value(self):
        """Define um valor padrão baseado no tipo de dado."""
        now = datetime.today()

        if self.data_type == "date":
            default_date = now.strftime("%Y-%m-%d")
            self.set_date(default_date)

        elif self.data_type in ["datetime", "timestamp"]:
            default_date = now.strftime("%Y-%m-%d")
            default_time = now.strftime("%H:%M:%S")
            self.set_date(default_date, default_time)

        elif self.data_type == "time":
            default_time = now.strftime("%H:%M:%S")
            self.set_date("", default_time)  # Apenas define o tempo

        else:
            print(f"Tipo de dado '{self.data_type}' não reconhecido para valor padrão.")


  

    def set_date(self, date: str, time: str = "00:00"):
        """Define uma data e hora no widget, forçando um valor válido."""
        try:
            if self.data_type in DATA_TYPE_FORMATS:  # Garante que o tipo é válido
                format_str = DATA_TYPE_FORMATS[self.data_type]  # Obtém o formato correto
                
                # Remover fuso horário caso exista
                date = date.split("+")[0]  # Remove "+00:00" ou outro fuso
                
                if self.data_type in ["datetime", "timestamp", "date"] and date:
                    if hasattr(self, 'date_entry') and self.date_entry is not None:
                        self.date_entry.set_date(datetime.strptime(date.split(" ")[0], "%Y-%m-%d"))  # Pega só a data

                if self.data_type in ["datetime", "timestamp", "time"]:
                    time_clean = time.split(" ")[-1][:8]  # Mantém apenas HH:MM:SS
                    datetime.strptime(time_clean, "%H:%M:%S")  # Valida o formato
                    if hasattr(self, 'time_entry') and self.time_entry is not None:
                        self.time_entry.set_time(time_clean)

            self.update_entry()

        except ValueError as e:
            error_message = f"Erro ao definir data/hora: {date} {time}. Detalhes: {e}"
            # print(error_message)
            log_message(self, error_message, level="error")



    def show_entry(self):
        """Torna o Entry visível novamente."""
        self.entry.grid()
        
    def hide_entry_field(self):
        """Esconde o campo de entrada do DateEntry e mantém apenas o botão."""
        self.date_entry.configure(width=2)  # Reduz a largura para esconder o campo de texto
        for child in self.date_entry.winfo_children():
            if isinstance(child, ttk.Entry):  # Verifica se é um campo de entrada
                child.grid_remove()
                return
            
    def hide_entry(self):
        """Torna o Entry invisível."""
        self.entry.grid_remove()
