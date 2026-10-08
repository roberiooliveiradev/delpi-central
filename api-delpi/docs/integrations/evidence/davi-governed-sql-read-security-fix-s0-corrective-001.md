# DAVI GOVERNED SQL READ — S0 CORRECTIVE 001 EVIDENCE

TASK_ID: `DAVI-GOVERNED-SQL-READ-SECURITY-FIX-S0-CORRECTIVE-001`
PARENT: `DAVI-GOVERNED-SQL-READ-SECURITY-FIX-S0-001` = `ACCEPT_WITH_REQUIRED_CORRECTIVE`
SCOPE: closes the two residual fail-closed defects found by Architecture review — **no parser, no dependency, no DAVI/MCP/AuthZ/route/allowlist change.**
STATUS: `S0_CORRECTIVE_PASS`

This document summarizes `davi-governed-sql-read-security-fix-s0-corrective-001.json` (same directory).

## 1. SOURCE STATE

| Field | Value |
|---|---|
| base_sha | `05a8e7a9661d9117814a47fd9db28aa1c83ceeaf` |
| fix_commit | `72bf2041fc` |
| execution_drift | NON_CAUSAL (2 drifts) — `e05f9fa0 → 05a8e7a9` (helpdesk-api only) during preflight; zero api-delpi/SQL/DAVI paths; rebased, evidence rerun |

## 2. DEFECT A — FAKE CTE NAME FROM STRING LITERAL

**Before (PROVEN, validator-level):** `_extract_cte_names()` scanned comment-stripped but
string-intact text. `SELECT 'WITH ZZ9999 AS (' AS note FROM ZZ9999` minted a fake CTE name from the
literal, so the unauthorized physical source `ZZ9999` resolved as a CTE → `ALLOWED`.

**Fix:** `_mask_string_literals()` blanks all `'...'` contents (escaped `''` handled via quote-toggle)
before CTE-name extraction. Literals can no longer feed lexical extraction — `ALLOWED → DENY`.

**Preserved:** `'WITH ZZ9999 AS ('` in a string with an authorized source still PASSes — literals are
data. Real CTEs, multiple CTEs, CTE-with-comments, and CTE bodies containing CTE-like strings all PASS.

## 3. DEFECT B — ALLOWED PREFIX MASKING QUALIFIED/TRAILING SYNTAX

**Before (PROVEN, validator-level):** `_resolve_single_source()` validated only the first
`[A-Z0-9_@#]+` token. `FROM SB1010.ZZ9999`, `SB1010..ZZ9999`, `SB1010.[ZZ9999]`, `SB1010."ZZ9999"`
(and spaced `SB1010 . ZZ9999`) passed on the allowlisted prefix while the qualified tail was never
checked.

**Fix:** after resolving the bare token, the immediate continuation is checked — adjacent `.`, `[`,
`"` denied, and the next non-whitespace `.` denied (T-SQL permits whitespace inside multipart names).
Aliases (`t a`, `t AS a`), `WHERE`, `JOIN/ON`, `WITH (NOLOCK)`, statement end and closing parens
remain PASS.

## 4. SECURITY GATES (probe + tests)

| Case | Before | After |
|---|---|---|
| FAKE_CTE_FROM_STRING | ALLOWED | DENY |
| REAL_CTE_ALLOWED_TABLE | PASS | PASS |
| REAL_CTE_UNAUTHORIZED_TABLE | DENY | DENY |
| CTE body containing CTE-like string | PASS | PASS |
| ALLOWED_PREFIX_DOT_SUFFIX | ALLOWED | DENY |
| ALLOWED_PREFIX_DOUBLE_DOT_SUFFIX | ALLOWED | DENY |
| ALLOWED_PREFIX_BRACKET_SUFFIX | ALLOWED | DENY |
| ALLOWED_PREFIX_QUOTED_SUFFIX | ALLOWED | DENY |
| SPACED_DOT / FOUR_PART / QUAL_IN_JOIN / QUAL_IN_SUBQUERY / CTE_NAME_DOT | ALLOWED | DENY |
| NORMAL_ALIAS / AS_ALIAS / WHERE / JOIN / NOLOCK | PASS | PASS |
| SELECT_INTO / COMMA_JOIN / BRACKETED / QUOTED / APPLY / DML / DDL / EXEC | DENY | DENY (unchanged) |

Pre-existing conservative over-block kept: banned keywords (e.g. `INTO`) inside string literals still
deny — documented, unchanged.

## 5. CONSUMER COMPATIBILITY

| Syntax | Consumers via `/data/sql` | Disposition |
|---|---|---|
| CTE-like text literals | 0 | NO_PROVEN_CONSUMER |
| Qualified sources (`t.<x>`) | 0 working — `refugos_fase0_probe.py` uses `INFORMATION_SCHEMA.TABLES`, already denied pre-corrective (`INFORMATION_SCHEMA` not allowlisted); `sys.*`/`dbo.*` probes are pyodbc-direct | NO_PROVEN_CONSUMER |

breaking_changes: none · migration_required: none

## 6. DATA_SQL_SKIP_TABLE_WHITELIST

Not changed. The qualified-source denial lives inside `_validate_table_sources`, consistent with S0's
treatment of comma/bracket/quoted classes — the flag's documented bypass of the table-source
governance block is unchanged. DAVI governed SQL (S1+) must fail closed if the flag is active.

## 7. TESTS

| Suite | Result |
|---|---|
| focused (whitelist + hardening + corrective-001) | 116 passed (40 new corrective cases) |
| `-k "sql_validator or data_sql or readonly_sql"` | 117 passed |
| `-k davi` | 1202 passed, 4 failed — same exact git-dependent capability freeze tests as S0 (`git` absent in container); PRE_EXISTING environmental, non-causal |
| adversarial probe | 18/18 cases correct |

## 8. DAVI INVARIANTS (recomputed)

allowlist v21 · governed operations 89 · Agent Intelligence 2026.10.07.2 · MCP tool count 2 ·
allowed_tables 53 · `execute_readonly_sql` remains GENERIC_SQL_FORBIDDEN · generic-SQL discovery
zero candidates.

## 9. NOT DONE

No AST/parser (S1), no new permission, no route/contract change, no DAVI promotion, no deploy, no
production SQL execution.

NEXT_STEP: `DAVI-GOVERNED-SQL-READ-STRUCTURAL-HARDENING-S1-001`
