# 180 — DÉLIA · DAVI-Exclusive Domain Access Completion — Contract Hardening

**TASK_ID:** `DELIA-C3-DAVI-EXCLUSIVE-DOMAIN-ACCESS-COMPLETION-01`
**Executor:** Cursor / Devin
**Base HEAD:** `6a17646ce5251c84c35f0fa842b5e09265869250`
**Decisão de produto:** explícita do usuário — DÉLIA consome as capacidades empresariais da API DELPI exclusivamente através do DAVI. Direção **não** reaberta.
**Status:** implementado localmente; deploy NÃO autorizado/não executado; queries produtivas = 0.

---

## 1. Reancoragem

HEAD/origin `6a17646c` (contém doc 179 + revisão independente); worktree limpa antes do diff. Autoridades 16→50→17→49→51→52→21→20→25; docs 170–179; revisão independente do doc 179; ledger. Fase C3 — CP/RQ não avançado.

## 2. Owner/contract gate — WP1

Revalidado no HEAD o estado do contrato do owner (`api-delpi/app/content/davi_external_read_allowlist.json`):

| Capability | Disposição no contrato do owner | Resultado |
|---|---|---|
| `get_product_summary` | `explicitlyNotApproved` — `coverageDisposition: DEFER` (“Composite product snapshot remains deferred; not a Wave 2 READ capability”) | **`OWNER_DECISION_REQUIRED`** — declaração direta preservada |
| `search_customers` | nenhuma decisão de cobertura na allowlist | **`OWNER_DECISION_REQUIRED`** — declaração direta preservada |

`get_product_detail` reconfirmado **não** como superset de `get_product_summary` (sem stock/prices). Nenhuma rota HTTP existente foi tratada como aprovação MCP. **WP1 está bloqueado por decisão do owner — não implementável nesta task sem violar o gate de allowlist.** As duas declarações diretas permanecem como único remanescente legítimo do binding; `DELIA_OPENAPI_DELPI_*` preservados porque ainda alimentam essas duas capabilities.

## 3. WP2 — endurecimento do contrato de erros MCP

Problema (revisão doc 179, P1): `VALIDATION_ERROR` era amplo — cobria rejeição de argumentos, elegibilidade e falha de execução — e a DÉLIA o mapeava para `OWNER_ARGUMENT_REJECTED` apenas pela ausência de `recoverable:false`.

Contrato implementado (vocab owner-publicado em `dynamic_information/errors.py`, projetado verbatim no wire por `mcp_tool_result` structuredContent):

| Código | Semântica | `recoverable` |
|---|---|---|
| `ARGUMENT_VALIDATION` | argumentos propostos violam o contrato | `true` **somente aqui** |
| `CAPABILITY_NOT_ALLOWED` | ação não elegível / token inválido | `false` — terminal |
| `OWNER_EXECUTION_ERROR` | falha de execução no owner | `false` — terminal |
| `AUTHENTICATION_REQUIRED` | sem credencial válida | `false` — terminal |
| `AUTHORIZATION_DENIED` | permissão negada | `false` — terminal |

- `execute_service.py`: todos os `GovernedExecutionError` anotados com `code=` tipado (não-eligível → `CAPABILITY_NOT_ALLOWED`; `ArgumentValidationError` → `ARGUMENT_VALIDATION`; runner/executor/plan/resultado não-ok → `OWNER_EXECUTION_ERROR`).
- `server.py`: `typed_error_tool_result(code, message, recoverable=...)` emite `{code, recoverable, message}`; `validation_error_tool_result` → `ARGUMENT_VALIDATION` + `recoverable:true`; `CandidateTokenError` → `CAPABILITY_NOT_ALLOWED`; `GovernedExecutionError` → `exc.code` (default `OWNER_EXECUTION_ERROR`), `recoverable` apenas se `ARGUMENT_VALIDATION`; `_authz_error_result` → `AUTHENTICATION_REQUIRED` (meta WWW-Authenticate preservada) / `AUTHORIZATION_DENIED` com payload estruturado.
- DÉLIA `specialist_interop._normalize_outcome`: reparação exige **ambos** `code=="ARGUMENT_VALIDATION"` **e** `recoverable is True`; `_OWNER_ERROR_CODE_MAP` projeta `AUTHENTICATION_REQUIRED→mcp_authentication_failed`, `AUTHORIZATION_DENIED→mcp_authorization_denied`, `CAPABILITY_NOT_ALLOWED→capability_not_allowed_in_phase`; todo o resto → `mcp_protocol_error`. Sem matching por mensagem, sem branch por produto/provider, sem recuperabilidade inferida.

## 4. WP3 — classificação de autorização

- Transporte 401/403: inalterado (`mcp_authentication_failed`/`mcp_authorization_denied`).
- Tool-result `Forbidden`/`Unauthorized` (PermissionError do owner): agora `AUTHORIZATION_DENIED`/`AUTHENTICATION_REQUIRED` tipados → `mcp_authorization_denied`/`mcp_authentication_failed` — antes era `mcp_protocol_error` genérico.
- Executor de catálogo `outcome=unauthorized/forbidden` → `PermissionError` → mesmos códigos tipados.
- Nenhuma negação entra no ciclo de reformulação READ; metadata MCP nunca vira autorização.

