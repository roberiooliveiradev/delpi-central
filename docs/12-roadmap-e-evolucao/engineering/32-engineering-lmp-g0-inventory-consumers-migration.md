# ENGINEERING.LMP.G0 — Inventário integral, consumidores transversais e arquitetura de migração

**Data:** 2026-10-28
**Baseline Git:** `BASE_HEAD = 1f34403767a91670a21a9ba6086df4b4b3cf49e0` (`HEAD = origin/main`; `3060ab0741` confirmado ancestral via `git merge-base --is-ancestor`)
**Natureza:** missão de descoberta/arquitetura — **nenhum código funcional alterado**
**Status geral:** inventário com evidência para os itens `PROVEN`; lacunas externas marcadas `TO_INVENTORY`

---

## 0. Resumo executivo

O ecossistema LMP hoje é servido pela **api-delpi** sobre três camadas distintas de dados e regras:

1. **LMPs (dados TOTVS Protheus):** leitura SQL pesada (`LMPQueryRepository`, 4.216 linhas) sobre `AD1010` (cabeçalho OV), `AIJ010` (eventos/histórico de workflow), `SB1010` (produtos) e `SG1010` (BOM — contagem de PI), mais a view dedicada `dbo.VW_DELPI_OV_EVENTOS_ENRIQUECIDOS` (definida em `LMPS_VIEWS.SQL`). A semântica de classificação LMP (processos/estágios `000002/000003/000008/000012/000013`, residência mínima de 30 min em engenharia, políticas de período, prioridade `LMP > AMOSTRA > OUTROS`) está **embutida no SQL** — é regra de negócio de Engenharia materializada em infraestrutura, não mera extração.
2. **Regras derivadas em Python:** `LMPBusinessRules` (SLA por nível de PI: N1=4d, N2=8d, N3=20d úteis + 1 dia de tolerância; classificação Pontual/Atrasado/Andamento/Retornada), serviços de domínio de histórico/enriquecimento (656 linhas em `app/domain/services/`), e o use case `ListLMPDashboardUseCase` (agregação de KPIs, charts, cache).
3. **Não conformidades LMP (dados DELPI, não TOTVS):** persistidas em **PostgreSQL** no schema `engineering.lmp_nonconformities` via `PluginBaseRepository` — dados criados pelo app, com CRUD completo, histórico de alterações, tags, streak e import/export.

O contrato público são **19 endpoints** sob `/engineering/lmps*` na api-delpi, com envelope `api_delpi_success`, AuthN por JWT Keycloak e AuthZ por permissões resolvidas do Core `/me` (`require_any_permission`).

**Consumidores comprovados no repositório:**

| Consumidor | Rotas usadas | Tipo |
|---|---|---|
| `plugins/dashboard-lmps` (MFE legado) | todas as 19 rotas LMP + `/products/*` + `/dashboard/department-idd` | DIRECT / RUNTIME_PROVEN |
| `plugins/dashboard-engineering` (MFE legado "Dashboard Engenharia") | `/lmps/dashboard`, `/summary`, `/charts`, `/items` + `/dashboard/department-idd` | DIRECT / RUNTIME_PROVEN |
| `engineering-api` `/v1/home` | `GET /engineering/lmps` (Bearer humano delegado) | DIRECT / RUNTIME_PROVEN |
| `engineering-api` `/v1/overview` | `GET /engineering/lmps/dashboard/summary` (3 KPIs LMP + campos `goal_*` enriquecidos por SI) | DIRECT / RUNTIME_PROVEN |
| `strategic-indicators-api` | `GET /engineering/lmps/dashboard/summary` (`summary_mode=kpi`, `listing_type=LMP`, Bearer delegado) | DIRECT / RUNTIME_PROVEN |
| `tv-dashboard-api` | catálogo `tv_data_routes.json` com todas as rotas LMP (gerado do OpenAPI da api-delpi) | INDIRECT (catálogo/proxy genérico) |
| `minha-delpi-ai-api` (DÉLIA) | feature `engineering_lmps` no catálogo de capacidades; `select_lmp`; presenter KPI | DIRECT (path-level) — escopo exato TO_INVENTORY |
| `plugins/api-delpi-console` | smoke suite → `/lmps/dashboard/summary` | INDIRECT (operação) |
| `plugins/engineering` (Portal Engenharia) | link de navegação `/apps/dashboard-lmps` | INDIRECT (navegação) |
| `shared/delpi_api_client` | `list_lmps`, `get_lmp`, `get_lmp_dashboard`, `get_lmp_dashboard_summary` | INDIRECT (biblioteca) |

**Relação circular já existente e gerida:** api-delpi → strategic-indicators-api (enriquecimento de metas via `DashboardGoalsService`) **e** strategic-indicators-api → api-delpi (realizado via `DelpiEngineeringGateway`). O ciclo é cortado em runtime por `_is_internal_request_declared_by_si()` (service token + `caller_app` autodeclarado), que faz a api-delpi **omitir o enriquecimento de metas** quando o chamador interno é o SI. Qualquer migração deve preservar esse corte — e **não pode** introduzir `engineering-api → api-delpi → engineering-api` (hoje engineering-api já consome api-delpi para LMP; um "BFF de retorno" na api-delpi criaria exatamente esse ciclo).

---

## 1. Objetivo e limites

Produzir inventário factual, com evidência `arquivo:linha`, para embasar decisão arquitetural de migração do Dashboard LMPs e das regras LMP para a `engineering-api`, preservando api-delpi como integração de origem e todos os consumidores.

**Fora de escopo:** implementação, migração, desativação, alteração de qualquer serviço, deploy. Achados de segurança são registrados, não corrigidos.

---

## 2. Inventário do aplicativo legado `plugins/dashboard-lmps`

### 2.1 Rotas do MFE

Base: `/apps/dashboard-lmps` (`src/app/routes.ts`, `src/App.tsx`, `src/main.tsx`).

