# SURI-MCP-FULL-PARITY-P0 — Inventário funcional integral do Portal Suprimentos

Data: 2026-10-30 · Task: `SURI-MCP-FULL-PARITY-P0` · HEAD de referência: `8a822e29c1`
Escopo: inventário + contrato + planejamento. **Zero implementação nesta etapa.**

Fontes provadas em código (não documentação): `plugins/supplies` (manifest + App.tsx + features + api clients), `supplies-api` (14 blueprints, `auth_decorators`, `supplies_permissions`, gateways), `purchase-requests-api`, `api-delpi`, `external-data-api`, `core-api`, `delpi_mcp` shared.

## 1. Modelo de autorização efetiva

| Código | Uso |
|---|---|
| `supplies.access` | Todas as views exceto admin; leitura, exports e writes de preferência/workflow |
| `supplies.manage` | `/administration` (manifest), `GET /suppliers/integration-status`, transições comex `manage`-gated, ver perfil de outro usuário |
| `estoque-seguranca.access` | Apenas o deep link legado da Home (`safety_stock_below`) — não é permission da página |
| Filial (`01`/`02`) | **Filtro, nunca permissão** (BRANCH-AUTHZ.DOCS.R1 reconciliado); `require_unit(s)` fail-closed |
| `mcp:tools` | Binding de transporte OAuth — nunca permissão de negócio |

Policies BFF: `can_enter_shell` (access OR manage), `can_use_portal/analytics/operations/purchase_requests/market_intelligence/export` (access), `can_administer` (manage). O MCP reconstrói `EffectiveUser` via Core `/me` com o Bearer do chamador e reaplica as mesmas policies — **paridade de AuthZ já estrutural**.

## 2. Superfície real do Portal (manifest × código)

### 2.1 Páginas REAIS (12 + detalhes/rotas ocultas)

| Página | Rota | Estado | Capacidades efetivas | Endpoint(s) BFF | Producer | AuthZ |
|---|---|---|---|---|---|---|
| Início/Hub | `/apps/supplies` | REAL | grid filtrado por capability, busca de rotas, favoritos, atalhos com contagens reais (`purchase_requests_ordering/receiving`, `purchase_orders_late`, `late_deliveries`, `safety_stock_below`) | `/me/capabilities`, `/me/preferences` + dados das páginas-fonte | pg + producers | access |
| Visão geral | `/overview` | REAL | período presets + from/to + branch, refresh, CTA OTD | `GET /analytics/overview` (fan-out: OTD, stock-value, turnover, CPV, negotiation-savings, safety-stock, POs, SCs abertas, indicadores SI via `/dashboard/department-indicators`) | api-delpi + PR-api + SI via api-delpi | access |
| OTD Analytics | `/analytics/otd` | REAL (oculta, não-manifest) | gauges por filial, série temporal | `GET /analytics/otd`, `GET /analytics/otd/series` | api-delpi | access |
| Solicitações de compras | `/purchase-requests` | REAL | filtros (período, unidade, nº, produto, solicitante facet, CC facet, etapa), chips de atenção, sort/paginação server-side, export XLSX | `GET /purchase-requests[/summary|/requesters|/cost-centers|/export|/{branch}/{num}]`, `GET /purchase-requests/requesters/{id}/photo` | **PR-api** + core-api (identity enrich + photo scope guard) | access |
| Pedidos de compra | `/purchase-orders` + detalhe | REAL | mesma família de filtros; export XLSX; link fornecedor→ficha | `GET /purchase-orders[/export|/{branch}/{num}]` | api-delpi | access |
| Entregas/atrasos | `/deliveries` | REAL | presets, unidade, pontualidade/status | `GET /deliveries/late` (paged comp) | api-delpi | access |
| Fornecedores lista | `/suppliers` | REAL | busca, blocked-state, UF; widget manage-only integration-status | `GET /suppliers`, `GET /suppliers/integration-status` (manage) | api-delpi (S2S) | access / manage no widget |
| Fornecedor 360 | `/suppliers/{code}/{store}` | REAL DETAIL | seções da ficha, edição (ver W), enrichment reviews | `GET /suppliers/{code}/{store}`, `GET /suppliers/catalogs/{kind}` (14 kinds allowlist), `GET /suppliers/postal-codes/{cep}`, `GET /suppliers/operations/{id}`, `GET/POST .../enrichment-reviews[...]` | api-delpi(S2S) + pg + registry provider | access |
| Novo fornecedor | `/suppliers/new` | REAL (oculta) | fluxo assistido: CNPJ/nome/manual, preview (read-only), duplicados, CEP assist, revisão | `POST /suppliers/creation-preview` (semântica read-only), `GET /suppliers/existing-suppliers`, `POST /suppliers` (B-01) | api-delpi(S2S) + registry provider | access |
| Estoque | `/inventory` | REAL | filial, armazém, tabela paginada | `GET /inventory/stock-balances/summary|items` | api-delpi | access |
| Estoque de segurança | `/safety-stock` + detalhe | REAL | filial, status/chips, grupo, UM, busca, toggles, detalhe página, branch-choice dialog | `GET /safety-stock/filters|summary|items`, `GET /safety-stock/items/{code}/details|suppliers` | api-delpi | access |
| Auditoria de consumo | `/consumption-audit` | REAL | busca OP (fragmento + sugestões), presets, filtros avançados, seleção 2–10, comparação, detalhe OP | `GET /consumption-audit/orders[/{op}]`, `GET /consumption-audit/comparison` | api-delpi(S2S, scope `consumption-audit.read`) | access |
| Inteligência de Mercado | `/market-intelligence` | REAL | Metais/Câmbio/Indicadores, multi-select instrumentos, granularidade, view chart/table/compare, export CSV/XLSX, comex selector (busca produto, NCM direto, catálogo NCM, views salvas CRUD, governança manage) | 9× `GET /market-intelligence/*`, `/comex/products/search`, `/comex/ncm-governance[...]`, `/comex/views[CRUD]` | external-data-api(S2S) + api-delpi(S2S) + pg | access (+manage nas transições) |
| Perfil de usuário | `/users/{id}` | REAL (oculta) | identidade+foto, atalhos, preferências (self), SCs relacionadas | `GET /users/{id}/profile|related-requests|photo`, `PATCH` (self) | core-api + PR-api + pg | self \| manage |
| Ajuda/Manual | `/help` | REAL | TOC, deep-links, FAQ, glossário | nenhum | in-proc content | access |

