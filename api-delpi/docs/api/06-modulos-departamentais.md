# 06 — Módulos departamentais

Métricas e consultas analíticas por área, alimentadas principalmente pelo **TOTVS Protheus**.

**Permissão padrão:** `api-delpi.access` (exceto engenharia e qualidade, indicados abaixo).

**Formato:** envelope `{ success, message, data }`.

Parâmetros comuns de período:

| Parâmetro | Descrição |
|---|---|
| `branch` | Filial (2 caracteres quando validado). |
| `start_date` / `end_date` | Intervalo de análise. |

---

## Financeiro

> **Atenção — montagem dupla:** em `main.py` o mesmo router é incluído com `prefix="/financial"` e `prefix="/finacial"` (typo legado).  
> **URLs efetivas (equivalentes):** `/financial/rol` e `/finacial/rol` — prefira `/financial/*` em novas integrações.

| Método | Rota (preferida) | Descrição |
|---|---|---|
| GET | `/financial/rol` | Receita Operacional Líquida (ROL). |
| GET | `/financial/ebitda_pct` | EBITDA % (planilha; filial vazia = consolidado). |
| GET | `/financial/fixed_cost_pct` | Custos fixos % (planilha; filial vazia = consolidado). |
| GET | `/financial/pmr` | Prazo médio de recebimento. |

---

## Comercial — `/commercial`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/commercial/head_office_rol_target_pct` | Meta % ROL matriz (filial fixa `01`). |
| GET | `/commercial/branch_rol_target_pct` | Meta % ROL filial (filial fixa `02`). |
| GET | `/commercial/closing-rate` | Taxa de conversão de vendas. Ver [comercial-taxa-conversao-estagios.md](./comercial-taxa-conversao-estagios.md). |
| GET | `/commercial/sales-order-otd` | OTD de pedidos de venda (linhas SC6 entregues no prazo). |
| GET | `/commercial/new-business-rol-pct` | % ROL de novos negócios (exclui clientes WEG). |
| GET | `/commercial/new-clients-average` | Média mensal de novos clientes. |
| GET | `/commercial/new-clients-rol-pct` | % do ROL de clientes novos. |
| GET | `/commercial/rol/series` | Série temporal de ROL (`granularity`: day, week, month, year). |
| GET | `/commercial/proposals` | Listagem paginada de propostas (OV). Filtros: `start_date`, `end_date`, `branch`, `status` (`won`/`open`), `customer_segment` (`weg`/`new_business`), `page`, `page_size`, `sort_by`, `sort_dir`, `search`. Ver `plugins/dashboard-commercial/docs/PROPOSTAS-PERIODO.md`. |
| GET | `/commercial/proposals/{proposal_number}` | Detalhe da proposta (AD1010 + cliente/vendedor + **`list_products[]`** ADJ010). Query: `branch` (obrig.), `revision` opcional. Produtos via `LMPQueryRepository.list_ov_products` (SQL compartilhado com LMP). |
| GET | `/commercial/proposals/{proposal_number}/history/events` | Histórico AIJ010 da OV — mesmo pipeline que LMP (`get_lmp_history_events`). Query: `branch`, `revision`, `date_start`, `date_end` (período aceito pelo MFE; **não** dispara batch de listagem). |

**MFE `dashboard-commercial`:** detalhe em `/apps/dashboard-commercial/proposta/{proposal_number}` consome **`GET /commercial/proposals/{proposal_number}`** + **`/history/events`** em paralelo (`useCommercialProposalDetail`). Estrutura BOM por produto: **`GET /products/{code}/structure`** (`useCommercialProductStructures`). Documentação: `plugins/dashboard-commercial/docs/DETALHE-PROPOSTA.md`.

**Performance (`/commercial/.../history/events`):** ver § Engenharia — histórico (`/history/events`); custo O(eventos da OV), não varredura `AllListingAnchorRaw`.

**Performance (séries e ROL — jun/2026):**

