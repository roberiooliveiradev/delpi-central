# E11.S8 — Clean Architecture residual + smoke credentials

**Status:** COMPLETE_GATE (RQ11-09 ATENDIDO; RQ11-08 residual inventariado)  
**Cobre:** RQ11-08, RQ11-09

## CUTOVER — credentials (RQ11-09)

- Removidos defaults versionados `SMOKE_USER=rober` / `SMOKE_PASSWORD=1234` em ~80 scripts.
- Helper canônico: `scripts/smoke_credentials.py` → `require_smoke_credentials()` (exit 2 se ausente).
- 73 smokes passam a `USER, PASSWORD = require_smoke_credentials()`.
- Gate `SEMANTIC_SMOKE_CREDENTIAL_DEFAULT` full-tree: **0**.
- Debt semântico full-tree total: **0** (todos os SEMANTIC_* limpos neste HEAD).

## GENERALIZAÇÃO

| Caso | Resultado |
|---|---|
| env ausente | SystemExit 2 |
| env presente | tuple user/password |
| debt scan smoke | 0 findings |

## Clean Architecture (RQ11-08) — residual

Movimentação ampla domain→infrastructure (generation/FS) **não** foi big-bang nesta subetapa (risco de regressão sem wiring). Residual permanece inventariado em D11-08 / S0; enforcement Phase3 + composition root vigentes. Remoção física de FS em domain → **E11.S10 residual scan** se ainda material.

## Residual

- Outros defaults não-credencial (`SMOKE_BASE_URL`, realm, client_id) permanecem (não são secrets).
- RQ11-08 cleanup físico de boundaries: S10 se debt/arquitetura ainda apontar.
