import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from sqlalchemy import inspect
import threading

class AnalysisFrame(ttk.Frame):
    def __init__(self, master, df: pd.DataFrame, engine,table_name,query_executed):
        super().__init__(master)
        self.df = df
        self.table_name = table_name
        self.engine = engine
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        # Título
        header = ttk.Label(self, text="Análise de Tabela", font=("Arial", 14, "bold"))
        header.grid(row=0, column=0, pady=10, padx=10, sticky="w")

        # Área de texto com scroll
        self.text_area = tk.Text(self, wrap="none", height=20)
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.text_area.yview)
        y_scroll.grid(row=1, column=1, sticky="ns")
        self.text_area.configure(yscrollcommand=y_scroll.set)
        # Barra de progresso
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Botões de análise
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        btn_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        ttk.Button(btn_frame, text="Cancelar Análise", command=self.cancel_analysis).grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Button(btn_frame, text="Tipos de Dados", command=self.show_data_types).grid(row=0, column=0, sticky="ew", padx=5)
        ttk.Button(btn_frame, text="Ver Relações", command=self.show_table_relations).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(btn_frame, text="Mal Formados", command=self.show_malformed).grid(row=0, column=2, sticky="ew", padx=5)
        ttk.Button(btn_frame, text="Duplicados", command=self.show_duplicates).grid(row=0, column=3, sticky="ew", padx=5)
        ttk.Button(btn_frame, text="Exportar Excel", command=self.export_to_excel).grid(row=0, column=4, sticky="ew", padx=5)
        ttk.Button(btn_frame, text="Resumo Estatístico", command=self.show_summary).grid(row=0, column=5, sticky="ew", padx=5)
        
    def cancel_analysis(self):
        self._stop_thread = True
        self.progress_bar.stop()
        self.update_text_area("Análise cancelada pelo usuário.")
    
    def show_malformed(self):
        self._stop_thread = False
        self.progress_bar.start()
        threading.Thread(target=self.process_malformed, daemon=True).start()
    
    def show_summary(self):
        try:
            # Gera o resumo estatístico
            summary_df = self.df.describe(include="all")

            # Começa a compor o texto de saída com explicações
            output = [
                "📈 **Resumo Estatístico da Tabela:**\n",
                "Este resumo fornece uma visão geral das colunas, incluindo contagens, valores únicos, médias, desvios padrão e outras estatísticas importantes.\n",
                "Legenda das Métricas:\n",
                "• count — Quantidade de registros não nulos (preenchidos)\n"
                "• unique — Número de valores únicos (somente para colunas categóricas)\n"
                "• top — Valor mais frequente (moda)\n"
                "• freq — Quantidade de vezes que o valor mais frequente aparece\n"
                "• mean — Média (somente para colunas numéricas)\n"
                "• std — Desvio padrão (dispersão dos dados)\n"
                "• min — Valor mínimo\n"
                "• 25% — Primeiro quartil (25% dos dados abaixo desse valor)\n"
                "• 50% — Mediana (metade dos dados abaixo/acima)\n"
                "• 75% — Terceiro quartil (75% dos dados abaixo desse valor)\n"
                "• max — Valor máximo\n\n",
                "📊 Estatísticas por Coluna:\n"
            ]

            output.append(summary_df.to_string())

            self.update_text_area("\n".join(output))
        except Exception as e:
            self.handle_error("Erro ao gerar resumo", e)


    def update_text_area(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see("1.0")

    def show_data_types(self):
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(self.table_name)

            if not columns:
                self.update_text_area("❌ Nenhuma coluna encontrada na tabela.")
                return

            text = "📊 Tipos de Dados:\n\n"
            for col in columns:
                name = col["name"]
                col_type = str(col["type"])
                text += f"• {name}: {col_type}\n"

            self.update_text_area(text)
        except Exception as e:
            self.handle_error("Erro ao verificar tipos de dados", e)

    def show_table_relations(self):
        try:
            inspector = inspect(self.engine)
            foreign_keys = inspector.get_foreign_keys(self.table_name)
            result = []

            if not foreign_keys:
                result.append(f"🔍 A tabela **'{self.table_name}'** não possui relações com outras tabelas.")
            else:
                result.append(f"🔗 **Relações Encontradas da Tabela '{self.table_name}':**\n")
                result.append("Essas são as chaves estrangeiras (foreign keys) que indicam como esta tabela se conecta com outras no banco de dados.\n")
                
                for i, fk in enumerate(foreign_keys, start=1):
                    referred_table = fk['referred_table']
                    local_cols = ", ".join(fk['constrained_columns'])
                    remote_cols = ", ".join(fk['referred_columns'])
                    constraint_name = fk.get('name', 'sem nome')
                    result.append(
                        f"🔸 Relação {i}:\n"
                        f"    • 🔑 Coluna(s) local(is): `{local_cols}`\n"
                        f"    • 🗃️ Referencia a tabela: `{referred_table}`\n"
                        f"    • 📌 Coluna(s) na outra tabela: `{remote_cols}`\n"
                        f"    • 🧩 Nome da restrição (constraint): `{constraint_name}`\n"
                    )

            self.update_text_area("\n".join(result))

        except Exception as e:
            self.handle_error("Erro ao verificar relações da tabela", e)



    # def show_malformed(self):
    #     try:
    #         # Verifica valores nulos
    #         null_summary = self.df.isnull().sum()

    #         # Verifica strings vazias (apenas em colunas do tipo objeto/string)
    #         empty_summary = self.df.select_dtypes(include="object").apply(
    #             lambda c: (c.astype(str).str.strip() == "")
    #         ).sum()

    #         # Monta resumo de colunas com dados malformados
    #         output = ["📉 Resumo de Colunas com Valores Nulos ou Vazios:\n"]
    #         for col in self.df.columns:
    #             total_null = null_summary[col]
    #             total_empty = empty_summary.get(col, 0)
    #             if total_null > 0 or total_empty > 0:
    #                 output.append(f"• {col}: {total_null} nulos, {total_empty} vazios")

    #         # Filtra linhas malformadas
    #         is_null = self.df.isnull().any(axis=1)
    #         is_empty = self.df.select_dtypes(include="object").apply(
    #             lambda c: c.astype(str).str.strip() == ""
    #         ).any(axis=1)
    #         malformed = self.df[is_null | is_empty]

    #         if not malformed.empty:
    #             output.append("\n🧪 Registros Mal Formados:\n")
    #             output.append(malformed.to_string(index=False))

    #             # Pergunta se deseja exportar
    #             save = messagebox.askyesno("Exportar?", "Deseja exportar os registros mal formados para Excel?")
    #             if save:
    #                 file_path = filedialog.asksaveasfilename(
    #                     defaultextension=".xlsx",
    #                     filetypes=[("Excel Files", "*.xlsx")],
    #                     title="Salvar Registros Mal Formados"
    #                 )
    #                 if file_path:
    #                     malformed.to_excel(file_path, index=False)
    #                     messagebox.showinfo("Exportação", f"Arquivo salvo com sucesso:\n{file_path}")
    #         else:
    #             output.append("\n✅ Nenhum registro mal formado encontrado.")

    #         self.update_text_area("\n".join(output))
    #     except Exception as e:
    #         self.handle_error("Erro ao verificar registros mal formados", e)


    def show_duplicates(self):
        try:
            if self.df.empty:
                self.update_text_area("❌ O DataFrame está vazio.")
                return

            duplicated = self.df[self.df.duplicated(keep=False)]

            if duplicated.empty:
                self.update_text_area("✅ Nenhum registro duplicado encontrado.")
                return

            output = [f"⚠️ {len(duplicated)} registros duplicados encontrados:\n"]

            # Mostrar os duplicados agrupados
            grouped = duplicated.groupby(list(self.df.columns)).size().reset_index(name='Ocorrências')
            output.append("📌 Registros Duplicados Agrupados:\n")
            output.append(grouped.to_string(index=False))
            output.append("")

            # Verificar colunas que causam duplicatas
            output.append("🔍 Colunas com maior contribuição para duplicações:\n")
            for col in self.df.columns:
                dup_col = self.df[self.df.duplicated(subset=[col], keep=False)]
                if not dup_col.empty:
                    output.append(f"• {col} → {len(dup_col)} registros duplicados por essa coluna")

            self.update_text_area("\n".join(output))
        except Exception as e:
            self.handle_error("Erro ao verificar duplicatas", e)
    
    def process_malformed(self):
        try:
            # Verifica valores nulos
            null_summary = self.df.isnull().sum()

            # Verifica strings vazias (apenas em colunas do tipo objeto/string)
            empty_summary = self.df.select_dtypes(include="object").apply(
                lambda c: (c.astype(str).str.strip() == "")
            ).sum()

            # Monta resumo de colunas com dados malformados
            output = ["📉 Resumo de Colunas com Valores Nulos ou Vazios:\n"]
            for col in self.df.columns:
                total_null = null_summary[col]
                total_empty = empty_summary.get(col, 0)
                if total_null > 0 or total_empty > 0:
                    output.append(f"• {col}: {total_null} nulos, {total_empty} vazios")

            # Filtra linhas malformadas
            is_null = self.df.isnull().any(axis=1)
            is_empty = self.df.select_dtypes(include="object").apply(
                lambda c: c.astype(str).str.strip() == ""
            ).any(axis=1)
            malformed = self.df[is_null | is_empty]

            if not malformed.empty:
                output.append("\n🧪 Registros Mal Formados:\n")
                output.append(malformed.to_string(index=False))

                # Pergunta se deseja exportar
                save = messagebox.askyesno("Exportar?", "Deseja exportar os registros mal formados para Excel?")
                if save:
                    file_path = filedialog.asksaveasfilename(
                        defaultextension=".xlsx",
                        filetypes=[("Excel Files", "*.xlsx")],
                        title="Salvar Registros Mal Formados"
                    )
                    if file_path:
                        malformed.to_excel(file_path, index=False)
                        messagebox.showinfo("Exportação", f"Arquivo salvo com sucesso:\n{file_path}")
            else:
                output.append("\n✅ Nenhum registro mal formado encontrado.")

            # Atualiza a área de texto com o resumo
            self.update_text_area("\n".join(output))
        except Exception as e:
            self.handle_error("Erro ao verificar registros mal formados", e)
        finally:
            # Para a barra de progresso quando o processo for concluído
            if not self._stop_thread:
                self.progress_bar.stop()

    def handle_error(self, title, error):
        messagebox.showerror(title, str(error))


    def export_to_excel(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=f"{self.table_name}_analise.xlsx",
                filetypes=[("Excel Files", "*.xlsx")]
            )
            if not file_path:
                return
            self.df.to_excel(file_path, index=False)
            messagebox.showinfo("Exportação", f"Arquivo salvo com sucesso:\n{file_path}")
        except Exception as e:
            self.handle_error("Erro ao exportar", e)

    def handle_error(self, title, error):
        messagebox.showerror(title, str(error))
