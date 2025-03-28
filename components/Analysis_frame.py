import tkinter as tk
from tkinter import ttk, messagebox

class HelpWindow(tk.Toplevel):
    """
    Janela auxiliar que fornece explicações detalhadas das funcionalidades
    do aplicativo através de opções selecionáveis.
    """
    
    def __init__(self, parent, title="Ajuda e Informações"):
        super().__init__(parent)
        self.parent = parent
        
        # Configurações da janela
        self.title(title)
        self.geometry("700x500")
        self.minsize(500, 400)
        self.transient(parent)  # Faz esta janela relacionada à janela principal
        self.grab_set()         # Força o foco nesta janela
        
        # Torna a janela responsiva
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Cria o frame principal
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)
        
        # Painel esquerdo com lista de opções
        self.options_frame = ttk.LabelFrame(main_frame, text="Funcionalidades")
        self.options_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        # Painel direito com detalhes
        details_frame = ttk.LabelFrame(main_frame, text="Detalhes")
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        
        # Área de texto para detalhes
        self.details_text = tk.Text(details_frame, wrap="word", padx=10, pady=10)
        self.details_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Scrollbar para texto de detalhes
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.details_text.configure(yscrollcommand=scrollbar.set)
        
        # Botões de controle
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        close_button = ttk.Button(button_frame, text="Fechar", command=self.destroy)
        close_button.pack(side="right", padx=5)
        
        # Inicializar opções vazias
        self.options = []
        
    def add_options(self, options_dict):
        """
        Adiciona opções à lista.
        
        Args:
            options_dict: Dicionário no formato {nome_opção: {"texto": "texto detalhado", "imagem": None}}
        """
        self.options = options_dict
        
        # Limpar opções existentes
        for widget in self.options_frame.winfo_children():
            widget.destroy()
            
        # Criar uma lista com as opções
        for i, (option_name, _) in enumerate(self.options.items()):
            option_btn = ttk.Button(
                self.options_frame, 
                text=option_name, 
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
            
            # Limpar área de texto
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            
            # Inserir título
            self.details_text.insert(tk.END, f"{option_name}\n\n", "title")
            self.details_text.tag_configure("title", font=("Arial", 14, "bold"))
            
            # Inserir detalhes
            self.details_text.insert(tk.END, details["texto"])
            
            # Desativar edição
            self.details_text.config(state=tk.DISABLED)
            
            # Mostrar imagem se disponível
            # Implementação futura
        else:
            messagebox.showwarning("Opção não encontrada", f"A opção '{option_name}' não existe.")

# Exemplo de uso com AnalysisFrame
class AnalysisFrame(ttk.Frame):
    """Frame para análise detalhada da tabela com layout responsivo."""

    def __init__(self, master, df):
        super().__init__(master)
        self.df = df
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._create_widgets()
        
        # Preparar conteúdo de ajuda
        self.help_content = {
            "Resumo Estatístico": {
                "texto": """O recurso de Resumo Estatístico calcula e exibe estatísticas descritivas para todas as colunas numéricas do seu conjunto de dados:

• Contagem (count): Número de valores não nulos
• Média (mean): Valor médio dos dados
• Desvio Padrão (std): Dispersão dos valores em relação à média
• Mínimo (min): Menor valor da coluna
• 25% (25%): Primeiro quartil - 25% dos dados estão abaixo deste valor
• 50% (50%): Mediana - valor central da coluna
• 75% (75%): Terceiro quartil - 75% dos dados estão abaixo deste valor
• Máximo (max): Maior valor da coluna

Este recurso é útil para entender rapidamente a distribuição dos seus dados numéricos e identificar possíveis valores atípicos.

Para colunas não numéricas, o resumo mostrará informações básicas como contagem, frequência e valores únicos.
""",
                "imagem": None
            },
            "Ver Duplicatas": {
                "texto": """A função Ver Duplicatas identifica e exibe todas as linhas duplicadas presentes no seu conjunto de dados.

Duas ou mais linhas são consideradas duplicatas quando possuem exatamente os mesmos valores em todas as colunas. Por padrão, todas as instâncias das linhas duplicadas são mostradas, incluindo a primeira ocorrência.

Quando usar:
• Para identificar erros de entrada de dados
• Para detectar registros duplicados antes de realizar análises
• Para limpeza de dados

Se nenhuma duplicata for encontrada, uma mensagem "Nenhum registro duplicado encontrado" será exibida.

Dica: Após identificar duplicatas, você pode considerar removê-las do seu conjunto de dados antes de prosseguir com análises mais complexas.
""",
                "imagem": None
            },
            "Registros Mal Formados": {
                "texto": """A função Registros Mal Formados detecta e exibe linhas que contêm:

• Valores nulos (NaN, None, NULL)
• Strings vazias ("")
• Strings que contêm apenas espaços em branco

Esta função é essencial para identificar dados incompletos ou mal formatados que podem afetar a qualidade da sua análise.

Quando usar:
• Antes de iniciar qualquer análise de dados
• Como parte do processo de limpeza de dados
• Para identificar padrões de dados ausentes

Se não houver registros mal formados, uma mensagem "Nenhum registro mal formado encontrado" será exibida.

Dica: Considere estratégias para lidar com registros mal formados, como remoção, imputação (preenchimento) de valores ausentes, ou correção dos dados.
""",
                "imagem": None
            },
            "Tipos de Dados": {
                "texto": """A função Tipos de Dados mostra o tipo de dado de cada coluna no seu conjunto de dados:

• int64: Números inteiros
• float64: Números decimais
• object: Principalmente texto (strings) ou dados mistos
• datetime64: Datas e horários
• bool: Valores booleanos (True/False)
• category: Dados categóricos

Conhecer os tipos de dados é fundamental porque:
• Influencia quais operações são possíveis em cada coluna
• Afeta o desempenho e o consumo de memória
• Determina quais métodos de visualização são apropriados

Dica: Algumas operações requerem conversão de tipos. Por exemplo, você não pode realizar cálculos numéricos em colunas do tipo 'object' sem primeiro convertê-las para um tipo numérico.
""",
                "imagem": None
            },
            "Valores Únicos": {
                "texto": """A função Valores Únicos conta e exibe o número de valores distintos em cada coluna do seu conjunto de dados.

Por exemplo, se uma coluna "Estado" contém os valores ["SP", "RJ", "SP", "MG", "SP"], o número de valores únicos será 3.

Esta informação é útil para:
• Identificar colunas categóricas
• Verificar se colunas que deveriam ter valores exclusivos (como IDs) realmente têm
• Entender a cardinalidade (número de valores possíveis) de cada coluna

Colunas com alta cardinalidade (muitos valores únicos) podem requerer abordagens específicas em análises estatísticas e visualizações.

Dica: Uma coluna com apenas um valor único não contribui com informação para análises e pode potencialmente ser removida, dependendo do contexto.
""",
                "imagem": None
            },
            "Contagem por Categoria": {
                "texto": """A função Contagem por Categoria analisa colunas do tipo texto (object) ou categóricas e mostra a frequência de cada valor único.

Para cada coluna categórica, esta função exibe:
• Lista de todos os valores únicos
• Contagem de ocorrências de cada valor
• Ordem decrescente por frequência

Isso é especialmente útil para:
• Entender a distribuição de categorias nos seus dados
• Identificar valores raros ou outliers categóricos
• Verificar o balanceamento de classes (importante para modelos de classificação)

Se não houver colunas categóricas no conjunto de dados, uma mensagem "Nenhuma coluna categórica encontrada" será exibida.

Dica: Para categorias com muitos valores únicos, considere agrupar valores menos frequentes em uma categoria "Outros" para simplificar análises subsequentes.
""",
                "imagem": None
            },
            "Exportar Análise": {
                "texto": """A função Exportar Análise permite salvar seu conjunto de dados atual em um arquivo externo para uso posterior ou compartilhamento.

Formatos suportados:
• CSV (Comma Separated Values): Formato de texto universal que pode ser aberto em qualquer programa de planilha ou editor de texto.
• Excel (.xlsx): Formato nativo do Microsoft Excel, mantém formatação e pode conter múltiplas planilhas.

Ao clicar nesta opção:
1. Uma janela de diálogo será aberta para escolher o local e nome do arquivo
2. Você poderá selecionar o formato desejado
3. O arquivo será salvo com todas as modificações e transformações aplicadas aos dados durante a análise

Dica: O formato CSV é mais compatível com diferentes sistemas e ferramentas, enquanto o Excel é melhor se você precisa manter formatação complexa ou planeja trabalhar exclusivamente no Excel.
""",
                "imagem": None
            }
        }

    def _create_widgets(self):
        """Cria os widgets de análise com layout responsivo."""
        # Cabeçalho
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.columnconfigure(0, weight=1)
        
        label = ttk.Label(header_frame, text="Análise Detalhada da Tabela", font=("Arial", 12, "bold"))
        label.grid(row=0, column=0, sticky="w")
        
        # Botão de ajuda que abre a janela com opções
        help_button = ttk.Button(header_frame, text="Ajuda Detalhada", command=self.show_help_window)
        help_button.grid(row=0, column=1, sticky="e")
        
        # Área de texto com scrollbars
        text_frame = ttk.Frame(self)
        text_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        
        self.text_area = tk.Text(text_frame, wrap="none", height=15, width=80)
        self.text_area.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_area.yview)
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        
        x_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=self.text_area.xview)
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.text_area.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Frame para botões com layout responsivo usando grid
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        buttons = [
            ("Resumo Estatístico", self.show_summary),
            ("Ver Duplicatas", self.show_duplicates),
            ("Registros Mal Formados", self.show_malformed_records),
            ("Tipos de Dados", self.show_data_types),
            ("Valores Únicos", self.show_unique_values),
            ("Contagem por Categoria", self.show_category_counts),
            ("Exportar Análise", self.export_analysis)
        ]
        
        # Organização dos botões em grid para melhor responsividade
        for i, (text, command) in enumerate(buttons):
            row, col = divmod(i, 4)  # 4 botões por linha
            ttk.Button(button_frame, text=text, command=command).grid(
                row=row, column=col, padx=5, pady=5, sticky="ew"
            )

    def show_help_window(self):
        """Abre a janela de ajuda com as opções detalhadas."""
        help_window = HelpWindow(self, title="Guia de Funcionalidades - Análise Detalhada")
        help_window.add_options(self.help_content)
        
        # Posiciona a janela de ajuda próxima à janela principal
        self.update_idletasks()
        x = self.winfo_rootx() + 50
        y = self.winfo_rooty() + 50
        help_window.geometry(f"+{x}+{y}")

    def update_text_area(self, text):
        """Atualiza a área de texto com os resultados da análise."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.config(state=tk.DISABLED)
        # Retorna ao início do texto
        self.text_area.see("1.0")

    # Os demais métodos (show_summary, show_duplicates, etc.) permanecem inalterados
    def show_summary(self):
        """Exibe um resumo estatístico dos dados."""
        try:
            summary = self.df.describe(include="all").to_string()
            self.update_text_area(summary)
        except Exception as e:
            self.handle_error("Erro ao gerar resumo estatístico", e)

    def show_duplicates(self):
        """Exibe registros duplicados."""
        try:
            duplicates = self.df[self.df.duplicated(keep=False)]
            self.update_text_area(duplicates.to_string() if not duplicates.empty else "Nenhum registro duplicado encontrado.")
        except Exception as e:
            self.handle_error("Erro ao verificar duplicatas", e)

    def show_malformed_records(self):
        """Exibe registros com valores nulos ou mal formados."""
        try:
            is_null = self.df.isnull().any(axis=1)
            is_empty_string = self.df.select_dtypes(include=["object"]).apply(lambda col: col.astype(str).str.strip() == "").any(axis=1)
            malformed = self.df[is_null | is_empty_string]
            self.update_text_area(malformed.to_string() if not malformed.empty else "Nenhum registro mal formado encontrado.")
        except Exception as e:
            self.handle_error("Erro ao verificar registros mal formados", e)

    def show_data_types(self):
        """Exibe os tipos de dados de cada coluna."""
        try:
            self.update_text_area(self.df.dtypes.to_string())
        except Exception as e:
            self.handle_error("Erro ao mostrar tipos de dados", e)

    def show_unique_values(self):
        """Exibe a contagem de valores únicos em cada coluna."""
        try:
            self.update_text_area(self.df.nunique().to_string())
        except Exception as e:
            self.handle_error("Erro ao contabilizar valores únicos", e)

    def show_category_counts(self):
        """Exibe a contagem de valores únicos para colunas categóricas."""
        try:
            categorical_cols = self.df.select_dtypes(include=["object", "category"])
            if categorical_cols.empty:
                self.update_text_area("Nenhuma coluna categórica encontrada.")
            else:
                formatted_counts = "\n\n".join([f"{col}:\n{self.df[col].value_counts().to_string()}" for col in categorical_cols])
                self.update_text_area(formatted_counts)
        except Exception as e:
            self.handle_error("Erro ao contar categorias", e)

    def export_analysis(self):
        """Exporta a análise para um arquivo CSV ou Excel."""
        filetypes = [("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")]
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes)

        if not file_path:
            return

        try:
            if file_path.endswith(".csv"):
                self.df.to_csv(file_path, index=False)
            else:
                self.df.to_excel(file_path, index=False)
            messagebox.showinfo("Exportação Concluída", f"Arquivo salvo em:\n{file_path}")
        except Exception as e:
            self.handle_error("Erro ao exportar", e)
            
    def handle_error(self, title, error):
        """Gerencia erros de forma centralizada."""
        messagebox.showerror(title, f"Erro: {str(error)}")
        self.update_text_area(f"Ocorreu um erro: {str(error)}")

# Exemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Demonstração da Janela de Ajuda")
    root.geometry("1000x600")
    
    # Criar um DataFrame de exemplo
    import pandas as pd
    import numpy as np
    
    data = {
        'Nome': ['João', 'Maria', 'Pedro', 'Ana', 'Carlos'],
        'Idade': [25, 30, 22, 28, 35],
        'Salário': [3500, 4200, 2800, 3900, 5000],
        'Departamento': ['TI', 'RH', 'Marketing', 'TI', 'Financeiro']
    }
    df = pd.DataFrame(data)
    
    # Adicionar a frame de análise
    frame = AnalysisFrame(root, df)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()