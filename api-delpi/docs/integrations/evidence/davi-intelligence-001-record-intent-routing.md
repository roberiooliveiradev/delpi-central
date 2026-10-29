# DAVI-INTELLIGENCE-001 — Row-record intent routing to canonical SQL

> **Task:** `DAVI-INTELLIGENCE-001` — Descoberta semântica, consultas e
> orquestração de dados. **Natureza:** correção de orquestração governada
> (menor diff; zero capabilities novas; zero MCP tools novas).

## 1. Defect statement

```text
User:   "Traga os 10 primeiros registros da SG1010."
DAVI:   "não possuo acesso à tabela"        (zero candidates)
User:   "...rota SQL..."                   (menciona o mecanismo)
DAVI:   resolve e consulta                  (alias SQL-only casou)
```

**Desired:** o usuário não precisa conhecer SQL, endpoint, MCP ou nome de
operação; o discovery deve rotear intenção de dados para a capability
governada existente.

## 2. Capability inventory (PROVEN vs TO_INVENTORY)

| Recurso | Rota/Operação | AuthZ backend | MCP | Status |
|---|---|---|---|---|
| SQL read-only canônico | `POST /data/sql` → `execute_readonly_sql` | `DATA_SQL_ACCESS` | discover→execute (`canonicalSqlRoute` opt-in; executável só via live `app.openapi()` — baseline snapshot não carrega `requestBody`, fail-closed) | **PROVEN** (allowlist v28+; restaurado pelo owner em 2026-10-19) |
| Busca de tabelas | `GET /system/tables/search` → `search_tables_by_description` | `SYSTEM_METADATA_ACCESS` | `BOUNDED_METADATA_READ` opt-in | PROVEN |
| Describe tabela | `GET /system/tables/{tableName}` → `get_protheus_table` | idem | idem | PROVEN |
| Colunas de tabela | `GET /system/tables/{tableName}/columns` → `list_protheus_table_columns` | idem | idem | PROVEN |
| Busca de colunas | `/columns/search` (global + in-table) | idem | idem | PROVEN |
| Índices/relations/schema/smoke/stats `/system` | demais ops | — | **não promovidas** (catálogo técnico/admin) | TO_INVENTORY |
| SQL arbitrário / proxy genérico | — | — | FORBIDDEN | — |

`POST /data/sql` aceita JSON `{sql}` ou `text/plain`; `SqlValidator`
(AST T-SQL) é a fronteira de segurança — somente SELECT. Nenhuma permissão
DAVI-local; backend 403 é a decisão final.

## 3. Root cause

Two-sided contract incompleto desde `CORRECTIVE-001`:

```text
metadata ops carry retrievalNegativePhrases
  ("mostre os registros", "traga os dados", "dump da tabela", ...)
        → row-access intents are suppressed from metadata (correct)
execute_readonly_sql had ONLY mechanism aliases
  ("consulta sql", "via sql", "select from", ...)
        → record/data/table-row intents found ZERO candidates
        → agent reported "não tenho acesso" (wrong taxonomy too)
```

Reproduction (live-seeded catalog, `seed_actions_from_openapi(app.openapi())`):

```text
BEFORE v29:
 "traga os 10 primeiros registros da SG1010" → 0 candidates
 "mostre os dados da tabela SG1010"          → 0 candidates
 "liste os registros da SB1010"              → 5 junk hits @0.521
 "quais campos existem na SG1010"            → search_protheus_columns_in_table 0.897 (ok)

AFTER v29:
 "traga os 10 primeiros registros da SG1010" → execute_readonly_sql 0.907
 "mostre os dados da tabela SG1010"          → execute_readonly_sql 0.907
 "liste os registros da SB1010"              → execute_readonly_sql 0.905
 "filtre os registros do mês atual"          → execute_readonly_sql 0.900
 "quero ver os dados dessa tabela"           → execute_readonly_sql 0.907
 "quais campos existem na SG1010"            → search_protheus_columns_in_table 0.897 (unchanged)
 "dados cadastrais da tabela SB1010"         → get_protheus_table 0.925 > sql 0.907 (longer alias wins)
 "mostre os dados do produto 10080034"       → get_product_detail (no sql bypass)
 "delete os registros da SG1010"             → 0 candidates (write guard)
```

## 4. Fix (bounded diff)

- `davi_external_read_allowlist.json` **v28→v29**: +27 data-intent aliases on
  `execute_readonly_sql` (registros/linhas/dados de tabela + verbos de leitura)
  espelhando as `retrievalNegativePhrases` das ops de metadata; `+1` alias
  `fabricantes` em `get_product_suppliers` (regressão pré-existente no HEAD:
  "pesquise fabricantes e informações técnicas…" não alcançava o op —
  V3-aceite restaurado); `coverageDecision` encadeada
  (`COMPLETE_ROW_RECORD_INTENT_ROUTING` ← SUPPLIER-V3).
- `davi_agent_intelligence.json` **2026.10.27.1→2026.10.29.1**:
  `flows.ad_hoc_sql_read` ganha nota de roteamento de intenção de registros,
  resolução de nome curto de tabela via metadata (nunca fabricar nome físico),
  `capabilities: [execute_readonly_sql]` e `refusal_taxonomy`
  (lacuna de capability ≠ ausência de dado ≠ 403 ≠ tabela não encontrada ≠
  zero linhas).
- `davi_agent_intelligence_service.py`: budget de diretivas 24→26 KiB
  (precedente: 16→20→24; adição governada ~0.7 KiB; transporte 64 KiB intacto).
- Testes: seção `INTELLIGENCE-001` em `test_davi_system_metadata.py` com seed
  live (o caminho de produção) — executável, roteamento, não-roubo de
  metadata/negócio, write guard; pins de versão/cadeia rebaselinados (+1 hop).
- Fixture `davi_discovery_quality_v1.json`: 246→254 casos (família
  `canonical_sql` + colisões); evidência do benchmark regenerada.

## 5. Verification

```text
UNIT/CONTRACT tests  = PASS — 475 pass (system_metadata + similarity +
                       dynamic_read + corrective + wave006 + real_user)
Benchmark (live seed) = PASS — 254 casos; top-1 0.9604 (vs 0.9591 anterior);
                       top1_required 0.9907; target misses 0; hard-negative
                       leaks 0; canonical_sql family top-1 = 1.0;
                       9 falhas = conjunto conhecido pré-existente
EXECUTION_DRIFT      = nenhum material; 1 regressão pré-existente V3 corrigida
                       (alias 'fabricantes'), 1 teste stale anotado
                       (baseline fail-closed vs live path — SEC-02 documentada)
MCP DISCOVERY        = contract shape inalterado (2 tools)
BACKEND AUTHZ        = inalterado — DATA_SQL_ACCESS final; sem RBAC local
LIVE AUTHENTICATED   = TEST_NOT_RUN — requer OAuth de usuário via provider
DEPLOYED SHA         = PENDING — deploy canônico após push/gates
```

## 6. Residual gaps / TO_INVENTORY

- Resolução de nome curto de tabela (SG1 → SG1010) é **instrução ao agente**:
  deve confirmar via metadata ops antes de formular SQL; não há sufixo
  automático no backend.
- Demais rotas `/system` (indexes, relations, schema, stats) permanecem
  não promovidas — catálogo técnico completo não é superfície DAVI.
- `NEGATIVE_BUSINESS_AUTHZ` (2ª identidade) e ratificação formal de negócio
  continuam gates independentes de publicação ampla.
