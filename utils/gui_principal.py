from tkinter import messagebox, simpledialog
import tkinter as tk
import traceback
from DatabaseManager import DatabaseManager, DatabaseUtils
from utils.logger import log_message as logmessage

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
            log_message(self,f"Novo perfil '{profile_name}' criado. Configure e salve-o.", "info")
            
def delete_profile(self):
    """Exclui um perfil salvo"""
    profile_name = self.current_profile.get()
    
    if not profile_name:
        log_message(self,"Nenhum perfil selecionado para exclusão.", "warning")
        return
    
    if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o perfil '{profile_name}'?"):
        self.config_manager.delete_profile(profile_name)
        self.log_message(f"Perfil '{profile_name}' excluído com sucesso.", "info")
        
        # Atualizar lista de perfis e limpar seleção atual
        self.profile_combo['values'] = self.config_manager.get_profile_names()
        self.current_profile.set("")
        
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
    
    log_message(self,f"Testando conexão com {db_type}...")
    
    try:
        
        if DatabaseUtils.test_connection( db_type,config ):
            log_message(self,f"Teste de conexão bem-sucedido com {db_type}!", "success")
            messagebox.showinfo("Teste de Conexão", f"Conexão bem-sucedida com {db_type}!")
        else:
            log_message(self,f"Falha no teste de conexão com {db_type}.", "error")
            messagebox.showerror("Teste de Conexão", f"Falha no teste de conexão com {db_type}.")
    except Exception as e:
        log_message(self,f"Erro no teste de conexão: {e}  ({type(e).__name__})\n{traceback.format_exc()}", "error")
        messagebox.showerror("Erro", f"Erro ao testar conexão: {e}")

def update_port(self, event=None):
    """Atualiza a porta padrão com base no tipo de banco selecionado."""
    db_type = self.db_type.get()
    self.port_var.set(str(DatabaseUtils.get_default_port(db_type)) if db_type != "SQLite" else "")
    self.host_var.set("" if db_type == "SQLite" else "localhost")  
      
def disconnect(self):
    """Desconecta do banco de dados"""
    if self.connection:
        try:
            self.connection.close()
            self.connection = None
            self.connection_status.set("Desconectado")
            self.button_mb.pack_forget()
            self.status_label.config(foreground="#dc3545")
            log_message(self,"Conexão encerrada com sucesso.", "info")
            if self.gui_gestao_db:
                self.gui_gestao_db.destroy()
                self.gui_gestao_db = None
        except Exception as e:
            log_message(self,f"Erro ao desconectar: {e}", "error")

def _update_connection_status(self, success, message):
    """Atualiza a interface com o status da conexão"""
    if not hasattr(self, "status_label"):
        print("Erro: status_label não foi inicializado corretamente!")
        return  # Evita continuar se status_label não existir

    if success:
        self.button_mb.pack(side=tk.RIGHT, padx=4)
        self.connection_status.set("Status: Conectado")
        self.status_label.config(foreground="#28a745")
        log_message(self,message, "success")
    else:
        self.connection_status.set("Status: Erro na Conexão")
        self.button_mb.pack_forget()
        self.status_label.config(foreground="#dc3545")
        log_message(self,message, "error")
def log_message(self, message, level="info"):
    # print("log message: ",message)
    if level == "info":
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"\n{message}")
        self.log_text.config(state=tk.DISABLED)
    logmessage(self, message, level)
    
def load_profile(self):
        """Carrega um perfil salvo"""
        profile_name = self.current_profile.get()
        
        if not profile_name:
            log_message(self,"Nenhum perfil selecionado.", "warning")
            return
        
        profile = self.config_manager.get_profile(profile_name)
        
        if profile:
            self.db_type.set(profile.get("db_type", "MySQL"))
            self.host_var.set(profile.get("host", "localhost"))
            self.port_var.set(profile.get("port", "3306"))
            self.user_var.set(profile.get("user", ""))
            self.password_var.set(profile.get("password", ""))
            self.database_var.set(profile.get("database", ""))
            log_message(self,f"Perfil '{profile_name}' carregado com sucesso.", "info")
        else:
            log_message(self,f"Perfil '{profile_name}' não encontrado.", "error")
            
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
    log_message(self,f"Perfil '{profile_name}' salvo com sucesso.", "success")
    
    # Atualizar lista de perfis no combobox
    self.profile_combo['values'] = self.config_manager.get_profile_names()

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
        self.root.after(0, lambda: _update_connection_status(self=self,success=True,message= f"Conectado ao {db_type} com sucesso!"))
        
        # Salvar último perfil usado
        if self.current_profile.get():
            try:
                with open("last_profile.txt", "w") as f:
                    f.write(self.current_profile.get())
            except Exception as e:
                self.log_message(f"Erro ao salvar perfil atual: {e}", "warning")
    
    except Exception as e:
        error_msg = str(e)
        self.root.after(0, lambda: _update_connection_status(self=self,success=False, message=f"Erro ao conectar ao {db_type}: {error_msg}"))

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