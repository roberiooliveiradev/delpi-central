# ENGINEERING.LMP.G4.C — Legacy MFE Parity & Dashboard Contract Evidence

| Campo | Valor |
|---|---|
| Gate | G4.C — inventário, paridade e contratos READ |
| Baseline | `04c176ec3670bb42414977b136d32649fa93a29b` (HEAD == origin/main) |
| Executor | Devin — EVA / Portal Engenharia DELPI |
| Status | `ACCEPT` proposto |
| Escopo | READ-only; sem cutover; sem writes; legado intacto |

---

## 1. Baseline e authorities

- `HEAD == origin/main == 04c176ec` na reancoragem (inclui `b62ac7c580` G4.B e trabalho concorrente DÉLIA/HELPDESK).
- Authorities lidos: `AGENTS.md`; `.cursor/rules` (centralized-rules-first, clean-code-architecture-guardrails, development-standards-index, english-code-identifiers); documentos LMP 32–39.
- MFE legado lido integralmente: `plugins/dashboard-lmps/src` (103 arquivos TS/TSX) + docs `DOCUMENTACAO.md`, `API_MAPPING.md`, `TESTING.md`, `STRUCTURE.md` + manifesto `dash-lmps-microfrontend.manifest.json`.
- Portal Engenharia inventariado: `plugins/engineering` (features home/overview/help, routes internos, manifest).
- Mudança concorrente do usuário preservada: `api-delpi/.../product_repository.py`, doc 119 controllership-finance, `infra/docker-compose.dev.yml` (`CF_S2S_TOKEN_URL`) e `route_contract_registry.py` — **não** entraram no commit.

## 2. Inventário do MFE legado (`plugins/dashboard-lmps`)

### 2.1 Telas e rotas internas

| Tela | Rota | Conteúdo |
|---|---|---|
| `DashboardLmpsPage` | `/apps/dashboard-lmps` | KPIs, NcStreakCard, gráficos, tabela, filtros, exports |
| `LmpDetailPage` | `/apps/dashboard-lmps/ov/{sale_number}` | Cards Proposta/Engenharia/Cliente, produtos + BOM, histórico/timeline/Gantt |
| `NonconformitiesPage` | `/apps/dashboard-lmps/nonconformities` | Lista NC (busca, ordenação, paginação) |
| `NonconformityDetailPage` | `/nonconformities/new` e `/{id}` | Formulário NC (hydrate via detalhe da OV) |

Manifesto: `dashboard-lmps` federado, `renderMode: "federated"`, permissões `dashboard-lmps.view` + `dashboard-lmps.nc.write`.

### 2.2 APIs consumidas

| Client | Base | Endpoints |
|---|---|---|
| `lmpApi.ts` | `/apps/api-delpi/engineering` | `/lmps`, `/lmps/dashboard`, `/lmps/dashboard/summary`, `/lmps/dashboard/charts`, `/lmps/dashboard/items`, `/lmps/{sale}`, `/lmps/{sale}/history/events`, `/lmps/{sale}/history/flow`, `/lmps/nonconformities` |
| `lmpNonconformityApi.ts` | `/apps/api-delpi/engineering/lmps/nonconformities` | `GET list`, `GET /{id}`, `GET /{id}/history`, `GET /streak`, `GET /problem-tags`, `POST`, `PUT /{id}`, `DELETE /{id}`, `GET /export`, `POST /import` |
| `productApi.ts` | `/apps/api-delpi/products` | `GET /products/search`, `GET /products/{code}/structure?max_depth=6` |
| `departmentIddApi.ts` | `/apps/api-delpi/dashboard` | `GET /department-idd` (SI — metas/IDD) |

### 2.3 Comportamento-chave

