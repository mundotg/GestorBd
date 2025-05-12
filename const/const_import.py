help_content = {
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