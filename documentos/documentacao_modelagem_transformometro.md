# Documentação de Modelagem e Regras de Cálculo

## 1. Visão geral

O Transformômetro é uma solução em Google Sheets + Apps Script para registrar processos, revisões, medições, investimentos, recursos compartilhados e indicadores financeiros derivados.

A modelagem foi estruturada para:
- manter histórico de versões de processo
- separar dado cadastral de dado derivado
- permitir comparação entre cenário baseline e cenários de transformação
- calcular economia, custo recorrente, ROI e payback ao longo do tempo
- suportar dashboard consolidado e por processo

O sistema é composto por seis tabelas principais de entrada:
- `processos`
- `revisao`
- `medicoes`
- `investimentos`
- `recursos_compartilhados`
- `revisao_recursos_compartilhados`

E por uma tabela técnica derivada:
- `dashboard_calculos`

---

## 2. Princípios de modelagem

### 2.1. Processo é o cadastro mestre
A aba `processos` representa a entidade principal do negócio.

Cada processo possui:
- identificação técnica
- código amigável
- nome
- filial
- setor
- status

### 2.2. Revisão é a unidade central de análise
A análise do sistema é centrada em `revisao_id`.

Isso significa que:
- o processo pode ter múltiplas revisões ao longo do tempo
- cada revisão representa um cenário mensurável
- os cálculos financeiros e operacionais são feitos por revisão
- o dashboard deriva os indicadores comparando revisões

### 2.3. Medição é a fotografia quantitativa da revisão
A aba `medicoes` registra os parâmetros operacionais e de custo utilizados para calcular o custo do processo em determinado cenário.

### 2.4. Investimento é separado de custo operacional
A aba `investimentos` registra custos ligados à implantação ou sustentação da melhoria.

Esses valores não se confundem com o custo operacional do processo.

### 2.5. Recurso compartilhado é custo operacional alocado
A aba `recursos_compartilhados` registra custos recorrentes compartilhados.

A aba `revisao_recursos_compartilhados` define quais revisões usam esses recursos e como o custo deve ser alocado.

### 2.6. Dashboard é derivado, nunca manual
A aba `dashboard_calculos` não é fonte de cadastro.

Ela deve ser sempre reconstruída por script a partir das tabelas de origem.

---

## 3. Estrutura das tabelas

## 3.1. Aba `processos`

### Finalidade
Cadastro mestre dos processos monitorados.

### Colunas
- `processo_id`
- `codigo_processo`
- `nome_processo`
- `descricao_processo`
- `filial_id`
- `setor_id`
- `gestor_responsavel`
- `objetivo_processo`
- `status_processo`
- `created_at`
- `updated_at`
- `deletado`

### Regras
- `processo_id` é a chave primária.
- `codigo_processo` é o identificador amigável.
- `filial_id` e `setor_id` são dimensões analíticas.
- `status_processo` deve respeitar o catálogo oficial.
- `deletado = TRUE` exclui logicamente o registro dos cálculos.

### Campos obrigatórios no formulário
Conforme `apps.js`, são obrigatórios:
- `nome_processo`
- `filial_id`
- `setor_id`
- `status_processo`

### Campos opcionais no formulário
- `descricao_processo`
- `gestor_responsavel`
- `objetivo_processo`

---

## 3.2. Aba `revisao`

### Finalidade
Registrar o histórico de versões do processo.

### Colunas
- `revisao_id`
- `processo_id`
- `versao_revisao`
- `chave_unica_processo_revisao`
- `descricao_revisao`
- `motivo_revisao`
- `cenario_tipo`
- `data_implantacao`
- `data_inicio_vigencia`
- `data_fim_vigencia`
- `revisao_ativa`
- `observacoes`
- `created_at`
- `updated_at`
- `deletado`

### Regras
- `revisao_id` é a chave primária.
- `processo_id` referencia `processos.processo_id`.
- `versao_revisao` deve ser tratada sempre como texto.
- `chave_unica_processo_revisao` representa a unicidade de `processo_id + versao_revisao`.
- `cenario_tipo` define o tipo do cenário da revisão.
- `data_inicio_vigencia` e `data_fim_vigencia` definem a validade da revisão ao longo do tempo.
- `revisao_ativa` indica a revisão vigente para uso operacional no momento.
- `deletado = TRUE` exclui logicamente o registro dos cálculos.