- `GET /commercial/rol/series`: cache da resposta completa (`commercial-rol-series|…`) + cache por bucket em `FinancialRepository.get_rol` (`financial-rol|…`). TTL: `QUERY_CACHE_TTL_SECONDS` (default 300 s). Beneficia também KPIs que reutilizam `get_rol` (CPV, custos %, etc.).
- SQL ROL: leitura com `WITH (NOLOCK)` em SD2/SA1/SF4/SD1. Console: `operation_id=get_commercial_rol_series`; validar hit rate na aba **Cache** em polling de dashboard (30 s).

---

## RH — `/hr`

**Permissão:** `api-delpi.access` **ou** `dashboard-hr.view`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/hr/branches` | Filiais disponíveis no Portal RH. |
| GET | `/hr/snapshot` | Snapshot agregado (headcount, turnover, PDI, avaliações). |
| GET | `/hr/active-pdi-count` | Contagem/detalhe de PDIs ativos. |
| GET | `/hr/performance-reviews-completion` | Conclusão de avaliações de desempenho. |

Parâmetros comuns: `branch`, `start_date`, `end_date` (normalização de datas Portal RH).

---

## Produção — `/production`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/production/direct_labor_cost_pct` | Custo de mão de obra direta % ROL. |
| GET | `/production/production_cost_pct` | Custo de produção % ROL. |
| GET | `/production/depreciation_pct` | Depreciação % ROL. |
| GET | `/production/overall_equipment_effectiveness_pct` | OEE (%) — média agregada de `EFICIENCIA_PERCENTUAL` (tempo previsto ÷ tempo real). |
| GET | `/production/oee` | OEE produção — resumo, listagem paginada de apontamentos (view fabril), filtros `status` (`valid` / `outlier`) e `product_type` (`PA` / `PI`). |
| GET | `/production/oee/appointments/{appointment_id}` | Detalhe do apontamento — roteiro (SG2), estrutura (BOM), análise de tempos e **`time_analysis.findings`** (alertas automáticos). |
| GET | `/production/oee/series` | Série temporal de OEE por filial. |
| GET | `/production/eficiencia-fabril/dashboard` | Dashboard eficiência fabril (agregado SQL + paginação; `items[].appointment_id`). |
| GET | `/production/eficiencia-fabril/appointments` | Apontamentos eficiência fabril (carga bulk; `appointment_id` para detalhe). |

**Performance (`/production/eficiencia-fabril/appointments`):**

- SQL: CTE `H6_RANKED` (uma varredura em SH6010 por período) + join na view — evita `OUTER APPLY` correlacionado em bulk.
- Cache: resposta completa em `query_cache` (namespace `eficiencia-fabril-appointments`, TTL `QUERY_CACHE_TTL_SECONDS`, default 300 s).
- Console: `operation_id=list_eficiencia_fabril_appointments`; caller `eficiencia-fabril` — após o primeiro load do período, recargas devem ser cache hit (&lt; 500 ms).
| GET | `/production/on_time_delivery_pct` | OTD produção (%) — apenas OPs de PA (`SB1010.B1_TIPO = 'PA'`). |
| GET | `/production/otd` | OTD produção — resumo, listagem paginada de OPs de PA e filtro `status` (`on_time` / `late`). |
| GET | `/production/otd/series` | Série temporal de OTD por filial. |

**Faixa válida de eficiência (OEE e eficiência fabril):** 0–199% — ver [regras-faixa-eficiencia-producao.md](./regras-faixa-eficiencia-producao.md). Changelog jun/2026 (tempos, fórmulas, auto-refresh): [producao-eficiencia-changelog-jun2026.md](./producao-eficiencia-changelog-jun2026.md).

**Listagem OEE (`GET /production/oee`):** mesma view e filtros da eficiência fabril (`build_fabril_view_filters`); `oee_pct` na listagem = `EFICIENCIA_PERCENTUAL` (tempo previsto ÷ tempo real); `appointment_id` via `production_fabril_sh6010_apply` para detalhe.

**Detalhe (`GET /production/oee/appointments/{id}`):** `oee_pct` e `time_analysis.efficiency_from_times_pct` calculados por tempos (roteiro SG2/SHY + horários); diagnóstico em `time_analysis.findings` via `production_appointment_time_analysis`.

