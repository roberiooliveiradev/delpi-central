# Lousa da Fase 5 — Strategic Indicators

## Etapa atual
**Fase 5 — Indicators**

## Status da fase
**Em andamento**

## Objetivo da fase
Conectar a tela de indicadores à API real, com foco exclusivo em:

- `GET /apps/api-delpi/strategic-indicators/indicators`

Esta fase termina quando a tela de indicadores deixar de usar mock e passar a renderizar dados reais da API, preservando a UX analítica já existente.

---

## Escopo que entra nesta fase
- rota agregadora `GET /apps/api-delpi/strategic-indicators/indicators`
- catálogo analítico de indicadores
- integração incremental por departamento
- filtros analíticos da tela de indicadores
- filtro de mês de referência
- backend e frontend da rota de indicadores
- loading, erro e sucesso da tela de indicadores

## Escopo que não entra nesta fase
- `GET /trends`
- `GET /alerts`
- integração real da tela de presentation
- novas evoluções de settings/audit/change-requests
- qualquer etapa futura do roadmap

---

## Estratégia da fase
### Regra de implementação
A Fase 5 será conectada **um departamento por vez**, mas mantendo uma **rota pública única**:

- `GET /apps/api-delpi/strategic-indicators/indicators`

### Regra de UX
As pages **não podem perder funcionalidades já existentes**.
A tela de indicadores deve preservar:

- síntese analítica
- filtros analíticos
- leitura por departamento
- prioridades imediatas
- tabela e detalhe rápido
- filtro de mês de referência

A evolução correta é por **troca de fonte de dados**, e não por simplificação da page.

---

## Primeira iteração da fase
**Departamento conectado primeiro: Engenharia**

### Motivo
Engenharia já possui duas fontes reais disponíveis no projeto:

- **LMP** para prazo de projetos
- **Transforma Mais** para ganhos financeiros

### Indicadores conectados nesta iteração
- `% de Projetos Concluídos no Prazo`
- `Ganhos Financeiros do TRANSFORMA+ DELPI`

---

## Segunda iteração da fase
**Departamento conectado em seguida: Produção**

### Motivo
Produção já possui as rotas reais dos 5 indicadores oficiais da área:

- `direct_labor_cost_pct`
- `production_cost_pct`
- `depreciation_pct`
- `overall_equipment_effectiveness_pct`
- `on_time_delivery_pct`

### Regra funcional aplicada
- Produção existe em matriz e filial
- o indicador consolidado da Fase 5 usa a **média entre as unidades**
- a consolidação é feita no provider do Strategic Indicators

### Indicadores conectados nesta iteração
- `Custo Mão de Obra Direta / ROL`
- `Custos de Produção / ROL`
- `Depreciação / ROL`
- `OEE (Eficiência Global dos Equip.)`
- `OTD (Entrega no Prazo)`

---

## Terceira iteração da fase
**Departamento conectado em seguida: Comercial**

### Motivo
Comercial já possui as rotas reais dos 5 indicadores oficiais da área:

- `head_office_rol_target_pct`
- `branch_rol_target_pct`
- `closing-rate`
- `new-clients-average`
- `new-clients-rol-pct`

### Regra funcional aplicada
- Comercial tem escopo misto
- `ROL Matriz / Meta` usa escopo `matrix_only`
- `ROL Filial / Meta` usa escopo `branch_only`
- os demais indicadores comerciais entram como `consolidated`
- a agregação é feita dentro do provider do Strategic Indicators

### Indicadores conectados nesta iteração
- `ROL Matriz / Meta`
- `ROL Filial / Meta`
- `Taxa de Fechamento de Negócios`
- `Número de Novos Clientes (média mensal)`
- `% ROL de Novos Clientes`

---

## Fontes reais conectadas
### Engenharia — LMP
Fonte usada para:
- `% de Projetos Concluídos no Prazo`

Base técnica:
- `/engineering/lmps/dashboard`
- composer de LMP com `LMPQueryRepository`
- uso do resumo com `percent_dentro_prazo`

### Engenharia — Transforma Mais
Fonte usada para:
- `Ganhos Financeiros do TRANSFORMA+ DELPI`

Base técnica:
- `/engineering/transforma-mais/processes/summary`
- composer de Transforma Mais com `ProcessRepository`
- cálculo a partir do novo campo de resumo bruto do período

