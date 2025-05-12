# Nome do ambiente virtual
VENV=venv
PYTHON=$(VENV)/Scripts/python.exe
PIP=$(VENV)/Scripts/pip.exe
ACTIVATE=$(VENV)/Scripts/activate

# Nome do arquivo principal da aplicação
MAIN=app.py
# Cria o ambiente virtual
setup:
	@echo "🔧 Criando ambiente virtual..."
	@if not exist $(VENV) python -m venv $(VENV)
	@echo "✅ Ambiente virtual criado!"

# Instala dependências do requirements.txt
install: setup
	@echo "📦 Instalando dependências..."
	@$(PIP) install -r requirements.txt
	@echo "✅ Dependências instaladas!"

# Ativa o ambiente virtual
activate:
	@echo "💻 Ativando ambiente virtual..."
	@cmd /k "$(ACTIVATE)"

# Executa a aplicação
run: install
	@echo "🚀 Iniciando aplicação..."
	@$(PYTHON) $(MAIN)

# Limpa arquivos temporários
clean:
	@echo "🧹 Limpando arquivos temporários..."
	@rmdir /s /q __pycache__ || echo "Nenhum cache para limpar."
	@echo "✅ Limpeza concluída!"
# Remove o ambiente virtual
reset:
	@echo "🔄 Removendo ambiente virtual..."
	@if exist $(VENV) rmdir /s /q $(VENV)
	@echo "✅ Ambiente virtual removido!"
freeze:
	@pip freeze > requirements.txt

execute: 
	@pyinstaller --onefile --noconsole --hidden-import=pyodbc --hidden-import=sqlalchemy main.py 
