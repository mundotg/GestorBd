from datetime import datetime
from tkinter import  ttk
import tkinter as tk
import traceback

from utils.metodoGui import _add_placeholder

def _create_tooltip(self, widget, text):
    """
    Cria um tooltip (dica flutuante) para um widget.
    
    Args:
        widget: Widget que receberá o tooltip
        text: Texto a ser exibido no tooltip
    """
    def enter(event):
        """Mostra o tooltip quando o mouse entra no widget."""
        try:
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25

            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)  # Remove bordas da janela
            self.tooltip.wm_geometry(f"+{x}+{y}")  # Posiciona próximo ao widget

            # Cria label com o texto do tooltip
            label = ttk.Label(self.tooltip, text=text, justify=tk.LEFT,
                            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                            font=("", 9, "normal"))
            label.pack(ipadx=3, ipady=2)
        except Exception:
            # Ignora erros na criação do tooltip - não é crítico
            pass

    def leave(event):
        """Remove o tooltip quando o mouse sai do widget."""
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except Exception:
                # Ignora erros ao destruir o tooltip
                pass

    # Vincula eventos de mouse para mostrar/ocultar o tooltip
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

def _update_status_label(self,status_label=None,column_for_show=None):
    """
    Atualiza o label de status com a contagem de colunas selecionadas.
    """
    if not status_label or not status_label.winfo_exists():
        return
        
    selected_count = sum(1 for selected in column_for_show.values() if selected)
    status_label.config(text=f"{selected_count} de {len(self.column)} colunas selecionadas")

