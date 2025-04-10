import json
import threading
from pathlib import Path
import pandas as pd
from typing import Dict, Any, Optional, List
from utils.logger import logger


class ConfigManager:
    """Gerencia perfis de conexão salvos em um arquivo JSON."""
    
    _lock = threading.Lock()  # Lock para evitar condições de corrida
    
    def __init__(self, config_path: str = "db_profiles.json",base_path="tabela_salvas") -> None:
        """
        Inicializa o gerenciador de perfis de conexão.

        :param config_path: Caminho do arquivo de configuração (padrão: "db_profiles.json").
        """
        self.config_file = Path(config_path)
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
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
        print(f"_save_profiles: ")
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
        for key, value in config.items():
            print(key, value)
            try:
                json.dumps(value)
            except TypeError as e:
                print(f"Erro ao serializar a chave '{key}' com valor '{value}' (tipo: {type(value)})")
                logger.error(f"Configuração inválida para o perfil '{name}': {e}")
                return False
        

        with self._lock:
            print(f"Salvando perfil: {name}")
            logger.info(f"Salvando perfil: {name}")
            self.profiles[name] = config
            print(f" self.profiles[name] = config")
            result = self._save_profiles()
            print("result = self._save_profiles()")
        
        if result:
            logger.info(f"Perfil '{name}' salvo com sucesso.")
        else:
            logger.error(f"Falha ao salvar perfil '{name}'.")
        return result
   

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
    def save_table_to_excel(self, df: pd.DataFrame, table_name: str) -> bool:
        """
        Salva os dados de um DataFrame em um arquivo Excel.
        :param df: DataFrame com os dados da tabela.
        :param table_name: Nome da tabela para salvar.
        :return: True se salvar com sucesso, False caso contrário.
        """
        try:
            file_path = self.base_path / f"{table_name}.xlsx"
            df.to_excel(file_path, index=False)
            logger.info(f"Tabela '{table_name}' salva com sucesso em '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar tabela '{table_name}': {e}")
            return False

    def save_table_metadata(self, df: pd.DataFrame, table_name: str, current_profile: str) -> bool:
        """
        Salva os metadados da tabela em um arquivo JSON.

        :param df: DataFrame contendo os dados.
        :param table_name: Nome da tabela.
        :param current_profile: Nome do perfil atual.
        :return: True se salvar com sucesso, False caso contrário.
        """
        try:
            metadata = {
                "table_name": table_name,
                "columns": list(df.columns),
                "dtypes": df.dtypes.astype(str).to_dict()
            }

            profile_path = self.base_path / current_profile
            profile_path.mkdir(parents=True, exist_ok=True)  # Garante que o diretório do perfil existe.

            metadata_path = profile_path / f"{table_name}_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

            logger.info(f"Metadados da tabela '{table_name}' salvos com sucesso em '{metadata_path}'.")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar metadados da tabela '{table_name}': {e}")
            return False

    def load_table_metadata(self, table_name: str, current_profile: str) -> Optional[Dict[str, Any]]:
        """
        Carrega os metadados da tabela a partir do arquivo JSON.

        :param table_name: Nome da tabela.
        :param current_profile: Nome do perfil atual.
        :return: Dicionário com os metadados ou None se não existir.
        """
        metadata_path = self.base_path / current_profile / f"{table_name}_metadata.json"

        if not metadata_path.exists():
            logger.warning(f"Metadados da tabela '{table_name}' não encontrados para o perfil '{current_profile}'.")
            return None

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            logger.info(f"Metadados da tabela '{table_name}' carregados com sucesso.")
            return metadata
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao carregar metadados da tabela '{table_name}': {e}")
            return None
