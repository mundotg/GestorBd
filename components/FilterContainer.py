# -*- coding: utf-8 -*-
from datetime import datetime
import traceback
from typing import Any
from sqlalchemy import inspect, text
import tkinter as tk
from tkinter import ttk
from components.Data_wiget2 import DateTimeEntry
from components.DataWidget import DatabaseDateWidget
from components.filter_column_show_in_consulta import FilterColumnShowInConsulta
from config.salavarInfoAllColumn import get_columns_by_table, save_columns_to_file
from utils.filter_util import  _add_filter_widget_cache, _create_date_widget, get_selected_columns
from utils.validarText import _fetch_enum_values, validar_numero

class FilterContainer(ttk.LabelFrame):
    def __init__(self, parent, log_message, database_name, enum_values, columns, engine: Any, db_type: str,
                 update_table_widget, status_var: Any, table_combobox: Any, *args, **kwargs):
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
        self.column_filters = {}
        self.column_filters_entry_between = {}
        self.column_filters_combobox_operation = {}
        self.column_for_show = {}
        self.LAZY_LOAD_BATCH = 30
        self._setup_ui()
        
    def update_column_filters(self, col_name: str, widget: Any, status_label: Any, event=None, lista={}):
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
        # Configurar o container principal com padding consistente
        self.configure(padding="10 5 10 5")
        
        # Configurar o container para preencher todo o espaço disponível
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.container = ttk.Frame(self)
        self.container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configurar o container para preencher todo o espaço
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        # Configurar o canvas para ser responsivo
        self._setup_canvas()
        self._setup_scrollbars()
        self._setup_buttons()

        self.table_combobox.bind("<<ComboboxSelected>>", self.load_columns)

    def _setup_canvas(self):
        # Criar um canvas com fundo leve
        self.filter_canvas = tk.Canvas(self.container, borderwidth=0, highlightthickness=0,
                                       background="#f9f9f9")
        self.filter_canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Criar o frame rolável com espaçamento adequado
        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.filter_window = self.filter_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configurar o scrollable_frame para responsividade adequada
        for i in range(5):  # Para 5 colunas (Coluna, Tipo, Filtro, Operação, Entre)
            self.scrollable_frame.columnconfigure(i, weight=1 if i == 2 else 0)
        
        # Vincular eventos para redimensionamento
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", 
                                  lambda e: self.filter_canvas.configure(
                                      scrollregion=self.filter_canvas.bbox("all")))

    def _setup_scrollbars(self):
        # Usar estilo padrão para scrollbars ao invés de personalizar
        self.v_scrollbar = ttk.Scrollbar(self.container, orient="vertical", 
                                         command=self.filter_canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 2))
        
        self.h_scrollbar = ttk.Scrollbar(self.container, orient="horizontal", 
                                         command=self.filter_canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        
        # Configurar o canvas para usar as scrollbars
        self.filter_canvas.configure(
            yscrollcommand=self.v_scrollbar.set, 
            xscrollcommand=self.h_scrollbar.set
        )
        
        # Adicionar suporte para rolagem de mouse
        # self.filter_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.filter_canvas.bind("<MouseWheel>", self._on_mousewheel_lazy)
        self.filter_canvas.bind("<Shift-MouseWheel>", self._on_horizontal_scroll)

    def _setup_buttons(self):
        # Frame de botões com espaçamento melhorado
        button_frame = ttk.Frame(self.container)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 5), sticky="ew")

        # Configuração para espaçamento adequado entre os botões
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0, minsize=100)
        button_frame.columnconfigure(2, weight=0, minsize=100)
        
        # Checkbox para aplicar filtro
        self.aplicar_filter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            button_frame, 
            text="Aplicar Filtro", 
            variable=self.aplicar_filter_var, 
            command=self.abrir_modal_selecao
        ).grid(row=0, column=0, padx=(5, 10), pady=5, sticky="w")
        
        # Botão para limpar filtros
        ttk.Button(
            button_frame, 
            text="Limpar Filtros", 
            command=self.clear_filters
        ).grid(row=0, column=2, padx=(0, 5), pady=5, sticky="e")

    def _on_canvas_configure(self, event):
        # Ajustar a largura da janela do canvas para preencher o espaço disponível
        canvas_width = event.width - 5  # Reduzindo um pouco para evitar clipping
        self.filter_canvas.itemconfig(self.filter_window, width=canvas_width)
        
        # Atualizar a região de rolagem
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
        
    def create_frame_filter_scroll(self):
        # Limpar frame existente se houver
        if hasattr(self, "scrollable_frame") and self.scrollable_frame and self.scrollable_frame.winfo_exists():
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
                
        # Criar um novo frame rolável para os filtros com espaçamento adequado
        self.scrollable_frame = ttk.Frame(self.filter_canvas, padding="5 5 5 5")
        self.filter_window = self.filter_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configurar colunas para melhor layout
        for i in range(5):  # Para 5 colunas possíveis
            weight = 1 if i == 2 else 0  # Coluna do filtro expande mais
            self.scrollable_frame.columnconfigure(i, weight=weight)
        
        # Vincular eventos para redimensionamento
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", 
                                  lambda e: self.filter_canvas.configure(
                                      scrollregion=self.filter_canvas.bbox("all")))

    def _on_mousewheel_lazy(self, event):
        self.filter_canvas.yview_scroll(-1 * (event.delta // 120), "units")

        # Detecta se chegou perto do final para carregar mais
        bbox = self.filter_canvas.bbox("all")
        if bbox:
            _, y0, _, y1 = bbox
            visible_bottom = self.filter_canvas.canvasy(self.filter_canvas.winfo_height())
            if visible_bottom + 100 >= y1:  # Se faltam menos de 100px
                if self.next_lazy_row < len(self.columns):
                    self.load_columns_lazy(start_row=self.next_lazy_row)

    
    def _on_horizontal_scroll(self, event):
        self.filter_canvas.xview_scroll(-1 * (event.delta // 120), "units")
    
    def clear_filters(self):
        """Limpa todos os campos de filtro sem destruir os widgets"""
        if not hasattr(self, 'column_filters') or not self.column_filters:
            return
        
        for col_name, widget in self.column_filters.items():
            # Limpar o widget baseado em seu tipo
            if isinstance(widget, ttk.Entry):
                widget.config(state="normal")
                widget.delete(0, tk.END) 
            elif isinstance(widget, ttk.Combobox):
                if widget['values']:
                    widget.set(widget['values'][0])  # Resetar para o primeiro valor
                else:
                    widget.set('')
            elif isinstance(widget, ttk.Checkbutton):
                # Para checkbutton, acessar a variável associada
                for child in widget.winfo_children():
                    if isinstance(child, tk.BooleanVar):
                        child.set(False)
                # Se o widget não tem filhos com variáveis, tentar buscar atributos
                if hasattr(widget, 'variable'):
                    widget.variable.set(False)
            elif isinstance(widget, DatabaseDateWidget):
                # Limpar widget de data
                if hasattr(widget, 'clear'):
                    widget.clear()
                else:
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.delete(0, tk.END)
                        elif isinstance(child, ttk.Combobox):
                            child.set('')
        
        # Limpar também os widgets de operação "entre"
        for col_name, widget in self.column_filters_entry_between.items():
            if widget and hasattr(widget, 'delete'):
                widget.delete(0, tk.END)
            elif widget and hasattr(widget, 'set'):
                widget.set('')
                
        # Resetar comboboxes de operação
        for col_name, combo in self.column_filters_combobox_operation.items():
            if combo['values']:
                combo.set(combo['values'][0])
    
    def get_for_query(self):
        """Retorna string formatada para uso em consultas SQL"""
        try:
            selected_columns = get_selected_columns(self)
            if not selected_columns:
                return "*"
            
            # Ajustando a formatação para diferentes SGBDs
            formatted_columns = []
            for column in selected_columns:
                # Ajustar sintaxe conforme o tipo de banco de dados
                if self.db_type == 'mysql':
                    formatted_columns.append(f"`{column}`")  # MySQL: backticks
                elif self.db_type == 'sqlserver':
                    formatted_columns.append(f"[{column}]")  # SQL Server: colchetes
                elif self.db_type == 'oracle':
                    formatted_columns.append(f'"{column}"')  # Oracle: aspas duplas
                else:
                    formatted_columns.append(f'"{column}"')  # PostgreSQL: aspas duplas (padrão)
            
            return ", ".join(formatted_columns)
        
        except Exception as e:
            self.log_message(f"Erro ao montar string de colunas para query: {e}", "error")
            return "*"
   
    def abrir_modal_selecao(self):
        """Abre o modal para seleção de colunas."""
        self.fechar_modal_anterior()

        # Cria novo modal com tamanho adequado e posicionamento relativo
        try:
            modal = tk.Toplevel()
            modal.title("Seleção de Colunas")
            modal.geometry("400x450")
            modal.minsize(350, 400)
            
            # Posicionar o modal relativo à janela principal
            if self.parent:
                x = self.parent.winfo_rootx() + 50
                y = self.parent.winfo_rooty() + 50
                modal.geometry(f"+{x}+{y}")
            
            # Adicionar bordas e estilo ao modal
            modal.configure(padx=10, pady=10)
            
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
            if hasattr(self.filtro_colunas, 'is_modal_open') and self.filtro_colunas.is_modal_open():
                try:
                    if hasattr(self.filtro_colunas, 'winfo_exists') and self.filtro_colunas.winfo_exists():
                        self.filtro_colunas.destroy()

                    if hasattr(self.filtro_colunas, 'parent') and self.filtro_colunas.parent and self.filtro_colunas.parent.winfo_exists():
                        self.filtro_colunas.parent.destroy()

                except Exception as e:
                    self.log_message(
                        f"Erro ao destruir janela anterior: {e} ({type(e).__name__})",
                        level="warning"
                    )
                    
                    
    def load_columns_lazy(self, start_row=0):
        end_row = min(start_row + self.LAZY_LOAD_BATCH, len(self.columns))
        headers = ["Coluna", "Tipo", "Filtro", "Operação"]
        header_style = ("Helvetica", 9, "bold")

        # Se for a primeira vez, cria o cabeçalho
        if start_row == 0:
            if hasattr(self.scrollable_frame, 'winfo_exists') and self.scrollable_frame.winfo_exists():
                self.create_frame_filter_scroll()
            for col, header in enumerate(headers):
                header_label = ttk.Label(self.scrollable_frame, text=header, font=header_style)
                header_label.grid(row=0, column=col, sticky=tk.W, padx=5, pady=5)

            ttk.Separator(self.scrollable_frame, orient='horizontal').grid(
                row=1, column=0, columnspan=len(headers)+1, sticky="ew", pady=5, padx=2)

        # Adiciona as colunas no intervalo atual
        self.example_text = {}  # Limpa o texto de exemplo
        for i, col in enumerate(self.columns[start_row:end_row], start=start_row+2):
            col_name = col["name"]
            col_type = str(col["type"]).lower().split(" ")[0]

            ttk.Label(self.scrollable_frame, text=col_name).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Label(self.scrollable_frame, text=col_type).grid(row=i, column=1, sticky=tk.W, padx=5, pady=3)
            # _add_filter_widget(self, col, col_type, i, validar_numero)
            try:
                _add_filter_widget_cache(self, col, col_type, i, validar_numero)
            except Exception as e:
                self.log_message(f"Erro ao adicionar widget de filtro: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
               

        self.next_lazy_row = end_row

    def load_columns(self, event=None) -> None:
        self.table_name = self.table_combobox.get().strip()
        self.column_for_show = {}
        if not self.table_name:
            return
        
        self.columns = get_columns_by_table(f'{self.db_type}{self.database_name}{self.table_name}', "tables_columns_data.pkl", log_message=self.log_message)
        if not self.columns:
            inspector = inspect(self.engine)
            self.columns = inspector.get_columns(self.table_name, schema=None)
            for column in self.columns:
                column['table'] = self.table_name
            save_columns_to_file({f'{self.db_type}{self.database_name}{self.table_name}': self.columns}, "tables_columns_data.pkl", log_message=self.log_message)

        self.column_filters.clear()
        self.column_filters_entry_between.clear()
        self.column_filters_combobox_operation.clear()
        self.column_for_show.clear()

        if not self.enum_values:
            # print("Carregando valores ENUM...")
            self.enum_values=_fetch_enum_values(self=self, columns=self.columns, text=text, table_name=self.table_name, traceback=traceback)
            # print(f"Valores ENUM carregados: {self.enum_values}")

        self.LAZY_LOAD_BATCH = 30
        self.next_lazy_row = 0

        self.load_columns_lazy()  # Carrega o primeiro lote!

        self.status_var.set(f"Colunas carregadas para tabela: {self.table_name}")


    def create_widget_operation_between(self, colname: str, col_type, row, no_data: bool)->Any:
        """Cria o campo extra para operação 'Entre' e retorna o widget."""
        entry = None
        
        if "int" in col_type or "integer" in col_type:
            vcmd = self.register(validar_numero)
            entry = ttk.Entry(self.scrollable_frame, validate="key", 
                              validatecommand=(vcmd, "%P"), width=15)

        elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
            vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
            entry = ttk.Entry(self.scrollable_frame, validate="key", 
                              validatecommand=(vcmd, "%P"), width=15)

        elif "date" in col_type or "timestamp" in col_type or "time" in col_type:
            try:
                test,entry = _create_date_widget(self, self.scrollable_frame, colname, col_type, row,4)
            except Exception as e:
                self.log_message(f"Erro criando widget de data para 'entre': {e}\n{traceback.format_exc()}", level="error")
                entry = ttk.Entry(self.scrollable_frame, width=15)
        
        # Armazenar a referência do widget apropriada
        
        self.column_filters_entry_between[colname] = entry
            
        return entry
  