| Rota | Página | Funcionalidade |
|---|---|---|
| `/apps/dashboard-lmps` | `DashboardLmpsPage.tsx` | Dashboard: summary/KPIs, charts, items paginados, filtros, exportação |
| `/apps/dashboard-lmps/nonconformities` | `NonconformitiesPage.tsx` | Lista de NCs, streak, problem-tags, export/import |
| `/apps/dashboard-lmps/nonconformities/new` | `NonconformityDetailPage.tsx` (modo create) | Criação de NC (write) |
| `/apps/dashboard-lmps/nonconformities/{id}` | `NonconformityDetailPage.tsx` | Detalhe/edição/exclusão de NC + histórico |
| `/apps/dashboard-lmps/ov/{sale_number}` | `LmpDetailPage.tsx` | Detalhe da OV: dados LMP, eventos e fluxo de histórico, estrutura de produtos |

Props do host: `getAccessToken`, `pathname`, `hasPermission` (`src/main.tsx`). Permissão frontend para writes de NC: **`dashboard-lmps.nc.write`**.

### 2.2 API calls do frontend

Arquivo `src/api/lmpApi.ts` — base `/apps/api-delpi/engineering` + `unwrapApiDelpiEnvelope`:

| Método | Endpoint | Uso |
|---|---|---|
| GET | `/lmps/` | lista paginada (legado) |
| GET | `/lmps/dashboard` | payload completo (summary+charts+items) |
| GET | `/lmps/dashboard/summary` | KPIs isolados |
| GET | `/lmps/dashboard/charts` | gráficos |
| GET | `/lmps/dashboard/items` | itens paginados |
| GET | `/lmps/{saleNumber}` | detalhe OV |
| GET | `/lmps/{saleNumber}/history/events` | eventos de histórico |
| GET | `/lmps/{saleNumber}/history/flow` | fluxo/timeline |

`src/api/lmpNonconformityApi.ts`:

| Método | Endpoint | Write? |
|---|---|---|
| GET | `/lmps/nonconformities` | — |
| GET | `/lmps/nonconformities/{id}` | — |
| GET | `/lmps/nonconformities/{id}/history` | — |
| GET | `/lmps/nonconformities/streak` | — |
| GET | `/lmps/nonconformities/problem-tags` | — |
| GET | `/lmps/nonconformities/export` | — (download) |
| POST | `/lmps/nonconformities` | **SIM** |
| PUT | `/lmps/nonconformities/{id}` | **SIM** |
| DELETE | `/lmps/nonconformities/{id}` | **SIM** |
| POST | `/lmps/nonconformities/import` | **SIM** |

`src/api/productApi.ts`: `GET /products/search`, `GET /products/{code}/structure`.
`src/api/departmentIddApi.ts`: `GET /dashboard/department-idd` (params `department_id`, `competence`, `start_date`, `end_date`, `branch`).

**Conversão de datas:** `YYYY-MM-DD` → `YYYYMMDD` antes da chamada (`src/utils/dates.ts`); valores já `YYYYMMDD` passam. Filtros: `start_date`, `end_date`, `branch`, `listing_type`, `status`, `page`, `page_size`. Estado de filtro persistido em URL (`utils/filterUrl.ts`, `routeParser.ts`).

### 2.3 Capacidades de UI

- **Dashboard:** cards KPI (total, % no prazo, lead time médio, metas SI enriquecidas — `goalDisplay.ts`), charts por nível/status/lead time (`lmpCharts.ts`), tabela de itens com ordenação cliente (`useClientTableSort`), paginação cliente (`useClientPagination`), série de evolução (`lmpEvolutionSeries.ts`, `timeSeriesAggregation.ts`, `periodBuckets.ts`), competence-linked dates (`useCompetenceLinkedDates.ts`).
- **Exportação:** `src/export/` — builders de sheets (`lmpsDashboardSheets.ts`, `dashboardExportBuilders.ts`), `xlsx@0.18.5` (package.json), diretório `pdf/`, CSV (`utils/csv.ts`, `exportLmpsCsv.ts`). Formatos: XLSX, PDF, CSV.
- **Detalhe OV:** dados LMP, painel de histórico (eventos + flow/gantt — `historyGlobalGantt.ts`, `historyFormatting.ts`, `historyPreferences.ts`), estruturas de produto (`useLmpProductStructures.ts`, `productStructureTree.ts`).
- **Não conformidades:** CRUD completo (`useNcSectionEdit.ts`, `ncFormModel.ts`, `ncProblemTags.ts`), histórico de alterações, streak, tags, export/import.
- **Departamental:** IDD por departamento (`useDepartmentIdd.ts`, `departmentIddFilters.ts`) via `/dashboard/department-idd`.
- **Testes:** 1 arquivo (`utils/lmpsGoalPresentation.structural.test.mjs`) — cobertura mínima; **lacuna de paridade de frontend**.

Estado: **PROVEN** (leitura direta de código; funcionalidade em produção presumida por deploy ativo — não reexecutada nesta missão).

---

## 3. Inventário das rotas LMP na api-delpi

Arquivo: `api-delpi/app/interface/http/routes/engineering/engineering_router.py` (891 linhas), `lmp_nonconformity_router.py` (641), `lmp_route_helpers.py` (60). Prefixo do router: `/engineering`.

### 3.1 Endpoints LMP (TOTVS)