## 5. WP4 — paridade funcional

| Capability | INPUT | OUTPUT | PAGINAÇÃO | ERRO | DECISÃO |
|---|---|---|---|---|---|
| `search_products` | PARCIAL — DAVI: `code, description, group_code, page, page_size`; direto tinha `product_type, sort, direction, customer_reference` (este já deny-by-default) | projetada `product_code, description, group_category` | equivalente (`page/page_size`) | hardening acima | `OWNER_DECISION_REQUIRED` para filtros extras |
| `get_product_stock` | compatível | projeção owner bounded | n/d | idem | migrada (doc 179) |
| `get_product_summary` | — | — | — | — | `OWNER_DECISION_REQUIRED` (DEFER) — direta preservada |
| `search_customers` | — | — | — | — | `OWNER_DECISION_REQUIRED` (sem decisão) — direta preservada |

Nenhuma perda funcional silenciosa: os filtros não-cobertos são gap de contrato do owner, registrado, não emulado.

## 6. WP5 — remoção do binding direto

**Não executada — gate falhou por bloqueio legítimo do owner.** `openapi_declarations.delpi.json` mantém exatamente as 2 capabilities sem substituto aprovado. Estado residual medido: `DIRECT_DELPI_CAPABILITIES=2`, `DAVI_CAPABILITY_COVERAGE=PARTIAL`. Componentes OpenAPI compartilhados preservados.

## 7. WP6 — RED/GREEN

- api-delpi (`test_external_capabilities_mcp.py`, +4): schema error → `ARGUMENT_VALIDATION`+`recoverable:true` (discover e execute); token desconhecido → `CAPABILITY_NOT_ALLOWED`+`false`; sem autorização → tipado `AUTHENTICATION_REQUIRED|CAPABILITY_NOT_ALLOWED`+`false`.
- DÉLIA (`test_specialist_interop_usecase.py`, 9 testes): `ARGUMENT_VALIDATION`+`recoverable:true` → `owner_argument_rejected`; `VALIDATION_ERROR` genérico → `mcp_protocol_error` (regressão P1 fechada); `ARGUMENT_VALIDATION` sem flag e com `false` → terminal; untyped → terminal; `AUTHORIZATION_DENIED`→`mcp_authorization_denied`; `AUTHENTICATION_REQUIRED`→`mcp_authentication_failed`; `CAPABILITY_NOT_ALLOWED`→`capability_not_allowed_in_phase`; `OWNER_EXECUTION_ERROR`→`mcp_protocol_error`.
- api-delpi suite tocada: 15/15 + 43/43 (mcp/conformance/intelligence/spike) + 189 passed / 1 falha **ambiental pré-existente** em `test_davi_capability_wave_002_freeze` (subprocess `git` ausente na imagem — não relacionado ao diff).
- delia-api suite completa: única falha = `PRE_EXISTING_CRI_CONTRACT_DRIFT` (residual do owner da instrução, inalterado).
- Architecture gate `audit_architecture_phase3 --base HEAD --check`: **OK**.

## 8. WP8 — eval E2E pareado (local, zero rede)

`governed_davi_migration_eval.py` atualizado para o contrato tipado + cenários novos + matriz de cobertura das 4 capabilities:

| Cenário | B0 direto | B1 DAVI |
|---|---|---|
| declared recoverable | SUCCESS / 2 wire | SUCCESS / 4 wire (discover+execute por invoke) |
| undeclared / non-recoverable / transient | terminal | terminal |
| forbidden | AUTHZ_DENIED | AUTHZ_DENIED |
| repeated rejection | bounded | bounded |
| `VALIDATION_ERROR` legado (B1) | — | **terminal** (P1 fechado) |
| `AUTHORIZATION_DENIED` tool-result (B1) | — | **AUTHZ_DENIED** (WP3) |
| `CAPABILITY_NOT_ALLOWED` (B1) | — | terminal |
| `OWNER_EXECUTION_ERROR` (B1) | — | terminal |

`capability_coverage`: `search_products`/`get_product_stock` MIGRATED; `get_product_summary`/`search_customers` OWNER_DECISION_REQUIRED.

Runtime real DAVI: **INCONCLUSIVE** — exigiria ambiente autorizado; não executado nesta task. FALSE_POSITIVES=0; FABRICATED_RECORDS=0; UNAUTHORIZED_ACTS=0; UNAUTHORIZED_PREPARES=0; loops bounded.

## 9. Arquivos alterados

- `api-delpi/app/application/external_capabilities/dynamic_information/errors.py` — vocabulário tipado + `code` em `GovernedExecutionError`.
- `api-delpi/app/application/external_capabilities/dynamic_information/execute_service.py` — `code=` em todos os raise sites.
- `api-delpi/app/interface/mcp/server.py` — `typed_error_tool_result`, authz tipado, mapping de exceções; `VALIDATION_ERROR_CODE` removido (nome amplo).
- `api-delpi/tests/test_external_capabilities_mcp.py` — +4 testes do wire tipado.
- `delia-api/app/application/specialist_interop/specialist_interop.py` — gate estrito `ARGUMENT_VALIDATION`+`recoverable:true`; `_OWNER_ERROR_CODE_MAP` de authz/capability.
- `delia-api/tests/test_specialist_interop_usecase.py` — 9 testes do contrato endurecido.
- `delia-api/scripts/governed_davi_migration_eval.py` — códigos tipados, 4 cenários novos, matriz de cobertura.

