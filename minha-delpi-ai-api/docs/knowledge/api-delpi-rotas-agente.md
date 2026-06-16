# API DELPI — Guia de rotas para agentes operacionais

**Uso:** anexar este documento à inteligência do agente (base de conhecimento / RAG) ou colar trechos relevantes no `system_prompt` de agentes que usam o provider OpenAPI `api-delpi`.

**Provider:** `api-delpi` · **Base no gateway:** `/apps/api-delpi` · **OpenAPI:** `/apps/api-delpi/openapi.json`

**Última revisão:** alinhada à `api-delpi` em **09/06/2026** (playbooks fabril + parâmetros obrigatórios e sessão ativa no chat base).

Após mudanças na API, rode `scripts/sync_api_delpi_openapi.py` (reimport + embeddings + catálogo) e **reindexe** este documento na base de conhecimento.

**Catálogo gerado (lista completa path → operationId):** [`_generated/api-delpi-openapi-catalog.md`](./_generated/api-delpi-openapi-catalog.md)

---

## Regras gerais

1. Para dados operacionais (produto, estoque, LMP, KPIs, SQL), use **`execute_external_action`** com a action correta — não invente valores.
2. O backend escolhe a action por `summary`, `description`, `path` e `operationId` do OpenAPI. Priorize o **path** e o **summary** em português; alguns `operationId` são longos (gerados automaticamente pelo FastAPI).
3. Código de produto aceita máscara (`10.080.055` → enviar normalizado sem pontos na API).
4. Em follow-up ("estoque **desse** produto", "mesma OV"), use o código ou número mencionado antes na conversa.
5. **Não confunda** estoque de um item com indicador agregado de estoque da empresa.
6. Rotas de **dashboard** (LMP, comercial, RH, produção, qualidade) exigem permissões de dashboard ou `api-delpi.access` conforme a rota — o token do usuário precisa estar autorizado.
7. **Código de grupo ≠ código de produto.** «Grupo 1008» usa `GET /products/search` com `group_code=1008`. **Nunca** chame `/products/1008/analyser` só porque o número tem 4 dígitos.
8. Perguntas do tipo «consegue buscar por grupo?» são **capacidade** — responda com a rota e parâmetros; só execute a API quando o usuário pedir a busca de fato.
9. Rotas **paginadas** (`page`, `page_size`, `total`): quando o usuário pedir **total/completo/tabela completa/traga tudo**, o chat base consolida várias páginas automaticamente (`CHAT_PAGINATION_*`). Não peça ao usuário para clicar «próxima página» se ele pediu a listagem completa.
10. **ROL genérico** («rol do mês», KPI financeiro) → `GET /financial/rol` com `start_date`/`end_date`. **Série/gráfico comercial de ROL** → `GET /commercial/rol/series` com `granularity` (`day`, `week`, `month`, `year`).
11. **Data obrigatória (chat base, jun/2026):** rotas `factory-status`, `production-status`, `shipping-status` exigem data ou período informado pelo usuário — o chat **pergunta** antes de chamar a API (não usa default silencioso). Aceita *hoje*, *ontem*, *semana passada*, *este mês*, `DD/MM/YYYY` e intervalos.
12. **Resposta curta:** após o chat pedir código ou data, o usuário pode responder só com o valor (`90263059`, `hoje`, `01/06 a 15/06`). O pipeline recomponha a pergunta original automaticamente.
13. **Mesma consulta em sequência:** depois de um estoque (ou outra rota) bem-sucedido, novos códigos na mesma conversa continuam no **mesmo tipo** até o usuário pedir outra coisa (ex.: «estrutura», «analyser», pesquisa web).

---

## Permissões (resumo)

| Domínio | Permissões típicas |
|---------|-------------------|
| Produtos, vendas, suprimentos, SQL, sistema | `api-delpi.access` |
| Financeiro | `api-delpi.access` |
| Engenharia (LMP, Transforma Mais) | `api-delpi.access` ou `dashboard-engineering.view` ou `dashboard-lmps.view` |
| Comercial (KPIs) | `api-delpi.access` ou `dashboard-commercial.view` |
| Produção (KPIs) | `api-delpi.access` ou `dashboard-production.view` |
| RH | `api-delpi.access` ou `dashboard-hr.view` |
| Qualidade (métricas TOTVS) | `api-delpi.quality.access` ou `dashboard-quality.view` |
| SQL | `api-delpi.data` ou `api-delpi.access.full` |
| Metadados sistema (tabelas/colunas) | `api-delpi.access.full` ou `api-delpi.system` |

---

## Mapa rápido: intenção → rota