### 2.2 Páginas PLACEHOLDER (manifest rota, código PlaceholderPage)

`my-tasks` · `products` · `negotiations` · `indicators` · `administration` — sem feature code. São **TARGET/PLANNED do Portal**, não entram no denominador de paridade atual.

### 2.3 Writes reais existentes

| Write | Endpoint | Destino | Estado |
|---|---|---|---|
| Preferências | `PATCH /me/preferences`, `PATCH /users/{id}/profile` | pg `supplies` | PROVEN (self) |
| Enrichment review/decisions/bulk/prepare-update | `POST .../enrichment-reviews[...]` | pg (draft-only; `write_gate_enabled=False` — nunca ERP por design) | PROVEN |
| Comex NCM request | `POST /comex/ncm-governance` | pg | PROVEN |
| Comex transition | `POST /ncm-governance/{id}/transition` | pg + `PUT /v1/market-data/comex/ncm-allowlist` na ED-api (best-effort audited) | PROVEN (manage p/ algumas) |
| Comex views CRUD | `POST/PUT/DELETE /comex/views[/{id}]` | pg | PROVEN |
| Supplier create | `POST /suppliers` → api-delpi `POST /integrations/protheus/suppliers` | **Protheus ERP** | **PROVEN** (revisão 2026-10-30, `SURI-MCP-SUPPLIERS-WRITE-001` — classificação BLOCKED anterior era `STALE_EVIDENCE`; gates `=true` em prod, cadeia validada em runtime) |
| Supplier update | `PUT /suppliers/{code}/{store}` → api-delpi `PUT /integrations/...` | **Protheus ERP** | **PROVEN** (idem — cadeia completa até o REST provada com fornecedor inexistente → `PROTHEUS_SUPPLIER_NOT_FOUND`) |

### 2.4 Producers canônicos (ownership)

