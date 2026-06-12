# Especificação da Aplicação Transformômetro

> **Nota (jun/2026):** este documento descreve a especificação funcional original (planilha + Apps Script). A implementação entregue no monorepo usa **Postgres + transformometro-api + plugin MFE** como fonte de verdade. Para estado atual, pipeline e legado remanescente, ver [status-atual.md](./status-atual.md) e [README.md](./README.md).

## 1. Visão geral

O **Transformômetro** é uma ferramenta para registrar, acompanhar e mensurar melhorias de processos.

A aplicação permite cadastrar processos internos, registrar diferentes revisões ou versões desses processos, medir dados operacionais, lançar investimentos, associar recursos compartilhados e calcular indicadores financeiros como:

- custo operacional;
- economia bruta;
- economia líquida;
- custo recorrente;
- investimento acumulado;
- ROI;
- payback;
- evolução mensal dos resultados.

Atualmente a ferramenta existe em **Google Sheets + Apps Script**, usando abas como tabelas. A nova aplicação deve migrar essa lógica para uma arquitetura com:

- front-end web;
- API backend;
- banco de dados relacional;
- camada de cálculo;
- dashboard visual;
- autenticação de usuários;
- controle de permissões;
- histórico de alterações.

O sistema atual foi modelado para manter histórico de versões de processo, separar dados cadastrais de dados calculados, comparar cenários baseline contra melhorias e consolidar indicadores em dashboard.

---

## 2. Objetivo principal da ferramenta

A ferramenta deve responder à seguinte pergunta:

> “Quanto uma melhoria de processo economizou, quanto custou para implantar ou manter, e em quanto tempo o investimento se paga?”

Para isso, cada processo possui revisões. Uma revisão pode representar o cenário original, chamado de **baseline**, ou um cenário transformado, como melhoria, automação ou correção.

Os cálculos financeiros e operacionais não devem ser feitos diretamente sobre o processo, mas sobre a **revisão**. A unidade central de análise é `revisao_id`.

---

## 3. Entidades principais do sistema

### 3.1. Processo

Representa o cadastro mestre de um processo monitorado.

#### Campos

```txt
processo_id
codigo_processo
nome_processo
descricao_processo
filial_id
setor_id
gestor_responsavel
objetivo_processo
status_processo
data_criacao
data_atualizacao
deletado
```

#### Regras

- `processo_id` é a chave primária.
- `codigo_processo` é o identificador amigável exibido ao usuário.
- `filial_id` e `setor_id` são dimensões analíticas para filtros.
- `status_processo` deve seguir catálogo oficial.
- `deletado = true` representa exclusão lógica.
- Processos deletados não entram em listas, cálculos ou dashboards.

#### Campos obrigatórios no formulário

```txt
nome_processo
filial_id
setor_id
status_processo
```

---

### 3.2. Revisão

Representa uma versão, cenário ou etapa evolutiva de um processo.

Um processo pode ter várias revisões. Uma revisão nunca deve sobrescrever a anterior. O histórico deve ser preservado.

#### Campos

```txt
revisao_id
processo_id
versao_revisao
chave_unica_processo_revisao
descricao_revisao
motivo_revisao
cenario_tipo
data_implantacao
data_inicio_vigencia
data_fim_vigencia
revisao_ativa
observacoes
created_at
updated_at
deletado
```

#### Regras

- `revisao_id` é a chave primária.
- `processo_id` referencia `processos.processo_id`.
- `versao_revisao` deve ser sempre texto.
- A versão não pode ser tratada como número, para evitar erros como `1.1.0` virar data ou número.
- `chave_unica_processo_revisao` deve representar a combinação única de `processo_id + versao_revisao`.
- `cenario_tipo` define se a revisão é `baseline`, `melhoria`, `automacao` ou `correcao`.
- `data_inicio_vigencia` e `data_fim_vigencia` definem o período válido da revisão.
- Ao ativar uma nova revisão de um processo, as anteriores devem ser desativadas.
- Revisões antigas não devem ser apagadas; devem ser encerradas por vigência.
- `deletado = true` exclui logicamente a revisão.

#### Campos obrigatórios

```txt
processo_id
versao_revisao
cenario_tipo
data_inicio_vigencia
revisao_ativa
```

---

### 3.3. Medição

Representa a fotografia quantitativa de uma revisão.

A medição guarda os dados usados para calcular o custo operacional da revisão.

#### Campos