### Produção — fontes reais conectadas
Fontes usadas para:
- `Custo Mão de Obra Direta / ROL`
- `Custos de Produção / ROL`
- `Depreciação / ROL`
- `OEE`
- `OTD`

Base técnica:
- `/production/direct_labor_cost_pct`
- `/production/production_cost_pct`
- `/production/depreciation_pct`
- `/production/overall_equipment_effectiveness_pct`
- `/production/on_time_delivery_pct`

### Comercial — fontes reais conectadas
Fontes usadas para:
- `ROL Matriz / Meta`
- `ROL Filial / Meta`
- `Taxa de Fechamento de Negócios`
- `Número de Novos Clientes (média mensal)`
- `% ROL de Novos Clientes`

Base técnica:
- `/commercial/head_office_rol_target_pct`
- `/commercial/branch_rol_target_pct`
- `/commercial/closing-rate`
- `/commercial/new-clients-average`
- `/commercial/new-clients-rol-pct`

---

## Ajustes feitos nesta fase até agora
### Backend do Strategic Indicators
- criada a rota agregadora `GET /apps/api-delpi/strategic-indicators/indicators`
- criada a primeira iteração do provider de indicadores da Engenharia
- integração real com as fontes de LMP e Transforma Mais
- filtro por `department_id`
- suporte a `start_date` e `end_date`
- criada a segunda iteração com provider de Produção
- integração real de Produção com os 5 indicadores oficiais
- criada a terceira iteração com provider de Comercial
- integração real de Comercial com os 5 indicadores oficiais
- criada a quarta iteração com provider de Qualidade
- integração real de Qualidade com PPM, Kaizen e Audit 5S
- providers departamentais ajustados para tolerância a falha por indicador
- rota `/indicators` agora agrega Engenharia + Produção + Comercial + Qualidade
- a rota passou a devolver `items`, `errors` e `partial_success`
- rota `/executive-summary` passou a aceitar `competence`, `start_date` e `end_date`
- início da substituição do resumo executivo estático por cálculo central baseado em catálogo do plugin + measurements reais

### Backend do Transforma Mais
- identificado problema de mapeamento do ganho financeiro
- adicionada evolução no summary do Transforma Mais
- criado o novo campo:
  - `total_gross_savings_in_period`
- ajuste do calculator para somar `monthly_breakdown[].gross_savings_month`
- provider da Fase 5 atualizado para usar explicitamente esse campo

### Frontend da tela de indicadores
- criada a base para consumo da rota real `/indicators`
- adicionado filtro de mês de referência
- preservada a estrutura analítica já existente da page
- iniciada a remoção da dependência dos tipos antigos de `indicatorsMock`
- iniciado o desacoplamento dos componentes analíticos para aceitar tipo próprio da tela
- corrigida a chamada da API para respeitar o filtro de departamento
- corrigida a concorrência entre requests com proteção contra respostas antigas
- ajustada a UX para manter os dados anteriores visíveis durante atualização de filtros
- mantido card de carregamento/atualização sem desmontar a tela
- front adaptado para sucesso parcial, exibindo indicadores válidos mesmo quando parte das fontes falha
- a tela passou a mostrar aviso de fontes/indicadores com erro sem travar a aplicação
- página principal (`ExecutiveDashboardPage`) evoluída para consumir resumo executivo por competência/período
- adicionado filtro de mês de referência na home executiva
- removido valor fixo de nota exibida na metodologia da home
- corrigido o loop de atualização do resumo executivo causado por instabilidade do `getAccessToken` no hook
- home agora mantém os dados em tela durante refresh e remove corretamente o card de atualização ao concluir

---

## Contrato entregue até agora
### `GET /apps/api-delpi/strategic-indicators/indicators`
Entrega, nesta fase parcial, itens com:

- `department_id`
- `department_name`
- `indicator_id`
- `indicator_name`
- `weight_pct`
- `goal_2026`
- `scope_type`
- `value`
- `score`
- `gap`
- `trend`
- `classification`
- `source`

### Departamentos já servidos por essa rota
- `engineering`
- `production`
- `commercial`
- `quality`

---