### Regras de negócio
- um processo pode ter várias revisões
- uma revisão não deve sobrescrever a anterior
- o histórico deve ser preservado
- revisões passadas devem ser encerradas por vigência, não apagadas
- ao ativar uma nova revisão, as anteriores do mesmo processo devem ser desativadas

### Campos obrigatórios no formulário
Conforme `apps.js`, são obrigatórios:
- `processo_id`
- `versao_revisao`
- `cenario_tipo`
- `data_inicio_vigencia`
- `revisao_ativa`

### Campos opcionais no formulário
- `descricao_revisao`
- `motivo_revisao`
- `data_implantacao`
- `data_fim_vigencia`
- `observacoes`

---

## 3.3. Aba `medicoes`

### Finalidade
Registrar os parâmetros quantitativos e econômicos usados no cálculo do custo do processo.

### Colunas
- `medicao_id`
- `revisao_id`
- `volume_mensal`
- `tempo_medio_execucao_min`
- `tempo_retrabalho_min`
- `percentual_retrabalho`
- `percentual_erro`
- `quantidade_erros_mes`
- `custo_hora_mao_obra`
- `custo_unitario_erro`
- `custo_unitario_retrabalho`
- `custo_outros_desperdicios`
- `base_referencia_mes`
- `observacoes`
- `deletado`
- `created_at`
- `updated_at`

### Regras
- `medicao_id` é a chave primária.
- `revisao_id` referencia `revisao.revisao_id`.
- os campos numéricos devem ser tratados com parser compatível com vírgula decimal.
- `base_referencia_mes` é um metadado da medição, não a chave de competência da dashboard.
- `deletado = TRUE` exclui logicamente o registro dos cálculos.

### Regras para campos vazios
Campos numéricos vazios devem ser tratados como `0` para cálculo.

Isso vale para:
- `tempo_medio_execucao_min`
- `tempo_retrabalho_min`
- `percentual_retrabalho`
- `percentual_erro`
- `quantidade_erros_mes`
- `custo_hora_mao_obra`
- `custo_unitario_erro`
- `custo_unitario_retrabalho`
- `custo_outros_desperdicios`
- `volume_mensal`

### Campos obrigatórios no formulário
Conforme `apps.js`, são obrigatórios:
- `volume_mensal`
- `tempo_medio_execucao_min`
- `custo_hora_mao_obra`

### Campos opcionais no formulário
- `tempo_retrabalho_min`
- `percentual_retrabalho`
- `percentual_erro`
- `quantidade_erros_mes`
- `custo_unitario_erro`
- `custo_unitario_retrabalho`
- `custo_outros_desperdicios`
- `base_referencia_mes`
- `observacoes`

---

## 3.4. Aba `investimentos`

### Finalidade
Registrar custos ligados à implantação, desenvolvimento ou sustentação da revisão.

### Colunas
- `investimento_id`
- `revisao_id`
- `tipo_investimento`
- `categoria_investimento`
- `descricao_item`
- `quantidade`
- `valor_unitario`
- `valor_total`
- `data_investimento`
- `recorrencia`
- `meses_vigencia`
- `centro_custo`
- `observacoes`
- `deletado`
- `created_at`
- `updated_at`

### Regras
- `investimento_id` é a chave primária.
- `revisao_id` referencia `revisao.revisao_id`.
- `valor_total` é o valor principal de cálculo.
- `quantidade × valor_unitario` pode ser usado como conferência.
- `recorrencia` é o campo principal para definir o comportamento temporal do item.
- `tipo_investimento` é uma classificação gerencial.
- `deletado = TRUE` exclui logicamente o registro dos cálculos.

### Campos obrigatórios no formulário
Conforme `apps.js`, são obrigatórios:
- `tipo_investimento`
- `descricao_item`
- `quantidade`
- `valor_unitario`
- `recorrencia`

### Campos opcionais no formulário
- `categoria_investimento`
- `data_investimento`
- `meses_vigencia`
- `centro_custo`
- `observacoes`