```txt
medicao_id
revisao_id
volume_mensal
tempo_medio_execucao_min
tempo_retrabalho_min
percentual_retrabalho
percentual_erro
quantidade_erros_mes
custo_hora_mao_obra
custo_unitario_erro
custo_unitario_retrabalho
custo_outros_desperdicios
base_referencia_mes
observacoes
deletado
```

#### Regras

- `medicao_id` é a chave primária.
- `revisao_id` referencia `revisao.revisao_id`.
- Campos numéricos vazios devem ser tratados como `0` nos cálculos.
- O parser numérico deve aceitar vírgula decimal.
- `base_referencia_mes` é apenas metadado da medição.
- A competência do dashboard é calculada pela timeline mensal, não por `base_referencia_mes`.

#### Campos obrigatórios

```txt
volume_mensal
tempo_medio_execucao_min
custo_hora_mao_obra
```

---

### 3.4. Investimento

Registra custos ligados à implantação, desenvolvimento ou sustentação de uma revisão.

Esses custos são separados do custo operacional do processo.

#### Campos

```txt
investimento_id
revisao_id
tipo_investimento
categoria_investimento
descricao_item
quantidade
valor_unitario
valor_total
data_investimento
recorrencia
meses_vigencia
centro_custo
observacoes
deletado
created_at
updated_at
```

#### Regras

- `investimento_id` é chave primária.
- `revisao_id` referencia `revisao.revisao_id`.
- O front-end envia `quantidade` e `valor_unitario`.
- O backend deve calcular `valor_total = quantidade * valor_unitario`.
- `valor_total` é o valor principal usado nos cálculos.
- `recorrencia` define o comportamento temporal do investimento.
- `tipo_investimento` é classificação gerencial.
- `deletado = true` exclui o item dos cálculos.

#### Campos obrigatórios

```txt
tipo_investimento
descricao_item
quantidade
valor_unitario
recorrencia
```

---

### 3.5. Recurso compartilhado

Representa um custo recorrente compartilhado entre várias revisões.

Exemplos:

- software usado por vários processos;
- consultoria recorrente;
- ferramenta externa;
- licença;
- infraestrutura;
- recurso interno rateado.

#### Campos

```txt
recurso_compartilhado_id
codigo_recurso
nome_recurso
categoria_recurso
fornecedor
tipo_custo
recorrencia
valor_total_recorrente
data_inicio_vigencia
data_fim_vigencia
centro_custo
criterio_rateio
status_recurso
observacoes
deletado
created_at
updated_at
```

#### Regras

- O recurso não entra sozinho no dashboard.
- Ele precisa estar vinculado a uma revisão.
- `valor_total_recorrente` representa o custo total recorrente.
- `criterio_rateio` define como dividir o custo.
- `status_recurso = ativo` habilita o recurso.
- `deletado = true` exclui o recurso dos cálculos.

#### Campos obrigatórios

```txt
nome_recurso
tipo_custo
recorrencia
valor_total_recorrente
criterio_rateio
status_recurso
```

---

### 3.6. Vínculo entre revisão e recurso compartilhado

Entidade que conecta uma revisão a um recurso compartilhado.

#### Campos

```txt
vinculo_id
revisao_id
recurso_compartilhado_id
data_inicio_uso
data_fim_uso
ativo
peso_rateio
observacoes
deletado
created_at
updated_at
```

#### Regras

- `vinculo_id` é chave primária.
- `revisao_id` referencia `revisao.revisao_id`.
- `recurso_compartilhado_id` referencia `recursos_compartilhados.recurso_compartilhado_id`.
- `ativo = true` habilita o vínculo para cálculo.
- `peso_rateio` é usado quando o critério do recurso for `por_peso`.
- `deletado = true` exclui o vínculo dos cálculos.

---

## 4. Catálogos oficiais

A aplicação deve usar catálogos controlados para selects, filtros e validações.

### Filiais

```txt
01 = Matriz
02 = Filial
```

Importante: `filial_id` deve ser string, nunca número, para preservar valores como `01`.

### Setores

```txt
engenharia
qualidade
pcp
producao
comercial
compras
almoxarifado
```

### Status do processo

```txt
ativo
descontinuado
em_implantacao
```

### Tipos de cenário da revisão

```txt
baseline
melhoria
automacao
correcao
```

### Tipos de investimento

```txt
fixo
variavel
recorrente
unico
```

### Categorias de investimento e recurso

