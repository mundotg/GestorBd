import gc
from tkinter import messagebox
import traceback
from typing import Any
from components.CheckboxWithEntry import CheckboxWithEntry
from sqlalchemy import inspect, text
import tkinter as tk
from tkinter import ttk
from components.Data_wiget2 import DateTimeEntry
from components.DataWidget import DatabaseDateWidget
from components.filter_column_show_in_consulta import FilterColumnShowInConsulta
from config.salavarInfoAllColumn import get_columns_by_table, save_columns_to_file
from utils.filter_util import _update_column_selection, _update_status_label, get_selected_columns
from utils.validarText import _fetch_enum_values, validar_numero

class FilterContainer(ttk.LabelFrame):
    def __init__(self, parent, log_message,database_name,enum_values,columns, engine: Any, db_type: str,update_table_widget, status_var: Any, table_combobox: Any, *args, **kwargs):
        super().__init__(parent, text="Filtros", *args, **kwargs)
        self.log_message = log_message
        self.engine = engine
        self.status_var = status_var
        self.table_combobox = table_combobox
        self.parent = parent
        self.db_type = db_type.lower()
        self.update_table_widget = update_table_widget
        self.table_name = ""
        self.enum_values = enum_values
        self.columns = columns
        self.database_name = database_name
        self.filtro_colunas = None
        self.column_for_show = {}
        self._setup_ui()
        
    def update_column_filters(self,col_name:str, widget:Any,status_label:Any, event=None,lista={}):
        """
        Atualiza os filtros de coluna com os valores fornecidos.
        """
        
        if bool(lista.get(col_name)):  # Se o checkbox foi marcado
            lista[col_name] = False
            widget.set_value(False) 
        else:
            lista[col_name] = True
            widget.set_value(True) 
         # Atualiza o checkbox
        self.column_for_show = lista
        # Atualiza a contagem de colunas selecionadas
        if not status_label or not status_label.winfo_exists():
            return
            
        selected_count = sum(1 for selected in self.column_for_show.values() if selected)
        status_label.config(text=f"{selected_count} de {len(self.columns)} colunas selecionadas")
    
    def _setup_ui(self):
        # Configurar o container para preencher todo o espaço disponível
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.container = ttk.Frame(self)
        self.container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Configurar o container para preencher todo o espaço
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)
        
        self._setup_canvas()
        self._setup_scrollbars()
        self._setup_buttons()
        
        self.table_combobox.bind("<<ComboboxSelected>>",self.load_columns)
    
    def _setup_canvas(self):
        self.filter_canvas = tk.Canvas(self.container, borderwidth=0, highlightthickness=0)
        self.filter_canvas.grid(row=0, column=0, sticky="nsew")
        
        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.filter_window = self.filter_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configurar o scrollable_frame para que as colunas sejam responsivas
        self.scrollable_frame.columnconfigure(2, weight=1)  # A coluna dos widgets de filtro expande
        
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", lambda e: self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all")))
    
    def _setup_scrollbars(self):
        self.v_scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.filter_canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.h_scrollbar = ttk.Scrollbar(self.container, orient="horizontal", command=self.filter_canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.filter_canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.filter_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.filter_canvas.bind("<Shift-MouseWheel>", self._on_horizontal_scroll)
    
    
    def _setup_buttons(self):
        button_frame = ttk.Frame(self.container)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Configurar o button_frame para que os botões fiquem bem posicionados
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        self.aplicar_filter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_frame, text="Aplicar Filtro", variable=self.aplicar_filter_var, command=self.abrir_modal_selecao).grid(row=0, column=0, padx=10, sticky="w")
        ttk.Button(button_frame, text="Limpar Filtros", command=self.clear_filters).grid(row=0, column=1, padx=10, sticky="e")
    
    def _on_canvas_configure(self, event):
        self.filter_canvas.itemconfig(self.filter_window, width=event.width)
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
    def get_for_query(self):
        """Retorna string formatada para uso em consultas SQL Retorna uma string com as colunas selecionadas, separadas por vírgula, para uso em uma query SQL"""
        try:
            selected_columns = get_selected_columns(self)
            if not selected_columns:
                return "*"
            
            # Ajustando a formatação para diferentes SGBDs
            formatted_columns = []
            for column in selected_columns:
                # Aqui verificamos o tipo de banco de dados, ajustando a sintaxe conforme necessário
                if self.db_type == 'mysql':
                    formatted_columns.append(f"`{column}`")  # Para MySQL, usamos backticks
                elif self.db_type == 'sqlserver':
                    formatted_columns.append(f"[{column}]")  # Para SQL Server, usamos colchetes
                elif self.db_type == 'oracle':
                    formatted_columns.append(f'"{column}"')  # Para Oracle, usamos aspas duplas
                else:
                    formatted_columns.append(f'"{column}"')  # Para PostgreSQL, usamos aspas duplas (padrão)
            
            return ", ".join(formatted_columns)
        
        except Exception as e:
            self.log_message(f"Erro ao montar string de colunas para query: {e}", "error")
            return "*"
   
    def abrir_modal_selecao(self):
        """Abre o modal para seleção de colunas."""

        self.fechar_modal_anterior()

        # Cria novo modal
        try:
            modal = tk.Toplevel()
            modal.title("Seleção de Colunas")
            modal.geometry("390x410")

            # Instancia o seletor de colunas
            self.filtro_colunas = FilterColumnShowInConsulta(
                parent=modal,
                column=self.columns,
                column_for_show=self.column_for_show,
                log_message=self.log_message,
                table_name=self.table_name,
                update_column_filters=self.update_column_filters
            )

        except Exception as e:
            self.log_message(
                f"Erro ao criar filtro de colunas: {e} ({type(e).__name__})\n{traceback.format_exc()}",
                level="error"
            )


    def fechar_modal_anterior(self):
        """Fecha o modal anterior, se estiver aberto e for de outra tabela."""
        if hasattr(self, 'filtro_colunas') and self.filtro_colunas:
            if self.filtro_colunas.is_modal_open():
                try:
                    if self.filtro_colunas.winfo_exists():
                        self.filtro_colunas.destroy()

                    if self.filtro_colunas.parent and self.filtro_colunas.parent.winfo_exists():
                        self.filtro_colunas.parent.destroy()

                except Exception as e:
                    self.log_message(
                        f"Erro ao destruir janela anterior: {e} ({type(e).__name__})",
                        level="warning"
                    )
                finally:
                    gc.collect()

    def _on_mousewheel(self, event):
        self.filter_canvas.yview_scroll(-1 * (event.delta // 120), "units")
    
    def _on_horizontal_scroll(self, event):
        self.filter_canvas.xview_scroll(-1 * (event.delta // 120), "units")
    
    def clear_filters(self):
        """Limpa todos os campos de filtro sem destruir os widgets"""
        if not hasattr(self, 'column_filters'):
            self.column_filters = {}  # Inicializa caso ainda não exista
            return
        
        if not self.column_filters:
            return
        for col_name, widget in self.column_filters.items():
            # Limpar o widget baseado em seu tipo
            # print(f"name {col_name} valor {widget}")
            if isinstance(widget, ttk.Entry):
                widget.config(state="normal")
                widget.delete(0, tk.END) 
            elif isinstance(widget, ttk.Combobox):
                if widget['values']:
                    widget.set(widget['values'][0])  # Resetar para o primeiro valor
                else:
                    widget.set('')
            elif isinstance(widget, ttk.Checkbutton):
                # Para checkbutton, precisamos acessar a variável associada
                for child in widget.winfo_children():
                    if isinstance(child, tk.BooleanVar):
                        child.set(False)
                # Se o widget não tem filhos com variáveis, tentamos buscar por atributos
                if hasattr(widget, 'variable'):
                    widget.variable.set(False)
            elif isinstance(widget, DatabaseDateWidget):
                # Assumindo que o DatabaseDateWidget tem um método clear ou reset
                if hasattr(widget, 'clear'):
                    widget.clear()
                # Se não tiver, tentamos limpar os campos de entrada internos
                else:
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.delete(0, tk.END)
                        elif isinstance(child, ttk.Combobox):
                            child.set('')
    def create_frame_filter_scroll(self):
        if hasattr(self, "scrollable_frame") and self.scrollable_frame and self.scrollable_frame.winfo_exists():
            for widget in self.scrollable_frame.winfo_children():
                 widget.destroy()
            self.scrollable_frame.destroy()
        # Criar um novo frame rolável para os filtros
        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.filter_window = self.filter_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        # Configurar o scrollable_frame para que as colunas sejam responsivas
        self.scrollable_frame.columnconfigure(2, weight=1)  # A coluna dos widgets de filtro expande
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", lambda e: self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all")))
    
    def load_columns(self, event=None):
        self.table_name = self.table_combobox.get().strip()
        self.column_for_show = {}
        if not self.table_name:
            return
        
        self.create_frame_filter_scroll()
        table_name = f'{self.db_type}{self.database_name}{self.table_name}'
        try:
            self.columns = get_columns_by_table(table_name, "tables_columns_data.pkl", log_message=self.log_message)
            if self.columns:
                columns = self.columns
            else:
                inspector = inspect(self.engine)
                self.columns= inspector.get_columns(self.table_name, schema=None)
                if save_columns_to_file({table_name: self.columns}, "tables_columns_data.pkl", log_message=self.log_message):
                    self.log_message("salvo com sucesso","info")
                columns = self.columns
            # print(columns)    
            self.column_filters = {}
            
            _fetch_enum_values(self=self, columns=columns, text=text, traceback=traceback)
            
            headers = ["Coluna", "Tipo", "Filtro"]
            for col, header in enumerate(headers):
                ttk.Label(self.scrollable_frame, text=header, font=("", 9, "bold")).grid(row=0, column=col, sticky=tk.W, padx=5, pady=5)
            
            ttk.Separator(self.scrollable_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky="ew", pady=5, padx=2)
            
            for i, col in enumerate(columns, start=2):
                col_name, col_type = col["name"], str(col["type"]).lower()
                if " " in col_type:
                    col_value1 = col_type.split(" ")[0].lower()
                else:
                    col_value1 = col_type.lower()
                    
                ttk.Label(self.scrollable_frame, text=col_name).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
                ttk.Label(self.scrollable_frame, text=col_value1).grid(row=i, column=1, sticky=tk.W, padx=5, pady=3)
                self._add_filter_widget(col, col_type, i)
            
            self.status_var.set(f"Colunas carregadas para tabela: {self.table_name}")
        except Exception as e:
            self.log_message(f"Erro ao carregar colunas: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Erro ao obter colunas: {e}")
        # self.update_table_widget()  por enquanto não carrega a tabela logo que seleciona um item na combobox
    
    def get_column_filters(self):
        return self.column_filters
    
    def _add_filter_widget(self, col, col_type, row):
        no_data = True
        if "enum" in col_type or (self.enum_values.get(col["name"]) not in [None, "", []]):
            values = self.enum_values.get(col["name"], ["Valor não disponível"])
            if values and values[0] != "":
                values = [""] + values
            entry = ttk.Combobox(self.scrollable_frame, values=values, state="readonly")
            entry.set("")  # Set the first value as default
        
        elif "int" in col_type or "integer" in col_type:
            vcmd = self.register(validar_numero)
            entry = ttk.Entry(self.scrollable_frame, validate="key", validatecommand=(vcmd, "%P"))
        
        elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
            vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
            entry = ttk.Entry(self.scrollable_frame, validate="key", validatecommand=(vcmd, "%P"))
        
        elif "bool" in col_type or col_type in ["bit", "boolean"]:
            no_data = False
            # var = tk.BooleanVar(value=False)
            entry = CheckboxWithEntry(self.scrollable_frame)
            entry.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
            entry = entry.entry
        
        elif "date" in col_type or "timestamp" in col_type or "time" in col_type:
            try:
                widget = DateTimeEntry(self.scrollable_frame,col_type)
                widget.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
                entry = widget.entry
                no_data = False
            except Exception as e:
                self.log_message(f"Erro criando widget de data: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
                entry = ttk.Entry(self.scrollable_frame)
        
        else:
            entry = ttk.Entry(self.scrollable_frame)
        
        # Configurar o widget para ser responsivo
        if no_data:
            entry.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
        self.column_filters[col["name"]] = entry
        
    def on_date_change(self,selected_data):
        """Simple callback to handle date changes."""
        print(f"Date changed: {selected_data}")
        