### Regra operacional de gravação
O front envia `quantidade` e `valor_unitario`. O backend deve calcular e persistir `valor_total` de forma consistente.

---

## 3.5. Aba `recursos_compartilhados`

### Finalidade
Cadastrar recursos recorrentes compartilhados entre revisões.

### Colunas
- `recurso_compartilhado_id`
- `codigo_recurso`
- `nome_recurso`
- `categoria_recurso`
- `fornecedor`
- `tipo_custo`
- `recorrencia`
- `valor_total_recorrente`
- `data_inicio_vigencia`
- `data_fim_vigencia`
- `centro_custo`
- `criterio_rateio`
- `status_recurso`
- `observacoes`
- `deletado`
- `created_at`
- `updated_at`

### Regras
- `recurso_compartilhado_id` é a chave primária.
- `valor_total_recorrente` representa o custo total do recurso no período de recorrência.
- o recurso não entra sozinho no dashboard; ele precisa estar vinculado a uma revisão.
- `criterio_rateio` define como o custo será alocado entre as revisões elegíveis.
- `status_recurso = ativo` habilita o uso do recurso.
- `deletado = TRUE` exclui logicamente o registro dos cálculos.

### Campos obrigatórios no formulário
Conforme `apps.js`, são obrigatórios:
- `nome_recurso`
- `tipo_custo`
- `recorrencia`
- `valor_total_recorrente`
- `criterio_rateio`
- `status_recurso`

### Campos opcionais no formulário
- `categoria_recurso`
- `fornecedor`
- `data_inicio_vigencia`
- `data_fim_vigencia`
- `centro_custo`
- `observacoes`

---

## 3.6. Aba `revisao_recursos_compartilhados`

### Finalidade
Vincular recursos compartilhados às revisões.

### Colunas
- `vinculo_id`
- `revisao_id`
- `recurso_compartilhado_id`
- `data_inicio_uso`
- `data_fim_uso`
- `ativo`
- `peso_rateio`
- `observacoes`
- `deletado`
- `created_at`
- `updated_at`

### Regras
- `vinculo_id` é a chave primária.
- `revisao_id` referencia `revisao.revisao_id`.
- `recurso_compartilhado_id` referencia `recursos_compartilhados.recurso_compartilhado_id`.
- `ativo = TRUE` habilita o vínculo para cálculo.
- `peso_rateio` é usado quando o critério do recurso for `por_peso`.
- `deletado = TRUE` exclui logicamente o vínculo dos cálculos.

### Campos obrigatórios no formulário
Conforme `apps.js`, são obrigatórios:
- `revisao_id`
- `recurso_compartilhado_id`
- `ativo`

### Campos opcionais no formulário
- `data_inicio_uso`
- `data_fim_uso`
- `peso_rateio`
- `observacoes`

---

## 4. Catálogos oficiais do sistema

Os domínios controlados devem seguir os valores definidos em `options.gs`.

## 4.1. Filiais
- `01` = Matriz
- `02` = Filial

## 4.2. Setores
- `engenharia`
- `qualidade`
- `pcp`
- `producao`
- `comercial`
- `compras`
- `almoxarifado`

## 4.3. Status do processo
- `ativo`
- `descontinuado`
- `em_implantacao`

## 4.4. Tipos de cenário da revisão
- `baseline`
- `melhoria`
- `automacao`
- `correcao`

## 4.5. Booleanos exibidos em opções
- `TRUE`
- `FALSE`

## 4.6. Tipos de investimento
- `fixo`
- `variavel`
- `recorrente`
- `unico`

## 4.7. Categorias de investimento e recurso
- `software`
- `treinamento`
- `consultoria`
- `equipamento`
- `horas_internas`
- `terceiros`

## 4.8. Recorrências
- `unico`
- `mensal`
- `anual`

## 4.9. Critérios de rateio
- `igualitario`
- `por_revisoes_ativas`
- `por_peso`

## 4.10. Status do recurso
- `ativo`
- `inativo`

---

## 5. Regras gerais de leitura e integridade

### 5.1. Exclusão lógica
Registros com `deletado = TRUE` não devem participar de:
- seleções do formulário
- cálculos da dashboard
- comparações entre cenários
- rateios de recursos