### Produtos (`/products`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Achar produto sem código exato | `GET /products/search` | `search_products` |
| Listar produtos de um **grupo** (cadastro ERP) | `GET /products/search` | `search_products` + `group_code` |
| Dados cadastrais (descrição, tipo, unidade) | `GET /products/{code}` | `get_product_detail` |
| Resumo completo (cadastro + estoque + preços) | `GET /products/{code}/summary` | `get_product_summary` |
| Análise completa / ficha detalhada | `GET /products/{code}/analyser` | `get_product_analyser` |
| Saldo / estoque / disponível **de um código** | `GET /products/{code}/stock` | `get_product_stock` |
| Estrutura / BOM / componentes | `GET /products/{code}/structure` | `get_product_structure` |
| Estrutura + MPs exclusivas | `GET /products/{code}/structure/exclusivity` | `get_product_structure_exclusivity` |
| **Diretivas** (DELPI ou referência cliente) | `GET /products/directives/{identifier}` | `get_product_directives` |
| Situação produtiva (PA/PI/OP/apontamentos) | `GET /products/{code}/production-status` | `get_product_production_status` |
| Expedição / inspeção final do PA | `GET /products/{code}/shipping-status` | `get_product_shipping_status` |
| Status fabril completo | `GET /products/{code}/factory-status` | `get_product_factory_status` |
| Análise de preço de MP (compra, ICMS, orçamento, variação) | `GET /products/{code}/raw-material-price-intelligence` | `get_product_raw_material_price_intelligence` |
| Última NF / fornecedor / ICMS de compra (MP) | `GET /products/{code}/last-purchase` | `get_product_last_purchase` |
| Histórico de preço de compra (NF + variação %) | `GET /products/{code}/purchase-price-history` | `get_product_purchase_price_history` |
| Histórico de orçamento (SC + PC) | `GET /products/{code}/purchase-budget-history` | `get_product_purchase_budget_history` |
| Impacto de custo / Pareto MPs / simulação de reajuste (PA) | `GET /products/{code}/cost-impact-simulation` | `get_product_cost_impact_simulation` |
| Exportar estrutura em Excel | `GET /products/{code}/structure/excel` | (download; preferir JSON no chat) |
| **Onde é usado / produto pai / where used** | `GET /products/{code}/parents` | `get_product_parents` |
| Preço / tabela de preço / quanto custa | `GET /products/{code}/pricing` | `get_product_pricing` |
| Fornecedores do item | `GET /products/{code}/suppliers` | `get_product_suppliers` |
| Clientes do item | `GET /products/{code}/customers` | `get_product_customers` |
| Histórico de compras | `GET /products/{code}/purchases` | `get_product_purchases` |
| Resumo de vendas do item | `GET /products/{code}/sales` | `get_product_sales_summary` |
| Carteira / pedidos em aberto do item | `GET /products/{code}/sales/open-orders` | `get_product_sales_open_orders` |
| Faturamento do item | `GET /products/{code}/sales/billing` | `get_product_sales_billing` |
| Roteiro de fabricação | `GET /products/{code}/guide` | `get_product_guide` |
| Inspeção / qualidade do item | `GET /products/{code}/inspection` | `get_product_inspection` |
| Movimentações internas | `GET /products/{code}/internal-movements` | `get_product_internal_movements` |
| Notas de entrada | `GET /products/{code}/inbound-invoice-items` | `get_product_inbound_invoice_items` |
| Notas de saída | `GET /products/{code}/outbound-invoice-items` | `get_product_outbound_invoice_items` |

**Parâmetros comuns**

- `search`: `code`, `description`, `group_code`, `page`, `page_size`, `sort`, `direction`
- `stock`: `code` (path), `branch`, `location`, `page`, `page_size`
- `structure` / `parents`: `code` (path), `page`, `page_size`, `max_depth` (até 99)
- `structure/exclusivity`: `code` (path), `max_depth` (default 50)
- `production-status`: `code` (path), `reference_date`, `branch`, `max_depth`
- `shipping-status`: `code` (path), `reference_date` ou `date_start`+`date_end`, `branch`
- `factory-status`: `code` (path), `reference_date`, `date_start`, `date_end`, `branch`, `max_depth`
- `directives`: `identifier` (path — código DELPI `9026xxxx` ou referência cliente `B1_REFEREN`); `max_depth`, `branch` opcionais
- `raw-material-price-intelligence`, `last-purchase`, `purchase-price-history`, `purchase-budget-history`: `code` (path); `date_start`/`date_end` **opcionais** no chat (API default 12 meses); `branch`, `history_limit` quando aplicável
- `cost-impact-simulation`: `code` (path, **PA only**); `adjustment_percent` (ex.: 10 = +10%), `price_source` (`standard_cost` | `last_purchase`), `top_n`, `max_depth`
- `analyser`, `summary`, `pricing`: `code` (path)

