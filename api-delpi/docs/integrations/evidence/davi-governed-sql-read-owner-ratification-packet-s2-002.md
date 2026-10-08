# DAVI GOVERNED SQL — OWNER RATIFICATION PACKET

> **Task:** `DAVI-GOVERNED-SQL-READ-AUTHZ-RATIFICATION-S2-002`
> **Base:** `80b8c994b1` (S1 corrective fechado)
> **Escopo:** fallback analítico SQL READ-only, somente quando nenhuma
> capability canônica responde suficientemente. Nunca SQL genérico.

## O que já está FROZEN (não reabre)

| Decisão | Estado | Fonte |
|---|---|---|
| Backend AuthZ final (403 autoritativo) | FROZEN | `DAVI-READ-AUTHZ-REBASELINE-001` RATIFIED |
| Identidade = END_USER_ACCOUNT; user A não herda user B | FROZEN | `DAVI-READ-AUTHZ-REBASELINE-001` |
| Candidate token user-bound (HMAC + actor_id + exp) | PROVEN | `candidate_token.py` + `test_davi_dynamic_read.py:728-761` |
| Principal DB dedicado read-only exigido antes de produção | FROZEN | S1 source (`GOVERNED_SQL_DB_*`, fail-closed) |
| Auditoria application-level (actor + correlation_id) obrigatória | FROZEN | S1 executor |
| `CONTEXT_INFO`/impersonation NÃO exigido em V1 | FROZEN | Arquitetura |
| Generic SQL tool | FORBIDDEN | `GENERIC_SQL_FORBIDDEN` |
| MCP tools = 2 | FROZEN | `DAVI-MCP-TOOL-SURFACE-SIMPLIFICATION-001` |

## Decisões que exigem owner

---

### DECISION 1 — BUSINESS OWNER

**Question:** Quem responde pelo risco de negócio do fallback analítico
SQL sobre dados DELPI autorizados?

**Current evidence:** `BUSINESS_OWNER = TO_INVENTORY` é o estado canônico
documentado para famílias DAVI (`davi-capability-wave-002-freeze`,
`davi-governed-knowledge-freeze-001`) — nenhum owner nomeado provado em
source. Não é permitido inferir Comercial/Suprimentos/Controladoria/
Financeiro.

**Recommendation:** nomear owner de produto/dados da superfície DAVI
exposta; o fallback SQL toca todas as 53 tabelas allowlisted, então o
owner deve cobrir o perímetro inteiro ou delegar por família.

**Required answer:** `<owner/team/role>`

---

### DECISION 2 — PERMISSION MODEL

**Question:** O governed SQL reutiliza `api-delpi.data` (holders atuais
do `/data/sql` legado) ou ganha permissão dedicada?

**Options:**
- **A** — reutilizar `DATA_SQL_ACCESS` = `[api-delpi.access.full, api-delpi.data]`
- **B** — permissão dedicada backend-owned (conceito: `api-delpi.data.sql-governed`, nome não congelado)

**Recommendation:** **B** — holders legados (analistas internos,
consumidores service-token, SQL bruto) não devem herdar
automaticamente capability nova de Agent end-user.

**Required answer:** `A / B / alternative`

---

### DECISION 3 — BRANCH SCOPE

**Question:** Resultados governed SQL são restritos por filial?

**Current evidence:** `DAVI-READ-AUTHZ-REBASELINE-001` (RATIFIED) —
"branch = query filter; authorized user may query across branches;
`DAVI_BRANCH_AUTHZ = FORBIDDEN`". Para operações canônicas a política
está ratificada; o fallback SQL compartilha a mesma superfície DAVI.

**Options:**
- **A** — paridade com a política ratificada: filial é filtro, sem ACL de filial no plano SQL
- **B** — `BranchAccessGate` aplicado ao plano (exige mapeamento tabela→coluna-filial)
- **C** — negar consultas que toquem dados multi-filial sem filtro explícito

**Recommendation:** **A** — consistente com a decisão ratificada; o
backend (grant do principal + allowlist) é a fronteira técnica, e
DAVI não pode inventar AuthZ de filial. **Se o owner exigir B/C, o plano
precisa de metadados tabela→coluna-filial antes de S3.**

**Required answer:** `A / B / C / other`

---

### DECISION 4 — COLUMN POLICY

**Question:** Autorização de tabela implica autorização de todas as
colunas?

**Current evidence:** allowlist = 53 tabelas físicas;
`dataClassification = MINIMIZATION_REQUIRED_TAXONOMY_OPTIONAL`. Superfícies
de alto risco presentes no allowlist incluem `SA1010`, `SA2010`,
`SU5010`, `SD1010`, `SD2010`, `SYS_USR`, `SYP010` — campos de custo,
margem, fiscal, contato e usuário/sistema.

**Options:**
- **A** — table-level implica all-columns
- **B** — política de deny/allow por coluna
- **C** — views curadas no banco

**Recommendation:** **B ou C** para as tabelas sensíveis acima; `SYS_USR`
(credenciais/usuários) provavelmente deve sair do perímetro governed
mesmo estando no allowlist legado. Requer classificação por owner de dados.

**Required answer:** `A / B / C / other` + owner de classificação

---

### DECISION 5 — DB GRANTS

**Question:** Qual owner de infra/DBA provisiona o principal dedicado
`GOVERNED_SQL_DB_*` com SELECT-only nas 53 tabelas allowlisted?

**Current evidence:** source suporta (`SOURCE_SUPPORT = PROVEN`);
`REAL_DB_GRANTS = PENDING`. Sem provisionamento o caminho permanece
fail-closed (POLICY_UNAVAILABLE) — seguro, mas inoperante.

**Required answer:** `<DBA/infra owner>` + modelo de grant
(tabela-a-tabela vs schema/view intermediário)

---

### DECISION 6 — RATE POLICY (informativa; não bloqueia S2)

**Current evidence:** `MCP_RATE_POLICY = PENDING_OWNER_DECISION` é
estado canônico pre-existente do MCP inteiro. Valores numéricos podem
ficar `TO_INVENTORY` até workload medido; owner precisa ser nomeado.

**Required answer:** `<owner>` — valores podem seguir `TO_INVENTORY`

---

## Resultado

```text
S2_FINAL_VERDICT = OWNER_RATIFICATION_REQUIRED
```

Nenhum código de AuthZ foi alterado (regra §22 respeitada). O executor
governed segue **sem consumidor** — nenhuma rota, tool MCP, plano ou
candidato SQL foi criado.
