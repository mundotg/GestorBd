import threading
import tkinter as tk
from tkinter import ttk, font

class ComboBoxComBusca:
    """
    Classe para criar uma ComboBox com funcionalidade de busca e seleção.
    
    Parâmetros:
    - root (tk.Tk): A janela principal do Tkinter onde o widget será exibido.
    - options (list): Lista de opções a serem exibidas na ComboBox.
    - width (int, opcional): Largura da ComboBox (padrão é 300).
    - title_text (str, opcional): Texto do título acima da ComboBox (padrão é "Seleção de Item").
    - label_text (str, opcional): Texto da label explicativa (padrão é "Digite ou selecione uma opção:").
    - clear_button_text (str, opcional): Texto do botão de limpar (padrão é "Limpar").
    - confirm_button_text (str, opcional): Texto do botão de confirmar (padrão é "Confirmar").
    - on_confirm (callable, opcional): Função a ser chamada quando o botão de confirmação for pressionado.
    - on_clear (callable, opcional): Função a ser chamada quando o botão de limpar for pressionado.
    - on_select (callable, opcional): Função a ser chamada quando uma opção for selecionada.
    - kwargs (dict, opcional): Outros parâmetros adicionais para personalização.
    """
    
    def __init__(self, root, options, width=300, title_text="Seleção de Item", 
                 label_text="Digite ou selecione uma opção:", 
                 clear_button_text="Limpar", confirm_button_text="Confirmar",name_type_options="itens",
                 on_confirm=None, on_clear=None, on_select=None, **kwargs):
        self.root = root
        self.options = options
        self.width = width
        self.name_type_options = name_type_options
        self.filtered_options = options
        self.selected_option = tk.StringVar()
        self.thread_lock = threading.Lock()
        
        # Configura textos personalizáveis
        self.title_text = title_text
        self.label_text = label_text
        self.clear_button_text = clear_button_text
        self.confirm_button_text = confirm_button_text
        self.ps_on_confirm = on_confirm
        self.ps_on_clear = on_clear
        self.ps_on_select = on_select
        
        # Criando um frame para organizar os componentes
        self.main_frame = tk.Frame(self.root)
        # self.main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Configurando fontes personalizadas
        self.title_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.normal_font = font.Font(family="Helvetica", size=10)
        self.small_font = font.Font(family="Helvetica", size=9, slant="italic")
        
        # Título
        self.title = tk.Label(self.main_frame, text=self.title_text, font=self.title_font)
        self.title.pack(pady=(0, 15), anchor=tk.W)
        
        # Label
        self.label = tk.Label(self.main_frame, text=self.label_text, font=self.normal_font)
        self.label.pack(pady=(0, 5), anchor=tk.W)
        
        # Frame para ComboBox e contador
        self.combo_frame = tk.Frame(self.main_frame)
        self.combo_frame.pack(fill=tk.X, pady=(0, 5))
        
        # ComboBox como campo de busca
        self.style = ttk.Style()
        self.style.configure('Combo.TCombobox', padding=5)
        
        self.combo_box = ttk.Combobox(self.combo_frame, 
                                     textvariable=self.selected_option, 
                                     values=self.filtered_options, 
                                     state="normal",
                                     font=self.normal_font,
                                     style='Combo.TCombobox',
                                     width=width//10)  # Largura ajustada para a janela
        
        self.combo_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.combo_box.bind("<KeyRelease>", self.filter_options)
        self.combo_box.bind("<<ComboboxSelected>>", self.on_selection)
        
        # Contador de resultados
        self.counter_label = tk.Label(self.combo_frame, text=f"{len(self.options)} {self.name_type_options}", font=self.small_font)
        self.counter_label.pack(side=tk.RIGHT, padx=5)
        
        # Mensagem de status
        self.status_frame = tk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=5)
        
        self.status_icon = tk.Label(self.status_frame, text="", width=2)
        self.status_icon.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(self.status_frame, text="", font=self.small_font, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Frame para botões
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Botão de limpar
        self.clear_button = tk.Button(self.button_frame, text=self.clear_button_text, 
                                     command=self.clear_selection,
                                     font=self.normal_font,
                                     width=10)
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão de confirmar
        self.confirm_button = tk.Button(self.button_frame, text=self.confirm_button_text, 
                                       command=self.confirm_selection,
                                       font=self.normal_font,
                                       bg="#4CAF50", fg="white",
                                       width=10)
        self.confirm_button.pack(side=tk.RIGHT)
        
        # Variável para armazenar a opção confirmada
        self.confirmed_option = None
        
        # Atualizar o estado dos botões inicialmente
        self.update_buttons_state()
    def __del__(self):
    # Limpeza de recursos ao destruir a instância
        self.thread_lock = None
        if hasattr(self, '_after_id'):
            self.root.after_cancel(self._after_id)
            
    def set_options(self, new_options):
        """
        Atualiza as opções da ComboBox.
        
        Parâmetros:
        - new_options (list): Lista de novas opções a serem exibidas na ComboBox.
        """
        self.options = new_options
        self.filtered_options = new_options
        self.combo_box['values'] = self.filtered_options
        self.filter_options()
        
    def filter_options(self, event=None):
        if hasattr(self, "_after_id"):
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(150, self._do_filter)
    
    def _do_filter(self):
        """
        Filtra as opções de acordo com o termo de busca digitado na ComboBox.
        
        Parâmetros:
        - event (tk.Event, opcional): Evento que pode ser passado quando uma tecla for pressionada.
        """
        search_term = self.selected_option.get().lower()
        
        # Filtra as opções com base no que foi digitado
        self.filtered_options = [option for option in self.options if search_term in option.lower()]
        
        # Atualiza o contador
        self.counter_label.config(text=f"{len(self.filtered_options)} {self.name_type_options}")
        
        # Atualiza as opções da ComboBox
        self.combo_box['values'] = self.filtered_options
        
        # Atualiza mensagem de status
        if not self.filtered_options:
            self.status_icon.config(text="❌", fg="red")
            self.status_label.config(text="Nenhuma opção encontrada!", fg="red")
        elif search_term and len(self.filtered_options) < len(self.options):
            self.status_icon.config(text="🔍", fg="blue")
            self.status_label.config(text=f"Mostrando resultados para '{search_term}'", fg="blue")
        else:
            self.status_icon.config(text="✓", fg="green")
            self.status_label.config(text="Todas as opções disponíveis", fg="green")
        
        # Mantem a ComboBox aberta se houver opções
        # if self.filtered_options:
        #     self.combo_box.event_generate("<Down>")
        
        # Atualiza o estado dos botões
        self.update_buttons_state()
        
    def set_on_select_func(self,func):
        self.ps_on_select= func
        
    def on_selection(self, event=None):
        """
        Atualiza o status quando uma seleção é feita na ComboBox.
        
        Parâmetros:
        - event (tk.Event, opcional): Evento que ocorre quando uma seleção é feita na ComboBox.
        """
        selection = self.selected_option.get()
        if selection:
            self.status_icon.config(text="✓", fg="green")
            self.status_label.config(text=f"Selecionado: {selection}", fg="green")
        
        # Atualiza o estado dos botões
        self.update_buttons_state()
        
        if self.ps_on_select:
             self.run_ps_on_select_in_thread()

    def run_ps_on_select_in_thread(self):
        """Executa a função ps_on_select em uma nova thread, mas garante que apenas uma thread seja criada por vez."""
        # Verifica se já existe uma thread em execução
        if not self.thread_lock.locked():
            with self.thread_lock:  # Obtém o lock para garantir que apenas uma thread seja executada
                threading.Thread(target=self.ps_on_select).start()
    
    def clear_selection(self):
        """Limpa a seleção feita na ComboBox."""
        self.selected_option.set("")
        self.filter_options()
        if self.ps_on_clear:
            self.ps_on_clear()
    
    def confirm_selection(self):
        """Confirma a seleção feita na ComboBox."""
        selection = self.selected_option.get()
        if selection:
            self.confirmed_option = selection
            self.status_icon.config(text="✅", fg="green")
            self.status_label.config(text=f"Confirmado: {selection}", fg="green")
        else:
            self.status_icon.config(text="⚠️", fg="orange")
            self.status_label.config(text="Selecione uma opção primeiro!", fg="orange")
        if self.ps_on_confirm:
            self.ps_on_confirm()
    
    def update_buttons_state(self):
        """Atualiza o estado dos botões com base na seleção atual."""
        # Habilita/desabilita o botão de confirmar baseado na seleção
        if self.selected_option.get():
            self.confirm_button.config(state=tk.NORMAL)
        else:
            self.confirm_button.config(state=tk.DISABLED)
    
    def get_selected_option(self):
        """
        Retorna a opção selecionada ou confirmada.
        
        Retorno:
        - str: A opção selecionada ou confirmada.
        """
        return self.confirmed_option or self.selected_option.get()
    
    def grid(self, row=0, column=0, padx=10, pady=10, sticky="nsew"):
        """
        Organiza os widgets dentro da janela utilizando o grid do Tkinter de forma responsiva.

        Parâmetros:
        - row (int, opcional): A linha onde o componente principal será posicionado (padrão é 0).
        - column (int, opcional): A coluna onde o componente principal será posicionado (padrão é 0).
        - padx (int, opcional): Espaçamento horizontal externo (padrão é 10).
        - pady (int, opcional): Espaçamento vertical externo (padrão é 10).
        - sticky (str, opcional): Como os widgets serão ancorados dentro da célula (padrão é "nsew").
        """
        # Configuração do frame principal para expansão adequada
        if self.main_frame:
            self.main_frame.destroy()

        self.main_frame = tk.Frame(self.root, height=20)
        self.main_frame.grid(row=row, column=column, rowspan=2, padx=padx, pady=pady, sticky=sticky)
        self.main_frame.grid_columnconfigure(0, weight=0)  # Configuração de coluna fixa
        self.main_frame.grid_rowconfigure(0, minsize=10)  # Definindo altura mínima para a primeira linha

        current_row = 0  # Controle de linha interno ao frame

        # Título
        self.title = tk.Label(self.main_frame, text=self.title_text, font=self.title_font)
        self.title.grid(row=current_row, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        current_row += 1

        # Label
        self.label = tk.Label(self.main_frame, text=self.label_text, font=self.normal_font)
        self.label.grid(row=current_row, column=0, columnspan=2, pady=(0, 5), sticky="ew")
        current_row += 1

        # Frame para ComboBox e contador
        self.combo_frame = tk.Frame(self.main_frame)
        self.combo_frame.grid(row=current_row, column=0, columnspan=2, pady=(0, 5), sticky="ew")
        self.combo_frame.grid_columnconfigure(0, weight=1)  # ComboBox expansível
        self.combo_frame.grid_columnconfigure(1, weight=0)  # Contador com tamanho fixo
        current_row += 1

        # ComboBox como campo de busca
        self.style = ttk.Style()
        self.style.configure('Combo.TCombobox', padding=5)

        self.combo_box = ttk.Combobox(self.combo_frame, 
                                    textvariable=self.selected_option, 
                                    values=self.filtered_options, 
                                    state="normal",
                                    font=self.normal_font,
                                    style='Combo.TCombobox')
        self.combo_box.grid(row=0, column=0, sticky="ew")
        self.combo_box.bind("<KeyRelease>", self.filter_options)
        self.combo_box.bind("<<ComboboxSelected>>", self.on_selection)

        # Contador de resultados
        self.counter_label = tk.Label(self.combo_frame, text=f"{len(self.options)} {self.name_type_options}", font=self.small_font)
        self.counter_label.grid(row=0, column=1, padx=5,pady=5, sticky="ew")

        # Configuração da mensagem de status
        self.status_frame = tk.Frame(self.combo_frame)
        self.status_frame.grid(row=0, column=3, columnspan=2, padx=5,pady=5, sticky="ew")
        self.status_frame.grid_columnconfigure(1, weight=1)  # Texto de status expansível
        current_row += 1

        self.status_icon = tk.Label(self.status_frame, text="", width=2)
        self.status_icon.grid(row=0, column=0, sticky="ew")

        self.status_label = tk.Label(self.status_frame, text="", font=self.small_font, anchor="w")
        self.status_label.grid(row=0, column=1, sticky="ew")

        # Frame para botões
        self.button_frame = tk.Frame(self.combo_frame)
        self.button_frame.grid(row=0, column=3, columnspan=2, padx=5,pady=5, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=0)  # Botão de limpar não expansível
        self.button_frame.grid_columnconfigure(1, weight=1)  # Espaço entre botões expansível
        self.button_frame.grid_columnconfigure(2, weight=0)  # Botão de confirmar não expansível
        current_row += 1

        # Botão de limpar
        self.clear_button = tk.Button(
            self.button_frame, 
            text=self.clear_button_text, 
            command=self.clear_selection,
            font=self.normal_font,
            width=10,
            relief=tk.GROOVE,
            borderwidth=2,
            cursor="hand2"
        )
        self.clear_button.grid(row=0, column=0, sticky="w")

        # Espaçador (frame vazio) para empurrar os botões para as extremidades
        tk.Frame(self.button_frame).grid(row=0, column=1, sticky="ew")

        # Botão de confirmar
        self.confirm_button = tk.Button(
            self.button_frame, 
            text=self.confirm_button_text, 
            command=self.confirm_selection,
            font=self.normal_font,
            bg="#4CAF50", 
            fg="white",
            width=10,
            relief=tk.RAISED,
            borderwidth=2,
            cursor="hand2"
        )
        self.confirm_button.grid(row=0, column=1, sticky="e")

        # Adicionando um espaçador inferior para melhor distanciamento
        tk.Frame(self.main_frame, height=10).grid(row=current_row, column=0, columnspan=2)
        current_row += 1

        # Variável para armazenar a opção confirmada
        self.confirmed_option = None

        # Configura redimensionamento adequado para todas as linhas
        for i in range(current_row):
            if i == 0:  # Linha do título
                self.main_frame.grid_rowconfigure(i, weight=0, minsize=30)
            elif i == current_row - 1:  # Última linha (espaçador)
                self.main_frame.grid_rowconfigure(i, weight=1)  # Expande para preencher espaço
            else:
                self.main_frame.grid_rowconfigure(i, weight=0)

        # Atualizar o estado dos botões inicialmente
        self.update_buttons_state()

    
    # Método auxiliar para tratamento de foco no ComboBox
    def handle_focus_in(self):
        """Abre a lista de opções quando o ComboBox recebe foco"""
        if self.filtered_options:
            self.combo_box.event_generate("<Down>")


if __name__ == "__main__":
    # Criando a interface Tkinter
    root = tk.Tk()
    options = ["Banana", "Maçã", "Laranja", "Pera", "Melancia", "Abacaxi", 
                   "Uva", "Coco", "Morango", "Kiwi", "Manga", "Abacate", 
                   "Cereja", "Limão", "Goiaba", "Framboesa", "Amora"]
    app = ComboBoxComBusca(root, options)
    root.mainloop()