**Exemplos de frases → rota**

- "Qual a descrição do produto 10.080.055?" → `GET /products/{code}`
- "Resumo do produto 10080001" → `GET /products/{code}/summary`
- "Tem estoque do 10080047 na filial 01?" → `GET /products/{code}/stock`
- "Busca parafuso M8 na descrição" → `GET /products/search` (`description`)
- "Liste produtos do grupo MP" / "busque 3 produtos do grupo 1008" → `GET /products/search` (`group_code`, `page_size`)
- "Onde é usado o 10080001?" → `GET /products/{code}/parents`
- "Quanto custa o 10080001?" → `GET /products/{code}/pricing`
- "Quais MPs são exclusivas do 90261255?" → `GET /products/{code}/structure/exclusivity`
- "O produto já começou a produzir?" → `GET /products/{code}/production-status`
- "Quanto do PA já está liberado para expedição?" → `GET /products/{code}/shipping-status`
- "Qual o status do produto na fábrica?" → `GET /products/{code}/factory-status`
- "Análise de preço da matéria-prima 10080001" → `GET /products/{code}/raw-material-price-intelligence`
- "Última compra e ICMS do 10080001" → `GET /products/{code}/last-purchase`
- "Histórico de orçamento de compra do 10080001" → `GET /products/{code}/purchase-budget-history`
- "Quais materiais mais impactam o custo do PA 90261255?" → `GET /products/{code}/cost-impact-simulation`
- "Simule aumento de 10% nos materiais do 90261255" → `GET /products/{code}/cost-impact-simulation?adjustment_percent=10`
- "Diretivas 90260882" / "Diretivas 10018137" → `GET /products/directives/{identifier}`
- "Qual o preço de venda do 10080001?" → `GET /products/{code}/pricing` (**não** usar rotas de compra MP)

---

### Engenharia — LMP (`/engineering`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Listar / filtrar LMPs ou amostras | `GET /engineering/lmps` | `list_lmps` |
| Dashboard completo (legado / tabela) | `GET /engineering/lmps/dashboard` | `list_lmps_dashboard` |
| **Só KPIs** do dashboard LMP | `GET /engineering/lmps/dashboard/summary` | `get_lmps_dashboard_summary` |
| **Itens paginados** do dashboard | `GET /engineering/lmps/dashboard/items` | `list_lmps_dashboard_items` |
| **Gráficos** do dashboard LMP | `GET /engineering/lmps/dashboard/charts` | `get_lmps_dashboard_charts` |
| Detalhe de uma LMP por OV | `GET /engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` |
| Histórico AIJ010 (eventos) | `GET /engineering/lmps/{sale_number}/history/events` | `get_lmp_history_events` |
| Fluxo engenharia (idas/voltas) | `GET /engineering/lmps/{sale_number}/history/flow` | `get_lmp_history_flow` |
| Listar processos Transforma Mais | `GET /engineering/transforma-mais/processes` | `list_transforma_mais_processes` |
| Resumo Transforma Mais | `GET /engineering/transforma-mais/processes/summary` | `get_transforma_mais_summary` |

**Parâmetros úteis**

- Listagem / dashboard: `date_start`, `date_end`, `branch`, `listing_type` (`LMP`, `Amostra`, `Outro`), `status` (ex.: `Todos`), `page`, `page_size` (itens)
- Detalhe: `sale_number` = número da **ordem de venda (OV)** — não é código de produto; opcionalmente `date_start`, `date_end`, `branch` para alinhar ao painel/MFE `dashboard-lmps`
- Resposta do detalhe: `list_products[]` e **`list_history: []`** (histórico em rotas `/history/events` e `/history/flow`)
- Histórico: mesmos params do detalhe + opcional `revision`; `items[]` enriquecidos (`process_label`, `status_label`, `duration_display`, `is_open`, `is_current`, …); fluxo com `flow_transition*`
- Transforma Mais: `id`, `name_process`, `filial_id`, `sector_name`, `status`, `start_date`, `end_date`

**Exemplos**

- "Lista as LMPs da semana" → `GET /engineering/lmps`
- "KPIs do painel de LMP" → `GET /engineering/lmps/dashboard/summary`
- "Detalhe da LMP da OV 123456" → `GET /engineering/lmps/{sale_number}` (com `date_start`/`date_end`/`branch` se o usuário citou período ou filial)
- "Processos do Transforma Mais" → `GET /engineering/transforma-mais/processes`

