# DAVI-GOVERNED-SQL-READ-STRUCTURAL-HARDENING-S1-CORRECTIVE-001

> **PARTIALLY SUPERSEDED / ARCHITECTURE CORRECTED** — ver `davi-sql-canonical-route-architecture-rebaseline-001.md`.
> STRUCTURAL SQL VALIDATOR HARDENING = RETAINED (sqlglot AST policy da rota `/data/sql` permanece).
> DIRECT GOVERNED DB EXECUTOR (`GovernedSqlExecutor`, conexão dedicada, `GOVERNED_SQL_DB_*`) = SUPERSEDED/REMOVED — sem consumidor de produção; DAVI usa a rota canônica da API DELPI.
> DEDICATED GOVERNED_SQL_DB_* PRINCIPAL REQUIREMENT = SUPERSEDED FOR DAVI.
> `SqlValidationResult`/`validate_with_result`/`PROFILE_DAVI_GOVERNED` foram removidos junto com o caminho abandonado.


## Defeito corrigido

O executor governed declarava `tables: set[str] = set()` e nunca o
populava — `GovernedSqlResult.tables` e o contexto de auditoria saíam
vazios apesar da resolução estrutural existir no validator.

```text
STRUCTURAL TABLE RESOLUTION = PASS
TABLE OBSERVABILITY          = FAIL  → corrigido
SOURCE / EVIDENCE CONSISTENCY = FAIL → corrigido
```

## Correção

Contrato único de resolução semântica:

```python
@dataclass(frozen=True)
class SqlValidationResult:
    profile: str
    physical_tables: tuple[str, ...]   # dedup + sorted
    statement_count: int
```

Fluxo (uma única resolução, zero reparse no executor):

```text
statement
→ SqlValidator.validate_with_result(profile)
→ SqlValidationResult.physical_tables   (fonte autoritativa)
→ GovernedSqlResult.tables              (mesmo set)
→ audit log tables=<mesmo set>          (mesmo set)
```

`validate()` preserva o contrato booleano — wrappers internos chamam
`validate_with_result` uma única vez por caminho.

`physical_tables` exclui aliases de CTE, aliases de tabela derivada,
aliases de coluna e variáveis locais; contém apenas tabelas físicas
deduplicadas e ordenadas deterministicamente.

## Testes (A–H)

| Caso | Resultado |
|---|---|
| A `SELECT B1_COD FROM SB1010` | `["SB1010"]` |
| B join `SB1010 a JOIN SB2010 b` | `["SB1010","SB2010"]` |
| C CTE `WITH cte AS (...)` | `["SB1010"]` — alias CTE ausente |
| D subquery `IN (SELECT FROM SA1010)` | `["SA1010","SB1010"]` |
| E UNION `SB1010 ∪ SA1010` | `["SA1010","SB1010"]` |
| F `SELECT * FROM ZZ9999` | `OBJECT_NOT_ALLOWED`; connection factory **não chamada** |
| G self-join `SB1010 ⋈ SB1010` | `["SB1010"]` (dedup) |
| H ordem reversa no SQL | saída ordenada deterministicamente |
| spy `validate_with_result` | exatamente 1 chamada por execução |
| audit `tables=` | idêntico a `result.tables` |

## Regressão

| Suíte | Resultado |
|---|---|
| whitelist + hardening + s0-corrective + governed profile + executor | **199 passed** |
| Seleção ampla `sql|davi|mcp|dynamic|external_capability|governed` | **1964 passed**, 2 failed NON_CAUSAL (inspecoes-processo stale source asserts — baseline-repro, arquivos fora do diff) |
| S0 denials (SELECT INTO / DML / DDL / EXEC / comma / APPLY / qualified / delimited / bypass+governed) | intactos |

## Gate S1

```text
STRUCTURAL_VALIDATION         = PASS
PHYSICAL_TABLE_RESOLUTION     = PASS
TABLE_METADATA_PROPAGATION    = PASS
NO_DUPLICATE_PARSE            = PASS
EXECUTOR_RESULT_TABLES        = PASS
AUDIT_TABLES                  = PASS
UNAUTHORIZED_TABLE_BEFORE_DB  = PASS
S0_REGRESSION                 = PASS
DAVI SQL PROMOTION            = NONE
MCP_TOOL_COUNT                = 2
```

## Invariantes DAVI (inalterados)

allowlist_version=21 · governed_operations=89 ·
agent_intelligence=2026.10.07.2 · mcp_tool_count=2 ·
allowed_tables_count=53 · execute_readonly_sql=GENERIC_SQL_FORBIDDEN

## Commit

- `10dfeecd58` — `fix(api-delpi): propagate governed sql table metadata`