- **Filtros** `date_start`, `date_end`, `branch`, `listing_type`, `status` — multi-select, sincronizados na URL (`filterUrl.ts`, `syncLmpsFiltersToUrl`), compartilháveis.
- **KPIs** do summary: `percent_dentro_prazo` (R09 — inclui Andamento no numerador), `avg_lead_time` (R10), `total_lmps`; **Dias sem NC** via `NcStreakCard` (`/nonconformities/streak`); **metas/IDD** via `DepartmentIddBadge` (`/dashboard/department-idd`).
- **Gráficos:** `levelData`, `statusData`, `leadByLevel` (endpoint `/dashboard/charts` — agregado R11) + `evolutionData` **derivado no frontend** de `chartItems` via `aggregateLmpEvolutionSeries` (granularidade dia/semana/mês/ano). Fallback client-side (`buildLmpFallbackCharts`) quando `charts` vem vazio.
- **Tabela:** busca, ordenação client-side, colunas filial/proposta/**revisão**/**ciclo**/datas/SLA/status, paginação, clique → detalhe OV. Revisão=`homolog_revision` (fallback `measurement_revision`); Ciclo=`cycle_index` (política `work_month_lmp` — mesma OV em várias linhas).
- **Detalhe OV:** `useLmpDetail` dispara detalhe + `history/events` + `history/flow` em paralelo; escopo de filtros herdado (`useLmpDetailRequestScope`); lista permanece montada ao abrir detalhe.
- **Histórico:** toggle timeline/tabela (localStorage), filtros client (Todos/Engenharia/Em aberto/Revisão atual via `reference_revision`), `mergeHistoryFlowIntoEvents()`, mini-Gantt por evento + Gantt global, badges de entrada/avanço/retorno (`flow_transition_label`).
- **Exports:** CSV (`exportLmpsCsv`), Excel (`xlsx` lib, `lmpsDashboardSheets`/`dispatch`), PDF/print via motor canônico `@delpi/plugin-ui` (`export/pdf` re-exporta `printDelpiDocumentSpec` etc.) + `@media print` na página.
- **Resiliência:** mantém última carga válida em erro de refresh; auto-refresh 2 min com aba visível; tooltips `HelpTooltip`/`content/helpTooltips.ts`.

### 2.4 Permissões legadas

- `ENGINEERING_LMP_ACCESS` = `api-delpi.access` OR `dashboard-engineering.view` OR `dashboard-lmps.view` — rotas READ de LMP + NC.
- `ENGINEERING_LMP_NC_WRITE` = `api-delpi.access` OR `dashboard-lmps.nc.write` — POST/PUT/DELETE + import.
- `DASHBOARD_IDD_ACCESS` — conjunto amplo (incl. `dashboard-lmps.view`) para `/dashboard/department-idd`.

## 3. Matriz de paridade funcional

Classificação: **PROVEN** (evidência no SHA), **TO_INVENTORY** (precisa evidência antes do gate), **PLANNED** (contrato futuro definido), **TARGET** (destino acordado, ainda não implementável).