**Atenção:** número de OV **não** é código de produto. Para dashboard LMP no chat, prefira `list_lmps` ou detalhe por OV; rotas `/dashboard/*` são otimizadas para o MFE `dashboard-lmps`. O MFE abre detalhe em `/apps/dashboard-lmps/ov/{sale_number}` consumindo a mesma rota `get_lmp_by_sale_number`.

---

### Suprimentos — indicadores (`/supplies`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| **Valor total** de estoque (KPI) | `GET /supplies/stock-value` | `get_supplies_stock_value` |
| Giro de estoque (IDD) | `GET /supplies/inventory-turnover` | `get_supplies_inventory_turnover` |
| CPV (custo produção vendido) | `GET /supplies/cpv` | `get_supplies_cpv` |
| OTD (entrega no prazo compras) | `GET /supplies/otd` | `get_supplies_otd` |
| Economia em negociações de compras (IDD / planilha) | `GET /supplies/negotiation-savings/summary` | `get_supplies_negotiation_savings_summary` |

**Parâmetros importantes (`/supplies/stock-value`)**

- **Sem** `start_date`/`end_date`: saldo atual (SB2010).
- **Com** `start_date` e `end_date`: estimativa histórica (SB9010 + SD3010); retorna bloco `estimation` quando aplicável.
- `location` filtra no modo histórico.
- `top_limit` para ranking de locais.

**Parâmetros (`/supplies/inventory-turnover`)**

- `branch`, `location`, `start_date`, `end_date`, `strict_idd_period` (bool)
- Estoque do IDD usa a mesma lógica de valor de estoque (atual vs histórico).

**Exemplos**

- "Qual o valor total de estoque da empresa?" → `GET /supplies/stock-value` (**não** `/products/{code}/stock`)
- "Estoque do produto X" → `GET /products/{code}/stock` (**não** `stock-value`)
- "Giro de estoque em 2024" → `GET /supplies/inventory-turnover` com período
- "Qual o CPV?" → `GET /supplies/cpv`
- "Economia em negociações de compras em maio/2026?" → `GET /supplies/negotiation-savings/summary` com `start_date` e `end_date` (por filial em `branches`; consolidado = soma das filiais)
- "Economia de negociação da matriz/filial 01" → mesma rota com `branch=01`

**Parâmetros (`/supplies/negotiation-savings/summary`)**

- `start_date`, `end_date` — referência mensal do IDD (planilha `economia_negociacoes_compra`)
- `branch` — opcional (`01` / `02`)
- Sem linhas no período: `total_savings` e totais por filial vêm `null` (não zero)

Detalhes do cálculo histórico: `api-delpi/docs/api/supplies-estoque-historico.md`.

---

### Vendas — ordens (`/sales`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Listar ordens de venda no período | `GET /sales/` | `list_sale_orders` |

**Parâmetros:** `date_start`, `date_end`, `page`, `page_size`

Não confundir com detalhe de LMP (`/engineering/lmps/{sale_number}`) nem vendas de um produto (`/products/{code}/sales`).

---

### Comercial — indicadores (`/commercial`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Taxa de conversão de vendas | `GET /commercial/closing-rate` | `get_sales_conversion_rate` |
| ROL — série temporal | `GET /commercial/rol/series` | `get_commercial_rol_series` |
| OTD de pedidos de venda | `GET /commercial/sales-order-otd` | `get_sales_order_otd` |
| Média de novos clientes | `GET /commercial/new-clients-average` | `get_new_clients_average` |
| % ROL de clientes novos | `GET /commercial/new-clients-rol-pct` | `get_new_clients_rol_pct` |
| % ROL de novos negócios | `GET /commercial/new-business-rol-pct` | `get_new_business_rol_pct` |
| Meta % ROL matriz | `GET /commercial/head_office_rol_target_pct` | path `head_office_rol` |
| Meta % ROL filial | `GET /commercial/branch_rol_target_pct` | path `branch_rol_target` |
| Propostas comerciais (listagem) | `GET /commercial/proposals` | path `commercial/proposals` |

**Parâmetros comuns:** `branch` (2 chars quando aplicável), `start_date`, `end_date`; `rol/series` exige `granularity` (`day`, `week`, `month`, `year`).

**ROL — qual rota usar**

| Pedido do usuário | Rota | Observação |
|-------------------|------|------------|
| «rol do mês de março», «qual o rol», KPI financeiro agregado | `GET /financial/rol` | Período via `start_date`/`end_date` |
| «série de rol», evolução temporal comercial / gráfico | `GET /commercial/rol/series` | Obrigatório `granularity` |
| Metas % ROL matriz/filial | `GET /commercial/head_office_rol_target_pct` / `branch_rol_target_pct` | Metas, não valor realizado |

