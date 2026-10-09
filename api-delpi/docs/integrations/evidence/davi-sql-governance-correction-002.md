# DAVI-SQL-GOVERNANCE-CORRECTION-002

> **Task:** `DAVI-SQL-CANONICAL-ROUTE-GOVERNANCE-CORRECTION-002`
> **Natureza:** correção arquitetural fail-closed após review de
> Architecture/Coordination. Sem redesign, sem capability SQL alternativa,
> sem reintroduzir o caminho Governed SQL.

## Architecture decision (frozen)

```text
existing canonical API route
+ existing backend permission
+ route validator

!= approved DAVI semantic capability
```

`POST /data/sql` é uma rota canônica válida da API DELPI, mas os gates
próprios de capability DAVI nunca foram ratificados:

```text
business need                  = TO_INVENTORY
business/domain owner          = TO_INVENTORY
semantic capability            = TO_INVENTORY
data classification            = TO_INVENTORY
output allowlist               = TO_INVENTORY
external-processing approval   = TO_INVENTORY
consumer approval              = TO_INVENTORY
```

`BOUNDED_DYNAMIC_RESULTSET` era um boundary de budget/projection — não uma
semantic output allowlist (64 columns max ≠ 64 approved columns; 50 rows max
≠ approved business fields). Removido com a exposição (Abstraction Gate:
zero consumers reais).

## Estado resultante

```text
POST /data/sql                 = PRESERVED (canonical API DELPI route)
execute_readonly_sql API       = PRESERVED
DATA_SQL_ACCESS                = PRESERVED (backend-owned)
SqlValidator                   = PRESERVED (route owner)

DAVI SQL CAPABILITY            = TO_INVENTORY
DAVI SQL DISCOVERY             = DISABLED / FAIL-CLOSED
DAVI SQL EXECUTION             = DISABLED / FAIL-CLOSED
ad_hoc_sql_read                = REMOVED / INACTIVE

DAVI LOCAL AUTHZ               = NONE
DIRECT DB FROM DAVI            = FORBIDDEN
MCP TOOL COUNT                 = 2
```

## Correção aplicada (menor diff)

A exposição introduzida por `DAVI-SQL-CANONICAL-ROUTE-NORMALIZATION-001`
(commit `bb793ba64b`) foi revertida **somente na superfície DAVI**:

- allowlist `davi_external_read_allowlist.json`: v22/90 → v21/89 ops;
  entrada `execute_readonly_sql` removida; quarantine `sql`/`select`
  restaurada (v21 reason já declarava `execute_readonly_sql` como
  `GENERIC_SQL_FORBIDDEN`).
- `eligibility.py`: opt-in `canonicalSqlRoute` removido — markers SQL
  voltam a ser `STATUS_GENERIC_SQL_FORBIDDEN` incondicional
  (`GENERIC SQL = FORBIDDEN BY DEFAULT`).
- `argument_validator.py`: `sql` retorna ao conjunto global
  `_TRANSPORT_FORBIDDEN` — rejeitado em **qualquer** operação DAVI.
- `catalog_builder.py`: campo `response_contract` removido (zero consumers).
- `execute_service.py`: branch `BOUNDED_DYNAMIC_RESULTSET` removido.
- `projection.py`: `apply_dynamic_resultset_projection` +
  `RESPONSE_CONTRACT_BOUNDED_DYNAMIC_RESULTSET` removidos
  (Abstraction Gate — zero consumers reais).
- `davi_dynamic_read_budgets.json`: `execute_max_resultsets` /
  `execute_max_result_columns` removidos.
- `davi_agent_intelligence.json`: restaurado `2026.10.07.2` —
  `ad_hoc_sql_read` inexistente; nenhum fallback SQL.
- `branding.py`: instruções MCP restauradas («Never invent … SQL»).
- `.cursor/rules` plugin-mcp + workspace-agent: «boundary clarification»
  que auto-ratificava a exceção removida — regra transversal restaurada
  (generic SQL tool = forbidden).
- Discovery benchmark fixture: revertido ao corpus v21 (sem família
  `sql_route`; casos `GENERIC_SQL_NEGATIVE` voltam a exigir zero-candidate).

Mantido (RQ-6): remoção do caminho abandonado (`GovernedSqlExecutor`,
`GovernedSqlConnection`, `governed_sql_errors.py`, `PROFILE_DAVI_GOVERNED`,
`GOVERNED_SQL_DB_*`, `SqlValidationResult`/`validate_with_result`) — zero
consumidores runtime; e o hardening estrutural do `SqlValidator` da rota.

## Prova fail-closed (testes novos em `test_davi_dynamic_read.py`)

| Teste | Prova |
|---|---|
| `test_canonical_sql_route_not_davi_eligible` | rota existe no baseline OpenAPI, mas `davi_status=GENERIC_SQL_FORBIDDEN`, `executable=False` (T-1/RQ-1) |
| `test_sql_intent_queries_never_surface_sql_candidate` (6 queries) | SQL-intent nunca produz `execute_readonly_sql` candidato (T-1/RQ-2) |
| `test_candidate_token_cannot_authorize_sql_route` | token candidate actor-bound mintado para a op → `GovernedExecutionError` (T-2/RQ-3) |
| `test_sql_argument_rejected_on_other_operations` | `sql` rejeitado em outras ops via `_TRANSPORT_FORBIDDEN` (T-3/RQ-9) |

Regressões existentes preservadas: `test_classify_hard_blocks`
(`/data/sql` → GENERIC_SQL_FORBIDDEN), quarantine
`"execute sql no banco"` → 0 candidatos, `test_sql01_generic_sql_not_promoted`,
suítes da rota canônica `/data/sql` + `SqlValidator` intactas (T-5).

## Evidence anterior

`davi-sql-canonical-route-architecture-rebaseline-001` permanece como
histórico de execução, classificado
`IMPLEMENTATION=SUPERSEDED_BY_GOVERNANCE_CORRECTION` /
`ARCHITECTURE_ACCEPTANCE=REJECTED`. História não reescrita.

## Deploy / runtime

```text
DEPLOY                       = NOT_RUN
AGENT_STUDIO_SYNC            = PENDING
PROVIDER_REDISCOVERY         = TEST_NOT_RUN
LIVE / AUTHZ MATRIX          = TEST_NOT_RUN
```