## 10. Residuais

1. `OWNER_DECISION_REQUIRED` (api-delpi/DAVI owner): exposição de `get_product_summary` + `search_customers` na allowlist (ou substituto aprovado); `get_product_summary` está explicitamente `DEFER`.
2. `OWNER_DECISION_REQUIRED`: paridade de filtros de `search_products` (`product_type, sort, direction`; `customer_reference` permanece deny-by-default).
3. `PRE_EXISTING_CRI_CONTRACT_DRIFT` (owner da instrução).
4. Security residual doc 174 (exposição de credencial — sem ratificação do security owner) — gate de release produtivo permanece bloqueado.
5. Falha ambiental `test_davi_capability_wave_002_freeze` (binário `git` ausente na imagem de teste) — pré-existente.

## 11. Rollback

`git revert` do commit desta task restaura o wire `VALIDATION_ERROR` amplo e a classificação doc-179 na DÉLIA. Declarações diretas e binding OpenAPI não foram tocados → rollback não reabre cobertura perdida.

## 12. Veredito

`LOCAL_PASS_WITH_RESIDUAL` / **`PARTIAL_MIGRATION — CAPABILITY_MIGRATION_BLOCKED`**. O endurecimento de contrato (P1 da revisão) e a classificação tipada de autorização estão completos, testados e fail-closed. A arquitetura exclusiva **não** é declarada concluída: duas capabilities legítimas seguem no binding direto por decisão explícita do owner, preservadas — nunca removidas artificialmente.

`DEPLOY_EXECUTED=NO` · `PRODUCTION_QUERIES=0` · `MODEL_CHANGED=NO` · `KEYCLOAK_MODIFIED=NO` · `DOMAIN_API_MODIFIED=NO` · `INDEPENDENT_REVIEW=PENDING` · fase não avançada.


## Revisão independente da coordenação — 2026-10-28

**REVIEW=ACCEPT_WITH_RESIDUAL (MCP error contract hardening); EXCLUSIVE_DAVI=NOT_ACHIEVED; PROD_DEPLOY=NOT_AUTHORIZED.** Inspected GitHub main at `8e82850fcaa80a1b1dd03388fdfd4cb3747ee347`, changed file list and patches for api-delpi dynamic_information/errors.py, execute_service.py, interface/mcp/server.py and delia-api specialist_interop.py. Test counts, E2E and CI are executor-reported rather than independently rerun. No code or runtime changes made by reviewer.

**Accepted:** owner emits differentiated typed codes ARGUMENT_VALIDATION, CAPABILITY_NOT_ALLOWED, OWNER_EXECUTION_ERROR, AUTHENTICATION_REQUIRED, AUTHORIZATION_DENIED; MCP adapter restricts repair to code ARGUMENT_VALIDATION **and explicit recoverable:true**. Generic VALIDATION_ERROR and unspecified recoverability no longer trigger repair. Tool-result auth denials project as terminal authentication/authorization errors, rather than protocol noise; no new planner. Owner allowlist stays unchanged, respecting get_product_summary explicitlyNotApproved/DEFER and search_customers undecided. Synthetic paired wire evaluation supports parity for covered scenarios, not runtime-real cross-owner Business Outcome.

**Residual nuance:** the tool-result `validation_error_tool_result` remains a helper that emits ARGUMENT_VALIDATION/recoverable:true wherever invoked. Audit ALL its call sites across discover/execute: some failure modes might be candidate-token/discovery validation rather than fixable READ **arguments**, and typed recovery must never reinterpret denial, eligibility or stale token as argument repair. The reported code specifically maps CandidateTokenError to CAPABILITY_NOT_ALLOWED, which is favorable, but broader negative cases deserve contract tests. Unanticipated exceptions and tool failures remain terminal. Ensure sensitive content sanitized in error detail before provider normalization and no secret leakage.

**Blockers:** summary remains owner-approved DEFER (no override), search_customers has no approval. DELPI direct binding with two operations cannot be removed without safe replacement; product-search input parity incomplete for product_type/sort/direction. Contract owner must decide capability wave and field governance. Runtime DAVI tests in an authorized environment remain INCONCLUSIVE; local eval uses synthetic wire and scripted model. C3 remains unchanged. Pre-existing CRI drift and security key exposure (doc174) remain separate owner-gated residuals; production clearance BLOCKED.

**Verdict:** `ACCEPT_WITH_RESIDUAL_LOCAL` for typed-error correction; `CAPABILITY_MIGRATION_BLOCKED` for exclusive-DAVI objective, no deploy. Next step is a documented owner approval/rejection of DAVI coverage for the two operations plus explicit field decisions, followed by bounded capability migration, contract E2E and independent review, not another planner refactor.