| # | Método/Path | Linha | Use case | AuthZ |
|---|---|---|---|---|
| 1 | GET `/lmps` | :119 | `ListLMPUseCase` → `repository.list_lmps_page` | `ENGINEERING_LMP_ACCESS` |
| 2 | GET `/lmps/dashboard` | :170 | `ListLMPDashboardUseCase` + `enrich_dashboard_metric(goal_keys.ENGINEERING_LMP)` (:207) | `ENGINEERING_LMP_ACCESS` |
| 3 | GET `/lmps/dashboard/summary` | :234 | `GetLMPDashboardSummaryUseCase` (modos `kpi`/`full`) + enrich (:269) | `ENGINEERING_LMP_ACCESS` |
| 4 | GET `/lmps/dashboard/items` | :294 | `ListLMPDashboardUseCase` | `ENGINEERING_LMP_ACCESS` |
| 5 | GET `/lmps/dashboard/charts` | :344 | `ListLMPDashboardUseCase` | `ENGINEERING_LMP_ACCESS` |
| 6 | GET `/lmps/{sale_number}/history/events` | :390 | `GetLmpHistoryEventsUseCase` | `ENGINEERING_LMP_ACCESS` |
| 7 | GET `/lmps/{sale_number}/history/flow` | :442 | `GetLmpHistoryFlowUseCase` | `ENGINEERING_LMP_ACCESS` |
| 8 | GET `/lmps/{sale_number}` | :494 | `GetLMPUseCase` | `ENGINEERING_LMP_ACCESS` |

Query params comuns: `start_date`/`end_date` (canonical) + `date_start`/`date_end` (legado), `branch`, `listing_type`, `status`, `page`, `page_size`, `include_qtd_pi`, `summary_mode`. Helpers em `lmp_route_helpers.py` (`resolve_period_dates`, `build_list_lmp_request`).

### 3.2 Endpoints NC LMP (Postgres)

`lmp_nonconformity_router.py`:

| # | Método/Path | Linha | AuthZ |
|---|---|---|---|
| 9 | GET `/lmps/nonconformities` | :256 | `ENGINEERING_LMP_ACCESS` |
| 10 | GET `/lmps/nonconformities/problem-tags` | :348 | `ENGINEERING_LMP_ACCESS` |
| 11 | GET `/lmps/nonconformities/streak` | :373 | `ENGINEERING_LMP_ACCESS` |
| 12 | GET `/lmps/nonconformities/export` | :402 | `ENGINEERING_LMP_ACCESS` |
| 13 | POST `/lmps/nonconformities/import` | :435 | **`ENGINEERING_LMP_NC_WRITE`** |
| 14 | GET `/lmps/nonconformities/{id}/history` | :472 | `ENGINEERING_LMP_ACCESS` |
| 15 | GET `/lmps/nonconformities/{id}` | :500 | `ENGINEERING_LMP_ACCESS` |
| 16 | POST `/lmps/nonconformities` | :528 | **`ENGINEERING_LMP_NC_WRITE`** |
| 17 | PUT `/lmps/nonconformities/{id}` | :560 | **`ENGINEERING_LMP_NC_WRITE`** |
| 18 | DELETE `/lmps/nonconformities/{id}` | :609 | **`ENGINEERING_LMP_NC_WRITE`** |

Ator de auditoria resolvido do usuário autenticado (`_current_actor`, :215). Histórico de alterações via `lmp_nonconformity_history_diff` (domain service).

### 3.3 Endpoints adjacentes consumidos pelo app

| Endpoint | Arquivo | Owner |
|---|---|---|
| GET `/products/search` | `routes/products/` (api-delpi) | api-delpi/TOTVS SB1010 |
| GET `/products/{code}/structure` | idem | api-delpi/TOTVS SG1010 |
| GET `/dashboard/department-idd` | `routes/dashboard/dashboard_router.py`:100 | api-delpi → SI (IDD é dado do Strategic Indicators) |

### 3.4 Outras rotas sob `/engineering` (fora do escopo LMP, mesmo namespace)

`engineering_router.py`: `/transforma-mais/*` (:542, :589), `/mini-applicators/*` (:682–875, incl. POST golpes), `/transformometro/*` (:638). `metallographic_reports_router.py` (439 linhas): metalografia. **Conclusão:** o namespace `/engineering` na api-delpi é um agregado multi-domínio — a migração de LMP não pode assumir ownership do prefixo inteiro.

---

## 4. Regras de negócio — matriz e classificação

### 4.1 Regras Python (fichas resumidas)

`api-delpi/app/application/services/lmp_business_rules.py` (275 linhas) — `LMPBusinessRules`:

