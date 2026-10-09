# DAVI-GOVERNED-SQL-READ-STRUCTURAL-HARDENING-S1-001

> **PARTIALLY SUPERSEDED / ARCHITECTURE CORRECTED** — ver `davi-sql-canonical-route-architecture-rebaseline-001.md` (itself SUPERSEDED) e `davi-sql-governance-correction-002.md`.
> STRUCTURAL SQL VALIDATOR HARDENING = RETAINED (sqlglot AST policy da rota `/data/sql` permanece — a rota canônica é preservada).
> DIRECT GOVERNED DB EXECUTOR (`GovernedSqlExecutor`, conexão dedicada, `GOVERNED_SQL_DB_*`) = SUPERSEDED/REMOVED — sem consumidor de produção.
> DEDICATED GOVERNED_SQL_DB_* PRINCIPAL REQUIREMENT = SUPERSEDED FOR DAVI.
> `SqlValidationResult`/`validate_with_result`/`PROFILE_DAVI_GOVERNED` foram removidos junto com o caminho abandonado.
> DAVI SQL CAPABILITY = TO_INVENTORY — `POST /data/sql` não é capability DAVI aprovada (`DAVI-SQL-CANONICAL-ROUTE-GOVERNANCE-CORRECTION-002`).


## Escopo

S1 — Structural hardening do caminho read-only SQL da api-delpi, como
fundação para o Governed Analytical SQL READ (DAVI) sem promover SQL
genérico ao DAVI. Camadas novas são internas: **nenhuma rota, tool MCP,
OpenAPI ou capability nova foi exposta**.

## Decisões

| Item | Decisão |
|---|---|
| Parser | `sqlglot==30.21.0`, dialect `tsql` — spike aprovado: 18/18 casos positivos, 27/27 consumidores reais, todos os vetores adversariais distinguíveis estruturalmente |
| Autoridade | AST para tipos de statement e resolução de fontes físicas; camada lexical preservada como defesa em profundidade |
| Perfis | `legacy_readonly` (default — compatibilidade com consumidores existentes) e `davi_governed` (subconjunto estrito, ainda sem consumidor externo) |
| Conexão governed | `GOVERNED_SQL_DB_*` dedicado — **fail closed**; nunca cai em `TOTVS_DB_*` |
| Row bound | `fetchmany(N+1)` + descarte de conexão; sem `fetchall`; sem rewrite textual de TOP (sem AST-root injection confiável) — contenção client-side + timeout + limites de complexidade; custo residual de scan registrado |
| Erros | Taxonomia categorizada; diagnósticos brutos do SQL Server apenas em `detail` interno |

## Governed profile — gramática admitida

- Exatamente **um** statement analítico: `SELECT` ou `WITH ... SELECT`
- CTEs (inclusive múltiplas/recursivas), UNION, derived tables, joins com
  `ON`, GROUP BY/HAVING, window functions, DISTINCT, ORDER BY
- Placeholders posicionais `?` (binding pyodbc)
- Limites: 8000 chars, 8 tabelas físicas, 8 joins, 50 parâmetros
- Fontes físicas na allowlist (`allowed_tables.json`, 53 tabelas)

## Governed profile — denials estruturais

- Múltiplos statements, `DECLARE`, `SET`, table variables (`@T TABLE`)
- DML (`INSERT/UPDATE/DELETE/MERGE`), DDL, `EXEC`/`EXECUTE`, transações,
  `GRANT/REVOKE`
- `SELECT INTO` (incl. `#temp`), comma joins, `CROSS/OUTER APPLY`
- Fontes qualificadas (`db.dbo.T`, `srv.db.dbo.T`, `T.X`), delimitadas
  (`[T]`, `"T"`) ou sem nome (`OPENROWSET`, `OPENQUERY`, funções)
- Hints (`WITH (NOLOCK)`), `FOR XML`, `PIVOT`
- Fake-CTE via string literal; fontes não allowlisted em qualquer
  profundidade (subquery, CTE body, UNION branch, derived table)
- `DATA_SQL_SKIP_TABLE_WHITELIST` ativo → governed **fail closed**

## Legacy profile — compatibilidade

- Mesmo corpus de consumidores: `scripts/sql/*.sql` — 24/27 PASS; as 3
  falhas (`SET inválido ou não suportado`) são **idênticas ao baseline
  S0** (pre-existentes). Os 2 arquivos `app/**/*.sql` são DDL de view de
  referência — não passam pelo validator (nenhum `.py` os carrega).
- Zero regressões novas na matriz S0/S0-corretiva.

## Testes

| Suíte | Resultado |
|---|---|
| `test_sql_validator_table_whitelist.py` + `test_sql_validator_security_hardening.py` + `test_sql_validator_s0_corrective_001.py` + `test_sql_governed_profile.py` + `test_governed_sql_executor.py` + sql telemetry | **194 passed** |
| Seleção ampla (`-k "sql or davi or mcp or dynamic or external_capability or governed"`) | **1985 passed**, 4 failed NON_CAUSAL |
| Corpus consumidor real | 24/27 (3 pre-existing SET) |

### Falhas não-causais

- `test_davi_capability_wave_002_freeze`, `test_davi_capability_wave_003a_freeze`
  — `FileNotFoundError: 'git'` (host-dependent, mesma classe das 4 falhas
  já registradas em baseline)
- `test_inspecoes_processo_historico_sql`, `test_inspecoes_processo_operation_inspections`
  — assert de source em `InspecoesProcessoRepository`, arquivo fora do
  diff; reproduz em baseline limpo

## Residual checks

- MCP tool count: **2** produtivos (`discover`/`execute`); spike de
  document-transport continua env-gated off e fail-closed fora de prod —
  pre-existente, sem mudança
- `GENERIC_SQL_FORBIDDEN` intacto em eligibility; zero candidatos SQL
  genéricos na discovery
- Nenhum SQL via `CatalogActionPlan`
- Sem `fetchall` no caminho governed (teste dedicado)
- Sem credenciais/host/SQL em logs do executor (actor, correlation_id,
  query_hash, tabelas, limites, outcome)

## Invariantes DAVI (pós-S1)

| Invariante | Valor |
|---|---|
| allowlist_version | 21 |
| governed_operations | 89 |
| agent_intelligence | 2026.10.07.2 |
| mcp_tool_count | 2 |
| allowed_tables_count | 53 |
| execute_readonly_sql DAVI status | GENERIC_SQL_FORBIDDEN |

## Drift

- `origin/main` avançou `48a18814 → 13973e01` durante S1 — delia docs/script,
  public-hub, transformometro-api. Classificado **NON_CAUSAL**; worktree
  re-basado antes do commit.

## Limites declarados (handoff S2+)

- O executor governed exige `GOVERNED_SQL_DB_*` com principal read-only —
  **grant real é decisão de S2/S6**, ainda não provisionado.
- Contenção de linhas é client-side; não há garantia server-side de
  cardinalidade. Registrado como custo residual.
- S2 (owner/permission/branch/column policy) **não decidido** —
  `OWNER_RATIFICATION_REQUIRED` se não ratificado.

## Commit

- `0c02c6dbeb` — `feat(api-delpi): harden readonly sql validation with structural AST policy`