| Capacidade | Componente legado | API atual | Contrato futuro | Owner | Permissão | Paridade | Gap | Teste necessário | Gate |
|---|---|---|---|---|---|---|---|---|---|
| % dentro do prazo | `KpiCard` | `/lmps/dashboard/summary` | E-LMP-03 `/v1/lmps/summary` | eng-api | `engineering.access` | **PROVEN** (G4.B real) | — | regressão existente | G5 |
| Lead time médio | `KpiCard` | idem | E-LMP-03 | eng-api | `engineering.access` | **PROVEN** | — | idem | G5 |
| Total de propostas | `KpiCard` | idem | E-LMP-03 | eng-api | `engineering.access` | **PROVEN** (fix COUNT G4.B) | — | `test_summary_total_items_counts_all_listing_kinds` | G5 |
| Dias sem NC | `NcStreakCard` | `/nonconformities/streak` | **E-NC-04** (futuro, via owner NC) | api-delpi (NC) | `dashboard-lmps.view` → decisão | **PLANNED** | rota READ de NC não exposta pela eng-api | shadow streak | G5/G6 |
| Metas/IDD | `DepartmentIddBadge` | `/dashboard/department-idd` | composição via SI (delegação humana — padrão já usado por `/v1/overview`) | **Strategic Indicators** | `DASHBOARD_IDD_ACCESS` (humano delegado) | **PLANNED** | sem mudança de ownership; apresentação deve delegar Bearer humano como `overview_api_delpi.py` | integração + 403→forbidden | G5 |
| Filtros competência/datas/unidade/tipo/status | `FilterBar` | query params | E-LMP-01 `start/end_date, branch, listing_type, status` | eng-api | `engineering.access` | **PROVEN** (paridade de universos G4.B; CSV multi-select → resolver no adapter do Portal) | `branch`/`listing_type` aceitam CSV no legado — adapter deve expandir | smoke G5 | G5 |
| Gráfico nível/status/lead | `ChartCard` ×3 | `/lmps/dashboard/charts` | E-LMP-01 `data.charts` (R11 já no payload de `/v1/lmps`) | eng-api | `engineering.access` | **PROVEN** (domínio) | — | coberto por list tests | G5 |
| Evolução temporal (dia/semana/mês/ano) | `ChartCard` + `aggregateLmpEvolutionSeries` | derivado de `items` no frontend | **sem contrato novo** — deriva de E-LMP-01 `items` (mesma semântica: agregação UI) | frontend | — | **PLANNED** | reutilizar util migrado; nenhuma regra de negócio nova — agregação de exibição | snapshot série | G5 |
| Tabela registros (busca/ordenação/colunas/paginação) | `DataTable` | `/lmps/dashboard/items` | E-LMP-01 `/v1/lmps` | eng-api | `engineering.access` | **PROVEN** (237 itens, tolerância 0) | ordenação/busca são client-side — preservar no componente | comparação de página | G5 |
| Detalhe OV | `LmpDetailPage` | `/lmps/{sale}` | **E-LMP-02 `/v1/lmps/{sale_number}`** ✅ novo | eng-api | `engineering.access` | **PROVEN** — real: OV 003696, 0 diffs de campo | — | `test_detail_*` + real | G5 |
| Produtos da OV | tabela produtos | `list_products` no detalhe | E-LMP-02 `item.list_products` | api-delpi (fatos) | `engineering.access` | **PROVEN** | — | idem | G5 |
| BOM/estrutura | `ProductStructureTree` | `/products/{code}/structure` | **gap** — Products domain (fora LMP); decisão: consumo direto com Bearer humano delegado OU contrato E-PRD futuro | **Products (api-delpi)** | permissão de produtos do humano | **PLANNED** | eng-api não deve absorver catálogo de produtos | smoke BOM | G5 |
| Histórico eventos | `LmpHistorySection` | `/lmps/{sale}/history/events` | **E-LMP-04 `/v1/lmps/{sale}/history/events`** ✅ novo | eng-api | `engineering.access` | **PROVEN** — real: 14/14 eventos, 0 diffs | — | `test_history_events_enriched` | G5 |
| Fluxo ida/volta | `LmpHistoryTimeline` | `/lmps/{sale}/history/flow` | **E-LMP-05 `/v1/lmps/{sale}/history/flow`** ✅ novo | eng-api | `engineering.access` | **PROVEN** — real: 0 diffs (`flow_transition*`, `is_engineering_entry`) | — | `test_history_flow_enriched` | G5 |
| Timeline/Gantt | `HistoryEventGantt`, `HistoryGlobalGantt` | mesmos dados events/flow | composição frontend (componentes migrados) | frontend | — | **PLANNED** | nenhum dado adicional de backend | visual snapshot | G5 |
| Export CSV | `exportLmpsCsv` | client-side | client-side (idêntico) | frontend | — | **PLANNED** | — | golden file | G5 |
| Export Excel | `dispatch` + `xlsx` | client-side | client-side | frontend | — | **PLANNED** | — | golden file | G5 |
| Export PDF | `export/pdf` → `@delpi/plugin-ui` | client-side | client-side (motor canônico já compartilhado) | `@delpi/plugin-ui` | — | **PLANNED** | — | golden file | G5 |
| Impressão | `@media print` | — | mesma técnica | frontend | — | **PLANNED** | — | checklist visual | G5 |
| URL compartilhável | `filterUrl.ts` | — | `filterUrl` migrado/adaptado às rotas `/apps/engineering/*` | frontend | — | **PLANNED** | basePath muda | teste de URL | G5 |
| Navegação detalhe | `routeParser`, lista montada | — | `resolveEngineeringRoute` + view `lmp_detail` | frontend | — | **PLANNED** | estender resolver | e2e | G5 |
| NC — listagem | `NonconformitiesPage` | `GET /nonconformities` | **E-NC-01** (futuro READ) | api-delpi (NC) | `dashboard-lmps.view` → `engineering.access`? | **PLANNED** | contrato READ NC na eng-api | — | G6 |
| NC — detalhe/histórico | `NonconformityDetailPage` | `GET /{id}`, `/{id}/history` | **E-NC-02/03** | api-delpi (NC) | idem | **PLANNED** | idem | — | G6 |
| NC — create/edit/delete/import | idem | POST/PUT/DELETE/import | **write — fora do escopo G4.C** | api-delpi (NC) | `dashboard-lmps.nc.write` → decisão | **TARGET** | migração de writes não autorizada | — | G6+ |
| Loading/empty/error/tooltips/refresh/responsivo | componentes + hooks | — | componentes migrados | frontend | — | **PLANNED** | — | checklist | G5 |
| Auto-refresh 2 min | `useLmpsDashboard` | — | mesmo hook migrado | frontend | — | **PLANNED** | — | fake timer | G5 |

