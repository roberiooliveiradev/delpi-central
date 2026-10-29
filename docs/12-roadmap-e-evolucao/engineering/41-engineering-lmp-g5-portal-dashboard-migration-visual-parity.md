# ENGINEERING.LMP.G5 — Portal Dashboard Migration & Visual Parity Evidence

| Campo | Valor |
|---|---|
| Gate | G5 — migração da experiência LMP para o Portal Engenharia |
| Baseline | `49eee133284819981db5942035269a6509f1f99e` (HEAD == origin/main) |
| Executor | Devin — EVA / Portal Engenharia DELPI |
| Status | `ACCEPT_WITH_RESIDUAL` proposto |
| Escopo | READ-only; sem cutover; sem writes; legado intacto |

---

## 1. Baseline e authorities

- Reancoragem inicial em `1f6f6d1970` (G4.C); durante a sessão `origin/main`
  avançou para `49eee1332848` (commits concorrentes helpdesk +
  controllership-finance, FF — `1f6f6d` preservado como ancestral).
  `BASE_HEAD` efetivo da entrega: `49eee1332848`.
- Authorities lidos: `AGENTS.md`; `.cursor/rules` always-on +
  `platform-frontend-mfe-experience`, `platform-security-identity-authorization`,
  `platform-api-contracts-integration`, `contract-evolution-backward-compatibility`,
  `feature-help-sync`, `http-integration-resilience`, `test-and-commit`,
  `english-code-identifiers`; docs de Engenharia 32–40.
- Contratos vigentes confirmados no HEAD: E-LMP-01..05 (`/v1/lmps`,
  `/v1/lmps/summary`, `/v1/lmps/{sale}`, `/v1/lmps/{sale}/history/events`,
  `/v1/lmps/{sale}/history/flow`).

## 2. Inventário aplicado (baseline G4.C, doc 40)

- `plugins/dashboard-lmps` como referência funcional e visual integral.
- Copy-and-adapt para `plugins/engineering/src/features/lmps/` — **zero**
  import `plugins/engineering → plugins/dashboard-lmps` em runtime.
- 89 arquivos copiados seletivamente: api/, components/, hooks/, pages/
  (Dashboard + Detail), types/, utils/, export/, styles/, ui/, content/,
  constants/. **Sem páginas de NC** (lista/form) — readiness governada.

## 3. Estrutura da feature

```text
plugins/engineering/src/features/lmps/
  api/            lmpApi · lmpNonconformityApi · productApi ·
                  departmentIddApi · httpClient (delegação canônica)
  components/     FilterBar · LmpsNav · KpiCard · NcStreakCard ·
                  DepartmentIddBadge · DataTable(Section) · Pagination ·
                  ChartCard/Toolbar · DetailCard/FieldGrid ·
                  HistoryEventGantt · HistoryGlobalGantt ·
                  LmpHistorySection/Timeline ·
                  LmpProductStructuresSection · ProductStructureTree ·
                  RichTree · StructureLegend · LoadingActivity* ·
                  MultiSelectField · chart/filter/table utils
  hooks/          useLmpsDashboard · useLmpDetail · useLmpProductStructures ·
                  useDepartmentIdd · routerPath · loading · pagination · sorting
  pages/          DashboardLmpsPage · LmpDetailPage
  export/         CSV · XLSX · PDF (builders + buttons)
  utils/          filterUrl · routeParser · navigation · dates ·
                  goalDisplay · dashboardAggregates · lmpsClientFilters ·
                  historyFormatting · productStructureTree ·
                  operationalUnitLabels · export helpers
  styles/         lmps.css (escopo `.dashboard-lmps`)
  LmpsFeature.tsx raiz da feature (integração ao roteador do Portal)
```

## 4. Backend — contratos delegados novos (engineering-api)