## Validação já concluída
### Validado
- rota `/apps/api-delpi/strategic-indicators/indicators?department_id=engineering` respondendo
- indicador de LMP retornando corretamente
- indicador de Transforma Mais retornando corretamente após ajuste do campo bruto do período
- payload real da Engenharia já coerente com a fase
- rota `/apps/api-delpi/strategic-indicators/indicators?department_id=production` respondendo
- os 5 indicadores de Produção retornando na mesma rota agregadora
- front da tela de indicadores já batendo com a API no cenário validado de Produção
- rota `/apps/api-delpi/strategic-indicators/indicators?department_id=commercial` integrada ao backend agregador
- os 5 indicadores de Comercial já conectados na rota agregadora
- rota `/apps/api-delpi/strategic-indicators/indicators` passou a suportar sucesso parcial (`items` + `errors` + `partial_success`)
- falhas de uma fonte não derrubam mais toda a rota agregadora
- página principal passou a filtrar por mês de referência e consultar a API executiva com período real
- correção validada do estado de atualização preso na home executiva

### Exemplo funcional já validado
Para março/2026:
- `% de Projetos Concluídos no Prazo` retornou com valor real
- `Ganhos Financeiros do TRANSFORMA+ DELPI` retornou com `value = 4291.65`
- os indicadores de Produção já renderizaram coerentes com o payload da API

---

## Departamentos ainda não conectados nesta fase
Os seguintes departamentos **ainda não possuem rotas/fontes reais integradas na Fase 5** e, portanto, **ainda não entram no cálculo real desta etapa**:

### Financeiro
Indicadores ainda pendentes de integração real:
- `EBITDA / Receita Operacional`
- `% Custos Fixos / Receita Operacional`
- `Prazo Médio de Recebimento (PMR)`

### RH
Indicadores ainda pendentes de integração real:
- `Absenteísmo`
- `Turnover (Rotatividade)`
- `Satisfação Interna (Clima/Engajamento)`
- `% de PDIs Ativos`
- `Horas de Treinamento/Colaborador/mês`

### Suprimentos
Indicadores ainda pendentes de integração real:
- `CPV Consolidado (matriz e filial)`
- `OTD Consolidado de Compras`
- `Giro de Estoque Consolidado`
- `Valor Total do Estoque Consolidado`
- `Economia em Negociações de Compras`

### Regra temporária desta fase
- seguimos o desenvolvimento com os departamentos já conectados
- depois retornamos para integrar Financeiro, RH e Suprimentos
- somente após essa integração completa esses departamentos passam a entrar no cálculo real consolidado

---

## Pendências atuais da fase
### Frontend
- concluir a remoção total de qualquer resquício funcional de `indicatorsMock`
- validar cenários com mudança rápida de filtros
- validar mês com dados e mês sem dados
- validar retry após erro com dados já em tela
- validar a UX de sucesso parcial com múltiplos erros simultâneos

### Backend
- próximos departamentos ainda não conectados: `financial`, `hr`, `supplies`
- validar payloads reais de Qualidade para refinar leitura dos campos defensivos quando necessário

---

## Critério de conclusão da fase
A Fase 5 só estará concluída quando:

- `IndicatorsPage` deixar de depender funcionalmente de `indicatorsMock`
- a tela de indicadores renderizar dados reais pela rota `/indicators`
- os filtros analíticos forem preservados
- o mês de referência estiver funcionando
- a UX atual da page tiver sido mantida
- pelo menos as iterações completas de Engenharia, Produção, Comercial e Qualidade estiverem funcionando de ponta a ponta
- falhas pontuais de indicadores não derrubarem mais o departamento inteiro nem a rota agregadora

---

## Próximos passos imediatos
1. validar os payloads reais de Qualidade e refinar os campos lidos pelo provider quando necessário
2. confirmar estabilização completa da home executiva com cálculo real e filtro por competência
3. seguir removendo snapshots estáticos do resumo executivo, departamentos e detalhes
4. seguir o desenvolvimento do módulo e retornar depois para integrar `financial`, `hr` e `supplies` na rota agregadora e no cálculo real
1. concluir os ajustes dos componentes analíticos para o tipo próprio da tela
2. validar a `IndicatorsPage` com os dados reais de Engenharia
3. fechar formalmente a primeira iteração da Fase 5
4. decidir o próximo departamento a conectar na mesma rota agregadora

---

## Próxima fase
**Fase 6 — Trends**

### Ainda proibido nesta fase
- `GET /trends`
- `GET /alerts`
- qualquer avanço para fases seguintes antes do fechamento da Fase 5

