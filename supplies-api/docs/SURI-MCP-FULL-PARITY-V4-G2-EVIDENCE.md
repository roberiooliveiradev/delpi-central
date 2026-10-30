# SURI-MCP-FULL-PARITY-V4-G2 — EVIDENCE

Task: `SURI-MCP-FULL-PARITY-V4-G2` · Execução em worktree `delpi-central-g1-wt` · Base `2aa736eabf` (revisão G1).
Escopo da missão: código, contratos, testes e documentação — **sem deploy produtivo** (gate `SURI-MCP-V4-G2-DEPLOY-001` próprio).
Status por capacidade: `IMPLEMENTED_IN_CODE` / `TESTED_LOCALLY` / `DEPLOYED` / `AUTHENTICATED_RUNTIME_PROVEN`.

## 1. Inventário e contract freeze (G2.0)

Superfície real do Portal mapeada e congelada por ação — espelho exato
dos contratos query da `purchase-requests-api` (FastAPI) e da
`api-delpi` (rotas `/supplies/purchase-orders*`):

| Ação SURI | Rota owner | Vocabulário fechado | AuthZ BFF |
|---|---|---|---|
| `PR search` | `GET /purchase-requests` | branch[], date_from/to, request_number, requester_user_id[], cost_center[], product_code, supplier_code, order_number, overall_stage[], sort_by, sort_dir, page, page_size | `can_use_purchase_requests` + `require_units` |
| `PR summary` | `GET /purchase-requests/summary` | idem − sort/page | idem |
| `PR requesters` | `GET /purchase-requests/requesters` | idem − `requester_user_id`/`overall_stage` | idem |
| `PR cost_centers` | `GET /purchase-requests/cost-centers` | idem − `cost_center` (sem auto-filtro) | idem |
| `PR get` | `GET /purchase-requests/{branch}/{num}` | contexto opcional: `date_from`, `date_to`, `cost_center[]` | idem + `require_unit` |
| `PR export` | `GET /purchase-requests/export` | search − paginação | `can_export_purchase_requests` + `require_units` + branch não-vazio |
| `PO export` | `GET /supplies/purchase-orders/export` | search − paginação | `can_use_operations` + `require_units` |

Freeze aditivo registrado em `SURI-S1-CONTRACT-FREEZE-V3.md` §Adendo
rev.5 (`CATALOG_VERSION = 5`, cinco tools preservadas).

## 2. DECISION-G1 — exportações MCP (G2.3) — **FECHADA**

Alternativas avaliadas contra o contrato corrente:

| Alternativa | Decisão | Motivo |
|---|---|---|
| Binário XLSX/CSV direto | rejeitada | canal de artefato não homologado no transporte MCP vigente; sem contrato de consumo |
| Base64 inline | rejeitada | payload gigante sem limite explícito; segurança/UX ruins |
| Link de download | rejeitada | exige endpoint de download + retenção + auth — escopo novo não autorizado |
| **Dataset JSON + metadados** | **escolhida** | mesmo recorte autorizado; menor mecanismo compatível; precedente EVA `export_nonconformities`; LLM consome linhas diretamente |

Formato homologado: `data.items` = linhas canônicas do owner;
`data.export = {format: "json", row_count, portal_file_formats}`.
Materialização em arquivo permanece exclusiva do Portal.

Foto do solicitante: **não exposta** (bytes exigiriam canal não
homologado). `RequesterPhotoScopeGuard` não é contornado — o universo
autorizado continua sendo a faceta `requesters` enriquecida, e
`photo_url` segue apontando para a rota BFF protegida.

## 3. Implementação (G2.5)

- `constants.py`: `READ_ACTIONS_BY_ENTITY["purchase_requests"]` +
  `purchase_orders.export`; `PR_*_FILTER_KEYS`/`PO_EXPORT_FILTER_KEYS`
  por ação; `CATALOG_VERSION = 5`.
- `schemas.py`: 8 modelos fechados `extra="forbid"`
  (`PurchaseRequest*Filters`, `PurchaseRequestIdentity`,
  `PurchaseOrderExportFilters`).
- `tool_bridge.py`: `_PR_GATEWAY` (`PurchaseRequestsGateway`) +
  `_PR_REQUESTER_IDENTITY` (`RequesterIdentityService`) — mesmos
  singletons/políticas do BFF; `_pr_user`/`_pr_export_user`; handlers
  dedicados por ação; `PurchaseRequestsGatewayError` mapeado com a
  mesma semântica do `_gateway_error_response` do BFF (401/403/404/
  <500/≥500); dispatch `_dispatch_purchase_requests_read`.