| Rota | Owner downstream | Delegação | Estado honesto |
|---|---|---|---|
| `GET /v1/lmps/goal-context` | Strategic Indicators (`/engineering/lmps/dashboard/summary`) | Bearer humano | `forbidden`/`unavailable` → `{status}` explícito |
| `GET /v1/lmps/department-idd` | Strategic Indicators (`/dashboard/department-idd`, `department_id=engineering`) | Bearer humano | idem |
| `GET /v1/lmps/nonconformities/streak` | NC owner (`/engineering/lmps/nonconformities/streak`) | Bearer humano | idem |
| `GET /v1/products/{code}/structure` | Products (`/products/{code}/structure`) | Bearer humano | idem |

- `engineering.access` via Core em todas; principal humano exigido;
  `engineering.manage` isolado → 403; sem token → 401; S2S → 401.
- Implementação: `infrastructure/gateways/delegated_auxiliary.py` +
  `interface/http/routes/product_routes.py`; wiring em `main.py` e
  `lmp_composer.py`; allowlists OpenAPI atualizadas; testes em
  `tests/test_lmp_routes.py`/`test_auth_middleware.py`/`test_health.py`.

## 5. Frontend — adaptações relevantes

| Item | Decisão |
|---|---|
| `api/httpClient.ts` da feature | **delega** em `src/api/httpClient.ts` (getJson) — Bearer do host, caller-app `engineering`, timeout 15s, `HomeApiError` tipado. Segunda fonte de token **removida**. |
| `lmpApi.ts` | `ENGINEERING_API_BASE=/apps/engineering-api/v1`; datas normalizadas ISO; path `/lmps` sem barra final; E-LMP-01 consolida items+summary+charts. |
| `useLmpsDashboard` | 1 chamada `/v1/lmps` (era 3 no legado) + `goal-context` paralelo; metas mescladas ao summary (campos disjuntos); `null` quando unavailable/forbidden — **nunca meta inventada**. |
| `lmpNonconformityApi.ts` | novo adapter READ-only do streak via `/v1/lmps/nonconformities/streak`. |
| `productApi.ts` | `/v1/products/{code}/structure` (delegado, forbidden honesto). |
| `departmentIddApi.ts` | `/v1/lmps/department-idd` com `department_id`, competence, datas ISO, branch. |
| Rotas | `LMPS_BASE_PATH=/apps/engineering/lmps`; `resolveEngineeringRoute` view `lmps`; `LmpsFeature` replica o padrão do App legado (dashboard montado oculto no detalhe). |
| NC | nav → link externo `LEGACY_NONCONFORMITIES_HREF` para o MFE legado (operacional e autorizado); paths internos `nonconformities*` → estado pendente governado com CTA. **Zero write.** |
| Catálogo | `lmps` internal view, `requiredPermission: "engineering.access"` — `dashboard-lmps.view` **não** libera (teste negativo dedicado). |
| Manifest | rota `/apps/engineering/lmps` declarada (`showInMenu:false`); matching por maior prefixo já cobria aninhadas. |
| Help sync | Ajuda e card "Em breve" da Overview atualizados (CTA real para a feature). |
| CSS | `lmps.css` importado via `index.css`; seletor global `*{box-sizing}` removido — escopo `.dashboard-lmps` já existente. |
| plugin-ui | shim `plugin-ui.d.ts` estendido com a superfície real consumida (chart kit, filters kit, table kit, exports, goal/IDD, operational units, documento PDF) — contratos extraídos da fonte, não inventados. |
| Deps | `recharts ^3.10.1` adicionado (mesma versão do plugin-ui); `xlsx` via motor federado. |

## 6. Verificações executadas

### 6.1 Estáticas

| Comando | Resultado |
|---|---|
| `pytest engineering-api/tests/` | **311 passed** |
| `npm run typecheck` (engineering) | 0 erros |
| `npm run lint` | 0 erros, 11 warnings (padrão `set-state-in-effect` herdado do código legado — sem mudança de comportamento) |
| `npm run test` | **119 passed** (14 arquivos; +25 testes novos: contratos de adapter, parser de rotas, round-trip de filtros, permissão legada negativa) |
| `npm run build` | OK (remoteEntry + bundle novo servindo) |
| Audits `phase3`/`platform_guardrails`/`openapi_contracts`/`fastapi_authz`/`backend_boundaries` (base `49eee1`) | **0 findings** em todos |

