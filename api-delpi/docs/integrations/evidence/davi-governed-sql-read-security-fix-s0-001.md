# DAVI GOVERNED SQL READ — SECURITY FIX S0 EVIDENCE

TASK_ID: `DAVI-GOVERNED-SQL-READ-SECURITY-FIX-S0-001`
SCOPE: conservative hardening of the existing `POST /data/sql` (`execute_readonly_sql`) validator — **no DAVI promotion, no MCP surface, AuthZ, route contract, dependency, allowlist, permission, or provider change.**
STATUS: `SECURITY_FIX_S0_PASS`

This document summarizes `davi-governed-sql-read-security-fix-s0-001.json` (same directory).

## 1. SOURCE STATE

| Field | Value |
|---|---|
| base_sha | `8686552a1ea4c2054863c0636e1571b734bfed17` |
| rebase_sha | `e14aa8bf6af6e63dbe158c984474e5c41bb7f6fd` |
| fix_commit | `6c858b362b` |
| execution_drift | NON_CAUSAL — origin moved 8686552a → e14aa8bf (2 non-causal drifts: delia-api+plugins+docs, requests-api+docs); deltas = delia-api, plugins/bpmn-modeler, requests-api, docs; zero api-delpi/SQL/DAVI paths; rebased, evidence rerun |

## 2. DEFECTS CLOSED (validator-level evidence)

| Construct | Before | After |
|---|---|---|
| `SELECT * INTO t FROM allowed` | ALLOWED (write-bypass PROVEN; DB mutation NOT_PROVEN/TEST_NOT_RUN) | DENIED |
| `SELECT * INTO #tmp FROM allowed` | ALLOWED | DENIED |
| CTE + `SELECT INTO` | ALLOWED | DENIED |
| `FROM t1, t2` comma sources | second+ sources evaded allowlist | DENIED |
| `FROM [TABLE]` | not extracted | DENIED |
| `FROM "TABLE"` | not extracted | DENIED |
| `CROSS APPLY` / `OUTER APPLY` | operands not extracted | DENIED |

No adversarial statement was executed against any database (validator-level evidence only, per task §19).

## 3. SIDE-EFFECT INVARIANT (all DENY, no regressions)

`INSERT UPDATE DELETE MERGE CREATE ALTER DROP TRUNCATE EXEC EXECUTE sp_executesql BEGIN/COMMIT/ROLLBACK GRANT REVOKE SELECT INTO` — negative tests in `tests/test_sql_validator_security_hardening.py` (50 new cases).

## 4. TABLE-SOURCE FAIL-CLOSED

New bounded scanner validates every physical source under `FROM`/`JOIN` at any paren depth; unknown or unsupported
source syntax now yields a controlled rejection instead of "zero extracted → allowed". Denial classes (comma joins,
brackets, double quotes, APPLY) apply **even when** `DATA_SQL_SKIP_TABLE_WHITELIST` is on — the flag's historical
bypass semantics are preserved for extraction but do not silence the new structural guards.

Preserved grammar (positive coverage): simple SELECT, JOIN of allowed tables, CTEs (physical sources inside CTEs
still allowlisted), UNION (all branches), subqueries/derived tables (inner sources validated), multiple SELECTs ≤
`MAX_SELECTS`, `DECLARE`/`SET`, table variables, window functions, `PIVOT`, `FOR XML`, `NOLOCK`, `FOR SYSTEM_TIME`.

## 5. CONSUMER COMPATIBILITY

| Syntax | Consumers via `/data/sql` | Disposition |
|---|---|---|
| SELECT INTO | 0 (internal batch SQL in repositories/scripts bypasses the validator) | NO_PROVEN_CONSUMER |
| comma join | 0 | NO_PROVEN_CONSUMER |
| bracketed/quoted table ids | 0 | NO_PROVEN_CONSUMER |
| APPLY | 0 (`machine_load_operation_balance_probe` uses pyodbc directly, not the route) | NO_PROVEN_CONSUMER |

All 27 `scripts/sql/*.sql` investigation queries re-validated: 24 PASS; 3 fail on `SET NOCOUNT`-style statements via
the **pre-existing** `_validate_set_statement` rule — not causal to this change.

## 6. DATA_SQL_SKIP_TABLE_WHITELIST

Not changed. The flag remains a documented bypass of table allowlist extraction when enabled; S0's structural
denials are orthogonal and apply regardless. `TABLE_ALLOWLIST_BYPASS_MODE = EXISTING_BEHAVIOR / NOT FIXED IN S0`.
DAVI governed SQL (S1+) must fail closed if the flag is active in the target runtime.

## 7. TESTS

| Suite | Result |
|---|---|
| `test_sql_validator_table_whitelist.py` + `test_sql_validator_security_hardening.py` | 76 passed |
| `-k "sql_validator or data_sql or readonly_sql"` | 77 passed |
| `-k davi` | 1202 passed, 4 failed — git-dependent capability freeze/inventory tests (`git` binary absent in container; PRE_EXISTING environmental limitation, non-causal; run on host) |

## 8. DAVI INVARIANTS (recomputed)

allowlist v21 · governed operations 89 · Agent Intelligence 2026.10.07.2 · MCP tool count 2
(`discover_delpi_information`, `execute_delpi_information`) · `execute_readonly_sql` remains
GENERIC_SQL_FORBIDDEN / DAVI-ineligible · generic-SQL discovery still yields zero candidates.

## 9. NOT DONE (deferred)

No AST parser (S1), no new permission, no read-only DB principal, no row/byte caps, no output contract, no rate
limit, no DAVI promotion, no deploy, no production SQL execution.

NEXT_STEP: `DAVI-GOVERNED-SQL-READ-STRUCTURAL-HARDENING-S1-001`