---

### Financeiro (`/financial` e legado `/finacial`)

O router está montado **duas vezes** no serviço: prefira rotas com prefixo **`/financial`**. Existe legado **`/finacial`** (typo em `main.py`) — evite documentar ao usuário; no OpenAPI podem aparecer ambos.

| O usuário quer | Rota preferida | operationId (referência) |
|----------------|----------------|--------------------------|
| ROL | `GET /financial/rol` | `get_rol` |
| EBITDA % | `GET /financial/ebitda_pct` | `get_ebitda_pct` |
| Custo fixo % | `GET /financial/fixed_cost_pct` | `get_fixed_cost_pct` |
| PMR (prazo médio recebimento) | `GET /financial/pmr` | `get_pmr` |

**Parâmetros:** `branch`, `start_date`, `end_date` (conforme endpoint).

---

### Produção (`/production`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| OTD produção (%) | `GET /production/on_time_delivery_pct` | `get_on_time_delivery_pct` |
| **OTD produção — resumo e ordens** | `GET /production/otd` | `get_production_otd` |
| **Série temporal OTD produção** | `GET /production/otd/series` | `get_production_otd_series` |
| OEE (eficiência equipamentos) | `GET /production/overall_equipment_effectiveness_pct` | `get_overall_equipment_effectiveness_pct` |
| **OEE produção — resumo e apontamentos** | `GET /production/oee` | `get_production_oee` |
| **Detalhe apontamento OEE** | `GET /production/oee/appointments/{appointment_id}` | `get_production_oee_appointment_by_id` |
| **Série temporal OEE** | `GET /production/oee/series` | `get_production_oee_series` |
| **Eficiência fabril — dashboard** | `GET /production/eficiencia-fabril/dashboard` | `get_eficiencia_fabril_dashboard` |
| **Eficiência fabril — apontamentos** | `GET /production/eficiencia-fabril/appointments` | `list_eficiencia_fabril_appointments` |
| Custo direto mão de obra | `GET /production/direct_labor_cost_pct` | `get_direct_labor_cost_pct` |
| Custo de produção | `GET /production/production_cost_pct` | `get_production_cost_pct` |
| Depreciação % ROL | `GET /production/depreciation_pct` | `get_depreciation_pct` |

**Parâmetros (`GET /production/otd`)**

- `branch`, `start_date`, `end_date` — filtro de período (data prevista `C2_DATPRF`, formato ISO `YYYY-MM-DD`; API converte para Protheus `YYYYMMDD`).
- `status` — opcional: `on_time` (no prazo) ou `late` (atrasado).
- `page` (default `1`), `page_size` (default `20`, máx. `1000`).
- `sort_by`, `sort_dir` — ordenação server-side da listagem.

**Resposta:** `summary` (total OPs, no prazo, atrasadas, % OTD) + `orders` (listagem paginada com `status`, datas e produto).

**Parâmetros (`GET /production/oee`)**

- `branch`, `start_date`, `end_date` — filtro de período (`H6_DTPROD`, formato ISO `YYYY-MM-DD`).
- `status` — opcional: `valid` (OEE na faixa 0–199%) ou `outlier` (fora da faixa).
- `product_type` — opcional: `PA` ou `PI` (filtro `SB1010.B1_TIPO`).
- `work_center`, `production_order` — filtros opcionais.
- `page` (default `1`), `page_size` (default `20`, máx. `1000`).
- `sort_by`, `sort_dir` — ordenação server-side da listagem.

**Resposta:** `summary` (`oee_pct`, apontamentos válidos/fora da faixa) + `appointments` (view fabril: data, início/fim, OP, produto PA/PI, CT, operador, `oee_pct` = `EFICIENCIA_PERCENTUAL`, `status`, `appointment_id` via SH6010). Na UI do dashboard produção, listagem no padrão eficiência fabril (badge **Verificar** / **OK**).

**Parâmetros (`GET /production/oee/appointments/{appointment_id}`)**

- `appointment_id` (path) — `R_E_C_N_O_` do SH6010.
- `branch` — opcional; restringe a filial do apontamento.

**Resposta:** `appointment` (cadastro SH6010), `time_analysis` (setup, fator padrão, horas previstas/reais, `real_hours_source` = intervalo de horários ou tempo informado no apontamento, eficiência por tempos, **fórmulas em linguagem operacional** (`formula_planned`, `formula_real`, `formula_efficiency`), **`findings`** com alertas automáticos), `routing_operations` (roteiro SG2) e `structure` (BOM). Inclui `related_routes` para OP e produto.