```txt
software
treinamento
consultoria
equipamento
horas_internas
terceiros
```

### Recorrências

```txt
unico
mensal
anual
```

### Critérios de rateio

```txt
igualitario
por_revisoes_ativas
por_peso
```

### Status do recurso

```txt
ativo
inativo
```

---

## 5. Regras globais de integridade

### 5.1. Exclusão lógica

Todas as entidades principais devem ter campo `deletado`.

Registros com `deletado = true` não devem participar de:

- listas do front-end;
- selects;
- cálculos;
- dashboards;
- comparações;
- rateios;
- relatórios.

### 5.2. IDs

Todos os IDs podem ser UUID.

Sugestão:

```txt
processo_id = uuid
revisao_id = uuid
medicao_id = uuid
investimento_id = uuid
recurso_compartilhado_id = uuid
vinculo_id = uuid
dashboard_calculo_id = revisao_id + "::" + competencia
```

### 5.3. Datas

A aplicação deve evitar bugs de fuso e UTC.

Recomendação:

- armazenar datas puras como `DATE`, não `TIMESTAMP`;
- armazenar `created_at` e `updated_at` como timestamp com timezone;
- tratar competência mensal como string `yyyy-MM` e também como data normalizada no primeiro dia do mês;
- no front-end, enviar datas no formato ISO `yyyy-MM-dd`;
- evitar converter data pura para UTC quando a intenção for apenas calendário.

### 5.4. Textos sensíveis

Os campos abaixo devem ser string:

```txt
filial_id
codigo_processo
versao_revisao
base_referencia_mes
competencia
```

Isso evita erros como:

- filial `01` virar `1`;
- versão `1.1.0` virar data;
- mês de referência ser convertido incorretamente.

---

## 6. Regras da timeline mensal

A aplicação deve gerar cálculos mês a mês.

### Início da timeline

A timeline começa na menor data encontrada entre:

```txt
revisao.data_inicio_vigencia
revisao.data_implantacao
processos.data_criacao
```

### Fim da timeline

A timeline vai até o mês atual.

### Formato da competência

```txt
yyyy-MM
```

Exemplos:

```txt
2025-01
2025-09
2026-03
```

---

## 7. Vigência da revisão

Uma revisão entra no cálculo de um mês quando:

```txt
competencia >= data_inicio_vigencia
```

E, se existir `data_fim_vigencia`:

```txt
competencia <= data_fim_vigencia
```

Se `data_fim_vigencia` estiver vazia, a revisão continua válida até o mês atual.

---

## 8. Comparação entre cenários

### Baseline

A revisão com `cenario_tipo = baseline` é a referência de comparação do processo.

Para baseline:

```txt
custo_baseline = custo_atual
economia_bruta = 0
```

A baseline pode gerar linha no dashboard, mas não gera economia comparativa.

### Cenários comparáveis

Os cenários abaixo devem ser comparados contra uma baseline:

```txt
melhoria
automacao
correcao
```

### Seleção da baseline

Para cada revisão comparável, selecionar a baseline nesta ordem:

1. revisão do mesmo processo com `cenario_tipo = baseline`;
2. se não houver baseline, usar a menor `versao_revisao` do processo.

---

## 9. Cálculos operacionais

### 9.1. Custo de tempo

```txt
custo_tempo =
volume_mensal *
(tempo_medio_execucao_min / 60) *
custo_hora_mao_obra
```

### 9.2. Custo de retrabalho

Se `custo_unitario_retrabalho > 0`:

```txt
custo_retrabalho =
volume_mensal *
percentual_retrabalho *
custo_unitario_retrabalho
```

Caso contrário:

```txt
custo_retrabalho =
volume_mensal *
percentual_retrabalho *
(tempo_retrabalho_min / 60) *
custo_hora_mao_obra
```

### 9.3. Custo de erro

Se `custo_unitario_erro > 0`:

```txt
custo_erro =
quantidade_erros_mes *
custo_unitario_erro
```

Caso contrário:

```txt
custo_erro = 0
```

### 9.4. Outros desperdícios

```txt
custo_outros = custo_outros_desperdicios
```

### 9.5. Custo operacional total

```txt
custo_operacional =
custo_tempo +
custo_retrabalho +
custo_erro +
custo_outros +
custo_recursos_compartilhados
```

---

## 10. Recursos compartilhados

### Elegibilidade do recurso

Um recurso entra no cálculo se:

