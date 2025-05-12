import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from const.const_import import help_content
from components.HelpWindow import HelpWindow
# Exemplo de uso com AnalysisFrame
class AnalysisFrame(ttk.Frame):
    """Frame para análise detalhada da tabela com layout responsivo."""

    def __init__(self, master, df,log_message=None):
        super().__init__(master)
        self.df = df
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._create_widgets()
        
        # Preparar conteúdo de ajuda
        self.help_content = help_content
        self.log_message = log_message  # Armazena a mensagem de log, se fornecida
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
        """Exibe um resumo estatístico dos dados, com verificação de erros e validação do DataFrame."""
        try:
            # Verifica se o DataFrame não está vazio
            if self.df.empty:
                self.update_text_area("O DataFrame está vazio. Não é possível gerar um resumo.")
                return

            # Verifica se self.df é um DataFrame
            if not isinstance(self.df, pd.DataFrame):
                self.update_text_area("O objeto não é um DataFrame válido.")
                return

            # Gera o resumo estatístico com 'include="all"' para incluir todos os tipos de colunas
            summary = self.df.describe(include="all").to_string()

            # Verifica o tamanho do resumo e decide se deve mostrar a versão inteira ou um resumo parcial
            if len(summary) > 5000:  # Ajuste o tamanho conforme necessário
                self.update_text_area("Resumo muito grande. Exibindo apenas uma parte.")
                summary = self.df.describe(include="all").head(10).to_string()  # Exibe as primeiras linhas

            # Atualiza a área de texto com o resumo gerado
            self.update_text_area(summary)

        except Exception as e:
            # Exibe erro detalhado caso algo falhe
            self.handle_error(f"Erro ao gerar resumo estatístico: {str(e)}", e)


    def show_duplicates(self):
        """Exibe todos os registros duplicados no DataFrame, se houver."""
        try:
            # Primeiro, tenta encontrar registros duplicados, mantendo todos (keep=False)
            duplicates = self.df[self.df.duplicated(keep=False)]
            
            if not duplicates.empty:
                # Exibe duplicatas encontradas
                self.update_text_area(duplicates.to_string())
            else:
                # Se não encontrar duplicatas, tenta outra abordagem: agrupar por todas as colunas
                duplicates = self.df.groupby(list(self.df.columns)).filter(lambda x: len(x) > 1)
                if not duplicates.empty:
                    self.update_text_area(duplicates.to_string())
                else:
                    # Caso não haja duplicatas em colunas específicas, verifica por contagem de ocorrências
                    counts = self.df.value_counts()
                    duplicates = self.df.loc[counts[counts > 1].index]

                    if not duplicates.empty:
                        self.update_text_area(duplicates.to_string())
                    else:
                        # Nenhum registro duplicado encontrado
                        self.update_text_area("Nenhum registro duplicado encontrado.")
                
        except Exception as e:
            # Exibe erro mais detalhado caso a verificação falhe
            self.handle_error(f"Erro ao verificar duplicatas: {str(e)}", e)


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
        """Exibe os tipos de dados de cada coluna, com validações e tratamento de erros."""
        try:
            # Verifica se o DataFrame não está vazio
            if self.df.empty:
                self.update_text_area("O DataFrame está vazio. Não é possível exibir os tipos de dados.")
                return

            # Verifica se self.df é um DataFrame
            if not isinstance(self.df, pd.DataFrame):
                self.update_text_area("O objeto não é um DataFrame válido.")
                return

            # Obtém os tipos de dados e os formata de forma legível
            data_types = self.df.dtypes.to_string()

            # Verifica o tamanho dos tipos de dados para não sobrecarregar a interface
            if len(data_types) > 5000:  # Ajuste o tamanho conforme necessário
                self.update_text_area("Tipos de dados muito grandes para exibição completa. Exibindo um resumo.")
                data_types = self.df.dtypes.head(10).to_string()  # Exibe as primeiras linhas

            # Atualiza a área de texto com os tipos de dados
            self.update_text_area(data_types)

        except Exception as e:
            # Exibe erro detalhado caso algo falhe
            self.handle_error(f"Erro ao mostrar tipos de dados: {str(e)}", e)


    def show_unique_values(self):
        """Exibe a contagem de valores únicos em cada coluna do DataFrame."""
        try:
            # Verifica se o DataFrame não está vazio
            if self.df.empty:
                self.update_text_area("O DataFrame está vazio. Não é possível exibir valores únicos.")
                return

            # Verifica se self.df é um DataFrame
            if not isinstance(self.df, pd.DataFrame):
                self.update_text_area("O objeto não é um DataFrame válido.")
                return

            # Contabiliza os valores únicos em cada coluna
            unique_counts = self.df.nunique()

            # Verifica se o número de valores únicos é grande demais para exibição
            if len(unique_counts) > 50:  # Ajuste o limite conforme necessário
                self.update_text_area("Muitas colunas para exibir os valores únicos. Exibindo um resumo.")
                unique_counts = unique_counts.head(10)  # Exibe as primeiras 10 colunas, pode ajustar o número

            # Se não houver valores únicos, exibe mensagem apropriada
            if unique_counts.empty:
                self.update_text_area("Não há valores únicos para exibir.")
                return

            # Exibe a contagem de valores únicos
            self.update_text_area(unique_counts.to_string())

        except Exception as e:
            # Exibe erro detalhado caso algo falhe
            self.handle_error(f"Erro ao contabilizar valores únicos: {str(e)}", e)


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
        
        # Solicita ao usuário o caminho para salvar o arquivo
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes)
        
        # Verifica se o caminho do arquivo foi fornecido
        if not file_path:
            messagebox.showwarning("Nenhum arquivo selecionado", "Nenhum arquivo foi selecionado para exportação.")
            return
        
        # Verifica se o DataFrame está vazio
        if self.df.empty:
            messagebox.showwarning("DataFrame Vazio", "O DataFrame está vazio e não pode ser exportado.")
            return

        try:
            # Exporta para CSV ou Excel com base na extensão do arquivo selecionado
            if file_path.endswith(".csv"):
                self.df.to_csv(file_path, index=False)
            elif file_path.endswith(".xlsx"):
                self.df.to_excel(file_path, index=False)
            else:
                raise ValueError("Formato de arquivo não suportado. Apenas .csv e .xlsx são permitidos.")

            # Mensagem de sucesso após a exportação
            messagebox.showinfo("Exportação Concluída", f"Arquivo salvo com sucesso em:\n{file_path}")
        
        except Exception as e:
            # Captura e exibe qualquer erro ocorrido durante o processo de exportação
            error_message = f"Erro ao exportar o arquivo. Detalhes: {str(e)}"
            self.handle_error("Erro ao exportar", error_message)
            messagebox.showerror("Erro na Exportação", error_message)

            
    def handle_error(self, title, error):
        """Gerencia erros de forma centralizada."""
        messagebox.showerror(title, f"Erro: {str(error)}")
        self.update_text_area(f"Ocorreu um erro: {str(error)}")
        self.log_message(f"Erro: {str(error)}", "error")  # Loga a mensagem de erro, se fornecida