**`time_analysis.findings` (diagnóstico canônico):** serviço `production_appointment_time_analysis` — exemplos: eficiência fora da faixa 0–199%, tempo previsto/real ausente, intervalo muito curto, roteiro sem fator padrão, fallback em tempo informado no apontamento. Severidade: `error` | `warning` | `info`. Eficiência medida **somente por tempos** (não usa `H6_ZEFICI`). Changelog: `api-delpi/docs/api/producao-eficiencia-changelog-jun2026.md`.

**Não confundir rotas:** `GET /production/oee` (painel + listagem, view fabril) e `GET /production/eficiencia-fabril/*` (dashboard MOD/gráficos no MFE) compartilham `EFICIENCIA_PERCENTUAL` e `build_fabril_view_filters` — não duplicar regras de CT/status/faixa. **Detalhe de apontamento** (roteiro, tempos, alertas): sempre `GET /production/oee/appointments/{appointment_id}` — usado pelo OEE e pela eficiência fabril ao clicar na linha.

**Faixa válida (OEE e eficiência fabril):** KPIs e gráficos consideram apenas eficiência entre **0% e 199%** (outliers permanecem listáveis). Ver `api-delpi/docs/api/regras-faixa-eficiencia-producao.md`.

**Parâmetros (`GET /production/eficiencia-fabril/*`)**

- `date_start`, `date_end` — período obrigatório (`YYYY-MM-DD`).
- `branch`, `op`, `employee`, `work_center` — filtros opcionais.
- Dashboard (`get_eficiencia_fabril_dashboard`): `page`, `page_size`, `status_ok_only` (default `true`).
- Appointments bulk (`list_eficiencia_fabril_appointments`): `status_ok_only` (default `false` na API; MFE usa `false` na carga).

**Resposta (dashboard):** `summary` (eficiência média na faixa 0–199%, MOD, horas) + `charts` + `items` paginados com **`appointment_id`** (vínculo SH6010). Apontamentos fora da faixa aparecem na listagem do MFE como **Verificar**. Clique na linha → detalhe via `GET /production/oee/appointments/{appointment_id}` (mesmo contrato do painel OEE, incluindo `time_analysis.findings` e estrutura em árvore).

**UI do MFE (eficiência fabril):** filtros automáticos (período preservado, debounce em OP/operador/CT), turno com multiseleção, tabela com ordenação por coluna e exportação Excel dos dados filtrados/ordenados em memória.

#### Playbook 15 — operacional sem SQL (consumo, OPs, perdas, suprimentos)

Preferir estas rotas em vez de `POST /data/sql` quando o agente tiver a action habilitada:

| O usuário quer | Rota | operationId |
|----------------|------|-------------|
| Itens mais consumidos (geral) | `GET /production/consumption/top-items` | `get_production_consumption_top_items` |
| Consumo por centro de trabalho | `GET /production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` |
| Consumo validado por apontamento | `GET /production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` |
| Consumo real de um item | `GET /production/consumption/by-item/{code}` | `get_production_consumption_by_item` |
| Refugos / perdas por MP (ranking) | `GET /production/losses/top-materials` | `get_production_losses_top_materials` |
| Registros detalhados de refugo | `GET /production/losses/records` | `get_production_losses_records` |
| OPs em aberto na data | `GET /production/orders/open` | `get_production_orders_open` |
| OPs finalizadas na data | `GET /production/orders/finished` | `get_production_orders_finished` |
| OPs finalizadas sem baixa de MP | `GET /production/orders/finished-without-consumption` | `get_production_orders_finished_without_consumption` |
| Resumo de OPs por centro de trabalho | `GET /production/work-centers/order-summary` | `get_production_work_center_order_summary` |
| Tempo médio planejado por CT | `GET /production/work-centers/average-planned-time` | `get_production_work_center_average_planned_time` |
| Componentes sem empenho (travamento) | `GET /production/allocation-gaps` | `get_production_allocation_gaps` |
| Planejado × real por OP | `GET /production/planned-vs-real-time` | `get_production_planned_vs_real_time` |
| Programação / OPs do dia | `GET /production/schedule/today` | `get_production_schedule_today` |
| Produtos mais comprados (ranking) | `GET /purchases/top-products` | `get_purchases_top_products` |

**Parâmetros comuns:** `date_start`, `date_end`, `reference_date`, `branch`, `limit`, `code` (path em by-item).

**Não confundir:** `/purchases/top-products` (ranking global) ≠ `/products/{code}/purchases` (histórico de um produto).

