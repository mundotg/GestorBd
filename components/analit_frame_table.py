import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from sqlalchemy import inspect
import threading
from components.AdvancedDataAnalyzerFrame import AdvancedDataAnalyzerFrame
from const.const_import import output

class AnalysisFrame(ttk.Frame):
    def __init__(self, master, df: pd.DataFrame, engine,table_name,query_executed,log_message=None):
        super().__init__(master)
        self.df = df
        self.table_name = table_name
        self.engine = engine
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.log_message = log_message
        self.query_executed = query_executed
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
        ttk.Button(btn_frame, text="Valores Únicos", command=self.show_unique_values).grid(row=0, column=6, sticky="ew", padx=5)
        ttk.Button(btn_frame, text="modo avançado", command=self.modo_advancado).grid(row=0, column=7, sticky="ew", padx=5)
    def modo_advancado(self):
        root = tk.Tk()
        root.title("Analisador de Dados Avançado")
        root.geometry("800x600")
        # Criando e adicionando o frame à janela
        analyzer = AdvancedDataAnalyzerFrame(root, self.df,self.log_message)
        analyzer.pack(fill="both", expand=True)

        # Iniciando o loop da interface
        root.mainloop()
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
        """Exibe os tipos de dados e metainformações das colunas da(s) tabela(s)."""
        try:
            inspector = inspect(self.engine)
            # Garante que sempre estamos lidando com uma lista
            table_names = self.table_name if isinstance(self.table_name, list) else [self.table_name]

            all_lines = []

            for table in table_names:
                columns = inspector.get_columns(table)

                if not columns:
                    all_lines.append(f"❌ Nenhuma coluna encontrada na tabela {table}.")
                    continue

                self.column_types = {}
                self.primary_key_column = None

                linhas = [f"📊 Estrutura da Tabela: {table}\n"]

                for col in columns:
                    name = col.get("name", "—")
                    raw_type = col.get("type", "—")
                    col_type = str(raw_type)
                    nullable = "Sim" if col.get("nullable", True) else "Não"
                    default = col.get("default", "—")
                    is_primary = col.get("primary_key", False)
                    autoincrement = "Sim" if col.get("autoincrement", False) else "Não"
                    comment = col.get("comment", None)

                    length = getattr(raw_type, "length", None)
                    precision = getattr(raw_type, "precision", None)
                    scale = getattr(raw_type, "scale", None)

                    if length:
                        col_type += f"({length})"
                    elif precision is not None and scale is not None:
                        col_type += f"({precision},{scale})"

                    self.column_types[name] = col_type

                    if is_primary:
                        self.primary_key_column = name

                    linhas.append(
                        f"{'🔑' if is_primary else '•'} {name}: {col_type}\n"
                        f"    ├─ Pode ser nulo: {nullable}\n"
                        f"    ├─ Valor padrão: {default}\n"
                        f"    ├─ Autoincremento: {autoincrement}"
                        + (f"\n    └─ Comentário: {comment}" if comment else "\n")
                    )

                all_lines.extend(linhas)

            self.update_text_area("\n".join(all_lines))

        except Exception as e:
            self.handle_error("Erro ao verificar tipos de dados", e)


    def show_table_relations(self):
        try:
            if not isinstance(self.table_name, str) or any(kw in self.table_name.upper() for kw in ["SELECT", "JOIN", "FROM", "WHERE"]):
                self.update_text_area("⚠️ Relações não podem ser extraídas de consultas compostas. Forneça o nome de uma tabela real.")
                return

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

    def show_duplicates(self):
        """Exibe registros duplicados com análise detalhada e permite exportação."""
        try:
            if self.df.empty:
                self.update_text_area("❌ O DataFrame está vazio.")
                return

            # Identifica todos os registros duplicados (inclusive originais)
            duplicated = self.df[self.df.duplicated(keep=False)]

            if duplicated.empty:
                self.update_text_area("✅ Nenhum registro duplicado encontrado.")
                return

            output = []
            total_dups = len(duplicated)
            output.append(f"⚠️ {total_dups} registros duplicados encontrados (incluindo entradas originais):\n")

            # Agrupamento por todas as colunas
            grouped = duplicated.groupby(list(self.df.columns)).size().reset_index(name='Ocorrências')
            output.append("📌 Registros Duplicados Agrupados:\n")
            output.append(grouped.to_string(index=False))
            output.append("")

            # Colunas que mais causam duplicação
            output.append("🔍 Colunas com maior impacto nas duplicações:\n")
            contribs = []
            for col in self.df.columns:
                dup_col = self.df[self.df.duplicated(subset=[col], keep=False)]
                if not dup_col.empty:
                    contribs.append((col, len(dup_col)))

            contribs = sorted(contribs, key=lambda x: x[1], reverse=True)
            for col, count in contribs:
                output.append(f"• {col}: {count} registros duplicados com base apenas nesta coluna")

            self.update_text_area("\n".join(output))

            # Exportação opcional
            salvar = messagebox.askyesno("Exportar Duplicatas", "Deseja exportar os registros duplicados encontrados?")
            if salvar:
                filetypes = [("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")]
                file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes)
                if file_path:
                    if file_path.endswith(".csv"):
                        duplicated.to_csv(file_path, index=False)
                    else:
                        duplicated.to_excel(file_path, index=False)
                    messagebox.showinfo("Exportação Concluída", f"Registros duplicados exportados para:\n{file_path}")

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
        self.log_message(f" {error}",level="error")

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

