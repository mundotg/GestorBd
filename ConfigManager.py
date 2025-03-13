import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from logger import logger


class ConfigManager:
    """Gerencia perfis de conexão salvos em um arquivo JSON."""
    
    _lock = threading.Lock()  # Lock para evitar condições de corrida
    
    def __init__(self, config_path: str = "db_profiles.json") -> None:
        """
        Inicializa o gerenciador de perfis de conexão.

        :param config_path: Caminho do arquivo de configuração (padrão: "db_profiles.json").
        """
        self.config_file = Path(config_path)
        self.profiles: Dict[str, Dict[str, Any]] = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Carrega os perfis salvos do arquivo JSON. Se estiver corrompido, cria backup e reinicia."""
        if not self.config_file.exists():
            return {}

        try:
            return json.loads(self.config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.exception(f"Erro ao carregar perfis, criando backup: {e}")
            backup_path = self.config_file.with_suffix(".bak")
            self.config_file.rename(backup_path)
            logger.info(f"Arquivo corrompido movido para: {backup_path}")

            # Criar novo arquivo JSON vazio
            self.config_file.write_text("{}", encoding="utf-8")
            return {}

    def _save_profiles(self) -> bool:
        """Salva os perfis no arquivo JSON de maneira segura."""
        with self._lock:  # Garante que apenas uma thread escreve no arquivo por vez
            try:
                self.config_file.write_text(
                    json.dumps(self.profiles, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                return True
            except OSError as e:
                logger.exception(f"Erro ao salvar perfis: {e}")
                return False

    def save_profile(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Salva um novo perfil de conexão ou atualiza um existente.
        Valida se os dados são serializáveis antes de salvar.
        """
        try:
            json.dumps(config)  # Testa se o dicionário é serializável
        except TypeError as e:
            logger.error(f"Configuração inválida para o perfil '{name}': {e}")
            return False

        with self._lock:
            logger.info(f"Salvando perfil: {name}")
            self.profiles[name] = config
            result = self._save_profiles()
        
        if result:
            logger.info(f"Perfil '{name}' salvo com sucesso.")
        else:
            logger.error(f"Falha ao salvar perfil '{name}'.")
        return result
    def save_table(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """
        Salva uma tabela carregada no arquivo JSON.
        """
        return self.save_profile(f"table_{table_name}", {"data": data})
    

    def get_table(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém uma tabela carregada pelo nome.
        """
        profile = self.get_profile(f"table_{table_name}")
        return profile.get("data") if profile else None

    def delete_profile(self, name: str) -> bool:
        """
        Remove um perfil de conexão pelo nome.
        """
        with self._lock:
            if name in self.profiles:
                del self.profiles[name]
                logger.info(f"Perfil '{name}' removido.")
                return self._save_profiles()
        
        logger.warning(f"Tentativa de remover perfil inexistente: {name}")
        return False

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um perfil de conexão pelo nome.
        """
        with self._lock:
            profile = self.profiles.get(name)
        
        if profile is None:
            logger.warning(f"Perfil '{name}' não encontrado.")
        return profile

    def get_profile_names(self) -> List[str]:
        """
        Retorna a lista de nomes dos perfis salvos.
        """
        with self._lock:
            return list(self.profiles.keys())
    
    def clear_profiles(self) -> bool:
        """
        Limpa todos os perfis salvos.
        """
        with self._lock:
            self.profiles.clear()
            return self._save_profiles()

    def __str__(self) -> str:
        return f"ConfigManager(config_file={self.config_file})" 
    
    def open_file(self) -> str:
        """Carrega o último perfil salvo, se existir."""
        last_profile_path = Path("last_profile.txt")
        
        if not last_profile_path.exists():
            return ""
        
        try:
            last_profile = last_profile_path.read_text().strip()
            with self._lock:
                if last_profile in self.profiles:
                    return last_profile
        except Exception as e:
            logger.error(f"Erro ao carregar último perfil: {e}")
        
        return ""