## 4. Matriz de paridade visual/comportamental

Sem capturas estruturais novas implementadas nesta gate — a paridade visual será validada em G5 com a mesma composição dos componentes migrados. Inventário de superfícies visuais a preservar:

| Superfície | Origem | Estado |
|---|---|---|
| Grid de KPIs + NcStreakCard | `KpiCard`, `NcStreakCard` | TO_INVENTORY em G5 (snapshot) |
| FilterBar com IDD badge | `FilterBar`, `DepartmentIddBadge` | TO_INVENTORY |
| 4 ChartCards (pizza nível, pizza status, barras lead, linha evolução) | `ChartCard`, `chartColors` | TO_INVENTORY |
| Tabela com tooltips ⓘ e Revisão/Ciclo | `DataTable`, `helpTooltips` | TO_INVENTORY |
| Timeline + badges + mini-Gantt + Gantt global | `LmpHistoryTimeline`, `HistoryEventGantt`, `HistoryGlobalGantt` | TO_INVENTORY |
| BOM tree + legenda | `ProductStructureTree`, `RichTree`, `StructureLegend` | TO_INVENTORY |
| Estados loading/empty/error parcial | `useLmpsDashboard`, páginas | TO_INVENTORY |
| Impressão `@media print` | `index.css` | TO_INVENTORY |

`TEST_NOT_RUN` — paridade visual não executada nesta gate (nenhum componente migrado ainda).

## 5. Contratos Engineering API

### 5.1 Existentes (revalidados)

| ID | Rota | Evidência |
|---|---|---|
| E-LMP-01 | `GET /v1/lmps` (items + summary + charts R11) | G4.B real — 237 itens, 0 divergências |
| E-LMP-03 | `GET /v1/lmps/summary` | G4.B real — fix COUNT aplicado |
| `GET /v1/home`, `GET /v1/overview` | composição Portal | existentes — inclui delegação SI |

### 5.2 Implementados nesta gate

