import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

class AnalysisFrame(ttk.Frame):
    """Frame para análise detalhada da tabela com layout responsivo."""

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master)
        self.df = df
        self.columnconfigure(0, weight=1)  # Torna o frame responsivo horizontalmente
        self.rowconfigure(2, weight=1)     # Torna a área de texto expansível
        self._create_widgets()

    def _create_widgets(self):
        """Cria os widgets de análise com layout responsivo."""
        # Cabeçalho
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.columnconfigure(0, weight=1)
        
        label = ttk.Label(header_frame, text="Análise Detalhada da Tabela", font=("Arial", 12, "bold"))
        label.grid(row=0, column=0, sticky="w")
        
        help_button = ttk.Button(header_frame, text="?", width=3, command=self.show_help)
        help_button.grid(row=0, column=1, sticky="e")
        
        # Botão de descrição da funcionalidade
        info_frame = ttk.Frame(self)
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        info_frame.columnconfigure(0, weight=1)
        
        describe_button = ttk.Button(
            info_frame, 
            text="Sobre esta funcionalidade", 
            command=self.describe_functionality
        )
        describe_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

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

    def describe_functionality(self):
        """Exibe uma explicação detalhada sobre o propósito e os recursos desta funcionalidade utilizando HelpWindow."""
        from components.HelpWindow import HelpWindow  # Importação da classe HelpWindow

        # Definição das seções de ajuda para a janela informativa
        help_options = {
            "Visão Geral": {
                "texto": "A Análise Detalhada permite uma investigação aprofundada dos seus dados, auxiliando na identificação de padrões, inconsistências e insights valiosos. Essa ferramenta é essencial para avaliar a qualidade e a estrutura dos dados antes de avançar para análises mais complexas.",
                "imagem": None
            },
            "Funcionalidades Disponíveis": {
                "texto": "",
                "tags": {
                    "A ferramenta oferece diversas funcionalidades para facilitar sua análise:\n\n": "",
                    "• Resumo Estatístico: ": "bold",
                    "Gera estatísticas descritivas (média, mínimo, máximo, etc.) para colunas numéricas.\n\n": "",
                    "• Identificação de Duplicatas: ": "bold",
                    "Localiza e exibe registros duplicados na tabela.\n\n": "",
                    "• Detecção de Registros Mal Formados: ": "bold",
                    "Aponta linhas com valores nulos ou campos vazios que podem comprometer a análise.\n\n": "",
                    "• Tipos de Dados: ": "bold",
                    "Apresenta o tipo de dado de cada coluna (numérico, texto, data, etc.).\n\n": "",
                    "• Contagem de Valores Únicos: ": "bold",
                    "Exibe a quantidade de valores distintos por coluna.\n\n": "",
                    "• Análise de Categorias: ": "bold",
                    "Mostra a distribuição de valores em colunas categóricas.\n\n": "",
                    "• Exportação de Dados: ": "bold",
                    "Permite salvar a análise em formato CSV ou Excel para uso posterior.": ""
                },
                "imagem": None
            },
            "Melhores Práticas": {
                "texto": (
                    "Para otimizar sua análise e obter resultados mais precisos, siga estas recomendações:\n\n"
                    "1. Revise os registros mal formados antes de qualquer processamento avançado.\n"
                    "2. Identifique e trate duplicatas para evitar distorções.\n"
                    "3. Verifique os tipos de dados e corrija inconsistências.\n"
                    "4. Analise a contagem de categorias para detectar valores incomuns ou erros de digitação.\n"
                    "5. Utilize o resumo estatístico para identificar valores atípicos e padrões relevantes."
                ),
                "imagem": None
            },
            "Fluxo de Trabalho Recomendado": {
                "texto": (
                    "Para uma análise eficiente, siga este fluxo de trabalho:\n\n"
                    "1. Confirme os tipos de dados das colunas.\n"
                    "2. Identifique e corrija registros mal formados.\n"
                    "3. Verifique e elimine duplicatas.\n"
                    "4. Analise a distribuição dos dados usando o resumo estatístico.\n"
                    "5. Examine valores categóricos para evitar inconsistências.\n"
                    "6. Exporte os dados tratados para análises mais avançadas."
                ),
                "imagem": None
            }
        }

        # Inicialização da janela de ajuda
        help_window = HelpWindow(self, title="Análise Detalhada - Informações")
        help_window.add_options(help_options)

        

    def show_help(self):
        """Exibe um diálogo de ajuda."""
        messagebox.showinfo(
            "Ajuda - Análise Detalhada", 
            "Esta tela permite analisar seus dados de várias formas diferentes.\n\n"
            "Para começar, clique em algum dos botões abaixo da área de texto "
            "para executar uma análise específica.\n\n"
            "Você pode exportar os dados analisados usando o botão 'Exportar Análise'."
        )

    def update_text_area(self, text):
        """Atualiza a área de texto com os resultados da análise."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.config(state=tk.DISABLED)
        # Retorna ao início do texto
        self.text_area.see("1.0")

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