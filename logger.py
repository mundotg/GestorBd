import logging
# Configuração de logging
logging.basicConfig(
    filename="database_connector.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


logger = logging.getLogger(__name__)

def log_message(self, message, level="info"):
        """Adiciona mensagem ao log visual e ao arquivo de log"""
        if level == "info":
            logger.info(message)
            self.prefix = "[INFO]"
            self.tag = "info"
        elif level == "error":
            logger.error(message)
            self.prefix = "[ERRO]"
            self.tag = "error"
        elif level == "success":
            logger.info(message)
            self.prefix = "[SUCESSO]"
            self.tag = "success"
        elif level == "warning":
            logger.warning(message)
            self.prefix = "[AVISO]"
            self.tag = "warning"