- `server.py`: Literals/unions ampliados aditivamente; descrição `read`.
- Nenhuma tool nova, nenhum executor genérico, nenhuma permissão nova,
  nenhum bypass — `READ` permanece read-only (sem create/approve/cancel
  SC — BLOCKED B-03 preservado).

## 4. Testes (G2.6)

Suíte nova: `tests/interface/suri_mcp/test_purchase_requests_read.py`
(41 casos) — positivos por ação, sibling/negativos, unit-scope deny,
export contract, upstream error mapping (404/403/5xx/timeout), isolamento
cruzado SC↔PO↔suppliers.

```text
pytest tests/interface/suri_mcp         → 167 PASS, 0 FAIL
pytest tests (supplies-api completa)    → 888 PASS / 24 SKIP, 0 FAIL
```

Assertions do baseline atualizadas (`catalog_version == 5`, entidade
`purchase_requests` no catálogo, entity desconhecida continua 422).

## 5. Segurança (G2.4)

- AuthZ re-derivada por chamada: `can_use_purchase_requests` /
  `can_export_purchase_requests` / `can_use_operations` — todas
  delegam `supplies.access` canônico do Core `/me`.
- `require_units`/`require_unit` fail-closed (branch vazio/ausente →
  403 — espelha `AuthorizationError` do BFF).
- Export: branch não-vazio obrigatório (espelha BFF).
- Nenhuma permissão criada; Keycloak/Core RBAC/OAuth/audience/scopes
  inalterados; `WWW-Authenticate` em 401 preservado (`_error`).
- Enriquecimento de requester = `RequesterIdentityService` canônico
  (fallback gracioso preservado); foto fora da superfície MCP → guard
  não exercitado nem contornado.
- Nenhum banco de outro owner acessado; erros upstream honestos.

## 6. Residual RBAC do G1 (G2.8)

- **Grant:** `devin-smoke-r4` → role "Portal Suprimentos - Acesso"
  (INSERT direto em `user_roles` durante G1; revogação não comprovada).
- **Caminho canônico identificado:** `RemoveRoleFromUserUseCase` via
  `DELETE /admin/rbac/roles/<role_id>/users/<user_id>` na Core API —
  exige ator com `rbac.manage` + `roles.manage` (UI "Gestão de
  Acessos" consome esse endpoint).
- **Estado nesta execução:** o usuário e o grant não existem no stack
  local/dev (`delpi166-pc` — verificado em `user_entity` do Keycloak e
  `user_roles` do Core, 2026-10-30) — o grant vive no host produtivo,
  que esta sessão não alcança por SSH (rede) nem deve alcançar
  (`local-first-deploy`). Nenhum ator `rbac.manage` está disponível
  nesta execução para chamar a rota autorizada.
- **Classificação:** `EXECUTION_DRIFT` — ação administrativa fora da
  autoridade disponível. **Encaminhado ao owner Core:** revogar
  `user_roles(devin-smoke-r4, <role "Portal Suprimentos - Acesso">)`
  via endpoint acima (ou UI Gestão de Acessos), depois verificar
  permissões efetivas via `/me` — sem UPDATE/DELETE SQL direto.
- O residual **não bloqueia** o código G2 (missão explícita); o usuário
  de smoke do G1 não foi reutilizado em nenhum teste.

## 7. Status

```text
SC_SEARCH / SC_SUMMARY / SC_REQUESTERS / SC_COST_CENTERS / SC_GET / SC_EXPORT
PO_EXPORT (a somar aos PROVEN anteriores PO search/get + analyze)
→ IMPLEMENTED_IN_CODE + TESTED_LOCALLY
DEPLOYED / AUTHENTICATED_RUNTIME_PROVEN → pendentes (gate próprio)
SURI_CATALOG_VERSION = 5 · SURI_TOOL_COUNT = 5 · OAuth inalterado
```

## 8. Residual search

- Nenhuma regra de negócio duplicada: handlers compostos exclusivamente
  por `PurchaseRequestsGateway`, `DelpiApiGateway`,
  `RequesterIdentityService` e `AuthorizationService` canônicos.
- Nenhum acesso direto a banco de outro contexto.
- Nenhuma permissão/escopo inventado; `extra="forbid"` preservado.
- Nenhuma escrita — `execute` (suppliers) inalterado; regression verde.
- Nenhum trabalho de G3–G7 iniciado.
- Secrets: nenhum valor sensível em código/testes/docs.