```txt
deletado != true
status_recurso = ativo
competencia dentro da vigência do recurso
```

### Elegibilidade do vínculo

Um vínculo entra no cálculo se:

```txt
deletado != true
ativo = true
competencia dentro de data_inicio_uso e data_fim_uso
```

### Rateio igualitário

```txt
custo_alocado =
valor_total_recorrente / quantidade_de_vinculos_elegiveis
```

### Rateio por revisões ativas

```txt
custo_alocado =
valor_total_recorrente / quantidade_de_revisoes_elegiveis_no_mes
```

### Rateio por peso

```txt
custo_alocado =
valor_total_recorrente *
(peso_rateio / soma_dos_pesos_elegiveis)
```

Se `criterio_rateio = por_peso` e `peso_rateio` estiver vazio, considerar peso `1`.

---

## 11. Cálculos de economia

A economia sempre compara o cenário baseline com o cenário atual da revisão.

```txt
economia_tempo =
max(custo_tempo_baseline - custo_tempo_atual, 0)

economia_retrabalho =
max(custo_retrabalho_baseline - custo_retrabalho_atual, 0)

economia_erros =
max(custo_erro_baseline - custo_erro_atual, 0)

economia_outros =
max(custo_outros_baseline - custo_outros_atual, 0)

economia_recursos_compartilhados =
max(custo_recursos_compartilhados_baseline - custo_recursos_compartilhados_atual, 0)
```

### Economia bruta

```txt
economia_bruta =
economia_tempo +
economia_retrabalho +
economia_erros +
economia_outros +
economia_recursos_compartilhados
```

---

## 12. Cálculo dos investimentos

### Investimento único do mês

Entram itens onde:

```txt
deletado != true
recorrencia = unico
data_investimento pertence à competencia
```

Fórmula:

```txt
investimento_unico_mes = soma(valor_total)
```

### Custo recorrente mensal

Entram itens onde:

```txt
deletado != true
recorrencia = mensal ou anual
competencia dentro da vigência financeira do item
```

Se `recorrencia = mensal`:

```txt
custo_recorrente_mes += valor_total
```

Se `recorrencia = anual`:

```txt
custo_recorrente_mes += valor_total / 12
```

Se existir `meses_vigencia`, considerar o item a partir de `data_investimento` por essa quantidade de meses.

---

## 13. Indicadores finais

### Economia líquida do mês

```txt
economia_liquida_mes =
economia_bruta - custo_recorrente_mes
```

### Acumulados

```txt
investimento_unico_acumulado =
soma histórica de investimento_unico_mes

custo_recorrente_acumulado =
soma histórica de custo_recorrente_mes

economia_liquida_acumulada =
soma histórica de economia_liquida_mes
```

### ROI

```txt
roi =
(economia_liquida_acumulada - investimento_unico_acumulado)
/
investimento_unico_acumulado
```

```txt
roi_percentual = roi
```

No front-end, exibir em formato percentual.

### Payback

O payback é atingido no primeiro mês em que:

```txt
economia_liquida_acumulada >= investimento_unico_acumulado
```

Campos derivados:

```txt
payback_atingido
payback_meses
```

---

## 14. Sugestão de banco de dados

Recomendo banco relacional, preferencialmente **PostgreSQL**.

### Tabelas principais

```txt
processos
revisoes
medicoes
investimentos
recursos_compartilhados
revisao_recursos_compartilhados
dashboard_calculos
usuarios
audit_logs
```

### Tipos recomendados

```txt
id: uuid
textos: varchar/text
valores monetários: numeric(14,2)
percentuais: numeric(10,4)
datas puras: date
timestamps: timestamptz
booleanos: boolean
competencia: char(7) ou varchar(7)
```

### Índices importantes

```sql
processos(filial_id)
processos(setor_id)
processos(status_processo)
processos(deletado)

revisoes(processo_id)
revisoes(cenario_tipo)
revisoes(revisao_ativa)
revisoes(data_inicio_vigencia)
revisoes(data_fim_vigencia)
revisoes(deletado)

medicoes(revisao_id)
investimentos(revisao_id)
investimentos(data_investimento)
investimentos(recorrencia)

recursos_compartilhados(status_recurso)
revisao_recursos_compartilhados(revisao_id)
revisao_recursos_compartilhados(recurso_compartilhado_id)

dashboard_calculos(competencia)
dashboard_calculos(processo_id)
dashboard_calculos(revisao_id)
dashboard_calculos(filial_id)
dashboard_calculos(setor_id)
```

