# DAVI-GOVERNED-SQL-READ-AUTHZ-RATIFICATION-S2-001

> **SUPERSEDED / ARCHITECTURE CORRECTED** — ver `davi-sql-canonical-route-architecture-rebaseline-001.md` (`DAVI-SQL-CANONICAL-ROUTE-NORMALIZATION-IMPLEMENTATION-001`).
> O modelo «governed SQL dedicado com executor/principal próprio e gate de AuthZ DAVI-específico» foi corrigido: `execute_readonly_sql` (POST /data/sql) é uma rota canônica normal da API DELPI, exposta pelo mesmo broker discover→execute sob `DATA_SQL_ACCESS` do backend.
> Não há permissão SQL dedicada, executor DAVI direto ao banco, BranchAccessGate MCP, política de coluna MCP ou gate de business owner para a rota SQL.


## Status

`OWNER_RATIFICATION_REQUIRED` — S2 é um gate de autoridade, não de
código. Nenhuma decisão de autorização foi inventada; nenhum wiring foi
feito (o executor governed de S1 continua **sem consumidor**).

## Estado atual (fatos)

| Fato | Evidência |
|---|---|
| Rota existente `POST /data/sql` | `app/interface/http/routes/data_routes.py` — permissão `DATA_SQL_ACCESS = [API_DELPI_ACCESS_FULL, API_DELPI_DATA]` |
| Escopo de branch em `execute_readonly_sql` | **inexistente** — a consulta decide filial via colunas (`*_FILIAL`); não há filtro sistemático |
| Identidade do usuário | disponível via `delpi_auth.request_context.get_current_user()` (JWT propagado) |
| Precedente de branch-scope | `BranchAccessGate` + permissões `*.filial-01|02|es|sc` (reports, produção, 5s, kaizometro) |
| Conexão governed | `GOVERNED_SQL_DB_*` — principal dedicado exigido; **grant real não provisionado** |
| DAVI AuthZ | DAVI nunca decide AuthZ — backend é autoridade final |

## Decisões pendentes de owner (bloqueantes)

1. **Business owner** — quem assina o risco do fallback analítico SQL.
2. **Permission model** — reutilizar `DATA_SQL_ACCESS` (mesma permissão,
   mesmos holders) **ou** permissão dedicada (ex.: `api-delpi.data.sql-governed`)
   com rollout próprio. Decisão afeta quem pode executar.
3. **Branch scope** — (a) sem filtro (paridade com rota atual), (b)
   filtro sistemático de `*_FILIAL` por permissões `*.filial-*` no plano
   (requer mapeamento tabela→coluna-filial), ou (c) negar consultas que
   toquem dados multi-filial sem filtro explícito. Opção (b/c) exige
   owner de dados confirmar quais das 53 tabelas são branch-scoped.
4. **Column policy** — allowlist de tabelas existe (53); colunas
   sensíveis (custo, salário, margem) precisam de política explícita ou
   se aceita "table-level = suficiente".
5. **Negative AuthZ design** — resposta ao usuário sem permissão:
   403 padrão, redacted denial, ou descoberta que nunca oferece o
   candidato (preferred: candidato nunca gerado para usuário sem permissão).
6. **Database grants** — provisionamento do principal `GOVERNED_SQL_DB_*`
   com `SELECT` somente nas 53 tabelas allowlisted (ou schema/view
   intermediário). Owner de infra/DBA deve ratificar; hoje fail-closed.
7. **Identity propagation** — actor fim-a-fim: JWT subject → auditoria
   SQL (log/auditoria TOTVS). DB principal é serviço compartilhado —
   owner decide se auditoria applicational (correlation_id+actor log)
   satisfaz ou se exige `CONTEXT_INFO`/impersonation.
8. **Segregação do candidato** — candidate_token de SQL fallback bound ao
   usuário que descobriu (user-bound) — confirmação formal.

## Sem estas decisões

- S3 (contrato de saída) pode ser desenhado, mas não conectado.
- S4 (broker) não pode materializar candidatos sem permission model.
- S6 (live acceptance) impossível sem grants + rate policy.

## Recomendação técnica (não-decisão)

Submeter ao owner: permissão dedicada `api-delpi.data.sql-governed` +
`BranchAccessGate` no plano + grant `SELECT`-only nas 53 tabelas +
auditoria applicational com actor/correlation_id. O executor S1 já
suporta actor/correlation_id; falta apenas a decisão e o wiring.
