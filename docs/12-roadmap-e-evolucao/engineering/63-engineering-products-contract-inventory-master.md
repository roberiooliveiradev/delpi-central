# 63 — ENGINEERING.PRODUCTS — Documento Mestre de Inventário de Contratos

Status: `LIVING_DOCUMENT` — atualizado continuamente ao longo de G2–G9.
Missão: `ENGINEERING.PRODUCTS.E2E.MASTER.R1` (Plano Mestre doc 62; spec visual/funcional doc 61).
Baseline de reancoragem: `BASE_HEAD=848d77c86efa85774677e54388533abac55514b8` (=`origin/main` no G0).

## 0. Convenções de estado

- Capacidade: `PROVEN` (contrato existe no código e foi inspecionado) · `TO_INVENTORY` (suspeito, ainda não confirmado) · `PLANNED` (a implementar nesta missão) · `TARGET` (desejado, sem contrato) · `OWNER_BLOCKED` (depende de decisão/contrato de outro owner).
- Evidência/teste: `PASS` · `FAIL` · `PENDING` · `INCONCLUSIVE` · `TEST_NOT_RUN` · `STALE_EVIDENCE`.

## 1. Authorities e fontes lidas

| Fonte | Papel | Estado |
|---|---|---|
| Keycloak | IdP OAuth/OIDC; emite JWT humano | PROVEN |
| Core | RBAC efetivo (`/me`, grants) | PROVEN |
| API DELPI (`api-delpi`) | Owner oficial de Produtos/TOTVS (SB1, SG1, SA5), desenhos (file server) | PROVEN |
| Engineering API (`engineering-api`) | Façade/orquestrador do contexto Engenharia; delega Bearer humano | PROVEN |
| TOTVS/Protheus | Source of truth cadastral atrás da API DELPI | PROVEN (via owner) |
| Cockpit do Operador / file server | Owner do acervo de desenhos PDF (mount `DRAWING_PDF_LIBRARY_*`) | PROVEN (via owner) |
| Portal Engenharia (`plugins/engineering`) | Host frontend; consome engineering-api | PROVEN |
| EVA/MCP (`tool_bridge`/`semantic_bridge`) | Consumidor semântico governado | PROVEN |

## 2. Matriz de contratos — capacidade por capacidade

Formato: `OWNER → SOURCE OF TRUTH → ROUTE → REQUEST → RESPONSE → AUTHN/AUTHZ → CONSUMER → TESTE → EVIDÊNCIA`

### 2.1 Busca/listagem de produtos — `PROVEN`

- OWNER: API DELPI → SOURCE: TOTVS SB1 (via `ProductQueryRepositoryPort.search_products`)
- ROUTE: `GET /products/search` (`api-delpi/app/interface/http/routes/product_routes.py`, `search_products_route`, contract `search_products`)
- REQUEST (query): `code`, `description`, `group_code`, `subgroup`, `product_type` (lista CSV de 2 chars, ex. `MP,PI,PA`), `customer_reference`, `page>=1`, `page_size` (page_50_500), `sort`, `direction`. Filtro por "situação" (active/blocked) **não exposto** como query — gap registrado; `sort` validado contra allowlist no repositório.
- RESPONSE: envelope `product_success`, `operation_id=search_products`, `entity=product_search`, `shape=paged_list`; `data` = `Page[Product]` (`items` + `total`/`page`/`page_size`).
- AUTHN/AUTHZ: Bearer humano; `@require_any_permission(ENGINEERING_LMP_ACCESS)` = qualquer uma de `api-delpi.access`, `dashboard-engineering.view`, `dashboard-lmps.view`. **Precedente aprovado**: perfis de Engenharia (role "Analista de Engenharia - SC") possuem `dashboard-engineering.view`/`dashboard-lmps.view` → acesso efetivo sem `api-delpi.access`.
- CONSUMER: hoje LMP/NC enrichment; engineering-api façade **PLANNED**; EVA semantic `product.search` **PLANNED**.
- TESTE: `api-delpi/tests/test_product_routes_meta.py` + use-case tests — `TEST_NOT_RUN` nesta missão (rodar em G6).
- EVIDÊNCIA: código lido; `engineering` users passam por `dashboard-engineering.view`.

### 2.2 Detalhe cadastral — `PROVEN` (owner) / `PLANNED` (façade + narrowing)