| ID | Rota | Facts | Regra | Evidência real |
|---|---|---|---|---|
| E-LMP-02 | `GET /v1/lmps/{sale_number}` | F-LMP-02 | `compute_dashboard_fields` (R01–R05) + `list_history: []` | OV 003696 — **0 diffs** vs legado |
| E-LMP-04 | `GET /v1/lmps/{sale}/history/events` | F-LMP-03 `view=events` | `enrich_history_events` (labels, status, open/late/current, durations) | 14/14 eventos — **0 diffs** |
| E-LMP-05 | `GET /v1/lmps/{sale}/history/flow` | F-LMP-03 `view=flow` | `enrich_flow_transition_fields` | **0 diffs** |

Todos: `require_any_permission(["engineering.access"])` + `principal_type=="user"` + validação ISO de datas + estados honestos `forbidden`/`unavailable`/`not_found`/`empty` — **nunca** payload inventado.

### 5.3 Correção de infraestrutura desta gate

- `ENGINEERING_LMP_FACTS_TIMEOUT_SECONDS` (default **30s**) — o facts adapter herdava `HOME_SOURCE_TIMEOUT_SECONDS=5s`, bound da composição Home; F-LMP-02 legítimo mediu ~6s warm / ~18s cold → timeout honesto mas permanente. Timeout dedicado, ainda limitado, env-overridable.

### 5.4 Gaps de contrato (não implementados — por design desta gate)

| Gap | Motivo | Próximo gate |
|---|---|---|
| NC READs (list/detail/history/streak/problem-tags/export) | inventário feito; migração READ requer decisão de permissão (`engineering.access` vs preservar) | G5/G6 |
| NC writes | explícito fora de escopo | G6+ |
| BOM `/products/{code}/structure` | owner = Products domain; recomendação: consumo direto pelo MFE com Bearer humano (mesma permissão atual) **ou** contrato dedicado se coordenação preferir BFF | decisão G5 |
| Metas/IDD dashboard | owner = Strategic Indicators; padrão de composição já existe em `/v1/overview` (delegação humana → `forbidden` honesto) | G5 |
| Evolução temporal | semântica é agregação de exibição no frontend — não é regra de negócio; nenhum contrato backend novo necessário | G5 |

## 6. Ownership confirmado

| Conceito | Owner | Evidência |
|---|---|---|
| Regras LMP/KPIs/status/SLA/lead | Engineering API domain | `domain/lmp/*` |
| Facts/SQL/TOTVS | api-delpi | F-LMP-01..04, S2S |
| Metas/IDD/score consolidado | Strategic Indicators (api-delpi `strategic_indicators/`) | `/dashboard/department-idd`, `SI_DEPARTMENT_ID_VALUES` |
| NC persistence | api-delpi plugin Postgres | `postgres_lmp_nonconformity_repository.py` |
| Autorização efetiva | Core API | `engineering.access` via delpi_auth |
| Catálogo/BOM produtos | api-delpi Products domain | `/products/*` |

## 7. Estratégia de reuso e integração no Portal

**Decisão técnica (G4C-04): migração controlada de código (copy-and-adapt), não dependência runtime.**

1. **Migrar** (copiar para `plugins/engineering/src/features/lmps/`) os componentes/hooks do legado adaptados: `DataTable`, `FilterBar`, `KpiCard`, `NcStreakCard`, `ChartCard`, histórico/Gantt/BOM, exports e utils. São específicos de LMP — não são candidatos a `shared/` (regra: compartilhar só com 2+ consumidores neutros e sem regra de negócio).
2. **Substituir adapters:** `lmpApi.ts` → client sobre `/apps/engineering-api/v1/lmps*` (mesmos envelope e shapes funcionais).
3. **`@delpi/plugin-ui`** já provê o motor PDF/documento — reuso direto, zero duplicação.
4. **`httpClient.ts`** do Portal já injeta Bearer via `configureHttpClient` — padrão existente (`engineeringHomeApi`).
5. **Rotas internas:** estender `resolveEngineeringRoute` com views `lmps`, `lmps_detail` (path `/ov/{sale}` ou `/lmps/{sale}`), `nonconformities` — sem mudança de manifest (nested paths já cobertos por longest-prefix; novas entradas de menu somente em cutover governado).
6. **Sem dependência runtime** do Portal no MFE legado; legado permanece operacional até homologação + cutover governado.
7. Metas/IDD e NC: durante a transição, adapter do Portal pode continuar delegando Bearer humano às rotas oficiais existentes (mesma permissão do usuário) — **sem bypass e sem ownership transfer**.