| Owner | Responsabilidade |
|---|---|
| `supplies-api` | BFF, AuthZ, composição, pg `supplies` |
| `api-delpi` | Regras/consultas Protheus, catalogs, CEP, S2S scope enforcement, supplier REST writes (gates `PROTHEUS_SUPPLIER_CREATE/UPDATE_ENABLED=true` em prod — 2026-10-30) |
| `purchase-requests-api` | SCs, CCs, requesters, visibility-scopes/mappings admin (`_require_admin` interno), notification events |
| `strategic-indicators-api` | Metas/indicadores — alcançada **via** api-delpi `/dashboard/department-indicators` |
| `external-data-api` | Market data, comex imports, quotes, company registry provider |
| `core-api` | Identidade, permissões efetivas, fotos |

## 3. Superfície SURI hoje (revisão `SURI-MCP-SUPPLIERS-WRITE-001`, 2026-10-30)

| Tool | Cobertura executável | Estado |
|---|---|---|
| `get_context` | `context` (EffectiveUser+units), `catalog` | **PROVEN** |
| `read` | `entity=purchase_orders` apenas: `search`, `get` | **PROVEN** (1 entidade) |
| `analyze` | `purchase_orders_summary` apenas | **PROVEN** |
| `knowledge` | corpus versionado search/get/sources | **PROVEN** |
| `execute` | `entity=suppliers`: `create`, `update` — batch ≤10, `idempotency_key`, dup-precheck, correlation-id, outcome por operação | **PROVEN** (30 testes, suite 100/100) |
| `delete` | não registrada | TARGET contratual |

Reads passam por `DelpiApiGateway` com Bearer do usuário; writes passam
por `DelpiS2SApiGateway` (credencial S2S individual, scopes
`suppliers.create`/`.update` enforceados upstream) — paridade de caminho
com o BFF em ambos os casos.

## 4. Bloqueios revalidados (runtime/contrato, não doc)

| Bloqueio | Evidência |
|---|---|
| ~~Supplier ERP write OFF~~ | **SUPERADO 2026-10-30** — classificação anterior era `STALE_EVIDENCE`: gates `PROTHEUS_SUPPLIER_{CREATE,UPDATE}_ENABLED=true` em runtime; UPDATE provado end-to-end até o REST (`PROTHEUS_SUPPLIER_NOT_FOUND` p/ `999999/01`); CREATE com gate aberto até `resolve_actor_codusr` (POST não disparado por segurança); ver seção «Reconciliação» da MATRIX |
| SC create/approve/cancel | **Não existe no Portal** — `purchase-requests-api` só expõe reads + admin mappings; PRs nascem no ERP |
| Metais dados reais | `source_use_pending` quarentena LME; egresso `api.metalcharts.org` bloqueado por firewall Sophos em prod; storage permanente gated `PROVIDER_PERMANENT_STORAGE_RIGHT=PENDING` |
| Enrichment source | `COMPANY_REGISTRY_PROVIDER=unavailable` default fail-closed |
| `my-tasks` | residual sem owner (HOME-ATTENTION) |
| E11 safety-stock | `GATE-FEATURE=INCONCLUSIVE` — visual autenticado pendente (backend+frontend provados) |
| Administração | não implementada; admin real hoje = integration-status + comex governança inline (manage) |

## 5. Referência para tools de escrita (patterns existentes)

- **CLARA**: `execute`/`delete` governadas — capability registry, prepare→proposal(PG, TTL 900s, actor-bound, single-use)→commit, Portal step-up consent, idempotency, read-back `OUTCOME_VERIFICATION_FAILED`, batch.
- **EVA**: env flags `*_ACT_ENABLED*`, elicitation MCP com `target_echo`.
- **TÉO**: PREPARE tools → `commit_proposal`. **VISTA**: `prepare_change`→`commit_proposal` (idempotency obrigatório).
- **CAIO**: `execute`/`delete` stubadas `not_implemented` (deny-by-default honest).
- Shared `delpi_mcp.tool_metadata` já contém vocabulário `PREPARE`/`ACT` congelado — SURI adota sem mudar shared.

Pattern recomendado p/ SURI: closed `(entity, action)` capability registry + prepare/commit + confirmação explícita só para DELETE e operações com regra obrigatória; direct path para não-destrutivas inequívocas; idempotency key; read-back; audit channel `mcp/suri`.