| RULE_ID | Regra | Linhas | Classificação |
|---|---|---|---|
| LMP-R01 | `SLA_BY_LEVEL`: N1=4, N2=8, N3=20 (dias úteis) | :24-27 | ENGINEERING_DOMAIN_RULE |
| LMP-R02 | `get_nivel(qtd_pi)`: ≤10→N1, ≤20→N2, >20→N3 | :112-119 | ENGINEERING_DOMAIN_RULE (PI = proxy de complexidade — convenção Engenharia) |
| LMP-R03 | Tolerância SLA = +1 dia útil | :29, :126-140 | ENGINEERING_DOMAIN_RULE |
| LMP-R04 | `resolve_dashboard_status`: RETORNADA→Retornada; não-FINALIZADA→Andamento; FINALIZADA→Pontual se (fim ≤ data_limite+tol) OU (minutos ≤ sla_limite_min); senão Atrasado | :189-230 | ENGINEERING_DOMAIN_RULE |
| LMP-R05 | Calendário de dias úteis (só fim de semana; **sem feriados**) — `add_business_days`, `business_days_between` | :78-110 | ENGINEERING_DOMAIN_RULE (simplificação assumida — feriados não constam; gap documental) |
| LMP-R06 | `engineering_status` labels: ABERTA/FINALIZADA/PARCIAL/RETORNADA (match exato + ABERTA∈em-andamento) | :31-35, :147-187 | SOURCE_NORMALIZATION (rótulos vêm do TOTVS; a interpretação é domínio) |
| LMP-R07 | Datas: parse Protheus `YYYYMMDD`/planilha; resposta HTTP ISO `YYYY-MM-DD` | :39-75 | SOURCE_NORMALIZATION / PRESENTATION_ONLY |
| LMP-R08 | Enriquecimento de item dashboard (nível, SLA, data_limite, lead_time_util, status) | `list_lmp_dashboard_use_case.py`:32-59 | ENGINEERING_DOMAIN_RULE (composição) |
| LMP-R09 | KPI `% dentro do prazo` = itens com status **≠ "Atrasado"** / total LMP-only ×100, round 2 — inclui Andamento/Retornada como não-atrasado | :158-177 | ENGINEERING_DOMAIN_RULE (semântica sutil — fixture de paridade obrigatória) |
| LMP-R10 | `avg_lead_time` = média de `lead_time_util` (dias úteis) apenas de itens com datas completas, round 2 | :167-172 | ENGINEERING_DOMAIN_RULE |
| LMP-R11 | Charts: contagem por nível (ordem fixa N1/N2/N3), por status (`DASHBOARD_STATUS_VALUES`), lead médio por nível | :69-97 | ENGINEERING_DOMAIN_RULE (apresentação agregada) |
| LMP-R12 | Modos summary `kpi` vs `full`: kpi = fatos sem PI + BOM só para OVs FINALIZADA; full = batch com PI em todas | :246-268 | ENGINEERING_DOMAIN_RULE + performance |
| LMP-R13 | Cache de dashboard/summary (`lmp_dashboard_cache`, `lmp_dashboard_summary_cache`, `build_query_cache`) | services/lmp/* | PRESENTATION_ONLY/infra (invalidação/TTL TO_INVENTORY) |
| LMP-R14 | Enriquecimento de metas SI (`enrich_dashboard_metric`, `goal_keys.ENGINEERING_LMP="lmp"`) — attach `has_goal/goal_*`; falha SI → payload sem meta (degradação honesta) | `routes/shared/dashboard_goal_enrichment.py`:8-35 | CROSS_DOMAIN_RULE (meta = owner SI; attach = api-delpi) |
| LMP-R15 | Enriquecimento de eventos de histórico (correlação próximo evento, revisão de referência, painel) | `domain/services/lmp_history_event_enrichment.py` (266) | ENGINEERING_DOMAIN_RULE |
| LMP-R16 | Transição de fluxo + labels de processo/estágio (`resolve_process_label`, `resolve_stage_label`) | `lmp_history_flow_transition.py` (139), `lmp_process_stage_labels.py` (31) | ENGINEERING_DOMAIN_RULE |
| LMP-R17 | Semântica de `listing_kind` (LMP/AMOSTRA/OUTROS), inclusão por período, ciclo de revisão | `lmp_listing_kind_semantics_service.py` (62), `lmp_period_inclusion_semantics_service.py` (95), `lmp_listing_cycle_semantics_service.py` (63) | ENGINEERING_DOMAIN_RULE (espelha política do SQL — **dupla fonte de verdade a reconciliar**) |
| LMP-R18 | NC: histórico diff, ordenação de lista, normalização de problem-tags, streak | `domain/services/lmp/*` (4 arquivos) | ENGINEERING_DOMAIN_RULE (dados DELPI) |
| LMP-R19 | NC actor/auditoria (`_current_actor` do principal autenticado) | `lmp_nonconformity_router.py`:215 | CROSS_DOMAIN_RULE (auditoria plataforma) |

### 4.2 Semântica de negócio embutida em SQL (`LMPQueryRepository` + `LMPQuerySettings`)

`api-delpi/app/infrastructure/persistence/totvs/lmp_repositories/`:

| RULE_ID | Regra em SQL/settings | Evidência | Classificação |
|---|---|---|---|
| LMP-S01 | Tabelas oficiais: `AD1010` (OV), `AIJ010` (eventos workflow), `SB1010`, `SG1010` (BOM→`qtd_pi`, `max_bom_level=10`), view `VW_DELPI_OV_EVENTOS_ENRIQUECIDOS` | repository; `LMPS_VIEWS.SQL`; settings | SOURCE_EXTRACTION |
| LMP-S02 | Filiais escopo `["01","02"]` | `lmp_query_settings.py` | SOURCE_EXTRACTION (parametrizável) |
| LMP-S03 | **Residência mínima em engenharia ≥ 30 min** (só para `LISTING_KIND LMP`) | settings `min_engineering_residence_minutes`; repo `_engineering_residence_filter_sql`:118 | **ENGINEERING_DOMAIN_RULE em SQL** |
| LMP-S04 | Mapa processo→estágios: âncora LMP `{000002,000003}→{000003,000012}`; follow-up `→000013`; suporte eng. `→{000003,000008,000012}`; amostra `→{000002,000008}`; finalizado LMP `→000012` | settings `lmp_anchor_process_stages` etc.; repo :535-600 | **ENGINEERING_DOMAIN_RULE em SQL** (definição de "o que é LMP" — regra central de Engenharia) |
| LMP-S05 | Prioridade de classificação `LMP(2) > AMOSTRA(1) > OUTROS(0)` por revisão | settings `listing_kind_priority` | ENGINEERING_DOMAIN_RULE |
| LMP-S06 | Políticas de inclusão por período: `work_month_lmp` (padrão), `anchor_in_period`, `homolog_cycles_in_period`, variantes | settings + repo `_period_inclusion_policy`:200 | **ENGINEERING_DOMAIN_RULE em SQL** (define denominador dos KPIs) |
| LMP-S07 | `strict_residence_after_homolog` (default False): Homolog <30min→OUTRO | settings | ENGINEERING_DOMAIN_RULE |
| LMP-S08 | Minutos de engenharia por evento/revisão (CTEs `EngenhariaEventos`, `EngenhariaMinutosPorRevisao`, `first_engineering_arrival`) | repo :319-532 | ENGINEERING_DOMAIN_RULE em SQL (insumo de R04) |
| LMP-S09 | `qtd_pi` via BOM recursiva (nível ≤10, tipos `PA` raiz / `PI` componente) | settings + `get_lmp_pi_counts_by_ovs`:4184 | SOURCE_EXTRACTION + ENGINEERING_DOMAIN_RULE (definição PI) |
| LMP-S10 | Exclusão de deletados `D_E_L_E_T_=''`, `WITH (NOLOCK)` leitura analítica | `LMPS_VIEWS.SQL`, repo :49 | SOURCE_EXTRACTION |
| LMP-S11 | Dedup/ordenação de eventos (`ROW_NUMBER` por revisão/data/hora/stage/recno; `OUTER APPLY` próximo evento) | `LMPS_VIEWS.SQL` | SOURCE_NORMALIZATION |
| LMP-S12 | Candidatas por revisão vs ciclo de homolog vs mês de trabalho (`_uses_*` :205-218) | repo | ENGINEERING_DOMAIN_RULE em SQL |
| LMP-S13 | `get_earliest_ov_date`, paginação `list_lmps_page`, `get_lmp`, `list_ov_products`, painéis `get_lmp_*_panel_context` | repo :3655-3962 | SOURCE_EXTRACTION |
| LMP-S14 | Fatos de summary `get_lmp_dashboard_summary_facts` (:4104) vs batch full `get_lmp_dashboard_summary` (:4212) | repo | SOURCE_EXTRACTION (projeção) |

**Fronteira SQL×domínio (proposta, fundamentada):** permanecem na api-delpi S01, S02, S09(extração), S10, S11, S13, S14 — acesso a fonte, dedup físico e projeção de fatos. São **regras de Engenharia expressas em SQL** e candidatas a ownership Engineering (com decisão de execução SQL vs Python a avaliar por performance): S03, S04, S05, S06, S07, S08, S12 — hoje inseparáveis do query plan; extrair sem provar paridade em volume real é o maior risco técnico da migração. `ARCHITECTURE_DECISION_REQUIRED` para cada uma.

### 4.3 Contagem

- Regras Python identificadas: **19** (R01–R19)
- Regras/semânticas em SQL/settings: **14** (S01–S14)
- Total catalogado: **33** — das quais **~19 candidatas a ENGINEERING_DOMAIN_RULE** (total ou parcial), ~8 SOURCE_EXTRACTION/NORMALIZATION, 2 CROSS_DOMAIN, restantes PRESENTATION/infra.

---

## 5. Mapa SQL e fontes oficiais

| Fonte | Tipo | Conteúdo | Acesso |
|---|---|---|---|
| TOTVS Protheus `AD1010` | tabela | cabeçalho/dados da OV | SQL direto (NOLOCK) |
| TOTVS `AIJ010` | tabela | eventos de workflow (processo/estágio/datas/histórico) | SQL + view |
| TOTVS `SB1010` | tabela | produtos | SQL |
| TOTVS `SG1010` | tabela | BOM/estrutura (qtd PI) | SQL recursiva |
| `dbo.VW_DELPI_OV_EVENTOS_ENRIQUECIDOS` | view dedicada | eventos enriquecidos + próximo evento | `LMPS_VIEWS.SQL` |
| Postgres plugins `engineering.lmp_nonconformities` (+related) | schema | NCs, histórico, tags | `PluginBaseRepository` |
| strategic-indicators-api | API | metas `goal_*`, IDD departamental | `StrategicIndicatorsApiClient`, `/dashboard/department-idd` |

**Observação:** a pasta `RQ-060` é referência de auditoria, não filtro SQL (comentário repo :1406).

---

## 6. Consumidores — matriz completa

| Consumer | Contrato | Campos | AuthZ efetiva | Dependência | Estratégia |
|---|---|---|---|---|---|
| dashboard-lmps (MFE) | 19 rotas + products + dept-idd | todos | `dashboard-lmps.view`/`api-delpi.access`/`dashboard-engineering.view`; write: `dashboard-lmps.nc.write`/`api-delpi.access` | DIRECT/RUNTIME | Fase D — migrar para contratos engineering-api após paridade |
| dashboard-engineering (MFE) | `/lmps/dashboard{,/summary,/charts,/items}` + dept-idd | KPIs, charts, items | idem read | DIRECT/RUNTIME | Mesmo contrato — cutover conjunto ou fachada |
| engineering-api `/v1/home` | `GET /engineering/lmps` | `items[].{sale_number,sale_description,engineering_status,branch,start,end, revisions,costumer_name}` | delega Bearer; 403→seção forbidden | DIRECT/RUNTIME | Apontar gateway para novo contrato quando existir |
| engineering-api `/v1/overview` | `GET /engineering/lmps/dashboard/summary` | `total_lmps`/`total_items`, `percent_dentro_prazo`, `avg_lead_time` + `goal_*` | delega Bearer | DIRECT/RUNTIME | Engineering API pode passar a computar localmente (regra migrada) e buscar meta SI via contrato próprio |
| strategic-indicators-api | `GET /engineering/lmps/dashboard/summary` (`listing_type=LMP`, `summary_mode=kpi`) | `total_lmps`, `percent_dentro_prazo`, `avg_lead_time` | Bearer delegado ou token interno | DIRECT/RUNTIME | Preservar contrato de realizado; ver §7 |
| tv-dashboard-api | catálogo OpenAPI → data routes | genérico | TV permissions + proxy | INDIRECT | Compatibilidade OpenAPI — paths/opIds estáveis até cutover |
| DÉLIA (minha-delpi-ai-api) | feature `engineering_lmps`, markers `/engineering/lmps`, `select_lmp`, KPI presenter | paths/links; dados via catalog | conforme ação | DIRECT(path-level)/TO_INVENTORY(escopo runtime) | Manter operationIds/aliases ou remap no registry |
| api-delpi-console | smoke `/lmps/dashboard/summary` | sucesso | token operador | INDIRECT | Atualizar suite no cutover |
| Portal Engenharia (plugins/engineering) | navegação `/apps/dashboard-lmps` | href | `engineering.access` | INDIRECT | Reapontar feature card na Fase G |

**Gaps de consumidores externos:** integrações fora do monorepo (planilhas, BI, scripts operacionais, outros apps TOTVS-side) **não são observáveis pelo código** — `TO_INVENTORY` com validação por logs de acesso na api-delpi/gateway antes do cutover (LMP-G0-07/08 parcial).

---

## 7. Strategic Indicators — análise específica

**Realizado (Engenharia→SI):** `strategic-indicators-api/si_app/infrastructure/gateways/delpi_engineering_gateway.py` — `get_lmp_dashboard_summary(date_start, date_end, branch)` chama api-delpi `/engineering/lmps/dashboard/summary` com `listing_type=LMP`, `summary_mode=kpi`, `authorization=bearer_authorization_from_context()` (delegação humana — correto). Consumido por `engineering_metrics_snapshot_service`, `engineering_lmp_summary_cache`, `engineering_indicators_snapshot_provider`, `get_trends_real_use_case`. Indicadores afetados: `engineering-projects-on-time` / `lmp_on_time` (realizado), total e lead time.

**Meta (SI→api-delpi):** `DashboardGoalsService` (`api-delpi/.../strategic_indicators/dashboard_goals_service.py`) chama SI e faz attach de `has_goal/goal_label/goal_value/target/goal_*` no summary (`enrich_dashboard_metric`, source_key `"lmp"` — `dashboard_goal_source_keys.py`:48). TTL cache 45s.

**Anti-ciclo:** `_is_internal_request_declared_by_si()` — se `caller_app=="strategic-indicators-api"` + service token interno válido → pula enriquecimento (documentado: otimização, **não** autorização; token é plataforma-compartilhado e caller_app autodeclarado).

**Separação de ownership:** realizado LMP (contagem, %, lead time) = regra de Engenharia hoje executada na api-delpi. Meta, IDD, scores, agregação por período = **owner Strategic Indicators** — não migrar. `/dashboard/department-idd` (api-delpi) é fachada de leitura SI — consumer do dashboard, não dado LMP.

**Alternativas de compatibilidade para o realizado (após migração das regras):**

| Alt. | Descrição | Prós | Contras/Riscos |
|---|---|---|---|
| A | SI passa a consultar **engineering-api** (contrato oficial LMP) | Owner correto; elimina camada | Muda contrato corporativo do SI; novo AuthZ; `ARCHITECTURE_DECISION_REQUIRED` |
| B | api-delpi mantém `/engineering/lmps/dashboard/summary` como fachada → engineering-api | Zero mudança de consumer | **CICLO:** engineering-api (overview) já → api-delpi; se api-delpi → engineering-api para LMP e engineering-api → api-delpi para fatos LMP, temos `eng-api → api-delpi → eng-api`. Só viável se engineering-api **não** depender de api-delpi para os fatos — mas fatos vêm de TOTVS via api-delpi ⇒ ciclo real. **Rejeitada salvo split claro: api-delpi expõe fatos brutos e engineering-api computa regras; então a fachada api-delpi chamaria eng-api SEM eng-api chamar api-delpi naquele path — impossível hoje, pois eng-api precisaria dos fatos da própria api-delpi.** ⇒ **B inviável sem inversão: a fachada deveria morrer na api-delpi como resposta computada localmente (regra duplicada) — vira duplicação, não fachada.** |
| C | Manter endpoint na api-delpi **como owner transitório do realizado** até SI migrar (Alt. A), com contrato congelado | Sem ciclo; migração incremental | api-delpi segura regra de Engenharia por mais tempo — aceitável como fase |

**Recomendação:** **C → A**. Engineering API passa a computar regras LMP sobre fatos brutos da api-delpi (`engineering-api → api-delpi(facts) → TOTVS`); SI migra para engineering-api (Alt. A) com janela de dupla publicação medida por fixtures de paridade; o endpoint legado na api-delpi é aposentado depois que SI + dashboards saírem. **Nenhuma alternativa implementada nesta missão.**

---

## 8. AuthN/AuthZ — matriz

| Camada | Mecanismo | Evidência |
|---|---|---|
| AuthN | JWT Keycloak via `delpi_auth` FastAPI middleware; permissões resolvidas do **Core `/me`** | `shared/delpi_auth/middleware/fastapi_auth.py`:105, :283 |
| AuthZ rota | `require_any_permission(codes)` → `has_any_permission(user.permissions)`; superadmin bypass | `authorization.py`:86-118, `authz_core.py` |
| Read LMP | `ENGINEERING_LMP_ACCESS` = any{`api-delpi.access`, `dashboard-engineering.view`, `dashboard-lmps.view`} | `api_delpi_permissions.py`:229-233 |
| Write NC | `ENGINEERING_LMP_NC_WRITE` = any{`api-delpi.access`, `dashboard-lmps.nc.write`} | :234-237 |
| Frontend write gate | `hasPermission("dashboard-lmps.nc.write")` | `dashboard-lmps/src/main.tsx` |

**Achados (registro, sem correção):**
1. `api-delpi.access` — permissão genérica do módulo — **concede write de NC** (`ENGINEERING_LMP_NC_WRITE` a inclui). O frontend restringe a `dashboard-lmps.nc.write`, mas o backend aceita o código genérico ⇒ qualquer principal com `api-delpi.access` pode POST/PUT/DELETE/importar NCs. Classificação: `PROVEN` no código; impacto real depende do RBAC no Core. Candidato a endurecimento no desenho de contratos futuros.
2. Não há isolamento por filial/unidade em LMP (filtro `branch` é input, não claim) — TO_INVENTORY se política por filial é requisito.
3. Sem service-token elevation no caminho humano (comprovado na arquitetura F1); o token interno existe apenas para SI→api-delpi como sinal de composição (não autorização).

---

## 9. Grafos de dependências

**Atual (comprovado):**
```
dashboard-lmps ─┐
dashboard-eng ──┼─> /apps/api-delpi/engineering/lmps* ─> use cases ─> LMPBusinessRules
eng-api /home ──┤        (api-delpi, AuthZ any{3 perms})   + domain services
eng-api /overview┤                                      │
SI-api (realizado)┘                                     ├─> LMPQueryRepository ─> TOTVS AD/AIJ/SB/SG + VW
DÉLIA (paths) ──> /engineering/lmps (registry)          └─> Postgres engineering.lmp_nonconformities
api-delpi (summary) ─enrich─> SI-api (metas)   [ciclo cortado por caller_app+svc-token]
SI-api (dept-idd) <─ /dashboard/department-idd <─ dashboard-lmps/dashboard-eng
```

**Alvo candidato:**
```
Portal Engenharia (dashboard LMP) ─> eng-api /v1/lmps* ─┬─> regras LMP (domain migrado)
SI-api (realizado) ─────────────> eng-api /v1/lmps/summary┤
eng-api /v1/home|overview ─────────> (mesmo módulo interno) │
                                                        └─> api-delpi FACTS /engineering/lmps/facts* ─> TOTVS+view
NC write/read ─> eng-api /v1/lmp-nonconformities ─> Postgres engineering.* (schema ownership a decidir)
Metas/IDD ─> SI-api (inalterado; eng-api consome goal_* ou delega ao consumer)
```

**Riscos de ciclo:** (1) api-delpi→eng-api em qualquer path LMP enquanto eng-api→api-delpi facts — proibido; (2) enriquecimento SI dentro de eng-api chamando SI enquanto SI chama eng-api — requer o mesmo short-circuit caller_app ou separação clara: eng-api nunca enriquece com meta para chamadas originadas no SI (contrato "realized-only" para SI).

---

## 10. Contratos candidatos da Engineering API (proposta, não implementada)

| Candidato | Método/Path | Finalidade | AuthZ proposta |
|---|---|---|---|
| E-LMP-01 | GET `/v1/lmps` | lista paginada | `engineering.access` + granular futura |
| E-LMP-02 | GET `/v1/lmps/dashboard` | summary+charts+items | idem |
| E-LMP-03 | GET `/v1/lmps/summary` | KPIs (compat SI/engineering-overview) | idem + contrato interno SI |
| E-LMP-04 | GET `/v1/lmps/{sale}` | detalhe | idem |
| E-LMP-05 | GET `/v1/lmps/{sale}/history` | eventos+fluxo | idem |
| E-LMP-06 | GET `/v1/lmp-nonconformities*` (+/{id},/history,/streak,/problem-tags,/export,/import, POST/PUT/DELETE) | NC completo | read: `engineering.access`; write: **nova permissão dedicada** (`engineering.lmp-nc.write` — ARCHITECTURE_DECISION_REQUIRED; corrige achado §8.1) |
| E-LMP-07 | (api-delpi) GET `/engineering/lmps/facts*` | fatos brutos LMP para eng-api | service-to-service + escopo |

Filtros/formato: manter `start_date/end_date` ISO, `branch`, `listing_type`, `status`, `page/page_size`, `summary_mode`. Datas de resposta ISO (`YYYY-MM-DD`). Não duplicar `/products/*` e `/dashboard/department-idd` — permanecem com seus owners (produtos api-delpi/TOTVS; IDD SI). OpenAPI/operationIds preservados ou mapeados para DÉLIA/TV.

---

## 11. Paridade — plano verificável

**Fixtures (sobre os contratos reais):** LMP FINALIZADA no prazo por data; no prazo só por minutos (R04 OR); atrasada; RETORNADA; ABERTA/PARCIAL (→Andamento); revisão múltipla (prioridade LMP>AMOSTRA); residência <30min; OV cruzando virada de mês (`work_month_lmp`); BOM >10 níveis/sem PI; filial 01 vs 02; NC CRUD+histórico; fonte indisponível (SI goal timeout → sem `goal_*`); usuário sem permissão (403); permissão apenas `api-delpi.access` (comportamento write a definir).

**Critérios:** igualdade de `total_lmps`, `percent_dentro_prazo` (inclui Andamento no numerador — R09), `avg_lead_time`, itens (campos+datas ISO), charts (3 séries), históricos (contagem, ordenação, labels), NC (todos os campos+diff), status HTTP/envelope, latência ≤ baseline +20% medido em volume real; SI: realizado idêntico para `listing_type=LMP&kpi`.

---

## 12. Migração incremental (fases)

- **A — Contratos/fatos:** especificar `facts` na api-delpi (extração existente, projeção estável) + ADRs de ownership. 
- **B — Regras:** portar `LMPBusinessRules`+domain services+póliticas SQL-criticais para eng-api (decisão SQL×Python por regra).
- **C — Paridade backend:** fixtures+comparação dual-run (shadow) em volume real.
- **D — Portal Engenharia:** telas dashboard LMP (read) → detalhe/histórico → NC (write por último, com nova permissão).
- **E — EVA:** tools read-only sobre contratos aprovados (§14).
- **F — Consumers:** SI migra (Alt. A); dashboard-engineering e tv/DÉLIA: remap/contratos compatíveis.
- **G — Cutover:** navegação oficial → Portal; legado read-only.
- **H — Desativação:** remover `plugins/dashboard-lmps` só com paridade operacional comprovada, zero consumidores ativos (logs), rollback pronto.

NC tem **fonte de dados própria (Postgres)** — cutover separado do dashboard TOTVS.

---

## 13. Critérios de cutover e rollback

**Cutover:** paridade 100% fixtures+shadow; SI com realizado idêntico; permissões Core provisionadas; DÉLIA/TV remapeados; smoke produtivo.
**Rollback:** feature-flag/route switch no Portal para `/apps/dashboard-lmps` (app permanece deployado); revert de manifests; dados NC não mudam de lugar até fase própria — rollback nunca perde writes se NC migrar por último com dual-write ou migração única verificada.

---

## 14. Evolução da EVA (proposta)

| Tool candidata | Contrato | Tipo | Quando |
|---|---|---|---|
| `get_lmp_dashboard` | E-LMP-02/03 | READ | Fase E, após C |
| `search_lmps` | E-LMP-01 | READ | Fase E |
| `get_lmp_detail` | E-LMP-04 | READ | Fase E |
| `get_lmp_history` | E-LMP-05 | READ | Fase E |
| `analyze_lmp_performance` | composição de 02/03 | ANALYSIS (nunca recalcula regra oficial como fonte) | pós-aprovação |
| NC write tools | — | PREPARE/ACT somente após aprovação explícita e AuthZ dedicada | fora do horizonte V1 |

---

## 15. Riscos

| Risco | Prob. | Impacto | Mitigação | Gate |
|---|---|---|---|---|
| Ciclo eng-api↔api-delpi (fachada B) | M | A | Rejeitar B; contrato facts unidirecional | ADR |
| Divergência KPI por semântica sutil (R09 inclui Andamento) | A | A | Fixture dedicada + shadow | C |
| Dupla fonte listing_kind (SQL vs domain services) | M | A | Reconciliar em spec única | A/B |
| Performance ao sair regra do SQL | M | A | Benchmark volume real; manter CTEs como facts | B |
| Perda de consumer oculto (externo) | M | M | Logs de acesso 30-60d na api-delpi antes cutover | G |
| SI regression (realizado) | M | A | Contrato congelado + paridade dual | F |
| Escopo AuthZ insuficiente (`engineering.access` ≠ write NC) | M | M | Permissão dedicada NC (decisão Core) | D |
| Elevação por `api-delpi.access` em NC write (achado §8.1) | M | M | Nova permissão + revisão RBAC Core | D/ADR |
| Arredondamento/datas divergentes | M | M | Fixtures de borda | C |
| Desativação precoce do legado | B | A | Fase H só após critérios §13 | H |
| Cache compartilhado entre impl. | B | M | Caches por contrato; invalidação medida | C |

---

## 16. Decisões arquiteturais pendentes (`ARCHITECTURE_DECISION_REQUIRED`)

1. **Ownership das regras LMP:** transferir R01–R12, R15–R18 e S03–S08, S12 para engineering-api (proposto: sim).
2. **Execução das regras atualmente em SQL** (S03/S04/S06/S08): permanecem na query da api-delpi como "fatos enriquecidos" vs migram para Python na eng-api — trade-off latência×clareza; exige benchmark.
3. **Contrato corporativo SI:** Alt. A (SI→eng-api) aprovação formal; janela de dupla publicação.
4. **Permissão NC dedicada** (`engineering.lmp-nc.write`) + correção do aceite de `api-delpi.access` em write.
5. **Ownership do schema Postgres `engineering.lmp_nonconformities`** (api-delpi plugins DB vs novo store da eng-api) — dado não-TOTVS, decisão de dados.
6. **listing_kind/período:** fonte única de verdade entre SQL e `domain/services/lmp_*_semantics_service.py`.
7. **Fatos via novo endpoint api-delpi** vs eng-api consultando endpoints existentes com flags (`summary_mode`) — granularidade do contrato de integração.

---

## 17. Lacunas, premissas não verificadas, evidência fraca

- Consumidores externos ao monorepo: **TO_INVENTORY** (logs api-delpi/gateway, BI/planilhas).
- Feriados no cálculo de dias úteis: ausentes do código — confirmar com negócio se é intencional.
- Cobertura de testes do MFE legado: 1 arquivo — paridade dependerá de fixtures backend.
- Escopo exato do uso DÉLIA (link vs chamada de dados): parcialmente mapeado; ações de external_action sugerem execução de rotas — validar em runtime.
- TTL/invalidação real dos caches LMP (`build_query_cache`) não auditada em profundidade.
- `LMPS_VIEWS.SQL` implantado no banco de produção: presumido (view referenciada); não verificado em DB.
- Endpoints `/lmps/dashboard` vs trio summary/charts/items: frontends usam ambos — definir se contrato alvo expõe payload composto ou granulares.

## 18. Índice de evidências

- Frontend: `plugins/dashboard-lmps/src/{App.tsx,main.tsx,api/*.ts,hooks/*,export/*,utils/*}`; `package.json` (xlsx 0.18.5); `plugins/dashboard-engineering/src/api/engineeringApi.ts`:16-135.
- Rotas: `api-delpi/app/interface/http/routes/engineering/{engineering_router.py:119-540, lmp_nonconformity_router.py:215-641}`; `routes/dashboard/dashboard_router.py`:100.
- Regras: `application/services/lmp_business_rules.py` (todo); `application/use_cases/lmp/*` (6 arquivos); `domain/services/lmp*` (656 linhas, 6 arquivos); `domain/services/lmp/` (4 arquivos NC).
- SQL: `infrastructure/persistence/totvs/lmp_repositories/{lmp_query_repository.py (4.216), lmp_query_settings.py, LMPS_VIEWS.SQL}`; `persistence/plugins/repositories/engineering/postgres_lmp_nonconformity_repository.py` (schema `engineering.lmp_nonconformities`).
- AuthZ: `application/security/api_delpi_permissions.py`:20-21,229-239; `shared/delpi_auth/{authorization.py:86, authz_core.py, middleware/fastapi_auth.py:105}`.
- Consumers: `engineering-api/.../api_delpi_gateway.py`:1-77; `overview_api_delpi.py`:51-175; `strategic-indicators-api/.../delpi_engineering_gateway.py` (todo); `shared/delpi_api_client/client.py`:385-395; `tv-dashboard-api/tv_app/content/tv_data_routes.json`:10325-11111; `minha-delpi-ai-api/.../assistant_capabilities_catalog_generator.py`:100-102, `external_action_operational_route_selection_service.py`:257; `plugins/api-delpi-console/src/content/smokeSuites.ts`:22; `plugins/engineering` (homeViewModel href `/apps/dashboard-lmps`).
- SI internals: `api-delpi/app/application/services/strategic_indicators/{dashboard_goals_service.py, dashboard_goal_source_keys.py:48, dashboard_department_idd_service.py}`; `routes/shared/dashboard_goal_enrichment.py`.

---
*Documento de inventário — propostas marcadas como tais; nenhuma mudança de ownership foi executada.*