### 6.2 Smoke real (gateway `http://localhost`, usuário com `engineering.access`)

| Verificação | Resultado |
|---|---|
| `GET /v1/lmps?page_size=5` | 200 · 245 itens · `items+summary+charts+provenance` |
| Paridade KPIs vs `/apps/api-delpi/.../dashboard/summary` (out/2026) | **0 diffs**: `avg_lead_time=2.5`, `percent_dentro_prazo=100`, `total_lmps=10`, `total_items=14` |
| `GET /v1/lmps/003696` (detalhe) | 200 · available · 1 produto `80016697` |
| `GET /v1/lmps/003696/history/events` + `/flow` | 200 · available |
| `GET /v1/lmps/goal-context` | 200 · available · 10 campos `goal_*` |
| `GET /v1/lmps/department-idd` | 200 · available |
| `GET /v1/lmps/nonconformities/streak` | 200 · available |
| `GET /v1/products/80016697/structure` | 200 · available · 5 itens BOM |
| Sem token → `/v1/lmps` | **401** (fail-closed) |
| Token S2S (`client_credentials` engineering-api) → todas as rotas funcionais | **401** (principal não-humano rejeitado) |
| `remoteEntry.js` do MFE reconstruído | 200 (hash novo) |

### 6.3 Não executado (registro honesto)

- **Paridade visual em browser**: `TEST_NOT_RUN` — sem automação de browser
  disponível no ambiente. Build + contratos + smoke de API verificados;
  comparação visual desktop/tablet/mobile fica para execução humana com as
  capturas de referência da Coordenação.
- **Auto-refresh de 2 min**: não existe no código legado (verificado por
  busca integral — refresh é manual via `onRefresh`). Comportamento
  idêntico preservado; a premissa da missão diverge do baseline real.

## 7. Boundary e segurança

- AuthZ funcional exclusivamente `engineering.access` (Core/backend-first).
- Residual legado documentado: `dashboard-lmps.view` permanece no manifest
  do MFE legado (operacional); **não** concede acesso à feature nova
  (teste dedicado).
- Zero `engineering.*` em guards da api-delpi; delegação por Bearer humano;
  sem S2S no navegador; sem secrets no frontend.
- Storage keys `dashboard-lmps:*` (localStorage) e `documentTitle` de
  export preservados do legado — prefs do usuário compartilhadas entre as
  duas superfícies durante coexistência (decisão consciente, sem
  violação de contrato).

## 8. Residuais e pendências

1. Paridade visual browser: `TEST_NOT_RUN` (item 6.3).
2. NC READ/WRITE: nav externa + estado pendente; contrato e owner
   aguardam gate dedicado (não há writes no Portal).
3. `documentTitle`/storage keys namespace legado — débito cosmético
   documentado, remover no cutover governado.
4. Filtros multi-seleção operam client-side sobre a página carregada
   (≤500 itens) — semântica idêntica ao legado.
5. `evolutionData` não é contrato — agregação apresentacional sobre
   `items` de E-LMP-01 (como planejado na G4.C).

## 9. Veredicto

`ACCEPT_WITH_RESIDUAL` — dashboard funcional integrado ao Portal com
contratos oficiais, AuthZ backend-first, paridade de dados real (0 diffs
nos KPIs testados), zero regressão no legado e sem cutover. Residuais
honestos: paridade visual pendente de execução em browser, NC em
readiness governada, débitos cosméticos listados.

## 10. Próximo passo bounded

Coordenação revisa; execução humana da matriz de paridade visual
(protocolo do item 16 da missão); gate dedicado para NC READ/WRITE e
decisão de cutover **não** iniciados.