---

## 15. API backend esperada

### Processos

```txt
GET    /api/processos
GET    /api/processos/:id
POST   /api/processos
PUT    /api/processos/:id
DELETE /api/processos/:id
```

O delete deve ser lógico:

```txt
deletado = true
```

### Revisões

```txt
GET    /api/revisoes
GET    /api/revisoes/:id
GET    /api/processos/:processoId/revisoes
POST   /api/revisoes
PUT    /api/revisoes/:id
DELETE /api/revisoes/:id
POST   /api/revisoes/:id/ativar
```

Ao ativar uma revisão:

- definir `revisao_ativa = true` para ela;
- definir `revisao_ativa = false` para as demais revisões do mesmo processo.

### Medições

```txt
GET    /api/medicoes
GET    /api/revisoes/:revisaoId/medicoes
POST   /api/medicoes
PUT    /api/medicoes/:id
DELETE /api/medicoes/:id
```

### Investimentos

```txt
GET    /api/investimentos
GET    /api/revisoes/:revisaoId/investimentos
POST   /api/investimentos
PUT    /api/investimentos/:id
DELETE /api/investimentos/:id
```

No `POST` e `PUT`, o backend deve calcular `valor_total`.

### Recursos compartilhados

```txt
GET    /api/recursos-compartilhados
GET    /api/recursos-compartilhados/:id
POST   /api/recursos-compartilhados
PUT    /api/recursos-compartilhados/:id
DELETE /api/recursos-compartilhados/:id
```

### Vínculos de recursos

```txt
GET    /api/revisao-recursos-compartilhados
POST   /api/revisao-recursos-compartilhados
PUT    /api/revisao-recursos-compartilhados/:id
DELETE /api/revisao-recursos-compartilhados/:id
```

### Dashboard

```txt
POST /api/dashboard/recalcular
GET  /api/dashboard
GET  /api/dashboard/resumo
GET  /api/dashboard/evolucao
GET  /api/dashboard/processos/:processoId
```

Filtros esperados:

```txt
processo_id
filial_id
setor_id
cenario_tipo
competencia_inicio
competencia_fim
revisao_ativa
```

### Catálogos

```txt
GET /api/options
GET /api/options/filiais
GET /api/options/setores
GET /api/options/status-processo
GET /api/options/cenarios
GET /api/options/recorrencias
GET /api/options/criterios-rateio
```

---

## 16. Front-end esperado

A interface deve possuir módulos/telas para:

### 16.1. Gestão de processos

Funcionalidades:

- listar processos;
- filtrar por filial, setor e status;
- cadastrar processo;
- editar processo;
- excluir logicamente processo;
- abrir detalhes do processo;
- visualizar revisões vinculadas.

### 16.2. Gestão de revisões

Funcionalidades:

- listar revisões por processo;
- criar nova revisão;
- marcar revisão como ativa;
- encerrar vigência;
- diferenciar visualmente baseline, melhoria, automação e correção;
- impedir sobrescrita de revisão anterior;
- preservar histórico.

### 16.3. Medições

Funcionalidades:

- cadastrar dados operacionais da revisão;
- editar medição;
- validar campos obrigatórios;
- aceitar valores monetários e percentuais em formato brasileiro;
- tratar campos vazios como zero no cálculo.

### 16.4. Investimentos

Funcionalidades:

- cadastrar investimento;
- informar quantidade e valor unitário;
- calcular valor total automaticamente;
- selecionar recorrência;
- informar vigência;
- separar investimento único de custo recorrente.

### 16.5. Recursos compartilhados

Funcionalidades:

- cadastrar recurso;
- definir valor recorrente;
- definir critério de rateio;
- vincular recurso a revisões;
- informar peso de rateio quando aplicável.

### 16.6. Dashboard

Deve apresentar:

- economia bruta total;
- economia líquida total;
- investimento acumulado;
- custo recorrente acumulado;
- ROI;
- payback;
- gráfico mensal de economia;
- gráfico mensal de investimento;
- comparação baseline versus cenário atual;
- ranking de processos com maior economia;
- filtros por período, processo, filial e setor.

---

## 17. Comportamentos importantes herdados do Apps Script

A aplicação nova deve preservar estes comportamentos:

1. Campos obrigatórios devem ser validados no front e no backend.
2. Versão da revisão deve ser texto.
3. Filial deve ser texto para preservar `01` e `02`.
4. Valores monetários e percentuais devem aceitar formato brasileiro.
5. Datas devem evitar bug de UTC com um dia a menos.
6. Exclusão deve ser lógica.
7. Dashboard deve ser derivado, nunca editado manualmente.
8. Revisões devem preservar histórico.
9. Nova revisão ativa deve desativar revisões anteriores do mesmo processo.
10. Recursos compartilhados só entram no cálculo quando vinculados a revisões elegíveis.

---

## 18. Stack sugerida

### Backend

```txt
Node.js + NestJS
ou
Node.js + Express/Fastify
```

### Banco

```txt
PostgreSQL
```

### ORM

```txt
Prisma
ou
Drizzle ORM
ou
TypeORM
```

### Front-end

```txt
React
Next.js
Vite + React
```

### UI

```txt
Tailwind CSS
shadcn/ui
React Hook Form
Zod
Recharts
TanStack Query
```

### Autenticação

```txt
JWT
NextAuth
Auth.js
Supabase Auth
Clerk
```

---

## 19. Prompt direto para o agente de IA

```txt
Desenvolva uma aplicação web completa chamada Transformômetro.

O Transformômetro substitui uma solução atual feita em Google Sheets + Apps Script. A nova aplicação deve ter front-end, API backend e banco de dados relacional.

A ferramenta serve para cadastrar processos, registrar revisões desses processos, medir custos operacionais, registrar investimentos, alocar recursos compartilhados e calcular indicadores financeiros de melhoria, como economia bruta, economia líquida, ROI e payback.

A unidade central de cálculo é a revisão, identificada por revisao_id. Um processo pode ter múltiplas revisões. As revisões representam cenários, como baseline, melhoria, automação ou correção. O cenário baseline é a referência de comparação. Cenários de melhoria, automação e correção devem ser comparados contra a baseline do mesmo processo.

Implemente as seguintes entidades:

1. processos
2. revisoes
3. medicoes
4. investimentos
5. recursos_compartilhados
6. revisao_recursos_compartilhados
7. dashboard_calculos
8. usuarios
9. audit_logs

Use UUID como chave primária.

A tabela processos deve conter:
processo_id, codigo_processo, nome_processo, descricao_processo, filial_id, setor_id, gestor_responsavel, objetivo_processo, status_processo, data_criacao, data_atualizacao, deletado.

A tabela revisoes deve conter:
revisao_id, processo_id, versao_revisao, chave_unica_processo_revisao, descricao_revisao, motivo_revisao, cenario_tipo, data_implantacao, data_inicio_vigencia, data_fim_vigencia, revisao_ativa, observacoes, created_at, updated_at, deletado.

A tabela medicoes deve conter:
medicao_id, revisao_id, volume_mensal, tempo_medio_execucao_min, tempo_retrabalho_min, percentual_retrabalho, percentual_erro, quantidade_erros_mes, custo_hora_mao_obra, custo_unitario_erro, custo_unitario_retrabalho, custo_outros_desperdicios, base_referencia_mes, observacoes, deletado.

A tabela investimentos deve conter:
investimento_id, revisao_id, tipo_investimento, categoria_investimento, descricao_item, quantidade, valor_unitario, valor_total, data_investimento, recorrencia, meses_vigencia, centro_custo, observacoes, deletado, created_at, updated_at.

A tabela recursos_compartilhados deve conter:
recurso_compartilhado_id, codigo_recurso, nome_recurso, categoria_recurso, fornecedor, tipo_custo, recorrencia, valor_total_recorrente, data_inicio_vigencia, data_fim_vigencia, centro_custo, criterio_rateio, status_recurso, observacoes, deletado, created_at, updated_at.

A tabela revisao_recursos_compartilhados deve conter:
vinculo_id, revisao_id, recurso_compartilhado_id, data_inicio_uso, data_fim_uso, ativo, peso_rateio, observacoes, deletado, created_at, updated_at.

Todos os deletes devem ser lógicos usando deletado = true.

Campos como filial_id, codigo_processo, versao_revisao, base_referencia_mes e competencia devem ser string. Não converter filial 01 para número 1. Não converter versão 1.1.0 para data ou número.

Use catálogos controlados:
filiais: 01 Matriz, 02 Filial.
setores: engenharia, qualidade, pcp, producao, comercial, compras, almoxarifado.
status_processo: ativo, descontinuado, em_implantacao.
cenario_tipo: baseline, melhoria, automacao, correcao.
tipo_investimento: fixo, variavel, recorrente, unico.
categoria: software, treinamento, consultoria, equipamento, horas_internas, terceiros.
recorrencia: unico, mensal, anual.
criterio_rateio: igualitario, por_revisoes_ativas, por_peso.
status_recurso: ativo, inativo.

Crie API REST para CRUD de todas as entidades.

Crie endpoint POST /api/dashboard/recalcular para reconstruir dashboard_calculos.

O dashboard_calculos deve ter uma linha por revisao_id + competencia mensal.

A competência deve ter formato yyyy-MM.

A timeline mensal começa na menor data entre:
revisao.data_inicio_vigencia,
revisao.data_implantacao,
processos.data_criacao.

A timeline termina no mês atual.

Uma revisão entra no cálculo quando:
competencia >= data_inicio_vigencia
e, se existir data_fim_vigencia,
competencia <= data_fim_vigencia.

Para cada revisão comparável, selecionar baseline nesta ordem:
1. revisão do mesmo processo com cenario_tipo = baseline;
2. se não houver, menor versao_revisao do processo.

Cálculo de custo de tempo:
custo_tempo = volume_mensal * (tempo_medio_execucao_min / 60) * custo_hora_mao_obra.

Cálculo de retrabalho:
se custo_unitario_retrabalho > 0:
custo_retrabalho = volume_mensal * percentual_retrabalho * custo_unitario_retrabalho.
senão:
custo_retrabalho = volume_mensal * percentual_retrabalho * (tempo_retrabalho_min / 60) * custo_hora_mao_obra.

Custo de erro:
se custo_unitario_erro > 0:
custo_erro = quantidade_erros_mes * custo_unitario_erro.
senão:
custo_erro = 0.

Custo de outros:
custo_outros = custo_outros_desperdicios.

Custo operacional:
custo_operacional = custo_tempo + custo_retrabalho + custo_erro + custo_outros + custo_recursos_compartilhados.

Recursos compartilhados devem ser alocados apenas quando recurso e vínculo forem elegíveis na competência.

Critérios de rateio:
igualitario: valor_total_recorrente / quantidade_de_vinculos_elegiveis.
por_revisoes_ativas: valor_total_recorrente / quantidade_de_revisoes_elegiveis_no_mes.
por_peso: valor_total_recorrente * (peso_rateio / soma_dos_pesos_elegiveis).
Se peso estiver vazio no critério por_peso, usar peso 1.

Economias:
economia_tempo = max(custo_tempo_baseline - custo_tempo_atual, 0).
economia_retrabalho = max(custo_retrabalho_baseline - custo_retrabalho_atual, 0).
economia_erros = max(custo_erro_baseline - custo_erro_atual, 0).
economia_outros = max(custo_outros_baseline - custo_outros_atual, 0).
economia_recursos_compartilhados = max(custo_recursos_compartilhados_baseline - custo_recursos_compartilhados_atual, 0).
economia_bruta = soma das economias.

Investimento único do mês:
somar investimentos com recorrencia = unico e data_investimento na competência.

Custo recorrente do mês:
se recorrencia = mensal, somar valor_total.
se recorrencia = anual, somar valor_total / 12.
Se meses_vigencia existir, considerar somente o período de vigência a partir da data_investimento.

Economia líquida do mês:
economia_liquida_mes = economia_bruta - custo_recorrente_mes.

Acumulados:
investimento_unico_acumulado = soma histórica do investimento_unico_mes.
custo_recorrente_acumulado = soma histórica do custo_recorrente_mes.
economia_liquida_acumulada = soma histórica da economia_liquida_mes.

ROI:
roi = (economia_liquida_acumulada - investimento_unico_acumulado) / investimento_unico_acumulado.

Payback:
payback é atingido no primeiro mês em que economia_liquida_acumulada >= investimento_unico_acumulado.

O front-end deve ter telas para:
gestão de processos,
gestão de revisões,
medições,
investimentos,
recursos compartilhados,
vínculos de recursos,
dashboard.

O dashboard deve ter filtros por processo, filial, setor, cenário e período. Deve exibir cards de economia, investimento, ROI e payback, além de gráficos mensais de economia e investimento.

Valide tudo no front-end e no backend. Use parser compatível com formato brasileiro para números e moeda. Evite bug de UTC em datas puras.
```