### 5.2. Versão de revisão
`versao_revisao` deve ser tratada como texto visível da célula para evitar conversão incorreta pelo Google Sheets.

### 5.3. Datas
Campos de data devem ser interpretados com parser seguro. Em caso de vazio:
- datas estruturais podem ficar em branco
- regras de vigência devem usar fallback consistente

### 5.4. Revisão como centro de cálculo
Todos os cálculos derivados devem apontar para `revisao_id`.

### 5.5. Comportamento do formulário
O front-end destaca campos obrigatórios via `validateRequiredFields`.

Essa obrigatoriedade deve ser considerada regra funcional oficial do sistema.

---

## 6. Conceito da aba técnica `dashboard_calculos`

### Finalidade
Consolidar mensalmente os custos, economias e indicadores por revisão.

### Natureza
Tabela derivada, gerada por script.

### Unidade de linha
Uma linha por:
- revisão
- competência mensal

### Chave lógica sugerida
`dashboard_calculo_id = revisao_id + '::' + competencia`

Exemplo:
- `b2a88c7c-...::2025-09`

---

## 7. Regras de geração da timeline

### 7.1. Início da timeline
A timeline mensal deve começar na menor data relevante encontrada entre:
- `revisao.data_inicio_vigencia`
- `revisao.data_implantacao`
- `processos.created_at`

### 7.2. Fim da timeline
A timeline deve ir até o mês atual.

### 7.3. Competência
A competência mensal deve ser representada em formato `yyyy-MM`.

Exemplo:
- `2025-01`
- `2025-09`
- `2026-03`

---

## 8. Regras de vigência da revisão

Uma revisão entra no cálculo de um mês quando:
- `competencia >= data_inicio_vigencia`
- e, se existir `data_fim_vigencia`, `competencia <= data_fim_vigencia`

Se `data_fim_vigencia` estiver vazia:
- a revisão permanece válida até o mês atual

---

## 9. Regras de comparação entre cenários

## 9.1. Cenário baseline
A revisão com `cenario_tipo = baseline` é a referência de comparação do processo.

### Comportamento recomendado
- pode gerar linha técnica no dashboard
- mas não gera economia comparativa
- `custo_baseline = custo_atual`
- `economia_bruta = 0`

## 9.2. Cenários comparáveis
Geram comparação contra baseline:
- `melhoria`
- `automacao`
- `correcao`

## 9.3. Seleção da baseline de comparação
Para cada revisão comparável, a baseline do processo deve ser selecionada nesta ordem:
1. revisão do mesmo processo com `cenario_tipo = baseline`
2. se não houver, a menor `versao_revisao` do processo

---

## 10. Regras de cálculo de custo operacional

## 10.1. Custo de tempo
Formula:

`custo_tempo = volume_mensal × (tempo_medio_execucao_min / 60) × custo_hora_mao_obra`

## 10.2. Custo de retrabalho
### Regra preferencial
Se houver `custo_unitario_retrabalho` maior que zero:

`custo_retrabalho = volume_mensal × percentual_retrabalho × custo_unitario_retrabalho`

### Regra fallback
Caso contrário:

`custo_retrabalho = volume_mensal × percentual_retrabalho × (tempo_retrabalho_min / 60) × custo_hora_mao_obra`

## 10.3. Custo de erro
Se houver `custo_unitario_erro`:

`custo_erro = quantidade_erros_mes × custo_unitario_erro`

Caso contrário:

`custo_erro = 0`

## 10.4. Custo de outros desperdícios

`custo_outros = custo_outros_desperdicios`

## 10.5. Custo de recursos compartilhados
Esse custo é calculado a partir do cadastro do recurso e dos vínculos elegíveis da revisão no mês.

## 10.6. Custo operacional total da revisão

`custo_operacional = custo_tempo + custo_retrabalho + custo_erro + custo_outros + custo_recursos_compartilhados`

---

## 11. Regras de elegibilidade de recursos compartilhados

## 11.1. Elegibilidade do recurso
Um recurso pode participar do cálculo se:
- `deletado != TRUE`
- `status_recurso = ativo`
- a competência estiver dentro da vigência do recurso, quando houver `data_inicio_vigencia` e `data_fim_vigencia`