**Frases exemplo (RAG / agente):**

| Intenção | Exemplos naturais |
|----------|-------------------|
| Consumo ranking | «itens mais consumidos mês passado», «top consumo MP filial 01» |
| Compras ranking | «produtos mais comprados março», «ranking de compras» |
| Refugo ranking | «refugos matéria-prima março top 10», «scrap MP filial 02» |
| Refugo detalhe | «listar refugos detalhado», «registros de perda no período» |
| Programação hoje | «quais produtos serão produzidos hoje?», «cronograma produção hoje» |
| OPs abertas | «liste OPs em aberto hoje filial 01», «backlog produção» |
| OPs finalizadas | «quais OPs finalizadas hoje?» |
| Resumo por CT | «resumo de OPs por centro de trabalho hoje» |
| Consumo por CT | «maior consumo por centro de trabalho mês passado» |
| Consumo validado | «consumo validado por apontamento top 10» |
| Sem empenho | «componentes sem empenho hoje», «travamento por falta de empenho» |
| OP sem consumo | «OPs finalizadas sem consumo hoje» |
| Tempo planejado CT | «tempo médio planejado por CT hoje» |
| Consumo item | «consumo real do item 01010001» |
| Planejado × real | «compare tempo planejado e tempo real das OPs hoje» |

Vocabulário canônico: `production_operational_intent.json` · RAG: `capabilities.json` (`pathRules`, `commonExamples`, `richExamples.productionOperational`).

### RH (`/hr`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Listar filiais (Portal RH) | `GET /hr/branches` | path `hr/branches` |
| Snapshot RH (headcount, turnover, PDI, avaliações) | `GET /hr/snapshot` | `get_hr_snapshot` |
| PDIs ativos (detalhe) | `GET /hr/active-pdi-count` | path `active-pdi-count` |
| Avaliações de desempenho | `GET /hr/performance-reviews-completion` | path `performance-reviews` |

**Parâmetros:** `branch`, `start_date`, `end_date` (datas normalizadas Portal RH).

---

### Qualidade — métricas TOTVS (`/quality`)

Consultas analíticas no Protheus; **não** confundir com módulo NC em PostgreSQL.

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Filiais disponíveis | `GET /quality/branches` | path `quality/branches` |
| Listar não conformidades | `GET /quality/nonconformities` | path `nonconformities` |
| Série temporal de NC | `GET /quality/nonconformities/series` | path `nonconformities/series` |
| PPM interno — resumo | `GET /quality/ppm/internal/summary` | path `ppm/internal/summary` |
| PPM externo — resumo | `GET /quality/ppm/external/summary` | path `ppm/external/summary` |
| PPM interno — detalhado | `GET /quality/ppm/internal` | path `ppm/internal` |
| PPM externo — detalhado | `GET /quality/ppm/external` | path `ppm/external` |
| Série PPM interno | `GET /quality/ppm/internal/series` | path `ppm/internal/series` |
| Série PPM externo | `GET /quality/ppm/external/series` | path `ppm/external/series` |
| Auditoria 5S — resumo | `GET /quality/audit-5s/summary` | path `audit-5s/summary` |
| Kaizens — resumo | `GET /quality/kaizens/summary` | `get_kaizen_summary` |
| Kaizen — detalhe | `GET /quality/kaizens/{kaizen_id}` | `get_kaizen_by_id` |

**Kaizen — resumo vs. detalhe**

- Resumo do período (KPIs, `total_savings`, `list_kaizen` filtrada por data): `GET /quality/kaizens/summary` com `date_start`/`date_end`.
- Catálogo completo (sem filtro de data na listagem): mesma rota **sem** `date_start`/`date_end`.
- Ficha de um kaizen (investimento, economia/dia, economia/ano, parâmetros do cálculo): `GET /quality/kaizens/{kaizen_id}` — `kaizen_id` = campo `id` de `list_kaizen[]` (ex.: `01-16/01/2026-App resina CT-16`).

**Parâmetros (`/quality/nonconformities`)**

- `type`: `internal`, `external` ou `all`
- `branch`, `date_start`, `date_end`, `status`, `item_code`, `description`, `page`, `page_size`

**Rotas antigas (não usar)**

- `GET /quality/ppm/internal` como único resumo — preferir `/summary` e `/series`
- `GET /quality/nonconformities` sem sufixo era genérico; manter `type` explícito

---

### Dados — SQL (`/data`)

| O usuário quer | Rota | operationId (referência) |
|----------------|------|--------------------------|
| Executar SELECT / consulta analítica | `POST /data/sql` | `execute_readonly_sql` |

