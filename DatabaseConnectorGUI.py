import threading
import tkinter as tk
from tkinter import ttk
import traceback
from DatabaseManager import DatabaseManager
from config.ConfigManager import ConfigManager
from Theme import Theme
from utils.gui_principal import _connect_thread, _update_connection_status, delete_profile, disconnect, load_profile, log_message, new_profile, save_profile, test_connection, update_port, validate_connection_fields

class DatabaseConnectorGUI:
    """Interface gráfica para conexão com banco de dados."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Conector Avançado de Banco de Dados")
        self.root.geometry("660x540")
        self.root.minsize(460, 400)
        
        self._initialize_variables()
        self._load_theme()
        self._create_menu()
        self._create_gui()
        
        self.current_profile.set(self.config_manager.open_file())
        load_profile(self)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
    
    def _initialize_variables(self):
        """Inicializa as variáveis da interface."""
        self.config_manager = ConfigManager()
        self.connection = None
        self.engine = None
        
        self.db_type = tk.StringVar(value="MySQL")
        self.current_profile = tk.StringVar(value="")
        self.dark_mode = tk.BooleanVar(value=False)
        
        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.StringVar(value="3306")
        self.user_var = tk.StringVar(value="root")
        self.password_var = tk.StringVar(value="")
        self.database_var = tk.StringVar(value="")
        self.connection_status = tk.StringVar(value="Desconectado")
        self.button_mb = None
        self.status_label = None
        self.gui_gestao_db = None
    
    def _load_theme(self):
        """Carrega tema com suporte a tema claro/escuro mais sofisticado."""
        self.theme = Theme()
        
        system_theme = self._detect_system_theme()
        selected_theme = Theme.DARK if system_theme == 'dark' else Theme.LIGHT
        
        self.style = self.theme.apply_theme(self.root, selected_theme)
        self.root.configure(bg=self.style.lookup('TFrame', 'background'))
        
    def _detect_system_theme(self):
        """Detecta o tema do sistema operacional."""
        import platform
        
        system = platform.system()
        if system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                dark_mode, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return 'dark' if not dark_mode else 'light'
            except:
                return 'light'
        elif system == "Darwin":  # macOS
            return 'dark'
        else:
            return 'light'
        
    def _create_menu(self):
        """Cria a barra de menu."""
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Novo Perfil", command=lambda: new_profile(self))
        file_menu.add_command(label="Salvar Perfil", command=lambda: save_profile(self))
        file_menu.add_command(label="Excluir Perfil", command=lambda: delete_profile(self))
        file_menu.add_separator()
        file_menu.add_command(label="🚪❌Sair", command=self.quit_app)
        menubar.add_cascade(label="👤Arquivo", menu=file_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.root.config(menu=menubar)

    def _create_gui(self):
        """Cria a interface gráfica principal com layout aprimorado."""
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        main_frame.columnconfigure(0, weight=1)
        
        profile_frame = self._create_profile_section(main_frame)
        profile_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        connection_frame = self._create_connection_section(main_frame)
        connection_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        status_frame = self._create_status_section(main_frame)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        button_frame = self._create_section_button(main_frame)
        button_frame.grid(row=3, column=0, sticky="ew")
    
    def _create_profile_section(self, parent):
        """Cria a seção de perfil com layout aprimorado."""
        profile_frame = ttk.LabelFrame(parent, text="🔧 Perfil de Conexão", padding=10)
        
        profile_label = ttk.Label(profile_frame, text="Perfil:")
        profile_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.profile_combo = ttk.Combobox(
            profile_frame, 
            textvariable=self.current_profile, 
            values=self.config_manager.get_profile_names(), 
            width=25,
            state="normal"
        )
        self.profile_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        load_btn = ttk.Button(profile_frame, text="🔄Carregar", command=lambda: load_profile(self), width=10)
        load_btn.grid(row=0, column=2, padx=5)
        
        save_btn = ttk.Button(profile_frame, text="💾Salvar", command=lambda: save_profile(self), width=10)
        save_btn.grid(row=0, column=3, padx=5)
        
        profile_frame.columnconfigure(1, weight=1)
        
        return profile_frame
    
    def _create_connection_section(self, parent):
        """Cria seção de conexão com layout aprimorado."""
        conn_frame = ttk.LabelFrame(parent, text="🔌Configuração da Conexão", padding=10)
        
        fields = [
            ("🖥️ Banco de Dados:", self.db_type, "readonly"),
            ("🌐 Host:", self.host_var, "normal"),
            ("🚪 Porta:", self.port_var, "normal"),
            ("👤 Usuário:", self.user_var, "normal"),
            ("🔐 Senha:", self.password_var, "password"),
            ("🏷️ Nome BD:", self.database_var, "normal")
        ]
        
        for i, (label, var, state) in enumerate(fields):
            ttk.Label(conn_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            
            if label.startswith("🖥️"):
                options = ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle", "MongoDB", "MariaDB"]
                entry = ttk.Combobox(conn_frame, textvariable=var, values=options, width=25, state=state)
                entry.bind("<<ComboboxSelected>>", lambda: update_port(self))
            else:
                show = "*" if state == "password" else ""
                entry = ttk.Entry(conn_frame, textvariable=var, width=25, show=show, state=state)
            entry.grid(row=i, column=1, sticky="ew", pady=5)
        
        conn_frame.columnconfigure(1, weight=1)
        
        return conn_frame
    
    def _create_section_button(self, main_frame):
        button_frame = ttk.Frame(main_frame)
        ttk.Button(button_frame, text="🔌Conectar", command=self.connect, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌Desconectar", command=lambda: disconnect(self), width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🛠️Testar Conexão", command=lambda: test_connection(self), width=19).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.button_mb = ttk.Button(button_frame, text="📊Continuar com gestão da base de dados", command=self.open_gui_gestaodb)
        if not self.connection:
            self.button_mb.pack_forget()
        return button_frame
    
    def _create_status_section(self, parent):
        status_frame = ttk.Frame(parent)
        
        self.status_label = ttk.Label(
            status_frame, 
            textvariable=self.connection_status, 
            font=('Arial', 10, 'bold')
        )
        self.status_label.pack(fill=tk.X, pady=5)
        
        log_frame = ttk.LabelFrame(status_frame, text="📋 Log de Atividades")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_frame, 
            height=6, 
            wrap=tk.WORD, 
            font=('Consolas', 9),
            background="#f4f4f4",
            foreground="#333"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        return status_frame    
    
    def connect(self):
        """Inicia a conexão em uma thread separada."""
        if not self.host_var.get() or not self.database_var.get():
            log_message(self,"Preencha todos os campos obrigatórios!", "warning")
            return
        validation_errors = validate_connection_fields(self)
    
        if validation_errors:
            log_message(self,
                "Erro de Validação"+ 
                "Por favor, corrija os seguintes erros:\n" + "\n".join(validation_errors), "warning"
            )
            return
        
        config = {key: var.get() for key, var in zip(["host", "port", "user", "password", "database"], 
                                                    [self.host_var, self.port_var, self.user_var, self.password_var, self.database_var])}
        
        self.connection_status.set("Conectando...")
        threading.Thread(target=_connect_thread, args=(self,self.db_type.get(), config), daemon=True).start()
  
    

    def quit_app(self):
        """Fecha o aplicativo."""
        self.root.quit()
        self.root.destroy()


    def open_gui_gestaodb(self):
        """Abre uma nova interface de gestão da base de dados sem afetar a janela principal e herdando o tema."""

        if not self.connection:
            log_message(self,"Nenhuma conexão ativa para gerenciamento da base de dados.", "warning")
            return

        log_message(self,"Abrindo interface de gestão da base de dados...", "info")

        try:
            # Criar uma nova instância independente da interface
            new_root = tk.Toplevel(self.root)
            self.gui_gestao_db = new_root
            self.gui_gestao_db.title("Gestão da Base de Dados")

            # Aplicar tema herdado
            if self.dark_mode.get() if hasattr(self.dark_mode, "get") else self.dark_mode:
                new_root.configure(bg="#1e1e1e")  # Fundo escuro
                fg_color = "white"
            else:
                new_root.configure(bg="white")  # Fundo claro
                fg_color = "black"

            # Criar um rótulo apenas para teste do tema herdado
            label = tk.Label(new_root, text="Interface de Gestão da Base de Dados", bg=new_root["bg"], fg=fg_color, font=("Arial", 14))
            label.pack(pady=20)

            # Tentativa de importar DatabaseGUI
            try:
                from DatabaseGUI import DataAnalysisGUI
            except ImportError as e:
                log_message(self,f"Erro ao importar DatabaseGUI: {e}({type(e).__name__})\n{traceback.format_exc()}", "error")
                if self.gui_gestao_db:
                    self.gui_gestao_db.destroy()  # Fecha a nova janela em caso de erro
                self.gui_gestao_db = None
                return

            # Obtém o valor correto do tipo de banco de dados
            db_type_value = self.db_type.get() if hasattr(self.db_type, "get") else self.db_type

            # Inicializa a nova interface de gestão do banco de dados
            
            db_gui = DataAnalysisGUI(
                new_root, self.connection, self.engine, db_type_value,
                self.current_profile.get(),  # Certifica-se de que é uma string
                self.database_var, self.dark_mode, self.connection_status, self.config_manager, self.logmessage,self.root
            )

            #db_gui.root.protocol("WM_DELETE_WINDOW", self.Quit)
            new_root.mainloop()  # Mantém a nova janela ativa

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            log_message(self,f"Erro ao abrir a interface de gestão: {e}\n{error_details}", "error")
    def logmessage(self, message, level="info"):
                log_message(self, message, level)