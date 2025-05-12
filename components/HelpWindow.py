import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

class HelpWindow(tk.Toplevel):
    """
    Janela auxiliar que fornece explicações detalhadas das funcionalidades
    do aplicativo através de opções selecionáveis, com suporte a imagens
    e formatação de texto.
    """
    
    def __init__(self, parent, title="Ajuda e Informações", icon=None):
        super().__init__(parent)
        self.parent = parent
        
        # Configurações da janela
        self.title(title)
        self.geometry("800x600")
        self.minsize(600, 450)
        self.transient(parent)  # Faz esta janela relacionada à janela principal
        self.grab_set()         # Força o foco nesta janela
        
        # Definir ícone se fornecido
        if icon and os.path.exists(icon):
            self.iconphoto(False, tk.PhotoImage(file=icon))
            
        # Torna a janela responsiva
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Salvar referências às imagens para evitar coleta de lixo
        self.image_references = []
        
        # Criar o estilo personalizado para a janela
        self.style = ttk.Style()
        self.style.configure('Help.TFrame', background='#f0f0f0')
        self.style.configure('Help.TLabelframe', background='#f0f0f0')
        self.style.configure('Help.TLabelframe.Label', font=('Arial', 11, 'bold'))
        self.style.configure('HelpButton.TButton', font=('Arial', 10))
        
        # Cria o frame principal
        main_frame = ttk.Frame(self, style='Help.TFrame')
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=4)
        main_frame.rowconfigure(0, weight=1)
        
        # Painel esquerdo com lista de opções
        self.options_frame = ttk.LabelFrame(main_frame, text="Funcionalidades", style='Help.TLabelframe')
        self.options_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        # Adiciona um frame contendo os botões com scrollbar
        options_container = ttk.Frame(self.options_frame)
        options_container.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Canvas para permitir rolagem
        self.options_canvas = tk.Canvas(options_container)
        self.options_canvas.pack(side="left", fill="both", expand=True)
        
        # Scrollbar para opções
        options_scrollbar = ttk.Scrollbar(options_container, orient="vertical", command=self.options_canvas.yview)
        options_scrollbar.pack(side="right", fill="y")
        self.options_canvas.configure(yscrollcommand=options_scrollbar.set)
        
        # Frame interno para os botões de opções
        self.buttons_frame = ttk.Frame(self.options_canvas)
        self.buttons_frame_id = self.options_canvas.create_window((0, 0), window=self.buttons_frame, anchor="nw")
        
        # Configura eventos para redimensionamento
        self.buttons_frame.bind("<Configure>", self._configure_buttons_frame)
        self.options_canvas.bind("<Configure>", self._configure_canvas)
        
        # Painel direito com detalhes
        details_frame = ttk.LabelFrame(main_frame, text="Detalhes", style='Help.TLabelframe')
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        
        # Área de texto para detalhes
        self.details_text = tk.Text(details_frame, wrap="word", padx=10, pady=10, 
                                   font=("Arial", 10))
        self.details_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configuração de tags para formatação
        self.details_text.tag_configure("title", font=("Arial", 16, "bold"), foreground="#2c3e50")
        self.details_text.tag_configure("subtitle", font=("Arial", 12, "bold"), foreground="#34495e")
        self.details_text.tag_configure("code", font=("Courier New", 10), background="#f5f5f5")
        self.details_text.tag_configure("bold", font=("Arial", 10, "bold"))
        self.details_text.tag_configure("italic", font=("Arial", 10, "italic"))
        self.details_text.tag_configure("bullet", lmargin1=20, lmargin2=30)
        
        # Scrollbar para texto de detalhes
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.details_text.configure(yscrollcommand=scrollbar.set)
        
        # Frame para imagem (se houver)
        self.image_frame = ttk.Frame(details_frame)
        self.image_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(pady=10)
        
        # Botões de controle
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Botão de pesquisa
        self.search_var = tk.StringVar()
        search_frame = ttk.Frame(button_frame)
        search_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(search_frame, text="Buscar:").pack(side="left", padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        search_button = ttk.Button(search_frame, text="Buscar", command=self.search_topics)
        search_button.pack(side="left", padx=5)
        
        # Botão para imprimir
        print_button = ttk.Button(button_frame, text="Imprimir", style='HelpButton.TButton', 
                                 command=self.print_current_topic)
        print_button.pack(side="right", padx=5)
        
        # Botão para fechar
        close_button = ttk.Button(button_frame, text="Fechar", style='HelpButton.TButton', 
                                 command=self.destroy)
        close_button.pack(side="right", padx=5)
        
        # Inicializar opções vazias
        self.options = {}
        self.current_topic = None
        
        # Bind da tecla Escape para fechar
        self.bind("<Escape>", lambda event: self.destroy())
        
        # Centralizar na tela
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _configure_buttons_frame(self, event):
        """Atualiza a região rolável quando o frame de botões é modificado"""
        self.options_canvas.configure(scrollregion=self.options_canvas.bbox("all"))
    
    def _configure_canvas(self, event):
        """Atualiza a largura do frame de botões quando o canvas é redimensionado"""
        self.options_canvas.itemconfig(self.buttons_frame_id, width=event.width)
    
    def add_options(self, options_dict):
        """
        Adiciona opções à lista.
        
        Args:
            options_dict: Dicionário no formato {nome_opção: {"texto": "texto detalhado", 
                                                             "imagem": "caminho/para/imagem.png",
                                                             "tags": {"texto_formatado": "tag"}}}
        """
        self.options = options_dict
        
        # Limpar opções existentes
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
            
        # Criar uma lista com as opções
        for i, (option_name, _) in enumerate(self.options.items()):
            option_btn = ttk.Button(
                self.buttons_frame, 
                text=option_name, 
                style='HelpButton.TButton',
                command=lambda name=option_name: self.show_option_details(name)
            )
            option_btn.pack(fill="x", padx=5, pady=2)
            
        # Mostrar a primeira opção por padrão se existir
        if self.options:
            first_option = list(self.options.keys())[0]
            self.show_option_details(first_option)
    
    def show_option_details(self, option_name):
        """
        Mostra os detalhes da opção selecionada.
        
        Args:
            option_name: Nome da opção para mostrar os detalhes
        """
        if option_name in self.options:
            details = self.options[option_name]
            self.current_topic = option_name
            
            # Limpar área de texto
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            
            # Inserir título
            self.details_text.insert(tk.END, f"{option_name}\n\n", "title")
            
            # Inserir detalhes com formatação
            if "tags" in details and details["tags"]:
                # Texto com tags de formatação
                for txt_segment, tag in details["tags"].items():
                    self.details_text.insert(tk.END, txt_segment, tag)
            else:
                # Texto simples
                self.details_text.insert(tk.END, details["texto"])
            
            # Desativar edição
            self.details_text.config(state=tk.DISABLED)
            
            # Limpar imagem anterior
            for widget in self.image_frame.winfo_children():
                widget.destroy()
            
            # Mostrar imagem se disponível
            if "imagem" in details and details["imagem"] and os.path.exists(details["imagem"]):
                try:
                    img = Image.open(details["imagem"])
                    # Redimensionar mantendo proporção
                    max_width = 600
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_width = int(img.width * ratio)
                        new_height = int(img.height * ratio)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    self.image_references.append(photo)  # Para evitar coleta de lixo
                    
                    img_label = ttk.Label(self.image_frame, image=photo)
                    img_label.image = photo
                    img_label.pack(pady=10)
                    
                    # Adicionar legenda se disponível
                    if "legenda" in details and details["legenda"]:
                        caption = ttk.Label(self.image_frame, text=details["legenda"], 
                                          font=("Arial", 9, "italic"))
                        caption.pack()
                except Exception as e:
                    print(f"Erro ao carregar imagem: {e}")
        else:
            messagebox.showwarning("Opção não encontrada", f"A opção '{option_name}' não existe.")
    
    def search_topics(self):
        """Procura tópicos que correspondam ao texto de pesquisa"""
        search_text = self.search_var.get().lower()
        if not search_text:
            return
            
        # Procurar correspondências em tópicos e conteúdo
        matches = []
        for topic_name, details in self.options.items():
            # Verificar no título
            if search_text in topic_name.lower():
                matches.append(topic_name)
                continue
                
            # Verificar no texto
            if "texto" in details and search_text in details["texto"].lower():
                matches.append(topic_name)
                
        if matches:
            # Criar janela de resultados
            results_window = tk.Toplevel(self)
            results_window.title("Resultados da Pesquisa")
            results_window.geometry("400x300")
            results_window.transient(self)
            results_window.grab_set()
            
            ttk.Label(results_window, text=f"Resultados para '{search_text}':", 
                    font=("Arial", 11, "bold")).pack(pady=10, padx=10, anchor="w")
            
            results_frame = ttk.Frame(results_window)
            results_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            for topic in matches:
                result_btn = ttk.Button(
                    results_frame, 
                    text=topic,
                    command=lambda t=topic: [results_window.destroy(), self.show_option_details(t)]
                )
                result_btn.pack(fill="x", pady=2)
                
            ttk.Button(results_window, text="Fechar", 
                      command=results_window.destroy).pack(pady=10)
        else:
            messagebox.showinfo("Pesquisa", f"Nenhum resultado encontrado para '{search_text}'")
    
    def print_current_topic(self):
        """Função para imprimir o tópico atual (simulada)"""
        if not self.current_topic:
            messagebox.showinfo("Imprimir", "Nenhum tópico selecionado para imprimir.")
            return
            
        # Em uma aplicação real, implementaria a funcionalidade de impressão
        # Por enquanto, apenas mostra uma mensagem
        messagebox.showinfo("Imprimir", 
                          f"Simulando impressão do tópico: '{self.current_topic}'")
