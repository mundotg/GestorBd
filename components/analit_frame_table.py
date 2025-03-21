import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

class AnalysisFrame(ttk.Frame):
    """Frame para análise detalhada da tabela."""

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master)
        self.df = df
        self._create_widgets()

    def _create_widgets(self):
        """Cria os botões e widgets de análise."""

        label = ttk.Label(self, text="Análise Detalhada da Tabela", font=("Arial", 12, "bold"))
        label.pack(pady=5)

        self.text_area = tk.Text(self, height=15, width=80, wrap="none")
        self.text_area.pack(padx=5, pady=5)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        buttons = [
            ("Resumo Estatístico", self.show_summary),
            ("Ver Duplicatas", self.show_duplicates),
            ("Registros Mal Formados", self.show_malformed_records),
            ("Tipos de Dados", self.show_data_types),
            ("Valores Únicos", self.show_unique_values),
            ("Contagem por Categoria", self.show_category_counts),
            ("Exportar Análise", self.export_analysis)
        ]

        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def update_text_area(self, text):
        """Atualiza a área de texto com os resultados da análise."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.config(state=tk.DISABLED)

    def show_summary(self):
        """Exibe um resumo estatístico dos dados."""
        summary = self.df.describe(include="all").to_string()
        self.update_text_area(summary)

    def show_duplicates(self):
        """Exibe registros duplicados."""
        duplicates = self.df[self.df.duplicated(keep=False)]
        self.update_text_area(duplicates.to_string() if not duplicates.empty else "Nenhum registro duplicado encontrado.")

    def show_malformed_records(self):
        """Exibe registros com valores nulos ou mal formados."""
        is_null = self.df.isnull().any(axis=1)
        is_empty_string = self.df.select_dtypes(include=["object"]).apply(lambda col: col.astype(str).str.strip() == "").any(axis=1)
        malformed = self.df[is_null | is_empty_string]
        self.update_text_area(malformed.to_string() if not malformed.empty else "Nenhum registro mal formado encontrado.")

    def show_data_types(self):
        """Exibe os tipos de dados de cada coluna."""
        self.update_text_area(self.df.dtypes.to_string())

    def show_unique_values(self):
        """Exibe a contagem de valores únicos em cada coluna."""
        self.update_text_area(self.df.nunique().to_string())

    def show_category_counts(self):
        """Exibe a contagem de valores únicos para colunas categóricas."""
        categorical_cols = self.df.select_dtypes(include=["object", "category"])
        if categorical_cols.empty:
            self.update_text_area("Nenhuma coluna categórica encontrada.")
        else:
            formatted_counts = "\n\n".join([f"{col}:\n{self.df[col].value_counts().to_string()}" for col in categorical_cols])
            self.update_text_area(formatted_counts)

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
            messagebox.showerror("Erro ao Exportar", f"Erro: {str(e)}")
