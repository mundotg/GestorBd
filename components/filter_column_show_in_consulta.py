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
    """Gerencia a exibição de colunas em consultas com UI usando Tkinter."""

    def __init__(self, parent, column_for_show, column, log_message=None, table_name=None, update_column_filters=None):
        self.parent = parent
        self.column = column or []
        self.column_for_show = column_for_show or {}
        self.table_name = table_name
        self.log_message = log_message
        self.update_column_filters = update_column_filters

        self.select_all_var = tk.BooleanVar(value=False)
        self.status_label = None
        self.scrollable_frame = None
        self.tooltip = None

        self._build_ui()
        self._setup_event_bindings()
        self._populate_checkboxes()

    def _build_ui(self):
        """Constrói toda a estrutura visual da interface."""
        try:
            self.frame = ttk.Frame(self.parent)
            self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(3, weight=1)

            self.header_frame = ttk.Frame(self.frame)
            self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
            self._build_header_controls()

            ttk.Separator(self.frame, orient='horizontal').grid(row=1, column=0, sticky="ew", pady=5)

            self.scroll_container = ttk.Frame(self.frame)
            self.scroll_container.grid(row=2, column=0, sticky="nsew")
            self.scroll_container.columnconfigure(0, weight=1)
            self.scroll_container.rowconfigure(0, weight=1)
            self._build_scrollable_canvas()

            ttk.Separator(self.frame, orient='horizontal').grid(row=3, column=0, sticky="ew", pady=5)

            self.footer_frame = ttk.Frame(self.frame)
            self.footer_frame.grid(row=4, column=0, sticky="ew", pady=(5, 0))
            self.footer_frame.columnconfigure(0, weight=1)
            self._build_footer_controls()

            self.parent.protocol("WM_DELETE_WINDOW", lambda: _cancel_selection(self))
        except Exception as e:
            self._log_error(f"Erro ao construir a interface: {e}")
            messagebox.showerror("Erro", f"Erro ao construir a interface: {e}")

    def _build_header_controls(self):
        """Cria a área de seleção geral no topo."""
        select_all_frame = ttk.Frame(self.header_frame)
        select_all_frame.pack(side=tk.RIGHT)
        def _on_select_all():
            """Ação ao clicar no checkbox 'Selecionar Todos'."""
            _toggle_select_all(self, self.select_all_var)

        ttk.Checkbutton(
            select_all_frame,
            text="Selecionar Todos",
            variable=self.select_all_var,
            command= _on_select_all
        ).pack(side=tk.RIGHT, padx=5)

    def _build_scrollable_canvas(self):
        """Cria canvas com barras de rolagem para os checkboxes."""
        self.filter_canvas = tk.Canvas(self.scroll_container, highlightthickness=0)
        self.filter_canvas.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(self.scroll_container, orient="vertical", command=self.filter_canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.filter_canvas.configure(yscrollcommand=v_scroll.set)

        h_scroll = ttk.Scrollbar(self.scroll_container, orient="horizontal", command=self.filter_canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.filter_canvas.configure(xscrollcommand=h_scroll.set)

        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.scrollable_frame.columnconfigure(0, weight=1)

        self.canvas_window = self.filter_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags="content")

        self.scrollable_frame.bind("<Configure>", self._on_content_configure)
        self.filter_canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_footer_controls(self):
        """Cria o rodapé com rótulo de status e botões."""
        status_frame = ttk.Frame(self.footer_frame)
        status_frame.grid(row=0, column=0, sticky="w")

        self.status_label = ttk.Label(status_frame, text="0 colunas selecionadas")
        self.status_label.pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(self.footer_frame)
        button_frame.grid(row=0, column=1, sticky="e")

        ttk.Button(button_frame, text="Aplicar", command=lambda: _cancel_selection(self)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=lambda: _cancel_selection(self)).pack(side=tk.RIGHT, padx=5)

    def _setup_event_bindings(self):
        """Liga eventos de rolagem e redimensionamento."""
        try:
            self.frame.bind("<Configure>", self._on_frame_resize)
            self.filter_canvas.bind_all("<MouseWheel>", self._on_mousewheel_vertical)
            self.filter_canvas.bind_all("<Shift-MouseWheel>", self._on_mousewheel_horizontal)
        except Exception as e:
            self._log_error(f"Erro ao configurar eventos: {e}{type(e)}{e.__class__}{e.__traceback__}")
            messagebox.showerror("Erro", f"Erro ao configurar eventos: {e}")

    def _on_canvas_resize(self, event):
        self.filter_canvas.itemconfig("content", width=event.width)
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def _on_content_configure(self, event):
        self.filter_canvas.itemconfig("content", width=event.width)
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def _on_frame_resize(self, event):
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def _on_mousewheel_vertical(self, event):
        try:
            if self.filter_canvas.winfo_exists():
                self.filter_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass  # Ignora se o widget foi destruído

    def _on_mousewheel_horizontal(self, event):
        try:
            if self.filter_canvas.winfo_exists():
                self.filter_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass  # Ignora se o widget foi destruído

    def _populate_checkboxes(self):
        """Cria os checkboxes a partir das colunas disponíveis."""
        try:
            self.column_filters = {}
            self._add_column_headers()

            for i, col in enumerate(self.column, start=2):
                col_name = col.get("name", f"col_{i}")
                self._add_column_row(col_name, i)

            _update_status_label(self, self.status_label, self.column_for_show)
            self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
        except Exception as e:
            self._log_error(f"Erro ao carregar colunas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar colunas: {e}")

    def _add_column_headers(self):
        """Adiciona cabeçalhos da tabela de colunas."""
        font = ("Segoe UI", 10, "bold")

        ttk.Label(self.scrollable_frame, text="Coluna", font=font).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        ttk.Label(self.scrollable_frame, text="Selecionar", font=font).grid(row=0, column=1, sticky="e", padx=10, pady=(10, 5))

        ttk.Separator(self.scrollable_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 8))

    def _add_column_row(self, col_name, row):
        """Adiciona uma linha da tabela com checkbox."""
        try:
            if self.column_for_show.get(col_name) is None:
                self.column_for_show[col_name] = True

            checkbox = CheckboxWithEntry(
                self.scrollable_frame,
                label_text=col_name,
                entry_value=self.column_for_show[col_name],
                entry_width=7
            )
            checkbox.grid(row=row, padx=5, pady=5, sticky=tk.W)

            checkbox.checkbox.bind(
                "<Enter>",
                lambda event, cb=checkbox.checkbox, name=col_name:
                    _create_tooltip(self, cb, f"Selecione a coluna para exibir na consulta {name}")
            )
            checkbox.set_on_check(
                lambda event, name=col_name, cb=checkbox, lista=self.column_for_show, status_label=self.status_label:
                    self._safe_update_column(name, cb, status_label, event, lista)
            )

            self.column_filters[col_name] = checkbox
        except Exception as e:
            self._log_error(f"Erro ao adicionar linha da coluna '{col_name}': {e}")
            messagebox.showerror("Erro", f"Erro ao adicionar a coluna '{col_name}': {e}")
            
    def _safe_update_column(self, name, cb, status_label, event, lista):
        try:
            self.update_column_filters(name, cb, status_label, event, lista)
        except Exception as e:
            self._log_error(f"Erro ao atualizar coluna '{name}': {e}")
            messagebox.showerror("Erro", f"Erro ao atualizar a coluna '{name}': {e}")
    def _log_error(self, message):
        """Exibe ou registra uma mensagem de erro."""
        if self.log_message:
            self.log_message(f"[FiltroConsulta] {message}", level="error")
        else:
            print(f"[FiltroConsulta] {message}")
            print(traceback.format_exc())
