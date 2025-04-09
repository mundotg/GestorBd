from tkinter import messagebox, ttk
import tkinter as tk
import traceback
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
    select_all_var.set(False if select_all else True)  # Atualiza o estado do checkbox "Selecionar Todos"     
    _update_status_label(self, self.status_label, self.column_for_show)  # Atualiza o label de status
    # self.scrollable_frame.update_idletasks()  # Atualiza o layout imediatamente
    
def _cancel_selection(self):
    """
    Ação executada ao clicar no botão Cancelar.
    Atualmente não implementado (placeholder para futuras funcionalidades).
    """
    self.clear()
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
        

