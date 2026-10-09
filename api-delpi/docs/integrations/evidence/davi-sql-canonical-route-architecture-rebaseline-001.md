# DAVI-SQL-CANONICAL-ROUTE-ARCHITECTURE-REBASELINE-001

> **IMPLEMENTATION = SUPERSEDED_BY_GOVERNANCE_CORRECTION** — ver `davi-sql-governance-correction-002.md` (`DAVI-SQL-CANONICAL-ROUTE-GOVERNANCE-CORRECTION-002`).
> **ARCHITECTURE_ACCEPTANCE = REJECTED / EXECUTION_DRIFT.** A rota canônica da API DELPI `POST /data/sql` permanece válida e preservada (backend `DATA_SQL_ACCESS` + `SqlValidator`), mas uma rota canônica **não é** automaticamente uma capability DAVI aprovada. Os gates de capability (business need, owner, semantic capability, data classification, output allowlist, external-processing e consumer approval) nunca foram ratificados. `DAVI SQL CAPABILITY = TO_INVENTORY`; a exposição via discover→execute foi retirada (fail-closed). A remoção do caminho abandonado GovernedSqlExecutor/conexão/config permanece válida.

> **Task:** `DAVI-SQL-CANONICAL-ROUTE-NORMALIZATION-IMPLEMENTATION-001`
> **Base SHA:** `b57d627ac3d85cc902d2dab4e2e4395b88a6a365` (handoff baseline)
> **Rebased onto:** `912ac3ba99ba6bfa57fcd7294d46995e2a2070a7` (`origin/main`)
> **Drift:** NON_CAUSAL — commits upstream em tv-dashboard, bpmn-modeler e
> docs DÉLIA; nenhum tocou api-delpi SQL / DAVI / MCP / AuthZ / allowlist /
> candidate token / projection.

## Correção de arquitetura

O modelo «Governed SQL» anterior criava conceitos em torno da rota SQL que a
arquitetura não pede. A correção é: **SQL entra pelo broker normal como uma
rota canônica existente da API DELPI**.

```text
CORE/SHARED DELPI AUTH MODEL = autoridade de permissões do usuário
API DELPI                    = dona da rota + enforcement de permissão
POST /data/sql               = rota READ protegida normal da API DELPI
DATA_SQL_ACCESS              = conjunto de permissões backend vigente
                               [API_DELPI_ACCESS_FULL, API_DELPI_DATA]
DAVI                         = sem permissões locais
MCP                          = sem permissões locais
Agent                        = sem permissões locais
candidate_token              = integridade de execução (actor binding),
                               NÃO permissão de negócio
OAuth scopes                 = identidade/acesso de transporte,
                               NÃO permissão de negócio
```

## Veredito arquitetural

```text
SQL ROUTE                         = EXISTING CANONICAL API DELPI ROUTE
NEW SQL ROUTE                     = NONE
NEW SQL PERMISSION                = NONE
DAVI LOCAL AUTHZ                  = NONE / FORBIDDEN
MCP AUTHZ                         = NONE / FORBIDDEN
BACKEND AUTHZ                     = EXISTING API DELPI DATA_SQL_ACCESS
CORE/SHARED AUTH MODEL            = AUTHORITY FOR USER PERMISSIONS
SQL VALIDATION                    = API DELPI ROUTE RESPONSIBILITY
MCP ROLE                          = DISCOVERY + ORCHESTRATION + BOUNDED PROJECTION
DIRECT DATABASE ACCESS FROM DAVI  = FORBIDDEN
MCP TOOL COUNT                    = 2
```

## Rota

| Item | Valor |
|---|---|
| path | `POST /data/sql` |
| operationId | `execute_readonly_sql` |
| permissão | `@require_any_permission(DATA_SQL_ACCESS)` |
| validator | `SqlValidator` (sqlglot T-SQL AST — hardening S0/S1 retido) |
| request contract | `{"sql": "..."}` (JSON) — inalterado |
| response contract | inalterado para callers existentes (`sql`, `total_resultsets`, `resultsets[]`) |

## Caminho especial abandonado — removido

| Componente | Consumidor de produção | Ação |
|---|---|---|
| `GovernedSqlExecutor` | nenhum (somente testes/evidência) | REMOVED |
| `governed_sql_connection.py` | nenhum | REMOVED |
| `governed_sql_errors.py` | nenhum | REMOVED |
| `PROFILE_DAVI_GOVERNED` / `SqlValidationResult` / `validate_with_result` | nenhum | REMOVED do `sql_validator.py` (hardening estrutural retido) |
| `GOVERNED_SQL_DB_*` settings | nenhum | REMOVED de `app/config.py` |
| `tests/test_governed_sql_executor.py`, `tests/test_sql_governed_profile.py` | — | REMOVED |

DAVI não executa SQL diretamente: usa a rota canônica via
`CatalogActionPlan` → `CatalogActionExecutorPort` → POST /data/sql.

## DAVI allowlist