**Performance (KPI e séries OEE/OTD — jun/2026):**

- `GET /production/overall_equipment_effectiveness_pct`: KPI por filial via query agrupada + `NOLOCK` (`production_fabril_oee_kpi_sql.py`); cache `production-oee` e `production-oee-by-branch`. Changelog: [producao-eficiencia-changelog-jun2026.md](./producao-eficiencia-changelog-jun2026.md) §7.
- `GET /production/oee/series` e `GET /production/otd/series`: cache da resposta completa (`production-oee-series|…`, `production-otd-series|…`) + cache por filial/período nos repositórios (`production-oee|…`, `production-otd|…`, `production-oee-by-branch|…`). TTL: `QUERY_CACHE_TTL_SECONDS` (default 300 s).
- OTD: `WITH (NOLOCK)` em SC2/SB1. Console: `get_production_oee_series` / `get_production_otd_series` — após primeiro carregamento, polling do dashboard deve gerar hits na aba **Cache**.

**Rotas operacionais (Playbook 15):** consumo, OPs, perdas, programação — ver [13-producao-operacional.md](./13-producao-operacional.md).  
**Compras ranking:** `GET /purchases/top-products` — mesma doc.

---

## Suprimentos — `/supplies`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/supplies/cpv` | Custo de produto vendido (top fornecedores). |
| GET | `/supplies/otd` | On-Time Delivery compras. |

**Performance (`/supplies/otd`):**

- Use case: summary derivado do `monthly_breakdown` (uma varredura em `VW_PONTUALIDADE_FORNECEDORES_MENSAL` em vez de duas).
- Views com `WITH (NOLOCK)` (leitura analítica).
- Cache: resposta completa em `query_cache` (namespace `supplies-otd`, TTL `QUERY_CACHE_TTL_SECONDS`, default 300 s).
- Console: `operation_id=get_supplies_otd`; caller `strategic-indicators-api` — após o primeiro load do período, polling deve gerar cache hit (&lt; 500 ms).

| GET | `/supplies/stock-value` | Valor total de estoque (atual, histórico estimado SB9+SD3 ou fechamento SB9 na `end_date`). Parâmetro `stock_method=auto|estimated|official_closure`. Ver [supplies-estoque-historico.md](./supplies-estoque-historico.md). Reconciliação: [playbook](../roadmaps/playbook-correcao-estoque-supplies-inventario.md). |
| GET | `/supplies/inventory-turnover` | Giro de estoque (IDD). Herda `stock_method=auto` e expõe `stock_estimation` quando o período é histórico. |
| GET | `/supplies/negotiation-savings/summary` | Economia em negociações de compras (Google Sheets `idd_suprimentos`). |

Parâmetros adicionais:

| Rota | Parâmetro extra |
|---|---|
| `/cpv`, `/otd` | `top_limit` (default `5`, máx. `20`) |
| `/otd` | `details_limit` (default `20`, máx. `100`) |
| `/stock-value` | `start_date`, `end_date` (histórico; ambos obrigatórios juntos), `location`, `top_limit`, `summary_only`, `stock_method` (`auto` default, `estimated`, `official_closure`) |
| `/inventory-turnover` | `location`, `strict_idd_period` (bool); estoque via mesmo `stock_method=auto` internamente |

**Performance (`/supplies/stock-value` histórico):**