## 11.2. Elegibilidade do vínculo
Um vínculo pode participar do cálculo se:
- `deletado != TRUE`
- `ativo = TRUE`
- a competência estiver dentro de `data_inicio_uso` e `data_fim_uso`, quando houver

---

## 12. Regras de rateio de recursos compartilhados

O recurso compartilhado tem um custo total recorrente em `valor_total_recorrente`.

Esse custo deve ser alocado às revisões elegíveis conforme o `criterio_rateio` do recurso.

## 12.1. Critério `igualitario`
Divide o custo igualmente entre os vínculos elegíveis do recurso no mês.

Formula:

`custo_alocado = valor_total_recorrente / quantidade_de_vinculos_elegiveis`

## 12.2. Critério `por_revisoes_ativas`
Divide o custo entre as revisões elegíveis do recurso no mês.

Na prática, o conjunto elegível deve considerar:
- revisão válida no mês
- vínculo válido no mês
- recurso válido no mês

Formula:

`custo_alocado = valor_total_recorrente / quantidade_de_revisoes_elegiveis_no_mes`

## 12.3. Critério `por_peso`
Distribui o custo proporcionalmente ao `peso_rateio`.

Formula:

`custo_alocado = valor_total_recorrente × (peso_rateio / soma_dos_pesos_elegiveis)`

### Regra para peso vazio
Se `criterio_rateio = por_peso` e `peso_rateio` estiver vazio:
- tratar como `1`

### Regra para vínculo sem peso em outros critérios
Se o critério não for `por_peso`, `peso_rateio` pode ser ignorado.

---

## 13. Regras de cálculo de economia

As economias devem ser calculadas comparando o cenário baseline com o cenário atual da revisão comparável.

## 13.1. Economia de tempo

`economia_tempo = max(custo_tempo_baseline - custo_tempo_atual, 0)`

## 13.2. Economia de retrabalho

`economia_retrabalho = max(custo_retrabalho_baseline - custo_retrabalho_atual, 0)`

## 13.3. Economia de erros

`economia_erros = max(custo_erro_baseline - custo_erro_atual, 0)`

## 13.4. Economia de outros desperdícios

`economia_outros = max(custo_outros_baseline - custo_outros_atual, 0)`

## 13.5. Economia de recursos compartilhados

`economia_recursos_compartilhados = max(custo_recursos_compartilhados_baseline - custo_recursos_compartilhados_atual, 0)`

## 13.6. Economia bruta

`economia_bruta = economia_tempo + economia_retrabalho + economia_erros + economia_outros + economia_recursos_compartilhados`

---

## 14. Regras de cálculo financeiro dos investimentos

## 14.1. Princípio
Para cálculo temporal do dashboard, o campo que define o comportamento mensal do investimento é `recorrencia`.

`tipo_investimento` é mantido como classificação analítica.

## 14.2. Investimento único do mês
Entram itens em que:
- `deletado != TRUE`
- `recorrencia = unico`
- `data_investimento` pertence ao mês da competência

Formula:

`investimento_unico_mes = soma(valor_total)`

## 14.3. Custo recorrente mensal
Entram itens em que:
- `deletado != TRUE`
- `recorrencia = mensal` ou `recorrencia = anual`
- a competência está dentro da vigência financeira do item

### Regra mensal
Se `recorrencia = mensal`:

`custo_recorrente_mes += valor_total`

### Regra anual
Se `recorrencia = anual`:

`custo_recorrente_mes += valor_total / 12`

## 14.4. Vigência financeira do investimento
Se houver `meses_vigencia`, o item deve ser considerado a partir de `data_investimento` por esse número de meses.

Se não houver `meses_vigencia`:
- `mensal` permanece recorrente até o mês atual ou até regra futura de encerramento
- `anual` é mensalizado até o mês atual ou até regra futura de encerramento

---

## 15. Indicadores finais do dashboard

## 15.1. Economia líquida do mês

`economia_liquida_mes = economia_bruta - custo_recorrente_mes`

## 15.2. Acumulados

`investimento_unico_acumulado = soma histórica do investimento_unico_mes`