| Item | Antes | Depois |
|---|---|---|
| version | 21 | 22 |
| governed operations | 89 | 90 |
| `execute_readonly_sql` | quarantined/forbidden | allowlisted (`canonicalSqlRoute=CANONICAL_READONLY_SQL_ROUTE`, `executionMode=catalog_action`, `semanticTransport=SEMANTIC_READ_POST`) |
| `retrievalQuarantineTokens` | continha `sql`, `select` | removidos (stale — tokens de domínio remanescentes preservados) |

## Contrato de argumento

- `sql` sai do veto global: só é aceito quando owner-declared no requestBody
  OpenAPI **e** aprovado em `approvedInputFields` da allowlist.
- `argumentLimits.sql.maxLength = 8000`; `requireArguments = ["sql"]`.
- `_TRANSPORT_FORBIDDEN` inalterado: `url`, `host`, `path`, `method`,
  `operationId`, `authorization` → DENY global.
- `search_products`/`get_product_stock` + `{"sql": ...}` → DENY (unknown arg).

## Projeção

`responseContract = BOUNDED_DYNAMIC_RESULTSET`
(`apply_dynamic_resultset_projection`):

- remove o eco `sql` da rota no payload DAVI;
- mantém `total_resultsets`, `resultsets[].index|columns|total|data`;
- coerência de coluna: cada linha só mantém chaves presentes em `columns`;
- budgets: `execute_max_resultsets=8`, `execute_max_result_columns=64`,
  `execute_max_items=50`, `execute_max_response_bytes=65536`;
- truncamento explícito (`truncated`/`is_complete`).

## Discovery

- `execute_readonly_sql` participa do Technical Action Catalog normal;
  semantic aliases PT/EN adicionados na allowlist (consulta sql, consulta
  ad hoc, cruzar dados, …).
- Rotas canônicas específicas outrank SQL no próprio domínio
  (estoque → `get_product_stock`; descrição → `search_products`).
- Guard de intenção de escrita (não-AuthZ) bloqueia a candidatura READ da
  rota SQL em comandos de mutação (`delete`/`update`/`drop`/`insert`/
  `truncate`/`merge`/`alter`/`exec`/`create` + equivalentes PT).
- `DISCOVERY != AUTHORIZATION`: candidatura não é concessão; backend decide.

## AuthZ

- Nenhuma avaliação de permissão/role/branch/departamento foi adicionada em
  `dynamic_information`, handlers MCP ou Agent Intelligence.
- 401/403 do backend propagam normalmente (`unauthorized`/`forbidden`).
- Candidate token inalterado: actor-bound, HMAC, TTL, tamper-reject.

## Evidência supersedida

| Artefato | Estado |
|---|---|
| `davi-governed-sql-read-authz-ratification-s2-001.md` | SUPERSEDED (gate de AuthZ dedicado não se aplica — rota canônica usa AuthZ existente) |
| `davi-governed-sql-read-owner-ratification-packet-s2-002.md` | SUPERSEDED |
| `davi-governed-sql-read-structural-hardening-s1-001.*` | PARCIAL — validator hardening retido; executor/connection/perfil governed removidos |
| `davi-governed-sql-read-structural-hardening-s1-corrective-001.md` | PARCIAL — idem |

## Agent Intelligence

`2026.10.07.2` → `2026.10.08.1`. Novo flow `ad_hoc_sql_read`
(discover→execute, `confirmation_policy=read_only`).
`sql_arbitrary`/`generic_proxy`/`direct_db` permanecem FORBIDDEN.

## Testes (source-level, container `delpi-api-delpi`)

| Suíte | Resultado |
|---|---|
| `test_sql_validator_s0_corrective_001` + `security_hardening` + `table_whitelist` | 116 PASS |
| `test_davi_dynamic_read` (incl. 15 testes SQL-001..009 novos) | 145 PASS |
| `test_davi_read_only_intent_guard` | PASS |
| `test_davi_mcp_tool_surface_simplification` (2 tools) | PASS |
| `test_davi_agent_intelligence` + `agent_instructions_contract` | 32 PASS |
| Rebaseline asserts stale (89→90 ops, quarantine sql/select, startup bootstrap, inventory sync, wave_003a) | 361 PASS |
| **Suíte ampla** `-k "sql or davi or dynamic_information or mcp"` | **1931 PASS, 5 FAIL — todas NON_CAUSAL** |
| `test_davi_mcp_platform_conformance` | PASS |

### Falhas NON_CAUSAL (documentadas, sem código deste diff)

- `test_davi_capability_expansion_inventory` (2) + `test_davi_capability_wave_002_freeze` (1): invocam `git_sha("HEAD")` — o container `delpi-api-delpi` não tem binário `git` (déficit ambiental pré-existente).
- `test_inspecoes_processo_historico_sql` + `test_inspecoes_processo_operation_inspections`: upstream `131b0411c7` alterou `inspecoes_processo_repository.py` sem atualizar os testes (`historico_tela` assert). Zero arquivos inspeções neste diff — pré-existente em `origin/main`.

## Deploy / runtime

```text
DEPLOY                       = NOT RUN
AGENT_STUDIO_SYNC            = PENDING_MANUAL_SYNC
PROVIDER_REDISCOVERY         = TEST_NOT_RUN
LIVE_SQL_EXECUTION_VIA_DAVI  = TEST_NOT_RUN
```
