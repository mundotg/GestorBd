import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from DatabaseManager import DatabaseManager,DatabaseUtils
from logger import logger, log_message as logmessage
from ConfigManager import ConfigManager
from Theme import Theme



class DatabaseConnectorGUI:
    """Interface gráfica do aplicativo de conexão"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Conector Avançado de Banco de Dados")
        self.root.geometry("650x500")
        self.root.minsize(450, 400)
        
        # Gerenciadores
        self.config_manager = ConfigManager()
        self.connection = None
        self.engine = None
        self.db_type = tk.StringVar(value="MySQL")
        self.current_profile = tk.StringVar(value="")
        self.dark_mode = tk.BooleanVar(value=False)
        
        # Campos de conexão
        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.StringVar(value="3306")
        self.user_var = tk.StringVar(value="root")
        self.password_var = tk.StringVar(value="")
        self.database_var = tk.StringVar(value="")
        self.connection_status = tk.StringVar(value="Desconectado")
        self.prefix = ""
        self.tag = ""
        self.message = ""
      
        
        # Carregar tema
        self.theme = Theme()
        self.style = self.theme.apply_theme(self.root, Theme.LIGHT)
        
        # Criar a interface
        self.create_menu()
        self.create_gui()
        
        # Registrar handler para redimensionamento da janela
        self.root.bind("<Configure>", self.on_resize)
        
        # Carregar último perfil usado, se existir
        self.current_profile.set(self.config_manager.open_file())
        self.load_profile()
        
    def Quit(self):
        if self.connection:
            self.connection.close()
        self.root.quit()
    def log_message(self, message,level="info"):
        """Exibe mensagens na interface.""" 
        logmessage(self,message,level)
    def create_menu(self):
        """Cria a barra de menu"""
        menubar = tk.Menu(self.root)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Novo Perfil", command=self.new_profile)
        file_menu.add_command(label="Salvar Perfil", command=self.save_profile)
        file_menu.add_command(label="Excluir Perfil", command=self.delete_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.Quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        # Menu Visualização
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="Modo Escuro", variable=self.dark_mode, command=self.toggle_theme)
        menubar.add_cascade(label="Visualização", menu=view_menu)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Sobre", command=self.show_about)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_gui(self):
        """Cria a interface gráfica principal"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para perfis
        profile_frame = ttk.LabelFrame(main_frame, text="Perfil de Conexão", padding=10)
        profile_frame.pack(fill=tk.X, pady=(0, 10))
        
        profile_options = self.config_manager.get_profile_names()
        ttk.Label(profile_frame, text="Perfil:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.current_profile, values=profile_options, width=20)
        self.profile_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self.load_profile())
        
        ttk.Button(profile_frame, text="Carregar", command=self.load_profile).grid(row=0, column=2, padx=5)
        ttk.Button(profile_frame, text="Salvar", command=self.save_profile).grid(row=0, column=3, padx=5)
        
        # Frame para configuração da conexão
        conn_frame = ttk.LabelFrame(main_frame, text="Configuração da Conexão", padding=10)
        conn_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Tipo de banco de dados
        ttk.Label(conn_frame, text="Banco de Dados:").grid(row=0, column=0, sticky="w", pady=5)
        db_types = ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle", "MongoDB", "MariaDB"]
        db_type_combo = ttk.Combobox(conn_frame, textvariable=self.db_type, values=db_types, width=15, state="readonly")
        db_type_combo.grid(row=0, column=1, sticky="w", pady=5)
        db_type_combo.bind("<<ComboboxSelected>>", self.update_port)
        
        # Campos de conexão
        ttk.Label(conn_frame, text="Host:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(conn_frame, textvariable=self.host_var, width=20).grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(conn_frame, text="Porta:").grid(row=1, column=2, sticky="w", padx=(20, 5), pady=5)
        ttk.Entry(conn_frame, textvariable=self.port_var, width=8).grid(row=1, column=3, sticky="w", pady=5)
        
        ttk.Label(conn_frame, text="Usuário:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(conn_frame, textvariable=self.user_var, width=20).grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(conn_frame, text="Senha:").grid(row=2, column=2, sticky="w", padx=(20, 5), pady=5)
        ttk.Entry(conn_frame, textvariable=self.password_var, width=20, show="*").grid(row=2, column=3, sticky="w", pady=5)
        
        ttk.Label(conn_frame, text="Banco de Dados:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(conn_frame, textvariable=self.database_var, width=20).grid(row=3, column=1, sticky="w", pady=5)
        
        # Frame para botões de ação
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Conectar", command=self.connect, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Desconectar", command=self.disconnect, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Testar Conexão", command=self.test_connection, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="continuar com gestão da base de dados", command=self.open_gui_gestaodb, width=15).pack(side=tk.LEFT, padx=5)
        
        # Frame para status e log
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.connection_status, foreground="#dc3545")
        self.status_label.pack(fill=tk.X)
        
        # Log simplificado
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=6, width=50, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        self.log_text.config(state=tk.DISABLED)
    
    def update_port(self, event=None):
        """Atualiza a porta padrão com base no tipo de banco selecionado"""
        db_type = self.db_type.get()
        default_port = DatabaseUtils.get_default_port(db_type)
        
        if db_type == "SQLite":
            self.port_var.set("")
            self.host_var.set("")
        else:
            self.port_var.set(str(default_port))
            if not self.host_var.get():
                self.host_var.set("localhost")
    
    
        
        # Adicionar ao widget de texto
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{self.prefix} {self.message}\n", self.tag)
        self.log_text.tag_configure("error", foreground="#dc3545")
        self.log_text.tag_configure("success", foreground="#28a745")
        self.log_text.tag_configure("warning", foreground="#ffc107")
        self.log_text.tag_configure("info", foreground="#0078d7")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def connect(self):
        """Conecta ao banco de dados em uma thread separada"""
        # Preparar configuração da conexão
        db_type = self.db_type.get()
        if not self.host_var.get() or not self.database_var.get():
            self.log_message("Preencha todos os campos obrigatórios!", "warning")
            return
        config = {
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "user": self.user_var.get(),
            "password": self.password_var.get(),
            "database": self.database_var.get()
        }
        
        # Mostrar indicação visual de processamento
        self.connection_status.set("Conectando...")
        self.status_label.config(foreground="#ffc107")
        self.log_message(f"Iniciando conexão ao {db_type}...")
        
        # Iniciar conexão em thread separada
        threading.Thread(target=self._connect_thread, args=(db_type, config), daemon=True).start()
    
    def _connect_thread(self, db_type, config):
        """Thread para realizar a conexão"""
        try:
            # Se já existir uma conexão, fechar antes
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            
            # Conectar
            self.connection,self.engine = DatabaseManager.connect(db_type, config)
            print(self.connection)
            print(self.engine)
            # Atualizar UI
            self.root.after(0, lambda: self._update_connection_status(True, f"Conectado ao {db_type} com sucesso!"))
            
            # Salvar último perfil usado
            if self.current_profile.get():
                try:
                    with open("last_profile.txt", "w") as f:
                        f.write(self.current_profile.get())
                except Exception as e:
                    self.log_message(f"Erro ao salvar perfil atual: {e}", "warning")
        
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._update_connection_status(False, f"Erro ao conectar ao {db_type}: {error_msg}"))
    
    def _update_connection_status(self, success, message):
        """Atualiza a interface com o status da conexão"""
        if success:
            self.connection_status.set("Status: Conectado")
            self.status_label.config(foreground="#28a745")
            self.log_message(message, "success")
        else:
            self.connection_status.set("Status: Erro na Conexão")
            self.status_label.config(foreground="#dc3545")
            self.log_message(message, "error")
    
    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                self.connection_status.set("Desconectado")
                self.status_label.config(foreground="#dc3545")
                self.log_message("Conexão encerrada com sucesso.", "info")
            except Exception as e:
                self.log_message(f"Erro ao desconectar: {e}", "error")
            
    def open_gui_gestaodb(self):
        """Abre a interface de gestão da base de dados."""
        
        print("tetgghsgbbhbhsbh")
        if not self.connection:
            self.log_message("Nenhuma conexão ativa para gerenciamento da base de dados.", "warning")
            return

        self.log_message("Abrindo interface de gestão da base de dados...", "info")
        
        try:
            self.root.withdraw()  # Oculta a janela principal
            #self.root.update()
            from DatabaseGUI import open_gui_gestaodb
            # from DatabaseGUI import ChatClientGUI
            db_gui = open_gui_gestaodb(self.root, self.connection,self.engine, self.db_type.get(),self.current_profile,self.database_var,self.dark_mode,self.connection_status)
            db_gui.root.protocol("WM_DELETE_WINDOW", self.on_close_gestaodb)
            db_gui.root.mainloop()
        
        except Exception as e:
            self.log_message(f"Erro ao abrir a interface de gestão: {e}", "error")
            self.root.deiconify()  # Restaura a janela principal em caso de erro

    
    def test_connection(self):
        """Testa a conexão sem efetivamente conectar"""
        db_type = self.db_type.get()
        
        config = {
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "user": self.user_var.get(),
            "password": self.password_var.get(),
            "database": self.database_var.get()
        }
        
        self.log_message(f"Testando conexão com {db_type}...")
        
        try:
            
            if DatabaseUtils.test_connection( db_type,config ):
                self.log_message(f"Teste de conexão bem-sucedido com {db_type}!", "success")
                messagebox.showinfo("Teste de Conexão", f"Conexão bem-sucedida com {db_type}!")
            else:
                self.log_message(f"Falha no teste de conexão com {db_type}.", "error")
                messagebox.showerror("Teste de Conexão", f"Falha no teste de conexão com {db_type}.")
        except Exception as e:
            self.log_message(f"Erro no teste de conexão: {e}", "error")
            messagebox.showerror("Erro", f"Erro ao testar conexão: {e}")
    
    def save_profile(self):
        """Salva o perfil atual"""
        profile_name = self.current_profile.get()
        
        if not profile_name:
            profile_name = simpledialog.askstring("Salvar Perfil", "Nome do perfil:")
            if not profile_name:
                return
            self.current_profile.set(profile_name)
        
        config = {
            "db_type": self.db_type.get(),
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "user": self.user_var.get(),
            "password": self.password_var.get(),
            "database": self.database_var.get()
        }
        
        self.config_manager.save_profile(profile_name, config)
        self.log_message(f"Perfil '{profile_name}' salvo com sucesso.", "success")
        
        # Atualizar lista de perfis no combobox
        self.profile_combo['values'] = self.config_manager.get_profile_names()
    
    def load_profile(self):
        """Carrega um perfil salvo"""
        profile_name = self.current_profile.get()
        
        if not profile_name:
            self.log_message("Nenhum perfil selecionado.", "warning")
            return
        
        profile = self.config_manager.get_profile(profile_name)
        
        if profile:
            self.db_type.set(profile.get("db_type", "MySQL"))
            self.host_var.set(profile.get("host", "localhost"))
            self.port_var.set(profile.get("port", "3306"))
            self.user_var.set(profile.get("user", ""))
            self.password_var.set(profile.get("password", ""))
            self.database_var.set(profile.get("database", ""))
            
            self.log_message(f"Perfil '{profile_name}' carregado com sucesso.", "info")
        else:
            self.log_message(f"Perfil '{profile_name}' não encontrado.", "error")
    
    def delete_profile(self):
        """Exclui um perfil salvo"""
        profile_name = self.current_profile.get()
        
        if not profile_name:
            self.log_message("Nenhum perfil selecionado para exclusão.", "warning")
            return
        
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o perfil '{profile_name}'?"):
            self.config_manager.delete_profile(profile_name)
            self.log_message(f"Perfil '{profile_name}' excluído com sucesso.", "info")
            
            # Atualizar lista de perfis e limpar seleção atual
            self.profile_combo['values'] = self.config_manager.get_profile_names()
            self.current_profile.set("")
    
    def new_profile(self):
        """Cria um novo perfil"""
        profile_name = simpledialog.askstring("Novo Perfil", "Nome do novo perfil:")
        
        if profile_name:
            # Limpar campos e definir valores padrão
            self.db_type.set("MySQL")
            self.host_var.set("localhost")
            self.port_var.set("3306")
            self.user_var.set("root")
            self.password_var.set("")
            self.database_var.set("")
            
            # Definir o nome do perfil
            self.current_profile.set(profile_name)
            self.log_message(f"Novo perfil '{profile_name}' criado. Configure e salve-o.", "info")
    
    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        if self.dark_mode.get():
            self.style = self.theme.apply_theme(self.root, Theme.DARK)
            self.log_message("Tema escuro aplicado.", "info")
        else:
            self.style = self.theme.apply_theme(self.root, Theme.LIGHT)
            self.log_message("Tema claro aplicado.", "info")
    
    def show_about(self):
        """Exibe informações sobre o aplicativo"""
        about_text = """
        Conector Avançado de Banco de Dados
        Versão 2.0
        
        Um aplicativo para gerenciar múltiplas conexões de banco de dados
        com suporte a perfis e diversos tipos de bancos.
        
        © 2025 - Todos os direitos reservados
        """
        messagebox.showinfo("Sobre", about_text.strip())
    
    def on_resize(self, event=None):
        """Manipula o evento de redimensionamento da janela"""
        if event and event.widget == self.root:
            # Aqui podemos implementar lógica adicional para responsividade
            pass