- SQL canônico histórico: `stock_value_historical_sql.py`; fechamento oficial: `stock_value_official_closure_sql.py`.
- SI/IDD: `summary_only=true` + `stock_method=auto`.
- Cache: `query_cache` namespace `stock-value|…` (inclui `stock_method` na chave).
- `summary_only=true`: rollup `item_totals` (sem `estoque_item`); consolidado sem filial → fan-out filiais `01`/`02` com cache por filial.
- SQL histórico: `WITH (NOLOCK)` em SB9010 e SD3010 (leitura analítica).
- Console: `operation_id=get_supplies_stock_value`; detalhes em [supplies-estoque-historico.md](./supplies-estoque-historico.md#implementação-sql-e-performance-jun2026).
- MFE dashboard KPI: `summary_only=true` via `getStockValueSummary` (não carrega bundle completo).

---

## Engenharia — `/engineering`

**Permissão:** `api-delpi.access` **ou** `dashboard-lmps.view`

### LMP (Lista de Materiais de Projeto / ordens especiais)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/engineering/lmps` | Lista LMPs com filtros de data/filial. |
| GET | `/engineering/lmps/dashboard` | Dashboard agregado (`status` default `Todos`). Dados completos com items paginados. |
| GET | `/engineering/lmps/dashboard/summary` | Apenas KPIs (`total_lmps`, `total_items`, `percent_dentro_prazo`, `avg_lead_time`). Query leve (`eng_resumo_lite`, sem `ORDER BY`). Fase 1 do carregamento progressivo. |
| GET | `/engineering/lmps/dashboard/items` | Itens paginados do dashboard (tabela). |
| GET | `/engineering/lmps/dashboard/charts` | Dados de gráficos (levelData, statusData, leadByLevel, evolutionData). Fase 2 do carregamento progressivo. |
| GET | `/engineering/lmps/{sale_number}` | Detalhe por número de venda/ordem (OV). Cabeçalho, produtos, KPIs — **sem** histórico AIJ010 (lista vazia). Mesmo escopo do dashboard com `date_start`, `date_end` e `branch`. |
| GET | `/engineering/lmps/{sale_number}/history/events` | Eventos AIJ010 da OV (query lite). Timeline/tabela do MFE. |
| GET | `/engineering/lmps/{sale_number}/history/flow` | Transições de engenharia (entradas, avanços, retornos) com LEAD/LAG apenas nos eventos técnicos. |

**MFE `dashboard-lmps`:** tabela via `/dashboard/items` (ou carregamento progressivo legado `/dashboard`); clique na linha abre `/apps/dashboard-lmps/ov/{sale_number}`, que consome **`GET /engineering/lmps/{sale_number}`** + **`/history/events`** + **`/history/flow`** em paralelo (histórico montado no hook `useLmpDetail`).

| Query (detalhe e histórico) | Descrição |
|---|---|
| `date_start`, `date_end` | Período — alinha candidatos ao **detalhe** (`GET …/{sale_number}`) e listagem. Em **`/history/*`**, aceitos pelo MFE mas **não** alteram o SQL do contexto do painel (jun/2026). |
| `branch` | Filial — recomendado quando a OV existe em mais de uma filial. |
| `revision` | *(apenas `/history/*`)* Filtra uma revisão específica da OV; também define `reference_revision` quando informado. |

| Resposta `meta.relatedRoutes` (detalhe e histórico) | Descrição |
|---|---|
| `detail` | Esta OV (`/engineering/lmps/{sale_number}`). |
| `historyEvents` | Eventos AIJ010 (`/history/events`). |
| `historyFlow` | Fluxo engenharia (`/history/flow`). |
| `dashboardItems`, `dashboardSummary`, `dashboardCharts` | Rotas agregadas do painel. |
| `list` | Listagem paginada `/engineering/lmps`. |

**Resposta `data` (detalhe):** campos de classificação da listagem (`nivel`, `status`, `lead_time_util`, …), `list_products[]` e **`list_history: []`** (histórico em rotas dedicadas).

**`start_date` e lead time (dashboard com período):** `start_date`/`end_date` vêm do evento **âncora** da listagem (`ANCHOR_START_DATE`), não da primeira linha AIJ010 da OV. `lead_time_util` = dias úteis entre essas datas (`LMPBusinessRules`). `FIRST_ENG_DATE` (`OvFirstEngineeringArrival`) entra só no filtro OR de inclusão no período — usar como `start_date` inflava `avg_lead_time` em OVs reentrantes. Regressão SQL: `tests/test_lmp_query_repository_sql.py` (`test_header_lmp_uses_listing_anchor_start_with_period`, `test_candidate_period_filter_or_first_engineering_arrival`).

**Resposta `data` (`/history/events` e `/history/flow`):** `sale_number`, `branch`, `reference_revision`, `panel_start_date`, `items[]`, `total`.

**Contexto do painel (jun/2026):** `GetLmpHistoryEventsUseCase` e `GetLmpHistoryFlowUseCase` chamam `get_lmp_history_panel_context` — query **lite** em **AD1010** (`TOP 1` por filial + OV + revisão opcional). **Não** reutiliza `_sql_header_lmp` nem CTEs `AllListingAnchorRaw` (evita varredura global em AIJ010 quando o MFE envia `date_start`/`date_end`).

| Campo de contexto | Origem (lite) |
|---|---|
| `reference_revision` | `AD1_REVISA` da revisão solicitada ou última revisão da OV |
| `panel_start_date` | `AD1_DATA` (abertura da proposta) |
| `branch` | `AD1_FILIAL` |

O **detalhe** (`GET …/{sale_number}`) continua usando `_sql_header_lmp` com escopo de período quando aplicável. Só o contexto do histórico foi desacoplado.

**Enriquecimento de `items[]` em `/history/events`:** `GetLmpHistoryEventsUseCase` + `enrich_history_events()` (`lmp_history_event_enrichment.py`). SQL lite em AIJ010 (`AIJ_NROPOR = ?`); rótulos AC1010/AC2010 via lookup em cache por par processo+estágio.

**Performance (`/history/events`, `/history/flow`, `/commercial/.../history/events`):** 1× AD1010 + 1× AIJ010 por OV + lookups de rótulo — custo O(eventos da OV). Alerta `slow_sql` com preview `AllListingAnchorRaw` nessas rotas indica regressão (contexto voltou a usar `_sql_header_lmp`). Regressão SQL: `tests/test_lmp_query_repository_sql.py` (`test_history_panel_context_lite_*`).

**Enriquecimento de `items[]` em `/history/flow`:** `GetLmpHistoryFlowUseCase` + `enrich_flow_transition_fields()` (`lmp_history_flow_transition.py`) — `flow_transition`, `flow_transition_label`, `is_engineering_entry`, etc.

| Campo derivado (eventos) | Descrição |
|---|---|
| `process_label`, `stage_label` | AC1010/AC2010 (lookup) ou fallback em `lmp_process_stage_labels.py` |
| `status_label` | Mapeamento `AIJ_STATUS` 1–9; encerrado quando `DTENCE` preenchido |
| `duration_display` | Texto legível (ex.: «Em andamento · N dia(s)») |
| `is_open`, `is_late`, `is_current` | Situação do evento (`is_current` vs. `reference_revision` do painel) |
| `is_engineering_flow` | Badge Engenharia na UI |
| `flow_transition*` | Apenas em `/history/flow` (idas/voltas/avanços) |

> **Carregamento progressivo:** o frontend chama `/summary` → `/charts` → `/items` (ou `/dashboard` legado). A página renderiza KPIs/gráficos antes da tabela; detalhe da OV é rota separada acima.

| Query (listagem) | Descrição |
|---|---|
| `date_start`, `date_end` | Período. |
| `branch` | Filial. |
| `listing_type` | `Todos` (default), `LMP`, `Amostra` ou `Outro`. Com `LMP`, a SQL omite OVs «Outro» sem âncora de listagem (`EngSupportOvRef`). |
| `status` | Filtro de status do dashboard (`Todos`, `Pontual`, `Atrasado`, …). |
| `page`, `page_size` | Paginação (apenas `/dashboard` e `/items`). |

**Performance (`/dashboard/summary`, `/dashboard/charts`, `/dashboard/items`):**

- Repositório: batch com temp tables, `eng_resumo_lite=True`, sem ordenação final.
- Integradores que só precisam de KPI de LMP (ex.: Strategic Indicators) devem enviar `listing_type=lmp`.
- Cache: `query_cache` (namespace `lmp-dashboard`, TTL `QUERY_CACHE_TTL_SECONDS`, default 300s):
  - `|summary-rows|pi1` — linhas enriquecidas compartilhadas entre summary, charts e items (formato `{"rows": [...]}`).
  - `|summary-response` e `|charts-response` — respostas finais por filtro de status.
- Console: `operation_id=get_lmps_dashboard_charts` / `get_lmps_dashboard_summary`; alerta `slow_sql` acima de 2500 ms — após o primeiro carregamento do período, chamadas subsequentes devem ser cache hit (&lt; 500 ms).

### Transforma Mais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/engineering/transforma-mais/processes` | Lista processos de melhoria. |
| GET | `/engineering/transforma-mais/processes/summary` | Resumo agregado. |

Filtros de processos: `id`, `name_process`, `filial_id`, `sector_name`, `status`, `start_date`, `end_date`.

---

## Qualidade (métricas TOTVS) — `/quality`

**Permissão:** `api-delpi.quality.access` **ou** `dashboard-quality.view`

Consultas analíticas (TOTVS Protheus e Google Sheets).

| Método | Rota | Descrição |
|---|---|---|
| GET | `/quality/branches` | Filiais disponíveis para filtros. |
| GET | `/quality/nonconformities` | Lista NC do Protheus. |
| GET | `/quality/nonconformities/series` | Série temporal de NC. |
| GET | `/quality/kaizens/summary` | Resumo de kaizens (Google Sheets). |
| GET | `/quality/kaizens/{kaizen_id}` | Detalhe de um kaizen na planilha (`{kaizen_id:path}`). |
| GET | `/quality/kaizens/records` | Lista cadastro operacional (PostgreSQL). |
| POST | `/quality/kaizens/records` | Cria kaizen no PostgreSQL. |
| GET | `/quality/kaizens/records/{id}` | Detalhe cadastro (UUID). |
| PUT | `/quality/kaizens/records/{id}` | Atualiza cadastro. |
| DELETE | `/quality/kaizens/records/{id}` | Exclusão lógica do cadastro. |
| POST | `/quality/kaizens/records/import-from-sheet` | Importa linhas ativas da planilha para PostgreSQL. |
| GET | `/quality/audit-5s/summary` | Resumo auditorias 5S. |
| GET | `/quality/ppm/internal/summary` | PPM interno (resumo). |
| GET | `/quality/ppm/external/summary` | PPM externo (resumo). |
| GET | `/quality/ppm/internal/series` | Série PPM interno. |
| GET | `/quality/ppm/external/series` | Série PPM externo. |
| GET | `/quality/ppm/internal` | PPM interno (detalhado). |
| GET | `/quality/ppm/external` | PPM externo (detalhado). |

**Performance (PPM — jun/2026):**

- `GET /quality/ppm/{internal|external}/summary`: cache `ppm-summary|{type}|…` por período/filial (TTL `QUERY_CACHE_TTL_SECONDS`, default 300 s).
- `GET /quality/ppm/{internal|external}/series`: cache da série completa (`ppm-internal-series|…`, `ppm-external-series|…`); buckets reutilizam `ppm-summary`.
- SQL: `QI2010` com `WITH (NOLOCK)` em leituras analíticas.
- MFE `PpmPage`: carrega série interna ou externa sob demanda (modo comparar busca ambas). Console: `get_ppm_external_series` / `get_ppm_internal_series`.

---

## Inspeções de entrada — `/inspecoes-entrada`

**Permissão:** `inspecoes-entrada.view`, `inspecoes-entrada.view.filial-01`, `inspecoes-entrada.view.filial-02` ou `api-delpi.access`

Painel operacional de inspeção de recebimento (views TOTVS). Plugin: `inspecoes-entrada`.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/inspecoes-entrada/resumo` | KPIs por filial (pendentes, taxa aprovação, tempo médio). |
| GET | `/inspecoes-entrada/pendentes` | Listagem paginada aguardando laudo. |
| GET | `/inspecoes-entrada/pendentes-fornecedor` | Ranking fornecedor × pendências. |
| GET | `/inspecoes-entrada/rejeitadas-ensaiador` | Rejeições agrupadas por ensaiador. |
| GET | `/inspecoes-entrada/rejeitadas-produto` | Rejeições recentes por produto. |
| GET | `/inspecoes-entrada/historico` | Histórico laudado com filtros. |
| GET | `/inspecoes-entrada/historico/detalhe` | Cabeçalho + ensaios (QER). |

Parâmetro comum: `branch` (`01` \| `02`). Escopo por filial validado no router.

Documentação completa: [inspecoes-entrada.md](./inspecoes-entrada.md) · views: [ESPECIFICACAO-VIEW.md](../../../docs/12-roadmap-e-evolucao/inspecoes-entrada/ESPECIFICACAO-VIEW.md).

### GET /quality/nonconformities

| Query | Descrição |
|---|---|
| `type` | `internal`, `external` ou `all` (default). |
| `branch`, `date_start`, `date_end` | Filtros. |
| `status`, `item_code`, `description` | Filtros adicionais. |
| `page`, `page_size` | Paginação. |

### GET /quality/kaizens/summary

**Fonte:** Google Sheets (`QUALITY_SHEET_ID` + `QUALITY_KAIZEN_SHEET_GID`). Não usa TOTVS.

| Query | Descrição |
|---|---|
| `title` | Filtro parcial no título (`descricao`). |
| `status` | Filtro exato de status (ex.: `implantado`). |
| `branch` | Filial (`filial`). |
| `date_start`, `date_end` | Intervalo de datas (`DD-MM-YYYY`, `YYYY-MM-DD` ou `DD/MM/YYYY`). Opcionais — omitidos, `list_kaizen` traz todos os implantados. |

**Contagem (`total_kaizens`):** kaizens com status *implantado* cuja data de implantação (`data`) cai no intervalo (quando `date_start`/`date_end` informados).

**Ganhos (`total_savings`):** para cada kaizen *implantado* com dias ativos no período, soma `daily_savings × dias ativos`. Kaizens implantados antes do `date_start` continuam gerando ganho nos dias do intervalo (desde a data de implantação até `date_end`).

**Listagem (`list_kaizen`):** itens com `id`, `annual_savings` (`daily_savings × 365`) e demais campos cadastrais. O dashboard de qualidade usa chamada sem datas para catálogo completo na tabela.

#### Planilha — colunas lidas

| Coluna (header) | Campo API | Observação |
|---|---|---|
| `filial` | `branch` | |
| `descricao` | `title` | |
| `responsavel` | `accountable` | |
| `area_setor` | `sector` | |
| `custo_investimento` | `investment` | |
| `segudos_por_ocorrecia` / `segundos_por_ocorrencia` | — | Entrada do cálculo (aliases aceitos). |
| `ocorrecias_por_dia` / `ocorrencias_por_dia` | — | Entrada do cálculo (aliases aceitos). |
| `custo_hora` | — | Entrada do cálculo. |
| `status` | `status` | |
| `data` | `date_implemented` | Data de implantação. |
| `deleted` | — | Linhas marcadas são ignoradas. |

**Não ler da planilha:** `horas_poupadas_dia` e `ganho_diario` — removidas da planilha; a API calcula o ganho diário.

#### Cálculo

```
horas_poupadas_dia = (segundos_por_ocorrencia × ocorrencias_por_dia) / 3600
daily_savings      = horas_poupadas_dia × custo_hora   # arredondado em 2 casas
annual_savings     = daily_savings × 365               # arredondado em 2 casas
```

Se alguma das três entradas estiver ausente, `daily_savings` e `annual_savings` são `null` e o kaizen não contribui para `total_savings`.

#### Exemplo de resposta (`data`)

```json
{
  "date_start": "01-01-2026",
  "date_end": "31-01-2026",
  "total_kaizens": 1,
  "total_savings": 22.62,
  "list_kaizen": [
    {
      "id": "01-16/01/2026-App resina CT-16",
      "title": "App resina CT-16",
      "date_implemented": "16/01/2026",
      "status": "implantado",
      "accountable": "Ossamu",
      "sector": "Produção",
      "investment": 620.0,
      "daily_savings": 7.54,
      "annual_savings": 2752.10,
      "branch": "01"
    }
  ]
}
```

### GET /quality/kaizens/{kaizen_id}

**Fonte:** mesma planilha. Path: `kaizen_id` = `list_kaizen[].id` (ex.: `01-16/01/2026-App resina CT-16`). O segmento usa `{kaizen_id:path}` no FastAPI para aceitar barras no identificador.

Retorna ficha completa com entradas do cálculo: `seconds_per_occurrence`, `occurrences_per_day`, `hourly_cost`, `hours_saved_per_day`, além dos campos do resumo.

**operationId:** `get_kaizen_by_id` · **meta.entity:** `kaizen` · **meta.shape:** `scalar`

Testes unitários: `api-delpi/tests/test_kaizen_repository.py`. Integração Sheets: [12-testes-sem-totvs-google-sheets.md](./12-testes-sem-totvs-google-sheets.md).

### Cadastro operacional — `/quality/kaizens/records`

**Fonte:** PostgreSQL (`quality.kaizens`, migrations `V026`/`V027`). Plugin MFE: `cadastro-kaizen`. Documentação: [plugins/cadastro-kaizen/README.md](../../../plugins/cadastro-kaizen/README.md).

**Permissões:**

| Operação | Permissões aceitas |
|----------|-------------------|
| Leitura (GET) | `cadastro-kaizen.view`, `cadastro-kaizen.manage`, `dashboard-quality.view`, `api-delpi.quality.access`, `api-delpi.access` |
| Escrita (POST/PUT/DELETE/import) | `cadastro-kaizen.manage`, `api-delpi.quality.access`, `api-delpi.access` |

#### GET /quality/kaizens/records

| Query | Descrição |
|-------|-----------|
| `branch` | `01` ou `02` |
| `status` | `em_andamento`, `implantado`, `descontinuado`, `cancelado` |
| `savings_type` | `tempo`, `material`, `financeiro`, `qualitativo`, `misto` |
| `title` | Filtro parcial no título |
| `date_start`, `date_end` | Intervalo em `date_implemented` (ISO) |
| `page`, `page_size` | Paginação (máx. 200) |

**operationId:** `list_kaizen_records` · **meta.shape:** `paged_list`

#### POST /quality/kaizens/records

Body JSON com `branch_code`, `title` (obrigatórios), campos cadastrais e entradas de economia. A API infere `savings_type` quando omitido e calcula `daily_savings` / `annual_savings` via `KaizenSavingsCalculator`.

**operationId:** `create_kaizen_record` · **meta.shape:** `scalar`

#### POST /quality/kaizens/records/import-from-sheet

Importa todas as linhas **ativas** da planilha kaizen (`deleted` ignorado) para o PostgreSQL. Ignora duplicatas (filial + título + data de implantação).

Body opcional: `{ "dry_run": true }` — simula sem gravar.

**operationId:** `import_kaizens_from_sheet` · **meta.shape:** `scalar`

Resposta `data`: `{ "created", "skipped", "errors", "items": [...] }`.

Código: `ImportKaizensFromSheetUseCase`, `kaizen_sheet_import_mapper.py`, `kaizen_records_router.py`.

Testes: `tests/unit/test_import_kaizens_from_sheet_use_case.py`, smoke `test_quality_kaizen_*` em `test_route_meta_smoke.py`.

#### Revisões temporais (planejado — Fase 6)

> Especificação: [ESPECIFICACAO-REVISOES.md](../../../docs/12-roadmap-e-volucao/cadastro-kaizen/ESPECIFICACAO-REVISOES.md)

O cadastro atual guarda só o **estado corrente** em `quality.kaizens`. A evolução prevê `quality.kaizen_revisions` com snapshots por alteração (`effective_from` / `effective_until`), para:

- Calcular `total_savings` e `total_kaizens` em `GET /quality/kaizens/summary` com fidelidade histórica
- Auditar mudanças de status e economia na UI

Rotas planejadas: `GET /quality/kaizens/records/{id}/revisions`, `GET .../at?date=YYYY-MM-DD`. O `PUT` passará a aceitar `effective_from` e `change_reason` quando campos de cálculo mudarem.