- OWNER: API DELPI → SOURCE: TOTVS SB1
- ROUTE: `GET /products/{code}` (`PRODUCT_DETAIL`, `response_model=ProductDetailResponse`)
- REQUEST: `code` (path), `view=full|summary`, `legacy` (reservado).
- RESPONSE: `shape=product_snapshot`, `data.product` = campos da entidade `Product`. **`view=full` e `view=summary` incluem campos comerciais/custo/fiscais** (`sale_price`, `standard_cost`, `last_purchase_price`, `icms_rate`, `ncm_ipi_position`, …). Spec 61 proíbe expor custo/preço/fiscal sem contrato → **PLANNED**: novo `view=engineering` (allowlist cadastral/engenharia, sem comercial/custo/fiscal) no owner `narrow_product_fields`.
- AUTHN/AUTHZ: `@require_permission(API_DELPI_ACCESS)` — **gap**: perfis de Engenharia sem `api-delpi.access` recebem 403. Decisão (ver §4): estender para `require_any_permission(ENGINEERING_LMP_ACCESS)` no owner — aditivo, mesmo precedente de `search_products`.
- CONSUMER: engineering-api façade **PLANNED**; EVA `product.detail` **PLANNED**.
- TESTE: `test_product_routes_meta.py` — `TEST_NOT_RUN`.
- EVIDÊNCIA: `protheus_field_normalizer.PRODUCT_DETAIL_SUMMARY_FIELDS` lido — confirma exposição de preço/custo no summary atual.

### 2.3 Estrutura/BOM — `PROVEN` (ponta a ponta já existente)

- OWNER: API DELPI → SOURCE: TOTVS SG1 (via `build_list_structure_use_case`)
- ROUTE owner: `GET /products/{code}/structure` — params `max_depth`, `page`, `page_size`; `shape=hierarchy`.
- ROUTE façade (já existente): `GET /v1/products/{product_code}/structure` em `engineering-api/engineering_app/interface/http/routes/product_routes.py` — `engineering.access` + `principal_type=="user"` + delegação Bearer (`ApiDelpiDelegatedAuxiliary.fetch_product_structure`).
- AUTHN/AUTHZ: boundary `engineering.access`; downstream owner exige `api-delpi.access` → 401/403 viram `forbidden/owner_denied` honesto. **Gap AuthZ idêntico ao do detalhe** — perfis sem `api-delpi.access` ficam forbidden; resolvido pela mesma extensão para `ENGINEERING_LMP_ACCESS` (§4).
- CONSUMER: Portal (PLANNED), EVA semantic `product.structure` + tool `get_product_structure` — PROVEN.
- TESTE: `engineering-api/tests/test_lmp_routes.py`, `test_eva_mcp.py`, `api-delpi/tests/test_shared_structure_intermediates_routes.py` — existentes; `TEST_NOT_RUN` nesta missão.
- EVIDÊNCIA: código lido nas duas pontas.

### 2.4 Onde é usado (BOM reversa) — `PROVEN` (owner)

- OWNER: API DELPI → SOURCE: TOTVS SG1 reversa (`build_list_parents_use_case`)
- ROUTE: `GET /products/{code}/parents` (`PRODUCT_PARENTS` — summary "Onde o produto é usado (produtos pai / BOM reversa)")
- REQUEST: `code`, `max_depth`, `page`, `page_size`. RESPONSE: `shape=hierarchy`, `entity=product_parents`.
- AUTHN/AUTHZ: `require_permission(API_DELPI_ACCESS)` — mesmo gap §4.
- CONSUMER: engineering-api façade + EVA `product.where_used` — **PLANNED**.
- TESTE/EVIDÊNCIA: código lido; testes owner existentes — `TEST_NOT_RUN`.

### 2.5 Fornecedores do produto — `PROVEN` (owner)

- OWNER: API DELPI → SOURCE: TOTVS SA5 (`build_list_product_suppliers_use_case`)
- ROUTE: `GET /products/{code}/suppliers` (`PRODUCT_SUPPLIERS`)
- REQUEST: `code`, `page>=1`, `page_size` (page_50_500). RESPONSE: `shape=paged_list`, `entity=product_suppliers`.
- AUTHN/AUTHZ: `require_permission(API_DELPI_ACCESS)` — gap §4. Vínculo fornecedor é dado comercial sensível → ficha expõe somente vínculo (código/nome do fornecedor) já autorizado pelo owner; preço de compra **não** entra na visão engineering.
- CONSUMER: façade + EVA `product.suppliers` — **PLANNED**.
- EVIDÊNCIA: rota lida (`product_routes.py` ~L1249).