## 8. Segurança (revalidada)

- Novas rotas: `engineering.access` via Core; `principal_type=="user"` requerido; `engineering.manage` **não** concede acesso (teste); sem fallback legado.
- S2S: `X-Delpi-Service-Authorization` `engineering-api` client_credentials + Bearer humano delegado; `engineering-facts.read` + aud `api-delpi`; allowlist.
- api-delpi: **0 ocorrências** `engineering.access|manage` em `api-delpi/app/` (residual search).
- Nenhum token no frontend; `caller_app` nunca autoridade.

## 9. Testes e evidências

| Comando | Resultado |
|---|---|
| `pytest engineering-api/tests` | **303 passed** |
| `pytest api-delpi -k lmp` | **182 passed** |
| `audit_platform_guardrails` | 0 findings |
| `audit_openapi_contracts` | 0 findings |
| `audit_fastapi_authz` | 0 findings |
| `audit_architecture_phase3` | 0 findings |
| Real parity detail/events/flow (OV 003696, TOTVS dev) | **0 diffs** em todos os campos |
| Negative: detail `not_found`→404, `unavailable` honesto, 401 sem token, 403 sem permissão | coberto em `test_lmp_routes.py` |

`TEST_NOT_RUN`: paridade visual/frontend; NC; BOM/Products; IDD dashboard; shadow em lote dos novos endpoints (1 OV real verificada; corpus completo em G5 se requerido).

## 10. Arquivos alterados

```
engineering-api/engineering_app/application/models/lmp.py            (sale_number/revision em LmpQuery)
engineering-api/engineering_app/application/ports/lmp_facts.py       (fetch_fact, fetch_history)
engineering-api/engineering_app/application/use_cases/get_lmp_detail.py   (novo — E-LMP-02)
engineering-api/engineering_app/application/use_cases/get_lmp_history.py  (novo — E-LMP-04/05)
engineering-api/engineering_app/infrastructure/gateways/api_delpi_facts.py (F-LMP-02/03)
engineering-api/engineering_app/composition/lmp_composer.py          (builders + timeout dedicado)
engineering-api/engineering_app/config.py                            (ENGINEERING_LMP_FACTS_TIMEOUT_SECONDS)
engineering-api/engineering_app/interface/http/routes/lmp_routes.py  (3 rotas + mapper de estados)
engineering-api/tests/test_lmp_routes.py                             (stubs + 10 testes novos)
engineering-api/tests/test_health.py, test_auth_middleware.py        (allowlist OpenAPI)
docs/12-roadmap-e-evolucao/engineering/40-...md                      (este documento)
```

## 11. Riscos e residuais

- **Cold-start F-LMP-02** ~18s — monitorar; facts timeout agora 30s (bounded).
- Corpus real detalhe/histórico = 1 OV — ampliar em G5 se a coordenação exigir.
- CSV multi-select de filtros (`branch`, `listing_type`, `status`) — adapter do Portal deve preservar semântica.
- Decisão pendente: BOM/Products (consumo direto vs contrato dedicado) — `ARCHITECTURE_DECISION_REQUIRED` se a coordenação quiser proxy.
- Decisão pendente: permissão futura de NC (`dashboard-lmps.view` vs `engineering.access` exclusivo) — sem writes até decisão.

## 12. Readiness G5

**G5 = migração da experiência para Portal Engenharia.** Pré-requisitos satisfeitos: contratos READ funcionais completos para dashboard+detalhe+histórico (E-LMP-01..05), domínio com paridade real tolerância 0, estratégia de reuso definida, owners confirmados, legado intacto. Bloqueios remanescentes: decisão BOM, decisão permissão NC, corpus visual.
