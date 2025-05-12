from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Callable, Optional, Dict, Union, List, TypedDict
import traceback
import threading
from functools import partial
from utils.editar_detalher import _executar_consulta, _get_foreign_keys, _get_foreign_keys2, _obter_campo_primary_key, _obter_column_types, _preparar_consulta, _tabela_existe
from utils.validarText import (
    _atualizar_dataframe,
    _confirmar_salvamento,
    _convert_column_type_for_string_one,
    _executar_update,
    _fetch_enum_values,
    _lidar_com_erro_sql,
    _map_column_type,
    _notificar_sucesso,
    _obter_valores_atualizados,
    _tem_erros_de_validacao,
    build_update_query,
    quote_identifier,
    validar_numero,
    verificar_num_column
)

class ColumnInfo(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Any

class EditModal(tk.Toplevel):
    """Creates a modal to edit a record from a DataFrame and save to the database."""

    def __init__(
        self, master: Any, databse_name, engine, log_message, df: pd.DataFrame, table_name: str, row_index: int,
        primary_key_value: str, name_campo_primary_key: str, edit_enabled: bool, is_opened_callback: Optional[Callable] = None,
        db_type: str = "postgresql", on_data_change: Optional[Callable[[pd.DataFrame], None]] = None,
        column_types: Optional[Dict[str, str]] = None, enum_values: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize the EditModal.
        Args:
            master: The parent widget
            engine: SQLAlchemy engine
            df: DataFrame containing the data
            table_name: Name of the database table
            row_index: Index of the row being edited
            primary_key_value: Value of the primary key
            name_campo_primary_key: Column name of the primary key
            edit_enabled: Whether editing is allowed
            db_type: Database type (postgresql, mysql, etc.)
            on_data_change: Callback function when data changes
            column_types: Dictionary of column types
            enum_values: Dictionary of enum values for dropdown fields
        """
        super().__init__(master)
        self.df = df
        self.engine = engine
        self.table_name = table_name
        self.row_index = row_index
        self.name_campo_primary_key = name_campo_primary_key
        self.on_data_change = on_data_change
        self.edit_enabled = edit_enabled
        self.db_type = db_type.strip().lower()
        self.database_name = databse_name
        self.is_opened_callback = is_opened_callback
        self.enum_values = enum_values or {}
        self.column_info = column_types or {}
        self.column_types: Dict[str, str] = {}
        self.log_message = log_message
        self.field_entries: Dict[str, Union[ttk.Entry, ttk.Combobox, tk.BooleanVar]] = {}
        self.loading_thread = None

        self.record_id = (
            primary_key_value
            if primary_key_value
            else self.df.at[self.row_index, self.name_campo_primary_key]
        )

        # Configurar estilos
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Disabled.TEntry", foreground="#FFFFFF", fieldbackground="#0000FF")

        # Setup the basic window structure
        self._setup_window()
        
        # Start loading data in a separate thread
        self._load_data()
        # Check loading status periodically
        self._create_widgets()

    def _load_data(self):
        """Load data in a background thread"""
        try:
            # Get foreign key relationships
            if isinstance(self.table_name, str):
                self.foreign_key_relationship = _get_foreign_keys(self)
            else: 
                self.foreign_key_relationship = _get_foreign_keys2(self)
            # print(self.foreign_key_relationship)
            # Process the selected row
            self.linha_select_df = self.df.iloc[self.row_index].copy()
            if self.edit_enabled:
                verificar_num_column(self)
            
        except Exception as e:
            self.log_message(f"Error loading data: {str(e)}\n{traceback.format_exc()}", level="error")

    def _setup_window(self):
        """Configura a janela modal."""
        self.title(f'Carregando... {self.table_name}')
        self.geometry("600x600")  # Initially smaller until content is loaded
        self.minsize(500, 400)
        self.transient(self.master)
        self.grab_set()
        self.resizable(True, True)
        # Centraliza a janela
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def _on_close(self):
        """Evento ao fechar a janela."""
        if self.is_opened_callback:
            self.is_opened_callback()
        self.destroy()

    def _scroll_canvas(self, event, canvas):
        """Rola a área de conteúdo com o scroll do mouse."""
        if event.num == 5 or event.delta < 0:
            canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-1, "units")

    def _adjust_canvas_scrollregion(self, canvas):
        """Ajusta o tamanho do canvas para incluir todos os widgets."""
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _create_widgets(self):
        """Cria campos de entrada e botões."""
        # Clear the loading indicator
        # for widget in self.winfo_children():
        #     widget.destroy()
            
        # Update title
        self.title(f'Editar Registro - {self.table_name}')
        self.geometry("600x600")
            
        main_frame = ttk.Frame(self, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame, style="TFrame")
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 5), padx=10)

        ttk.Label(
            header_frame,
            text=f"Tabela: {self.table_name} | ID: {self.record_id}",
            font=("Arial", 12, "bold"),
            style="TLabel"
        ).pack(anchor=tk.W)

        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, padx=10)

        # Área de conteúdo com scroll
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(content_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        self.fields_frame = ttk.Frame(canvas, style="TFrame")

        canvas.create_window((0, 0), window=self.fields_frame, anchor=tk.NW, tags="win", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Botões de ação
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)

        self.save_button = ttk.Button(
            button_frame,
            text="✏Salvar",
            command=self._save_changes,
            state="normal" if self.edit_enabled else "disabled"
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(
            button_frame,
            text="🗑 Apagar",
            command=self._delete_record,
            state="normal" if self.edit_enabled else "disabled"
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text=" ❌Cancelar", command=self._on_close).pack(side=tk.RIGHT, padx=5)

        # Eventos de scroll e resize
        self.fields_frame.bind("<Configure>", lambda e: self._adjust_canvas_scrollregion(canvas))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("win", width=e.width - 4))
        
        # Use a more efficient binding method instead of bind_all
        canvas.bind("<MouseWheel>", lambda e: self._scroll_canvas(e, canvas))
        canvas.bind("<Button-4>", lambda e: self._scroll_canvas(e, canvas))
        canvas.bind("<Button-5>", lambda e: self._scroll_canvas(e, canvas))

        # Create the fields
        self._create_fields_efficiently()

    def _create_fields_efficiently(self):
        """Creates form fields more efficiently with batching."""
        try:
            # Convert to dictionary for faster lookups
            self.linha_select_df = self.linha_select_df.to_dict() if not isinstance(self.linha_select_df, dict) else self.linha_select_df
            
            # Cabeçalho estilizado
            header_frame = ttk.Frame(self.fields_frame)
            header_frame.grid(row=0, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=5)

            ttk.Label(header_frame, text="Campo", font=("Arial", 11, "bold"),
                    style="Header.TLabel").pack(side=tk.LEFT, padx=(0, 50))
            ttk.Label(header_frame, text="Valor", font=("Arial", 11, "bold"),
                    style="Header.TLabel").pack(side=tk.LEFT)

            # Separador
            ttk.Separator(self.fields_frame, orient="horizontal").grid(
                row=1, column=0, columnspan=3, sticky=tk.EW, pady=8
            )

            # Frame rolável
            scrollable_frame = ttk.Frame(self.fields_frame)
            scrollable_frame.grid(row=2, column=0, sticky=tk.NSEW)
            self.fields_frame.rowconfigure(2, weight=1)
            self.fields_frame.columnconfigure(0, weight=1)
            # print(self.foreign_key_relationship)
            for i, col in enumerate(self.column_info, start=2):
                self._create_field_batch(scrollable_frame, col,i)
                
                # Allow UI to update between batches
                # self.update_idletasks()

        except Exception as e:
            self.log_message(f"Erro ao criar campos: {str(e)}({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao criar campos de edição: {str(e)}")

    def _create_field_batch(self, parent_frame, col, i):
        """Cria um lote de widgets de campos dinamicamente."""
        col_name = col.get("name", f"coluna_{i}")
        col_type = str(col.get("type", "string")).lower()
        nullable = col.get("nullable", True)
        tabela = col.get("table")

        value = self.linha_select_df.get(col_name, "")
        self.log_message(f"Valor de {col_name}: {value}", level="info")

        # Container do campo
        field_row = ttk.Frame(parent_frame)
        field_row.pack(fill=tk.X, padx=5, pady=6, expand=True)

        # Label
        label_text = f"{col_name}{' *' if not nullable else ''}"
        label_style = "Required.TLabel" if not nullable else None
        label = ttk.Label(field_row, text=label_text, width=20, anchor=tk.W, style=label_style)
        label.pack(side=tk.LEFT, padx=(5, 10))

        # Criação do widget com base no tipo
        self._create_typed_widget_efficiently(field_row, col_name, col_type, value, nullable, tabela)


    def _create_typed_widget_efficiently(self, parent_frame, col_name, col_type, value, nullable, tabela):
        """Improved version of _create_typed_widget with performance optimizations."""
        try:
            str_value = str(value) if value is not None else ""
            self.linha_select_df[col_name] = str_value
            
            # Determine if this is a primary key or foreign key (only once per field)
            is_primary_key = col_name in getattr(self, 'primary_keys', []) or col_name == self.name_campo_primary_key
            
            # Avoid expensive lookups for each field
            if isinstance(self.table_name, str):
                foreign_table = self.foreign_key_relationship.get(col_name)
            else:
                foreign_table = self.foreign_key_relationship.get(tabela, {}).get(col_name)
            
            
            is_foreign_key = True if foreign_table else False
            state = "disabled" if False else "normal"

            # Cache the column type mapping
            if col_name not in self.column_types:
                self.column_types[col_name] = _map_column_type(col_type)

            # Container for the widget
            widget_container = ttk.Frame(parent_frame)
            widget_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

            widget = None

            # Simplified widget creation based on type
            if "enum" in col_type:
                values = self.enum_values.get(col_name, ["Valor não disponível"])
                widget = ttk.Combobox(widget_container, values=values,
                                    state="readonly" if not False  else "disabled",
                                    width=30)
                widget.set(str_value)
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            elif "int" in col_type:
                vcmd = self.register(validar_numero)
                widget = ttk.Entry(widget_container, validate="key",
                                validatecommand=(vcmd, "%P"),
                                state=state, width=30)
                widget.insert(0, str_value)
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            elif any(t in col_type for t in ["float", "decimal", "numeric"]):
                vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
                widget = ttk.Entry(widget_container, validate="key",
                                validatecommand=(vcmd, "%P"),
                                state=state, width=30)
                widget.insert(0, str_value)
                
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            elif col_type in ["bool", "boolean", "bit"]:
                is_checked = str_value.lower() in ("true", "1", "t", "yes", "sim", "verdadeiro")
                var = tk.BooleanVar(value=is_checked)

                switch_frame = ttk.Frame(widget_container)
                switch_frame.pack(side=tk.LEFT, fill=tk.X)

                widget = ttk.Checkbutton(switch_frame, variable=var,
                                        style="Switch.TCheckbutton", state=state)
                widget.pack(side=tk.LEFT, padx=5)

                status_label = ttk.Label(switch_frame, text="Sim" if is_checked else "Não")
                status_label.pack(side=tk.LEFT, padx=5)

                def update_status(*_):
                    status_label.configure(text="Sim" if var.get() else "Não")

                var.trace_add("write", update_status)
                self.field_entries[col_name] = var  # Store the variable instead of widget

            elif any(t in col_type for t in ["date", "time", "datetime", "timestamp"]):
                # Simplified date handling
                widget = None
                # Only create specialized widget if value needs formatting
                # print(f"Valor de {col_name} antes de criar widget: {value} ({type(value).__name__})")
                
                # Create a delayed action to create the date widget
                self.after(10, lambda cn=col_name, ct=col_type: self._create_date_widget(
                    widget_container, cn, ct, str_value
                ))

            else:
                widget = ttk.Entry(widget_container, state=state, width=30)
                widget.insert(0, str_value)
                widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            # Simple icon for primary key
            if is_primary_key and hasattr(widget, "configure"):
                widget.configure(style="Primary.TEntry")
                ttk.Label(widget_container, text="🔑", foreground="#3a87ad").pack(side=tk.LEFT, padx=2)

            # Create button for foreign key relationship - lazily
            if is_foreign_key:
                # Create lookup button with partial function to avoid closure issues
                print(f"Valor de {col_name} antes de criar widget: {str_value} ({type(str_value).__name__})")
                lookup_button = ttk.Button(
                    widget_container, text="🔍", width=3,
                    command=partial(self._ver_tabela_relacionada, foreign_table, value),
                    style="Lookup.TButton"
                )
                lookup_button.pack(side=tk.LEFT, padx=2)
                ttk.Label(widget_container, text=f"→ {foreign_table}",
                        foreground="#6c757d", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

            # Store the widget reference
            # print(f"Valor inserido no widget de {col_name}: {"existe" if widget else "não existe"}")
            if widget and col_name not in self.field_entries:
                self.field_entries[col_name] = widget

        except Exception as e:
            self.log_message(f"Erro ao criar widget '{col_name}': {e}({type(e).__name__})\n{traceback.format_exc()}", level="error")
            fallback = ttk.Entry(parent_frame, width=30)
            fallback.insert(0, str(value) if value else "")
            fallback.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.field_entries[col_name] = fallback

    def _create_date_widget(self, parent, col_name, col_type, value):
        """Cria um widget para visualizar/editar campos de data, mesmo com valores vazios ou nulos"""
        try:
            format_map = {
                "datetime": ("%Y-%m-%d %H:%M:%S", "AAAA-MM-DD HH:MM:SS"),
                "timestamp": ("%Y-%m-%d %H:%M:%S", "AAAA-MM-DD HH:MM:SS"),
                "date": ("%Y-%m-%d", "AAAA-MM-DD"),
                "time": ("%H:%M:%S", "HH:MM:SS"),
                "year": ("%Y", "AAAA"),
                "month": ("%m", "MM"),
                "day": ("%d", "DD"),
            }

            date_format, format_text = "%Y-%m-%d", "AAAA-MM-DD"
            for tipo, (fmt, label_fmt) in format_map.items():
                if tipo in col_type.lower():
                    date_format, format_text = fmt, label_fmt
                    break

            frame = tk.LabelFrame(parent, bd=1, relief=tk.SOLID, bg="#f0f0f0", text=format_text)
            frame.pack(side=tk.LEFT, padx=5, pady=2)

            entry = tk.Entry(frame, width=30, font=("Arial", 10), bd=0, bg="white")
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            if value:
                try:
                    if isinstance(value, datetime):
                        entry.insert(0, value.strftime(date_format))
                    else:
                        entry.insert(0, str(value).strip())
                except Exception:
                    self.log_message(f"Erro ao formatar data: {value} ({type(value).__name__})", level="error")
                    entry.insert(0, "")

            self.field_entries[col_name] = entry
            self.linha_select_df[col_name] = lambda: entry.get().strip()

        except Exception as e:
            self.log_message(f"Erro criando widget de data: {e}", level="error")


    def _save_changes(self):
        """Função principal para salvar alterações em qualquer banco de dados."""
        try:
            self.save_button.config(state="disabled")
            if _tem_erros_de_validacao(self):
                return

            updated_values = _obter_valores_atualizados(self)
            if not updated_values:
                messagebox.showinfo("Sem alterações", "Nenhuma alteração foi detectada.")
                self.log_message("Nenhuma alteração foi detectada.", level="info")
                return

            query = build_update_query(self, self.table_name, updated_values, self.name_campo_primary_key)
            if query is None or not _confirmar_salvamento(self):
                return

            _executar_update(self, query)
            _atualizar_dataframe(self, updated_values)
            _notificar_sucesso(self)

        except SQLAlchemyError as e:
            _lidar_com_erro_sql(self, e)
        except Exception as es:
            self.log_message(f"Erro ao atualizar o registro: {es} ({type(es).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao salvar as alterações: {str(es)}")
        finally:
            self.save_button.config(state="normal")

    def _delete_record(self):
        """Função para deletar um registro do banco de dados."""
        try:
            confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este registro?")
            if not confirm:
                return

            self.delete_button.config(state="disabled")
            query = text(f"DELETE FROM {quote_identifier(self.db_type, self.table_name)} WHERE {quote_identifier(self.db_type, self.name_campo_primary_key)} = :primary_key")
            params = {"primary_key": _convert_column_type_for_string_one(self.column_types, self.name_campo_primary_key, self.record_id)}

            with self.engine.begin() as conn:
                conn.execute(query, params)

            self.log_message(f"Registro {self.record_id} deletado com sucesso! query ={query}", level="info")
            messagebox.showinfo("Sucesso", "Registro deletado com sucesso!")
            
            self.df = self.df[self.df[self.name_campo_primary_key] != self.record_id]

            if self.on_data_change:
                self.on_data_change(self.df)
                
            self._on_close()

        except SQLAlchemyError as e:
            self.log_message(f"Erro SQL ao deletar o registro: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao deletar o registro: {str(e)}")
        except Exception as e:
            self.log_message(f"Erro ao deletar o registro: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao deletar o registro: {str(e)}")
        finally:
            self.delete_button.config(state="normal")
            
    def _ver_tabela_relacionada(self, tabela_referenciada, valor_chave):
        """
        Busca dados da tabela relacionada e abre uma modal para visualização/edição.
        Reutiliza a modal existente se já estiver aberta.
        """
        try:
            self.log_message(f"Buscando dados da tabela relacionada '{tabela_referenciada}' com chave {valor_chave}", level="info")
            
            if not valor_chave:
                self.log_message("Valor de chave não fornecido para consulta relacionada", level="warning")
                return
            
            # Verificar se já existe uma modal aberta para esta tabela
            modal_existente = getattr(self, 'modal_edit', None)
            
            # Start a loading indicator
            loading_window = tk.Toplevel(self)
            loading_window.title("Carregando...")
            loading_window.geometry("300x100")
            loading_window.transient(self)
            loading_window.grab_set()
            
            ttk.Label(loading_window, text=f"Carregando dados de {tabela_referenciada}...").pack(pady=10)
            progress = ttk.Progressbar(loading_window, mode="indeterminate")
            progress.pack(fill=tk.X, padx=20, pady=10)
            progress.start()
            
            # Center the loading window
            loading_window.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() // 2) - (loading_window.winfo_width() // 2)
            y = self.winfo_rooty() + (self.winfo_height() // 2) - (loading_window.winfo_height() // 2)
            loading_window.geometry(f"+{x}+{y}")
            
            # Use threading to avoid freezing the UI
            def load_related_data():
                try:
                    # Verificar se a tabela existe
                    if not _tabela_existe(self, tabela_referenciada):
                        self.after(0, lambda: loading_window.destroy())
                        return
                    
                    # Determinar a coluna de chave primária da tabela relacionada
                    campo_primary_key = _obter_campo_primary_key(self, tabela_referenciada)
                    if not campo_primary_key:
                        self.after(0, lambda: loading_window.destroy())
                        return
                    
                    # Preparar consulta segura para diferentes tipos de banco de dados
                    query, params = _preparar_consulta(self, tabela_referenciada, campo_primary_key, valor_chave)
                    
                    # Executar consulta
                    conn, df = _executar_consulta(self, query, params, tabela_referenciada, campo_primary_key)
                    if df is None:
                        self.log_message(f"Nenhum registro encontrado na tabela '{tabela_referenciada}' com {campo_primary_key}={valor_chave}", level="info")
                        self.after(0, lambda: loading_window.destroy())
                        return

                    column_types = _obter_column_types(self,tabela_referenciada)
                    enum_values = _fetch_enum_values(self=self, columns=column_types, text=text, table_name=tabela_referenciada, traceback=traceback)
                    
                    # Open the modal in the main thread
                    self.after(0, lambda: self._finish_opening_modal(
                        loading_window, df, tabela_referenciada, campo_primary_key, column_types, enum_values,
                        modal_existente
                    ))
                    
                except Exception as e:
                    self.log_message(f"Erro ao carregar dados relacionados: {str(e)}({type(e).__name__})\n{traceback.format_exc()}", level="error")
                    self.after(0, lambda: loading_window.destroy())
                    self.after(0, lambda e=e: messagebox.showerror("Erro", f"Falha ao carregar dados relacionados: {str(e)}"))
            
            # Start the thread
            threading.Thread(target=load_related_data, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"Erro ao iniciar carregamento de dados relacionados:  {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao iniciar carregamento: {str(e)}")


    def _finish_opening_modal(self, loading_window, df, tabela_referenciada, campo_primary_key, column_types, enum_values, modal_existente=None):
        """Finish opening the modal after data is loaded, reusing existing modal if available"""
        # Close the loading window
        loading_window.destroy()
        
        selected_row_index = 0  # Primeiro registro encontrado
        primary_key_value = df.iloc[selected_row_index][campo_primary_key]
        
        # Verificar se a modal existente é para a mesma tabela e ainda existe
        if modal_existente and hasattr(modal_existente, 'winfo_exists') and modal_existente.winfo_exists():
            if modal_existente.table_name == tabela_referenciada:
                # Atualizar a modal existente
                if modal_existente.atualizar_valores(df=df, row_index=selected_row_index, primary_key_value=primary_key_value):
                    # Trazer a modal para frente
                    modal_existente.lift()
                    modal_existente.focus_set()
                    return
        
        # Função de callback para fechar a modal
        def _fechar_modal():
            self.modal_edit = None
        
        # Criar nova modal se necessário
        self.modal_edit = EditModal(
            master=self, 
            databse_name=self.database_name,
            engine=self.engine, 
            log_message=self.log_message,
            df=df, 
            row_index=selected_row_index,
            is_opened_callback=_fechar_modal,
            name_campo_primary_key=campo_primary_key, 
            primary_key_value=primary_key_value,
            db_type=self.db_type,
            table_name=tabela_referenciada,
            on_data_change=self.on_data_change, 
            edit_enabled=self.edit_enabled,
            column_types=column_types, 
            enum_values=enum_values
        )
        
        # Exibir a modal
        self.modal_edit.focus_set()
    
    def atualizar_valores(self, df=None, row_index=None, primary_key_value=None):
        """
        Atualiza os valores dos campos existentes sem recriar a modal.
        
        Args:
            df (pd.DataFrame, optional): Novo DataFrame com dados atualizados
            row_index (int, optional): Novo índice da linha a ser editada
            primary_key_value (str, optional): Novo valor da chave primária
        """
        try:
            # Atualizar os dados se fornecidos
            if df is not None:
                self.df = df
            
            if row_index is not None:
                self.row_index = row_index
                
            if primary_key_value is not None:
                self.record_id = primary_key_value
            else:
                self.record_id = self.df.at[self.row_index, self.name_campo_primary_key]
            
            # Atualizar o título da janela
            self.title(f'Editar Registro - {self.table_name} | ID: {self.record_id}')
            
            # Obter nova linha selecionada
            self.linha_select_df = self.df.iloc[self.row_index].copy()
            if isinstance(self.linha_select_df, pd.Series):
                self.linha_select_df = self.linha_select_df.to_dict()
                
            # Atualizar valores dos campos
            for col_name, widget in self.field_entries.items():
                valor = self.linha_select_df.get(col_name, "")
                str_valor = str(valor) if valor is not None else ""
                
                # Identificar e atualizar com base no tipo de widget
                if isinstance(widget, tk.BooleanVar):
                    # Para checkbox/boolean
                    widget.set(str_valor.lower() in ("true", "1", "t", "yes", "sim", "verdadeiro"))
                elif isinstance(widget, ttk.Combobox):
                    # Para combobox/enum
                    if str_valor in widget["values"]:
                        widget.set(str_valor)
                    else:
                        widget.set("")
                elif hasattr(widget, "delete") and hasattr(widget, "insert"):
                    # Para widgets tipo Entry e similares
                    widget.delete(0, tk.END)
                    widget.insert(0, str_valor)
                    
            self.log_message(f"Valores atualizados com sucesso para {self.table_name} ID: {self.record_id}", level="info")
            return True
            
        except Exception as e:
            self.log_message(f"Erro ao atualizar valores: {str(e)}\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao atualizar valores dos campos: {str(e)}")
            return False