`custo_recorrente_acumulado = soma histórica do custo_recorrente_mes`

`economia_liquida_acumulada = soma histórica da economia_liquida_mes`

## 15.3. ROI
Formula recomendada:

`roi = (economia_liquida_acumulada - investimento_unico_acumulado) / investimento_unico_acumulado`

`roi_percentual = roi`

A formatação percentual deve ser aplicada na exibição.

## 15.4. Payback
O payback é atingido no primeiro mês em que:

`economia_liquida_acumulada >= investimento_unico_acumulado`

Campos derivados:
- `payback_atingido`
- `payback_meses`

---

## 16. Estrutura recomendada da aba `dashboard_calculos`

Colunas sugeridas:
- `dashboard_calculo_id`
- `competencia`
- `competencia_data`
- `processo_id`
- `codigo_processo`
- `nome_processo`
- `filial_id`
- `setor_id`
- `status_processo`
- `revisao_id`
- `versao_revisao`
- `cenario_tipo`
- `revisao_ativa`
- `baseline_revisao_id`
- `baseline_versao_revisao`
- `data_inicio_vigencia`
- `data_fim_vigencia`
- `volume_mensal`
- `tempo_medio_execucao_min_baseline`
- `tempo_medio_execucao_min_atual`
- `tempo_retrabalho_min_baseline`
- `tempo_retrabalho_min_atual`
- `percentual_retrabalho_baseline`
- `percentual_retrabalho_atual`
- `percentual_erro_baseline`
- `percentual_erro_atual`
- `quantidade_erros_mes_baseline`
- `quantidade_erros_mes_atual`
- `custo_hora_mao_obra_baseline`
- `custo_hora_mao_obra_atual`
- `custo_unitario_erro_baseline`
- `custo_unitario_erro_atual`
- `custo_unitario_retrabalho_baseline`
- `custo_unitario_retrabalho_atual`
- `custo_outros_desperdicios_baseline`
- `custo_outros_desperdicios_atual`
- `custo_tempo_baseline`
- `custo_tempo_atual`
- `custo_retrabalho_baseline`
- `custo_retrabalho_atual`
- `custo_erro_baseline`
- `custo_erro_atual`
- `custo_outros_baseline`
- `custo_outros_atual`
- `custo_recursos_compartilhados_baseline`
- `custo_recursos_compartilhados_atual`
- `custo_baseline`
- `custo_atual`
- `economia_tempo`
- `economia_retrabalho`
- `economia_erros`
- `economia_outros`
- `economia_recursos_compartilhados`
- `economia_bruta`
- `investimento_unico_mes`
- `investimento_unico_acumulado`
- `custo_recorrente_mes`
- `custo_recorrente_acumulado`
- `economia_liquida_mes`
- `economia_liquida_acumulada`
- `roi_percentual`
- `payback_meses`
- `payback_atingido`
- `created_at`
- `updated_at`

---

## 17. Diretrizes de implementação

### 17.1. Helpers reutilizáveis
A implementação deve reaproveitar funções utilitárias já existentes, como:
- `getSheetOrThrow_`
- `getHeaders_`
- `normalizeText_`
- `normalizeCellText_`
- `parseNumber_`
- `parseDateOrBlank_`
- `toBoolean_`
- `isTruthyDeleted_`

### 17.2. Leitura de versão
Para campos como `versao_revisao`, a leitura deve preferir o texto exibido para evitar bug de interpretação do Sheets.

### 17.3. Fonte da verdade das opções
Os catálogos definidos em `options.gs` são a fonte oficial dos valores aceitos em selects, filtros e validações.

### 17.4. Fonte da verdade dos obrigatórios
As regras de obrigatoriedade definidas em `apps.js` são a fonte oficial dos campos mínimos exigidos em cada formulário.

---

## 18. Próximos artefatos derivados

A partir desta documentação, os próximos componentes a serem implementados ou ajustados são:
- `DashboardCalculos.gs` para reconstrução da aba técnica
- camada de serviço para retorno do dashboard ao front-end
- nova aba visual de Dashboard na interface HTML
- gráficos de evolução mensal de investimento e economia
- filtros por processo, filial, setor e período