**Corpo:** JSON `{ "sql": "SELECT ..." }` ou `text/plain` com a query. Somente leitura (SELECT, CTE). Permissão: `api-delpi.data` ou `api-delpi.access.full`.

---

### Sistema — metadados Protheus (`/system`)

| O usuário quer | Rota | Notas |
|----------------|------|--------|
| Buscar tabelas por descrição | `GET /system/tables/search` | `description` (mín. 2 chars), `page`, `limit` |
| Metadados de uma tabela | `GET /system/tables/{tableName}` | SX2 |
| Colunas da tabela (paginado) | `GET /system/tables/{tableName}/columns` | `page`, `limit` |
| Buscar colunas dentro da tabela | `GET /system/tables/{tableName}/columns/search` | query `q` (mín. 2 chars) |
| Índices da tabela | `GET /system/tables/{tableName}/indexes` | SIX |
| Relacionamentos | `GET /system/tables/{tableName}/relations` | SX9 |
| Schema agregado completo | `GET /system/tables/{tableName}/schema` | SX2+SX3+SIX+SX9 |
| Busca global de colunas | `GET /system/columns/search` | `description`, `page`, `limit` |

Permissão: `api-delpi.access.full` ou `api-delpi.system`.

---

## Erros e respostas

| HTTP | Significado para o usuário |
|------|----------------------------|
| 200-299 | Sucesso — use `humanizedSummary` ou resposta direta do pipeline |
| 401 / 403 | Sem permissão para esta rota |
| 404 | Produto, OV ou recurso não encontrado |
| 422 | Parâmetro faltando ou inválido (código, datas, página) |
| 503 | Dependência indisponível (ex.: Portal RH em rotas `/hr`) |

Não pergunte se o usuário "tem permissão"; a API já valida com o token dele.

---

## Vocabulário (sinônimos)

| Domínio | Termos |
|---------|--------|
| Produto | produto, item, código, referência, ref, SKU, material, MP, insumo |
| Estoque item | estoque, saldo, disponível, quantidade, posição, armazém |
| Estrutura/BOM | estrutura, componentes, composição, bill of materials, BOM |
| Onde é usado | onde é usado, produto pai, parent, where used, utilizado em, pai do |
| Preço | preço, pricing, tabela de preço, quanto custa, custo |
| Notas | nota de entrada, nota de saída, NF-e, invoice, inbound, outbound |
| LMP | LMP, lista de materiais de projeto, amostra, ordem de venda, OV |
| OV | ordens de venda, pedidos de venda, OV, sale_number |
| Transforma Mais | transforma mais, processo de melhoria, engenharia |
| SQL | SQL, consulta, SELECT, query, dados, Protheus |
| KPI estoque | valor total de estoque, valor em estoque, indicador suprimentos, stock-value |
| KPI comercial | closing rate, conversão, ROL, OTD pedido, novos clientes, novos negócios |
| KPI financeiro | EBITDA, PMR, custo fixo, ROL |
| KPI produção | OTD produção, OTD produção (listagem OPs), série OTD, OEE (%), OEE produção (listagem apontamentos), série OEE, custo de produção, mão de obra, depreciação |
| Qualidade | não conformidade, NC, PPM, kaizen, 5S, auditoria |

---

## Checklist do administrador

1. Provider `api-delpi` com `authMode: user_token` e `openApiUrl` apontando para o gateway.
2. Agente com `allowRead` e actions de leitura/SQL habilitadas.
3. **Reimport OpenAPI** após deploy: `PYTHONPATH=/app python scripts/sync_api_delpi_openapi.py` (ou `POST .../providers/api-delpi/import` no admin).
4. Anexar **este documento** à base de conhecimento do agente (tags: `api-delpi`, `operacional`, `rotas`) **ou** referenciar no `system_prompt`.
5. Testar: estoque de código, OV de LMP, valor total de estoque com e sem período, PPM interno resumo, ROL financeiro do mês, listagem paginada com «traga tudo», SELECT simples.

---

## Referências técnicas

- Metadados OpenAPI (rotas com `summary`/`description` PT): `api-delpi/app/interface/http/openapi_agent_metadata.py`
- Documentação humana por módulo: `api-delpi/docs/api/06-modulos-departamentais.md`, `api-delpi/docs/api/02-produtos.md`, `api-delpi/docs/api/04-sistema-e-dados.md`
- Guia resumido: `api-delpi/docs/api/11-guia-agente-chat.md`
- Estoque histórico suprimentos: `api-delpi/docs/api/supplies-estoque-historico.md`
- Actions no chat: `minha-delpi-ai-api/docs/api/04-actions-openapi.md`
