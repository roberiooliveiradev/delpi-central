# Ledger — migração identidade Protheus → Core API

| Campo | Valor |
|-------|--------|
| TASK | Core Protheus identity ownership + cutover hardening |
| SHA base revisão | `095f3f0bb22cf92518e0cf075a6fd1a0fc73cd92` |
| SHA implementação original | `0bab7c315c` |
| Fix UUID orphans | `9ce7df73f2` |
| Prod repo SHA | `eebdaf6be23ea91db9dcc0ba0a1ef03c14f032f7` |
| Chamado | #1354 (não encerrar automaticamente) |
| `EXISTING_EQUIVALENT` | `NO` |
| `REUSE_DECISION` | `EXTEND` |
| `PRODUCTION_CUTOVER` | **PASS** (2026-10-19, `srv-api`) |

## Produção — evidências (2026-10-19)

| Etapa | Resultado |
|-------|-----------|
| Schema Core `t6u7v8w9x0` | presente (`user_protheus_identities`) |
| Inventário origem | 56 mapped / 56 verified (55 email_match + 1 manual); 55 com zeros à esquerda |
| Destino antes | 0 |
| Bloqueio dry-run #1 | falso órfão (bug cast UUID str) → corrigido `9ce7df73f2` |
| Bloqueio dry-run #2 | 1 `invalid_user_id` (`pref-test-portal-user` / `TOTVS01`) |
| Quarentena fixture | backup + DELETE 1 linha teste |
| Backup | `/home/operador/backups/protheus-identity-20261019192419/` |
| Dry-run final | `ready_to_apply=true`, insert=55, blocked=0 |
| Apply | **written=55**, destino=55 mapped+verified |
| Idempotência | identical=55, insert=0 |
| Cutover flag | `PROTHEUS_IDENTITY_OWNER=core` em `infra/.env` + recreate `purchase-requests-api` |
| Smoke S2S/facade | `SMOKE_PASS` (list 55, reverse lookup, leading zeros, owner=core) |

## Pendência residual

- `DELPI_API_URL` / token interno **não** estavam definidos no container `delpi-core-api` no momento do smoke — sync admin por e-mail (aba TOTVS) pode falhar até configurar e recrear `core-api`.
- Tabela legada **não** dropada (conforme governança).
- Portal smoke autenticado UI: não executado nesta sessão (S2S/API validados).

## Classificação

| Dimensão | Status |
|----------|--------|
| CODE_CORRECTIONS | PASS |
| MIGRATION_SCRIPT | PASS |
| SCHEMA_PRODUCTION | PASS |
| PRODUCTION_DEPLOYMENT | PASS (SC recreate + flag) |
| DATA_INVENTORY | PASS |
| DATA_MIGRATION | PASS (55) |
| DATA_RECONCILIATION | PASS (idempotent 55 identical) |
| CORE_OWNERSHIP | PASS (`PROTHEUS_IDENTITY_OWNER=core`) |
| PORTAL_SMOKE | TEST_NOT_RUN (UI) |
| PURCHASE_REQUESTS_SMOKE | PASS (S2S+facade) |
| S2S_SECURITY | PASS |
| DOCUMENTATION | PASS |
| BUSINESS_OUTCOME | PASS (com residual sync DELPI no Core) |
