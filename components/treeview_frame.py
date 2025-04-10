import tkinter as tk
from tkinter import ttk
import traceback
import pandas as pd
from typing import Any, Optional

class TreeViewFrame(ttk.Frame):
    """Cria um Treeview para exibir um DataFrame do pandas com colunas responsivas."""
    
    def __init__(self, master: Any,databse_name, show_edit_modal: Any,log_message:Any, df: Optional[pd.DataFrame] = None,
                 columns: Optional[dict[str, Any]] = None, column_width: int = 100, min_column_width: int = 50):
        super().__init__(master)
        self.df = df if df is not None else pd.DataFrame()
        self.column_width = column_width
        self.min_column_width = min_column_width
        self.show_edit_modal = show_edit_modal
        self.log_message=log_message
        self.columns = []
        for i, col in enumerate(columns, start=1):
            self.columns.append(col["name"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
       
        self.resizing_column = None
        self.resizing_x = 0
        self.databse_name = databse_name

        self._create_widgets()
        self._setup_columns()
        self.update_table(df, current_page=0, rows_per_page=0)
        self._bind_events()

    def _create_widgets(self):
        """Cria o Treeview e os scrollbars."""
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.grid(row=0, column=0, sticky="nsew")
        self.tree_frame.rowconfigure(0, weight=1)
        self.tree_frame.columnconfigure(0, weight=1)

        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree_yview)
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns")

        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree_xview)
        self.tree_scroll_x.grid(row=1, column=0, sticky="ew")
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=list(self.columns),
            show='headings',
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set,
            style="DataTable.Treeview"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

    def tree_yview(self, *args):
        """Vincula o scrollbar vertical ao Treeview."""
        self.tree.yview(*args)

    def tree_xview(self, *args):
        """Vincula o scrollbar horizontal ao Treeview."""
        self.tree.xview(*args)

    def _bind_events(self):
        """Configura eventos do Treeview."""
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<ButtonPress-1>", self._on_button_press)
        self.tree.bind("<ButtonRelease-1>", self._on_button_release)
        self.tree.bind("<B1-Motion>", self._on_motion)
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        """Ajusta o tamanho das colunas proporcionalmente ao redimensionar o widget."""
        if self.df.empty or event.width <= 1:
            return

        available_width = event.width - 20
        columns = self.tree["columns"]
        col_widths = [int(self.tree.column(col, "width")) for col in columns]

        if sum(col_widths) > 0:
            for i, col in enumerate(columns):
                new_width = max(self.min_column_width, int((col_widths[i] / sum(col_widths)) * available_width))
                self.tree.column(col, width=new_width)
    def _fechar_modal(self):
        # self.modal_aberto = False
        return
    def _on_double_click(self, event):
        """Abre o modal de edição ao dar duplo clique em um item."""
        # if self.modal_aberto:
        #     return
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            item_id = self.tree.identify_row(event.y)
            if item_id:
                try:
                    index = self.tree.index(item_id)  # Obtém o índice no TreeView
                    self.log_message(self, f"Duplo clique detectado. ID: {item_id}, Índice no TreeView: {index}")
                    self.show_edit_modal(index,self._fechar_modal)  # Passa o índice correto
                    # self.modal_aberto = True
                except Exception as e:
                    self.log_message(self, f"Erro ao identificar índice no TreeView: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")

    def _on_button_press(self, event):
        """Inicia o redimensionamento de colunas."""
        if self.tree.identify("region", event.x, event.y) == "separator":
            self.resizing_column = self.tree.identify_column(event.x)
            self.resizing_x = event.x

    def _on_button_release(self, event):
        """Finaliza o redimensionamento de colunas."""
        self.resizing_column = None

    def _on_motion(self, event):
        """Redimensiona a coluna durante o movimento do mouse."""
        if self.resizing_column:
            delta_x = event.x - self.resizing_x
            col_index = int(self.resizing_column.replace('#', '')) - 1
            col_name = self.tree["columns"][col_index]
            new_width = max(self.min_column_width, int(self.tree.column(col_name, "width")) + delta_x)
            self.tree.column(col_name, width=new_width)
            self.resizing_x = event.x

    def _setup_columns(self):
        """Configura as colunas do Treeview."""

        if self.df is None or self.df.empty:
            self.tree["columns"] = self.columns
            self.tree["show"] = "headings"
            self.log_message("Aviso: DataFrame está vazio ou indefinido. Nenhuma coluna será configurada.")
            return

        # Configura colunas com base no DataFrame
        self.tree["columns"] = list(self.df.columns)
        self.tree["show"] = "headings"

        for col in self.df.columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, width=self._calculate_column_width(col), anchor=tk.CENTER, minwidth=self.min_column_width)

    def _calculate_column_width(self, column_name):
        """Calcula a largura ideal de uma coluna."""
        if self.df.empty:
            return self.column_width
        
        sample = self.df.head(20)
        max_data_length = sample[column_name].astype(str).str.len().max() * 8 if column_name in sample else 0
        return max(len(str(column_name)) * 20, max_data_length, self.column_width)

    def update_table(self, df: pd.DataFrame, current_page: int, rows_per_page: int):
        """Atualiza a tabela com novos dados mantendo a paginação."""
        self.df = df.copy() if df is not None else pd.DataFrame()

        for row in self.tree.get_children():
            self.tree.delete(row)

        if list(self.tree["columns"]) != list(self.df.columns):
            self._setup_columns()

        start_idx = current_page * rows_per_page
        end_idx = min(start_idx + rows_per_page, len(self.df))
        paged_df = self.df.iloc[start_idx:end_idx] if rows_per_page > 0 else self.df

        for _, row in paged_df.iterrows():
            self.tree.insert("", "end", values=row.tolist())

    def get_selected_item(self):
        """Retorna o índice do item selecionado."""
        selection = self.tree.selection()
        return self.tree.index(selection[0]) if selection else None

    def select_item(self, index):
        """Seleciona um item pelo índice."""
        items = self.tree.get_children()
        if 0 <= index < len(items):
            item_id = items[index]
            self.tree.selection_set(item_id)
            self.tree.focus(item_id)
            self.tree.see(item_id)