def _toggle_select_all(self,select_all_var):
    """
    Seleciona ou desmarca todos os checkboxes visíveis no momento.
    Acionado pelo checkbox "Selecionar Todos".
    """
    select_all = select_all_var.get()
    # Atualiza apenas as linhas visíveis (não filtradas)
    for col_name, widget in self.column_filters.items():
        try:
            
            widget.set_value(bool(select_all))
            self.column_for_show[col_name] = bool(select_all)
        except Exception as e:
            if self.log_message:
                self.log_message(f"Erro ao selecionar/desmarcar coluna {col_name}: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
    # select_all_var.set(False if select_all else True)  # Atualiza o estado do checkbox "Selecionar Todos"     
    _update_status_label(self, self.status_label, self.column_for_show)  # Atualiza o label de status
    
def _cancel_selection(self):
    """
    Ação executada ao clicar no botão Cancelar.
    Atualmente não implementado (placeholder para futuras funcionalidades).
    """
    self.parent.destroy() 

def get_selected_columns(self):
    """
    Retorna lista com os nomes das colunas selecionadas.
    
    Returns:
        list: Lista de nomes de colunas selecionadas
    """
    return [col for col, selected in self.column_for_show.items() if selected]


def _update_column_selection(self,col_name, widget,event=None):
        """
        Atualiza o estado de seleção de uma coluna. Quando a coluna é selecionada ou desmarcada,
        a função ajusta o valor associado a essa coluna em `self.column_for_show`.
        Args:
            col_name: Nome da coluna cujos dados precisam ser atualizados.
            widget: O widget checkbox associado à coluna.
        """
        # print(event)
        # print(f"Atualizando seleção da coluna:{col_name} {widget.get_entry()} {self.column_for_show.get(col_name)}")
        # Atualiza o estado de seleção baseado no valor do checkbox
        


def _add_filter_widget(self, col, col_type, row,validar_numero):
    no_data = True
    containd_between_condition = False
    operations = ["="]
    entry = None  # garante que entry sempre exista
    col_name = col["name"]
    
    # Determinar o tipo apropriado de widget com base no tipo da coluna
    if "enum" in col_type or (self.enum_values.get(col_name) not in [None, "", []]):
        values = self.enum_values.get(col_name, ["Valor não disponível"])
        operations = ["=", "!="]
        if values and values[0] != "":
            values = [""] + values
        entry = ttk.Combobox(self.scrollable_frame, values=values, state="readonly", width=20)
        entry.set("")
    
    elif "int" in col_type or "integer" in col_type:
        vcmd = self.register(validar_numero)
        operations = ["=", "!=", "<", "<=", ">", ">=", "Entre"]
        entry = ttk.Entry(self.scrollable_frame, validate="key", 
                        validatecommand=(vcmd, "%P"), width=20)
        containd_between_condition = True

    elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
        vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
        operations = ["=", "!=", "<", "<=", ">", ">=", "Entre"]
        entry = ttk.Entry(self.scrollable_frame, validate="key", 
                        validatecommand=(vcmd, "%P"), width=20)
        containd_between_condition = True

    elif "bool" in col_type or col_type in ["bit", "boolean"]:
        no_data = False
        operations = ["="]
        
        # Criar frame para conter checkbox e label
        switch_frame = ttk.Frame(self.scrollable_frame)
        switch_frame.grid(row=row, column=2, sticky=tk.W, padx=5, pady=3)
        
        # Variável para controle do checkbox
        var = tk.BooleanVar(value=False)
        # Checkbox simples sem estilo personalizado
        widget = ttk.Checkbutton(switch_frame, variable=var)
        widget.pack(side=tk.LEFT, padx=5)
        str_var = tk.StringVar(value="")
        entry = ttk.Entry(self.scrollable_frame, textvariable=str_var, width=5)
        # Label que mostra o status
        status_label = ttk.Label(switch_frame, text="Não")
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Função para atualizar o texto do status
        def update_status(*_):
            status_label.configure(text="Sim" if var.get() else "Não")
            str_var.set("true" if var.get() else "false")
        
        var.trace_add("write", update_status)
        no_data = False

    elif "date" in col_type or "timestamp" in col_type or "time" in col_type:
        try:
            widget = DateTimeEntry(self.scrollable_frame, col_type)
            operations = ["Contém", "Antes de", "Depois de", "Entre"]
            widget.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
            entry = widget.entry
            no_data = False
            containd_between_condition = True
        except Exception as e:
            self.log_message(f"Erro criando widget de data: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            entry = ttk.Entry(self.scrollable_frame, width=20)

    else:  # String e outros tipos
        operations = ["Contém", "Não Contém"]
        entry = ttk.Entry(self.scrollable_frame, width=20)

    # Configurar combobox de operações com estilo consistente
    combo_op = ttk.Combobox(self.scrollable_frame, values=operations, 
                            state="readonly", width=12)
    combo_op.set(operations[0])
    combo_op.grid(row=row, column=3, sticky=tk.EW, padx=5, pady=3)

    # Bind para mostrar/ocultar o campo "entre"
    if containd_between_condition:
        between_entry = self.create_widget_operation_between(col_name, col_type, row, no_data)
        between_entry.grid_forget()  # Inicialmente oculto
        
        def on_op_change(event):
            selected_op = combo_op.get().strip()
            if selected_op == "Entre":
                between_entry.grid(row=row, column=4, sticky=tk.EW, padx=5, pady=3)
            else:
                between_entry.grid_forget()
        
        combo_op.bind("<<ComboboxSelected>>", on_op_change)

    # Armazenar referências dos widgets
    self.column_filters_combobox_operation[col_name] = combo_op
    if no_data and entry:
        entry.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
    self.column_filters[col_name] = entry
    

def _create_date_widget(self, parent, col_name, col_type, value, row=0, column=0):
    """Cria um widget para visualizar/editar campos de data usando grid, com exemplo baseado na data atual"""
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

        # Exemplo com a data atual
        if not self.example_text.get(col_name, ''):
            self.example_text[col_name] = f"ex: {datetime.now().strftime(date_format)}"

        frame = tk.LabelFrame(parent, bd=1, relief=tk.SOLID, bg="#f0f0f0", text=format_text)
        frame.grid(row=row, column=column, sticky=tk.EW, padx=5, pady=3)

        entry = tk.Entry(frame, width=30, font=("Arial", 10), bd=0, bg="white")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        _add_placeholder(entry, self.example_text[col_name],tk)

        if value:
            try:
                if isinstance(value, datetime):
                    entry.delete(0, tk.END)
                    entry.insert(0, value.strftime(date_format))
                    entry.config(fg="black")
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value).strip())
                    entry.config(fg="black")
            except Exception:
                self.log_message(f"Erro ao formatar data: {value} ({type(value).__name__})", level="error")
                entry.delete(0, tk.END)
        return entry, frame

    except Exception as e:
        self.log_message(f"Erro criando widget de data: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
        return None, None

            
def _add_filter_widget_cache(self, col, col_type, row, validar_numero):
    no_data = True
    containd_between_condition = False
    operations = ["="]
    entry = None
    col_name = col["name"]
    
    # Se não tiver no cache, criar normalmente
    if "enum" in col_type or (self.enum_values.get(col_name) not in [None, "", []]):
        values = self.enum_values.get(col_name, ["Valor não disponível"])
        operations = ["=", "!="]
        if values and values[0] != "":
            values = [""] + values
        entry = ttk.Combobox(self.scrollable_frame, values=values, state="readonly", width=20)
        entry.set("")

    elif "int" in col_type or "integer" in col_type:
        vcmd = self.register(validar_numero)
        operations = ["=", "!=", "<", "<=", ">", ">=", "Entre"]
        entry = ttk.Entry(self.scrollable_frame, validate="key", validatecommand=(vcmd, "%P"), width=20)
        containd_between_condition = True

    elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
        vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
        operations = ["=", "!=", "<", "<=", ">", ">=", "Entre"]
        entry = ttk.Entry(self.scrollable_frame, validate="key", validatecommand=(vcmd, "%P"), width=20)
        containd_between_condition = True

    elif "bool" in col_type or col_type in ["bit", "boolean"]:
        no_data = False
        operations = ["="]

        switch_frame = ttk.Frame(self.scrollable_frame)
        switch_frame.grid(row=row, column=2, sticky=tk.W, padx=5, pady=3)

        var = tk.BooleanVar(value=False)
        widget = ttk.Checkbutton(switch_frame, variable=var)
        widget.pack(side=tk.LEFT, padx=5)
        str_var = tk.StringVar(value="")
        entry = ttk.Entry(self.scrollable_frame, textvariable=str_var, width=5)
        status_label = ttk.Label(switch_frame, text="Não")
        status_label.pack(side=tk.LEFT, padx=5)

        def update_status(*_):
            status_label.configure(text="Sim" if var.get() else "Não")
            str_var.set("true" if var.get() else "false")

        var.trace_add("write", update_status)
        no_data = False

    elif "date" in col_type or "timestamp" in col_type or "time" in col_type:
        try:
            # widget = create_widget_operation_between(self.scrollable_frame, col_type)
            # widget.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
            entry,frame = _create_date_widget(self,self.scrollable_frame, col_name, col_type, None, row, 2)
            operations = ["Contém", "Antes de", "Depois de", "Entre"]
            no_data = False
            containd_between_condition = True
        except Exception as e:
            self.log_message(f"Erro criando widget de data: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            entry = ttk.Entry(self.scrollable_frame, width=20)

    else:
        operations = ["Contém", "Não Contém"]
        entry = ttk.Entry(self.scrollable_frame, width=20)

    # Cria combobox de operação
    combo_op = ttk.Combobox(self.scrollable_frame, values=operations, state="readonly", width=12)
    combo_op.set(operations[0])

    # Grid dos novos widgets
    if no_data and entry:
        entry.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
    combo_op.grid(row=row, column=3, sticky=tk.EW, padx=5, pady=3)

    # Controle para "Entre"
    if containd_between_condition:
        between_entry = self.create_widget_operation_between(col_name, col_type, row, no_data)
        # print(f"entre_entry: {between_entry}")
        between_entry.grid_forget()

        def on_op_change(event):
            selected_op = combo_op.get().strip()
            if selected_op == "Entre":
                between_entry.grid(row=row, column=4, sticky=tk.EW, padx=5, pady=3)
            else:
                between_entry.grid_forget()

        combo_op.bind("<<ComboboxSelected>>", on_op_change)

    # Guardar no cache

    # Armazenar as referências normais
    self.column_filters_combobox_operation[col_name] = combo_op
    self.column_filters[col_name] = entry

    
    
    