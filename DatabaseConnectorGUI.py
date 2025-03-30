import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import traceback
from DatabaseManager import DatabaseManager, DatabaseUtils
from utils.logger import log_message as logmessage
from config.ConfigManager import ConfigManager
from Theme import Theme

class DatabaseConnectorGUI:
    """Interface gráfica para conexão com banco de dados."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Conector Avançado de Banco de Dados")
        self.root.geometry("650x500")
        self.root.minsize(450, 400)
        
        self._initialize_variables()
        self._load_theme()
        self._create_menu()
        self._create_gui()
        
        self.current_profile.set(self.config_manager.open_file())
        self.load_profile()
        self.root.bind("<Configure>", self._on_window_resize)
    def _on_window_resize(self, event):
        """Ajusta o layout quando a janela é redimensionada."""
        width = event.width
        
        # Ajustes baseados na largura da janela
        if width < 600:
            # Layout compacto para telas menores
            self._create_compact_layout()
        elif width < 800:
            # Layout intermediário
            self._create_intermediate_layout()
        else:
            # Layout padrão para telas maiores
            self._create_default_layout()
    def _create_compact_layout(self):
        """Layout compacto para telas menores."""
        # Implementação de layout responsivo para telas compactas
        # Pode incluir redução de espaçamento, mudança de orientação dos elementos
        pass

    def _create_intermediate_layout(self):
        """Layout intermediário para telas de tamanho médio."""
        # Ajustes para telas de tamanho médio
        pass

    def _create_default_layout(self):
        """Layout padrão para telas maiores."""
        # Implementação do layout original com possíveis otimizações
        pass
    
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
        
        # Tema dinâmico baseado em preferência do sistema
        system_theme = self._detect_system_theme()
        selected_theme = Theme.DARK if system_theme == 'dark' else Theme.LIGHT
        
        self.style = self.theme.apply_theme(self.root, selected_theme)
        
        # Configurações adicionais de tema
        self.root.configure(bg=self.style.lookup('TFrame', 'background'))
    def _detect_system_theme(self):
        """Detecta o tema do sistema operacional."""
        import platform
        
        # Implementação simplificada, pode ser expandida
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
            # Lógica para macOS (pode variar)
            return 'dark'
        else:
            return 'light'
        
    def _create_menu(self):
        """Cria a barra de menu."""
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Novo Perfil", command=self.new_profile)
        file_menu.add_command(label="Salvar Perfil", command=self.save_profile)
        file_menu.add_command(label="Excluir Perfil", command=self.delete_profile)
        file_menu.add_separator()
        file_menu.add_command(label="🚪❌Sair", command=self.quit_app)
        menubar.add_cascade(label="👤Arquivo", menu=file_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.root.config(menu=menubar)

    def _create_gui(self):
        """Cria a interface gráfica principal com layout aprimorado."""
        # Configuração do layout principal com padding e grid
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuração de grid para melhor responsividade
        main_frame.columnconfigure(0, weight=1)
        
        # Seções com pesos de grid
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
        
        # Adiciona ícones e melhora alinhamento
        profile_label = ttk.Label(profile_frame, text="Perfil:")
        profile_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Combobox com largura ajustada e estado de foco
        self.profile_combo = ttk.Combobox(
            profile_frame, 
            textvariable=self.current_profile, 
            values=self.config_manager.get_profile_names(), 
            width=25,
            state="readonly"
        )
        self.profile_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        # Botões com ícones e espaçamento
        load_btn = ttk.Button(profile_frame, text="🔄Carregar", command=self.load_profile, width=10)
        load_btn.grid(row=0, column=2, padx=5)
        
        save_btn = ttk.Button(profile_frame, text="💾Salvar", command=self.save_profile, width=10)
        save_btn.grid(row=0, column=3, padx=5)
        
        # Configuração de grid
        profile_frame.columnconfigure(1, weight=1)
        
        return profile_frame
    
    def _create_connection_section(self, parent):
        """Cria seção de conexão com layout aprimorado."""
        conn_frame = ttk.LabelFrame(parent, text="🔌Configuração da Conexão", padding=10)
        
        # Campos de configuração com grid
        fields = [
            ("🖥️ Banco de Dados:", self.db_type, "readonly"),
            ("🌐 Host:", self.host_var, "normal"),
            ("🚪 Porta:", self.port_var, "normal"),
            ("👤 Usuário:", self.user_var, "normal"),
            ("🔐 Senha:", self.password_var, "password")
        ]
        
        for i, (label, var, state) in enumerate(fields):
            ttk.Label(conn_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            
            if label.startswith("🖥️"):  # Combobox para tipo de banco
                options = ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle", "MongoDB", "MariaDB"]
                entry = ttk.Combobox(conn_frame, textvariable=var, values=options, width=25, state=state)
                entry.bind("<<ComboboxSelected>>", self.update_port)
            else:
                show = "*" if state == "password" else ""
                entry = ttk.Entry(conn_frame, textvariable=var, width=25, show=show, state=state)
            
            entry.grid(row=i, column=1, sticky="ew", pady=5)
        
        # Configuração de grid
        conn_frame.columnconfigure(1, weight=1)
        
        return conn_frame
    
    def _create_section_button(self, main_frame):
        button_frame = ttk.Frame(main_frame)
        # button_frame.grid(fill=tk.X, pady=(0, 10))
        ttk.Button(button_frame, text="🔌Conectar", command=self.connect, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌Desconectar", command=self.disconnect, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🛠️Testar Conexão", command=self.test_connection, width=19).pack(side=tk.LEFT, padx=5,pady=5)
        self.button_mb = ttk.Button(button_frame, text="📊Continuar com gestão da base de dados", command=self.open_gui_gestaodb)
        if not self.connection:
            self.button_mb.pack_forget()
        return button_frame
    
    def _create_status_section(self, parent):
        """Cria seção de status com layout aprimorado."""
        status_frame = ttk.Frame(parent)
        
        # Status de conexão com cores e ícones
        self.status_label =  ttk.Label(
            status_frame, 
            textvariable=self.connection_status, 
            font=('Arial', 10, 'bold')
        )
        self.status_label.pack(fill=tk.X, pady=5)
        
        # Log com scrollbar e destaque
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
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        return status_frame
    
    def _create_connection_fields(self, parent):
        """Cria os campos de entrada para configuração da conexão."""
        fields = [
            ("Host:", self.host_var),
            ("Porta:", self.port_var),
            ("Usuário:", self.user_var),
            ("Senha:", self.password_var, "*")
        ]
        
        for i, (label, var, *show) in enumerate(fields):
            ttk.Label(parent, text=label).grid(row=i, column=0, sticky="w", pady=5)
            ttk.Entry(parent, textvariable=var, width=20, show=show[0] if show else "").grid(row=i, column=1, sticky="w", pady=5)
    
    def update_port(self, event=None):
        """Atualiza a porta padrão com base no tipo de banco selecionado."""
        db_type = self.db_type.get()
        self.port_var.set(str(DatabaseUtils.get_default_port(db_type)) if db_type != "SQLite" else "")
        self.host_var.set("" if db_type == "SQLite" else "localhost")
    
    def quit_app(self):
        if self.connection:
            self.connection.close()
        self.root.quit()
    
    def log_message(self, message, level="info"):
        # print("log message: ",message)
        if level == "info":
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"\n{message}")
            self.log_text.config(state=tk.DISABLED)
        logmessage(self, message, level)
    
    def validate_connection_fields(self):
        """Validate connection fields before attempting to connect."""
        errors = []
        
        # Check database type
        if not self.db_type.get():
            errors.append("Selecione um tipo de banco de dados")
        
        # Validate host (except for SQLite)
        if self.db_type.get() != "SQLite":
            if not self.host_var.get():
                errors.append("Host não pode estar vazio")
            
            # Validate port
            try:
                port = int(self.port_var.get())
                if port <= 0 or port > 65535:
                    errors.append("Porta inválida")
            except ValueError:
                errors.append("Porta deve ser um número válido")
        
        # Validate user credentials (except SQLite)
        if self.db_type.get() not in ["SQLite"]:
            if not self.user_var.get():
                errors.append("Usuário não pode estar vazio")
        
        return errors
    
    def connect(self):
        """Inicia a conexão em uma thread separada."""
        if not self.host_var.get() or not self.database_var.get():
            self.log_message("Preencha todos os campos obrigatórios!", "warning")
            return
        validation_errors = self.validate_connection_fields()
    
        if validation_errors:
            self.log_message(
                "Erro de Validação"+ 
                "Por favor, corrija os seguintes erros:\n" + "\n".join(validation_errors), "warning"
            )
            return
        
        config = {key: var.get() for key, var in zip(["host", "port", "user", "password", "database"], 
                                                      [self.host_var, self.port_var, self.user_var, self.password_var, self.database_var])}
        
        self.connection_status.set("Conectando...")
        threading.Thread(target=self._connect_thread, args=(self.db_type.get(), config), daemon=True).start()
  
    
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
        if not hasattr(self, "status_label"):
            print("Erro: status_label não foi inicializado corretamente!")
            return  # Evita continuar se status_label não existir

        if success:
            self.button_mb.pack(side=tk.RIGHT, padx=4)
            self.connection_status.set("Status: Conectado")
            self.status_label.config(foreground="#28a745")
            self.log_message(message, "success")
        else:
            self.connection_status.set("Status: Erro na Conexão")
            self.button_mb.pack_forget()
            self.status_label.config(foreground="#dc3545")
            self.log_message(message, "error")

    
    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                self.connection_status.set("Desconectado")
                self.button_mb.pack_forget()
                self.status_label.config(foreground="#dc3545")
                self.log_message("Conexão encerrada com sucesso.", "info")
                if self.gui_gestao_db:
                    self.gui_gestao_db.destroy()
                    self.gui_gestao_db = None
            except Exception as e:
                self.log_message(f"Erro ao desconectar: {e}", "error")
            
    def open_gui_gestaodb(self):
        """Abre uma nova interface de gestão da base de dados sem afetar a janela principal e herdando o tema."""

        if not self.connection:
            self.log_message("Nenhuma conexão ativa para gerenciamento da base de dados.", "warning")
            return

        self.log_message("Abrindo interface de gestão da base de dados...", "info")

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
                self.log_message(f"Erro ao importar DatabaseGUI: {e}", "error")
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
                self.database_var, self.dark_mode, self.connection_status, self.config_manager,self.log_message,self.root
            )

            #db_gui.root.protocol("WM_DELETE_WINDOW", self.Quit)
            new_root.mainloop()  # Mantém a nova janela ativa

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.log_message(f"Erro ao abrir a interface de gestão: {e}\n{error_details}", "error")



    
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
            self.log_message(f"Erro no teste de conexão: {e}  ({type(e).__name__})\n{traceback.format_exc()}", "error")
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
            "db_type": str(self.db_type.get()),  # Converter para string
            "host": self.host_var.get(),
            "port": str(self.port_var.get()),  # Garantir que seja string
            "user": self.user_var.get(),
            "password": self.password_var.get(),
            "database": self.database_var.get()
        }
        print(f'config = {config}')
        self.config_manager.save_profile(name=profile_name, config=config)
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
    

    
   