### 2.6 Desenhos técnicos — `PROVEN` (owner, contrato do acervo file server)

- OWNER: API DELPI → SOURCE: acervo PDF do file server (mount `DRAWING_PDF_LIBRARY_*`; `DrawingPdfLibraryStorage` — mesmo acervo consumido pelo Cockpit do Operador; localização por padrão de nome `CODIGO.pdf`, `_R<n>` revisão, `N-M` variante).
- ROUTES (`api-delpi/app/interface/http/routes/product_drawing_routes.py`):
  - `GET /products/drawings` — catálogo com filtros `code`/`exact`, `filename`, `revision`, `file_kind`, flags variante/revisão, range `modified_at`, `size`, `page`/`page_size`, `sort`/`direction` (allowlist em `_ALLOWED_SORT_FIELDS`).
  - `GET /products/{code}/drawing` — metadados (`found`, `filename`, `revision`, `variant_suffix`, `size_bytes`, `modified_at`, `media_type`).
  - `GET /products/{code}/drawing/pdf` — `FileResponse` `application/pdf` inline.
- ERROS honestos: acervo indisponível → **503** (`DrawingPdfLibraryUnavailableError`); sem desenho → **404**; path/storage inválido → 422/404. Distinção "produto sem desenho" vs "fonte indisponível" já implementada no owner.
- AUTHN/AUTHZ: `require_permission(API_DELPI_ACCESS)` nas 3 rotas — gap §4.
- CONSUMER: façade `GET /v1/products/{code}/drawing` + `…/drawing/pdf` (proxy binário) **PLANNED**; EVA `product.drawing_metadata` **PLANNED**; viewer do Portal consome somente via engineering-api — nunca file share direto.
- EVIDÊNCIA: rotas + storage lidos.

### 2.7 Histórico / revisões — `PARTIAL` / `OWNER_BLOCKED` (parcial)

- Existe: `GET /products/{code}/purchase-price-history` e `GET /products/{code}/purchase-budget-history` (`require_permission(API_DELPI_ACCESS)`, datas `start_date`/`end_date`, `branch`, `history_limit`). São históricos **de compras**, não revisão cadastral — e carregam preço (sensível).
- Campos de revisão cadastral: `Product.current_revision` (B1_REVATU), `last_revision_date` (B1_UREV) — disponíveis no detalhe.
- **Não existe** contrato de histórico de revisões cadastrais do produto (log de alterações SB1) nem endpoint de eventos → `OWNER_BLOCKED`: requer owner TOTVS/API DELPI. Decisão de implementação: aba Histórico renderiza revisão cadastral atual (proveniente do detalhe) +, quando autorizado, histórico de preço de compra como seção separada; ausência de histórico cadastral vira estado honesto "não implementado pela fonte".
- EVA `product.history` — PLANNED limitado ao que for `PROVEN` (revisão cadastral + purchase-price-history quando autorizado).

### 2.8 Edição (WRITE) — `OWNER_BLOCKED`

- Inventário das rotas de produto: apenas `POST /products/physical-locations` e `POST /products/inventory-blocks` — **ambos READ lógico** (batch lookup), não escrita.
- Não existe `PUT/PATCH/DELETE` de produto, fornecedor-vínculo, BOM ou desenho em `product_routes.py`/`product_drawing_routes.py`.
- Sem contrato WRITE oficial → G3 = **sem edição funcional**; ficha renderiza `Visualizar` apenas e Editar em estado honesto bloqueado (spec 61 "Editar só quando contrato WRITE oficial e autorização existirem"). EVA `execute` não recebe ações de produto.

### 2.9 Façade engineering-api existente — `PROVEN`

- `GET /v1/products/{product_code}/structure` (única rota de produtos hoje).
- Padrão: `require_any_permission(["engineering.access"])` → `resolve_user_context()` → exige `principal_type=="user"` → `HomeSourceContext(user_id, access_token, request_id)` → `ApiDelpiDelegatedAuxiliary` → `DownstreamClient.get(path, params, access_token, request_id)` → Bearer humano + `X-Delpi-Caller-App: engineering-api` + `X-Request-Id`.
- Erros: 401/403 downstream → `{status:"forbidden", reason:"owner_denied"}`; outros → `unavailable`; payload não-dict → `contract_error`. Sem S2S, sem bypass.
- `DownstreamClient` é JSON-only → **PLANNED**: `get_raw` binário para proxy do PDF de desenho.

### 2.10 EVA — registro semântico atual — `PROVEN` parcial

