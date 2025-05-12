import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import numpy as np

class AdvancedDataAnalyzerFrame(ttk.Frame):
    def __init__(self, master, df: pd.DataFrame, log_message: Any = None):
        super().__init__(master)
        self.df = df
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.log_message = log_message
        self._create_widgets()

    def _create_widgets(self):
        header = ttk.Label(self, text="Análise Avançada de Dados", font=("Arial", 16, "bold"))
        header.grid(row=0, column=0, pady=10, padx=10, sticky="w")

        self.text_area = tk.Text(self, wrap="word", height=20)
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Button(button_frame, text="Detectar Outliers", command=self.detect_outliers).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Correlação", command=self.plot_correlation).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Recomendações de Limpeza", command=self.cleaning_recommendations).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Visualizar Gráficos", command=self.plot_distributions).grid(row=0, column=3, padx=5)

    def update_text_area(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.config(state=tk.DISABLED)

    def _handle_error(self, error_message: str, context: str):
        messagebox.showerror("Erro", f"{context}:\n{error_message}")
        if self.log_message:
            self.log_message(f"[Erro - {context}] {error_message}",level="error")

    def detect_outliers(self):
        try:
            outlier_report = []
            for col in self.df.select_dtypes(include=np.number).columns:
                q1 = self.df[col].quantile(0.25)
                q3 = self.df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = self.df[(self.df[col] < lower) | (self.df[col] > upper)]
                if not outliers.empty:
                    outlier_report.append(f"🔍 Coluna '{col}' possui {len(outliers)} outliers.")
            self.update_text_area("\n".join(outlier_report) if outlier_report else "✅ Nenhum outlier encontrado.")
        except Exception as e:
            self._handle_error(str(e), "Detecção de Outliers")

    def plot_correlation(self):
        try:
            # Filtra as colunas numéricas
            numeric_df = self.df.select_dtypes(include=np.number)

            # Verifica se há colunas numéricas disponíveis para análise
            if numeric_df.empty:
                self.update_text_area("❌ Não foi possível calcular a correlação. Não há colunas numéricas no conjunto de dados.")
                return

            # Calcula a matriz de correlação entre as colunas numéricas
            corr = numeric_df.corr()

            # Gera o gráfico de mapa de calor (heatmap) para a matriz de correlação
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)

            # Exibe o gráfico na interface gráfica
            self._show_plot(fig, "Matriz de Correlação")

        except Exception as e:
            # Caso ocorra um erro, exibe uma mensagem explicativa e detalha o erro
            error_message = f"Ocorreu um erro ao tentar plotar a matriz de correlação: {str(e)}"
            self._handle_error(error_message, "Plotagem de Correlação")


    def cleaning_recommendations(self):
        try:
            issues = []
            
            # Verifica cada coluna do DataFrame
            for col in self.df.columns:
                # Verifica se há valores nulos na coluna
                nulls = self.df[col].isnull().sum()
                if nulls > 0:
                    issues.append(f"⚠️ {col}: Encontrados {nulls} valores nulos.")
                
                # Se a coluna for do tipo texto, verifica campos vazios
                if self.df[col].dtype == "object":
                    empty = (self.df[col].astype(str).str.strip() == "").sum()
                    if empty > 0:
                        issues.append(f"⚠️ {col}: Encontrados {empty} campos vazios ou contendo apenas espaços em branco.")
            
            # Exibe as recomendações de limpeza ou uma mensagem de sucesso
            if issues:
                self.update_text_area("\n".join(issues))  # Exibe todos os problemas encontrados
            else:
                self.update_text_area("✅ Nenhum problema evidente encontrado. As colunas estão limpas e sem erros.")

        except Exception as e:
            # Caso haja um erro, exibe uma mensagem explicativa e sugere possíveis causas
            error_message = f"❌ Ocorreu um erro ao gerar as recomendações de limpeza: {str(e)}. " \
                            "Verifique se o DataFrame contém dados válidos e se o tipo de dados das colunas está correto."
            self._handle_error(error_message, "Recomendações de Limpeza")


    def plot_distributions(self):
        try:
            # Seleciona as colunas numéricas
            numeric_cols = self.df.select_dtypes(include=np.number).columns
            
            # Verifica se existem colunas numéricas para visualização
            if numeric_cols.empty:
                self.update_text_area("❌ Nenhuma coluna numérica encontrada para a visualização das distribuições. Verifique se os dados são adequados para análise.")
                return

            # Cria os subgráficos para cada coluna numérica
            fig, axs = plt.subplots(nrows=len(numeric_cols), ncols=1, figsize=(6, 4 * len(numeric_cols)))
            
            # Garante que axs seja sempre uma lista, mesmo para uma única coluna
            if len(numeric_cols) == 1:
                axs = [axs]

            # Plota a distribuição para cada coluna numérica
            for i, col in enumerate(numeric_cols):
                sns.histplot(self.df[col], kde=True, ax=axs[i])
                axs[i].set_title(f"Distribuição de {col}")

            # Exibe o gráfico
            self._show_plot(fig, "Distribuições Numéricas")

        except Exception as e:
            # Exibe mensagem de erro caso ocorra alguma exceção
            error_message = f"❌ Ocorreu um erro ao gerar as distribuições: {str(e)}. " \
                            "Verifique se os dados estão corretamente formatados e se as colunas numéricas são adequadas para a visualização."
            self._handle_error(error_message, "Plotagem de Distribuições")


    def _show_plot(self, fig, title):
        try:
            # Cria uma nova janela (top-level) para exibir o gráfico
            win = tk.Toplevel(self)
            win.title(title)  # Define o título da janela

            # Cria um frame para o canvas
            canvas_frame = ttk.Frame(win)
            canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Cria o canvas do gráfico usando o Matplotlib
            canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            canvas.draw()  # Desenha o gráfico no canvas

            # Cria a barra de rolagem e a associa ao canvas
            scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.get_tk_widget().yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Configura o canvas para usar a barra de rolagem
            canvas.get_tk_widget().config(yscrollcommand=scrollbar.set)

            # Adiciona o canvas na janela e faz o gráfico ocupar todo o espaço disponível
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Botão para fechar a janela
            close_button = ttk.Button(win, text="Fechar", command=win.destroy)
            close_button.pack(side=tk.BOTTOM, pady=10)

            # Ajusta o tamanho da janela para o tamanho do gráfico
            win.geometry(f"{fig.get_figwidth() * 100:.0f}x{fig.get_figheight() * 100:.0f}")

        except Exception as e:
            # Caso ocorra um erro, exibe uma mensagem explicativa detalhada
            error_message = f"❌ Ocorreu um erro ao tentar exibir o gráfico '{title}': {str(e)}. " \
                            "Verifique se os dados passados para o gráfico estão corretos e tente novamente."
            self._handle_error(error_message, "Mostrar Gráfico")
