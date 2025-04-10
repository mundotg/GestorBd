from tkinter import messagebox, ttk
import tkinter as tk
import traceback
from components.CheckboxWithEntry import CheckboxWithEntry
from utils.filter_util import (
    _cancel_selection,
    _create_tooltip,
    _toggle_select_all,
    _update_status_label,
    get_selected_columns
)

class FilterColumnShowInConsulta:
    """Classe para gerenciar a exibição de colunas em consultas no banco de dados com UI aprimorada."""

    def __init__(self, parent,column_for_show, column, log_message=None, table_name=None,update_column_filters=None):
        self.table_name = table_name
        self.parent = parent
        self.column = column or []
        self.log_message = log_message
        self.update_column_filters = update_column_filters

        # Variáveis de controle de estado e UI
        self.show_in_consulta = False
        self.column_for_show =column_for_show
        self.column_filters = {}
        self.scrollable_frame = None
        self.select_all_var = tk.BooleanVar(value=False)
        self.status_label = None
        self.tooltip = None

        # Criação da estrutura de frames
        self._create_layout_structure()
        self._setup_event_bindings()
        self.create_fields_checkbox_for_show()

    def _create_layout_structure(self):
        """Cria a estrutura de layout com organização hierárquica clara usando grid"""
        # 1. Frame principal que contém tudo
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuração do layout grid para o frame principal
        self.frame.columnconfigure(0, weight=1)  # Coluna única expandível
        self.frame.rowconfigure(3, weight=1)     # A linha do conteúdo (scroll_container) deve expandir
        
        # 2. Frame para cabeçalho com pesquisa e controles
        self.header_frame = ttk.Frame(self.frame)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self._create_header_controls()
        
        # 3. Separador após o cabeçalho
        ttk.Separator(self.frame, orient='horizontal').grid(row=1, column=0, sticky="ew", pady=5)
        
        # 4. Container para canvas e barras de rolagem - uso de grid com sticky para expansão total
        self.scroll_container = ttk.Frame(self.frame)
        self.scroll_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=5)
        self.scroll_container.columnconfigure(0, weight=1)  # O canvas deve expandir horizontalmente
        self.scroll_container.rowconfigure(0, weight=1)     # O canvas deve expandir verticalmente
        
        # 5. Configuração do canvas com barras de rolagem e grid layout
        self._setup_scrollable_canvas()
        
        # 6. Separador antes do rodapé
        ttk.Separator(self.frame, orient='horizontal').grid(row=3, column=0, sticky="ew", pady=5)
        
        # 7. Frame para status e botões de ação no rodapé
        self.footer_frame = ttk.Frame(self.frame)
        self.footer_frame.grid(row=4, column=0, sticky="ew", pady=(5, 0))
        self.footer_frame.columnconfigure(0, weight=1)  # O status deve expandir
        self._create_footer_controls()
        self.parent.protocol("WM_DELETE_WINDOW", lambda thisClass=self: _cancel_selection(thisClass))

    def _create_header_controls(self):
        """Cria controles do cabeçalho (pesquisa e seleção)"""
        select_all_frame = ttk.Frame(self.header_frame)
        select_all_frame.pack(side=tk.RIGHT)
        
        select_all_cb = ttk.Checkbutton(select_all_frame, text="Selecionar Todos",
                                     variable=self.select_all_var,
                                     command=lambda var=self.select_all_var,  all=self: _toggle_select_all(all,var))
        select_all_cb.pack(side=tk.RIGHT, padx=5)

    def _setup_scrollable_canvas(self):
        """Configura o canvas com barras de rolagem vertical e horizontal usando grid"""
        # Canvas para conteúdo com rolagem
        self.filter_canvas = tk.Canvas(self.scroll_container, highlightthickness=0)
        self.filter_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Barra de rolagem vertical
        v_scrollbar = ttk.Scrollbar(self.scroll_container, orient="vertical", command=self.filter_canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.filter_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Barra de rolagem horizontal
        h_scrollbar = ttk.Scrollbar(self.scroll_container, orient="horizontal", command=self.filter_canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.filter_canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # Frame interno para conteúdo com grid layout
        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.scrollable_frame.columnconfigure(0, weight=1)  # Coluna única expandível
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")
        
        # Criar janela no canvas para colocar o frame interno
        self.canvas_window = self.filter_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags="content")
        
        # Configurar para expandir com o canvas
        self.scrollable_frame.bind("<Configure>", self._on_content_configure)
        
        # Garantir que o canvas expanda para o tamanho disponível
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        
    def _on_canvas_configure(self, event):
        """Ajusta o tamanho da janela interna conforme o canvas é redimensionado"""
        # Atualiza a largura da janela interna para caber no canvas
        width = event.width
        self.filter_canvas.itemconfig("content", width=width)
        
        # Atualiza a região de rolagem
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def _create_footer_controls(self):
        """Cria controles do rodapé (status e botões) usando grid para melhor distribuição"""
        # Frame para informações de status (à esquerda)
        status_frame = ttk.Frame(self.footer_frame)
        status_frame.grid(row=0, column=0, sticky="w")
        
        self.status_label = ttk.Label(status_frame, text="0 colunas selecionadas")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Frame para botões de ação (à direita)
        button_frame = ttk.Frame(self.footer_frame) 
        button_frame.grid(row=0, column=1, sticky="e")
        
        # Botões com espaçamento consistente
        ttk.Button(button_frame, text="Aplicar", command=lambda: _cancel_selection(self)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=lambda: _cancel_selection(self)).pack(side=tk.RIGHT, padx=5)

    def _setup_event_bindings(self):
        """Configura os eventos para a interface"""
        self.frame.bind("<Configure>", self._on_frame_configure)
        
        # Configurar eventos de scroll para o mouse
        self.filter_canvas.bind_all("<MouseWheel>", self._on_mousewheel_vertical)
        self.filter_canvas.bind_all("<Shift-MouseWheel>", self._on_mousewheel_horizontal)

    def _on_frame_configure(self, event):
        """Ajusta o tamanho da área rolável quando a janela é redimensionada"""
        if hasattr(self, 'filter_canvas') and hasattr(self, 'scrollable_frame') and self.scrollable_frame:
            self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def _on_mousewheel_vertical(self, event):
        """Gerencia o scroll vertical com o mouse"""
        self.filter_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_horizontal(self, event):
        """Gerencia o scroll horizontal com o mouse + Shift"""
        self.filter_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_fields_checkbox_for_show(self):
        """Inicializa a área de conteúdo com checkboxes para colunas"""
        try:
            self.column_filters = {}
            self._add_column_headers()

            # Adiciona as colunas disponíveis usando grid
            for i, col in enumerate(self.column, start=2):
                col_name = col.get("name", f"col_{i}")
                self._add_column_row(col_name, i)

            _update_status_label(self, self.status_label, self.column_for_show)
            self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

        except Exception as e:
            self._log_error(f"Erro ao carregar colunas: {e}")
            messagebox.showerror("Erro", f"Erro ao obter colunas: {e}")

    def _on_content_configure(self, event):
        """Ajusta o tamanho do canvas quando o conteúdo interno muda"""
        # Atualiza a largura da janela no canvas para corresponder à largura do frame interno
        width = event.width
        self.filter_canvas.itemconfig("content", width=width)
        
        # Atualiza a região de rolagem
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def _add_column_headers(self):
        """Adiciona cabeçalhos para as colunas na tabela usando grid"""
        # Estilo para cabeçalhos
        header_style = ("Segoe UI", 10, "bold")
        
        # Adiciona cabeçalhos usando grid
        ttk.Label(
            self.scrollable_frame,
            text="Coluna",
            font=header_style,
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        ttk.Label(
            self.scrollable_frame,
            text="Selecionar",
            font=header_style,
            anchor="e"
        ).grid(row=0, column=1, sticky="e", padx=10, pady=(10, 5))
        
        # Separador visual abaixo dos cabeçalhos
        separator = ttk.Separator(self.scrollable_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 8))

    def _add_column_row(self, col_name, row):
        """Adiciona uma linha para uma coluna na tabela"""
        try:
            
            # Checkbox com entrada
            if  self.column_for_show.get(col_name) is None:
                self.column_for_show[col_name] = True
            checkbutton = CheckboxWithEntry(
                self.scrollable_frame,
                label_text=col_name,
                entry_value=self.column_for_show[col_name],
                entry_width=7
            )
            checkbutton.grid(row=row, padx=5, pady=5, sticky=tk.W)
            
            # Tooltip e configuração de eventos
            checkbutton.checkbox.bind(
                "<Enter>",
                lambda event, cb=checkbutton.checkbox, name=col_name: 
                    _create_tooltip(self, cb, f"Selecione a coluna para exibir na consulta {name}")
            )
            checkbutton.set_on_check(
                lambda event, name=col_name, cb=checkbutton, lista=self.column_for_show, status_label=self.status_label: 
                    self.update_column_filters( name, cb,status_label, event,lista)
            )

            self.column_filters[col_name] = checkbutton
            

        except Exception as e:
            if self.log_message:
                self.log_message(f"Erro ao adicionar checkbox para coluna {col_name}: {e}{type(e).__name__})\n{traceback.format_exc()}", level="error")    

    def _log_error(self, message):
        """Registra uma mensagem de erro no log"""
        if self.log_message:
            self.log_message(message, level="error")
            
    def show_modal(self):
        """Exibe a janela modal para seleção de colunas"""
        self.parent.deiconify()

    def is_modal_open(self):
        """Verifica se a modal está aberta"""
        try:
            return bool(self.parent and self.parent.winfo_ismapped())
        except tk.TclError:
            return False

    def clear(self):
        """Limpa todos os recursos antes de destruir o componente"""
        try:
            # Remove bindings para evitar vazamento de memória
            if hasattr(self, 'filter_canvas'):
                self.filter_canvas.unbind_all("<MouseWheel>")
                self.filter_canvas.unbind_all("<Shift-MouseWheel>")
            
            # Limpa estruturas de dados
            self.column_filters.clear()
            # self.column_for_show.clear()
        except Exception as e:
            self._log_error(f"Erro ao limpar recursos: {e}")