- `semantic_bridge.py`: `("product","structure")` → `tool_get_product_structure`. Catálogo de resources inclui `product`/`products`.
- `tool_bridge.py`: tool legada `get_product_structure` (READ-only, delegada) mapeada para `read(product.structure)`.
- **PLANNED**: ações `product.search`, `product.detail`, `product.where_used`, `product.suppliers`, `product.drawing_metadata`, `product.history` (se proven) — mesmas tools semânticas existentes (`read`/`analyze`), sem tools MCP novas por aba.

### 2.11 Padrões frontend Portal Engenharia — `PROVEN` (inventário de convenções)

- `@delpi/plugin-ui`: `PageHero`, `EngineeringSectionRouteCard`, `EngineeringTimeline`, `InitialsAvatar`, `FieldLabel`+`HelpTooltip`, tokens light/dark.
- Home `ROUTE_ICONS` (Lucide, size=16) — `products: <Package/>` a adicionar.
- Padrões de NC/LMP para listagem, ficha, tabs, estados honestos, Playwright SSO real (`plugins/engineering/e2e`), vitest 157 testes.

## 3. Gaps e decisões de contrato

| # | Gap | Classificação | Decisão |
|---|---|---|---|
| G-1 | Rotas owner exigem `api-delpi.access`, ausente nos perfis de Engenharia (search é exceção, já usa `ENGINEERING_LMP_ACCESS`) | contrato owner | Estender read-routes necessárias para `require_any_permission(ENGINEERING_LMP_ACCESS)` — aditivo, precedente existente, no próprio owner |
| G-2 | `view=full/summary` do detalhe expõe preço/custo/fiscal | spec 61 | Novo `view=engineering` com allowlist cadastral no owner |
| G-3 | Sem filtro por "situação" (ativo/bloqueado) na busca | menor | Registrar; busca entrega `active`/`blocked` por item — filtro server-side fica `OWNER_BLOCKED` até contrato |
| G-4 | Sem histórico de revisões cadastrais | OWNER_BLOCKED | Aba Histórico = revisão cadastral + purchase-price-history se autorizado + estado honesto |
| G-5 | Sem WRITE de produto/BOM/fornecedor/desenho | OWNER_BLOCKED | G3 sem edição; botão Editar bloqueado honesto |
| G-6 | `DownstreamClient` só JSON | técnico | `get_raw` binário para proxy PDF governado |
| G-7 | Sort allowlist da busca owner | validar | Confirmar campos sortáveis no repositório em G2 |

## 4. Decisão de autorização downstream (G-1)

`ENGINEERING_LMP_ACCESS = [api-delpi.access, dashboard-engineering.view, dashboard-lmps.view]` (`api_delpi_permissions.py`). Perfis de Engenharia possuem os dois `dashboard-*` → `require_any_permission` resolve. Extensão **somente-leitura**, aditiva, aplicada a: `/{code}` (detail), `/{code}/structure`, `/{code}/parents`, `/{code}/suppliers`, `/drawings`, `/{code}/drawing`, `/{code}/drawing/pdf`. Não aplicada a rotas comerciais (customers, pricing, purchases, sales…) — fora do escopo da ficha.

## 5. Rotas engineering-api PLANNED (G2)

| Rota façade | Owner downstream | AuthZ boundary |
|---|---|---|
| `GET /v1/products` (search) | `/products/search` | `engineering.access` + owner |
| `GET /v1/products/{code}` (detail, view=engineering) | `/products/{code}` | idem |
| `GET /v1/products/{code}/structure` | `/products/{code}/structure` | PROVEN |
| `GET /v1/products/{code}/parents` | `/products/{code}/parents` | idem |
| `GET /v1/products/{code}/suppliers` | `/products/{code}/suppliers` | idem |
| `GET /v1/products/{code}/drawing` | `/products/{code}/drawing` | idem |
| `GET /v1/products/{code}/drawing/pdf` | `/products/{code}/drawing/pdf` (proxy binário) | idem |
| `GET /v1/products/{code}/purchase-price-history` | `/products/{code}/purchase-price-history` | idem (aba Histórico, seção autorizada) |

## 6. Estado de implementação (atualizado em G6)

### 6.1 Rotas engineering-api entregues — `PROVEN`

Todas em `engineering-api/engineering_app/interface/http/routes/product_routes.py`,
`engineering.access` + principal humano obrigatório + Bearer delegado ao owner:

| Rota façade | Owner | Estado |
|---|---|---|
| `GET /v1/products` | `GET /products/search?view=engineering` | PROVEN (E2E dev) |
| `GET /v1/products/{code}` | `GET /products/{code}?view=engineering` | PROVEN |
| `GET /v1/products/{code}/structure` | `GET /products/{code}/structure` | PROVEN (pré-existente) |
| `GET /v1/products/{code}/parents` | `GET /products/{code}/parents` | PROVEN |
| `GET /v1/products/{code}/suppliers` | `GET /products/{code}/suppliers?view=engineering` | PROVEN |
| `GET /v1/products/{code}/drawing` | `GET /products/{code}/drawing` | PROVEN |
| `GET /v1/products/{code}/drawing/pdf` | `GET /products/{code}/drawing/pdf` (proxy binário `get_raw`) | PROVEN |
| `GET /v1/products/{code}/purchase-price-history` | `GET /products/{code}/purchase-price-history` | PROVEN (forbidden honesto p/ perfis sem `api-delpi.access` — owner mantido estrito por carregar preço) |

Erros: owner 401/403 → `403 forbidden`; 404 → `404 not_found`; demais → `502 unavailable` com `data` de diagnóstico. `meta.operationId` em todos os envelopes.

### 6.2 Mudanças no owner (api-delpi) — `PROVEN`

- `PRODUCT_DETAIL_VIEW_VALUES += "engineering"`; `narrow_product_fields(view="engineering")` aplica `PRODUCT_DETAIL_ENGINEERING_FIELDS` (cadastral/engenharia/logística — **sem** `sale_price`, `standard_cost`, `last_purchase_price`, fiscais).
- `narrow_supplier_fields(view="engineering")` remove `last_price`/`last_price_date` do vínculo.
- `narrow_paged_items` aplica narrowing item a item em `search` e `suppliers`.
- AuthZ aditivo `require_any_permission(ENGINEERING_LMP_ACCESS)` em: `/{code}` detail, `/{code}/structure`, `/{code}/parents`, `/{code}/suppliers`, `/{code}/drawing`, `/{code}/drawing/pdf` (+`/{code}/drawings` no mesmo arquivo). `/{code}/summary`, `purchase-price-history`, `purchase-budget-history` e rotas comerciais **permanecem estritas** (`API_DELPI_ACCESS`).

### 6.3 EVA — paridade semântica — `PROVEN`

`read(product.*)` despacha somente por allowlist `(entity, action)` — sem tools MCP novas:

| Ação | Handler | Fonte |
|---|---|---|
| `product.search` | `tool_search_products` | façade search |
| `product.detail` | `tool_get_product_detail` | view=engineering |
| `product.structure` | `tool_get_product_structure` | PROVEN pré-existente |
| `product.where_used` | `tool_get_product_parents` | parents |
| `product.suppliers` | `tool_get_product_suppliers` | suppliers engineering |
| `product.drawing` | `tool_get_product_drawing` | metadados do acervo (PDF binário só via rota HTTP) |
| `product.history` | `tool_get_product_history` | revisão cadastral + purchase-price autorizado + `revision_history:not_implemented` honesto |

`product.update` registrado em `PLANNED_SEMANTIC_ACTIONS` como `not_implemented` (OWNER_BLOCKED §2.8). Ações fora do allowlist → `unknown_action_error`.

### 6.4 Frontend — `PROVEN`

- `plugins/engineering/src/features/products/` — listagem (hero, filtros oficiais, tabela server-sort/paginação, empty/error/loading honestos) + ficha (breadcrumb, hero compacto, badge `Visualizar`, `Editar` desabilitado com tooltip do gap §2.8, 6 abas na ordem da spec 61 com lazy load por aba e erro independente).
- Rota `/apps/engineering/products*` + catálogo `products` + ícone `Package` em `ROUTE_ICONS`.
- `e2e/specs/products.spec.ts` — 4 testes × 3 viewports (desktop/mobile/tablet), SSO real.
- CSS próprio em `index.css` (tokens `--en-*`, sem duplicar design system).

### 6.5 Estados residuais

- Filtro server-side por situação (ativo/bloqueado): `OWNER_BLOCKED` (§G-3) — badge Situação renderizado por linha.
- Histórico de revisões cadastrais: `OWNER_BLOCKED` (§2.7) — seção honesta `not_implemented`.
- `purchase-price-history` para perfis sem `api-delpi.access`: `forbidden` honesto — dado de preço exige a permissão comercial, intencional.
- Edição: `OWNER_BLOCKED` (§2.8) — sem contrato WRITE.
