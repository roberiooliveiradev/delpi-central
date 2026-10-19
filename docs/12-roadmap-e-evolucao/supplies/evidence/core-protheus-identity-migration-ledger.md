# Ledger — migração identidade Protheus → Core API

| Campo | Valor |
|-------|--------|
| TASK | Core Protheus identity ownership + cutover hardening |
| SHA base revisão | `095f3f0bb22cf92518e0cf075a6fd1a0fc73cd92` |
| SHA implementação original | `0bab7c315c` |
| Fix UUID orphans | `9ce7df73f2` |
| Wiring Core→api-delpi (compose) | `a6f37fe043` |
| Prod repo SHA implantado | `a6f37fe043130e2ca70d47d3e004852fd1cbd91f` |
| Chamado | #1354 (não encerrar automaticamente) |
| `EXISTING_EQUIVALENT` | `NO` |
| `REUSE_DECISION` | `EXTEND` |
| `PRODUCTION_CUTOVER` | **PASS** (2026-10-19, `srv-api`) |
| `CORE_DELPI_SYNC` | **PASS** (2026-10-19) |

## Produção — evidências cutover (2026-10-19)

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

## Produção — Core → API DELPI (2026-10-19)

| Etapa | Resultado |
|-------|-----------|
| Causa raiz | `infra/docker-compose.yml` do `core-api` **não** injetava `DELPI_API_URL` / `API_DELPI_INTERNAL_SERVICE_TOKEN` (dev já tinha) |
| Correção | wiring no compose prod + recreate só `core-api` via `up-prod-sequential.sh --fase core --build core-api` |
| SHA implantado | `a6f37fe043` |
| Config validada (sem secrets) | `DELPI_API_URL=http://delpi-api-delpi:8000` (default compose); `DELPI_API_TIMEOUT=30`; `API_DELPI_INTERNAL_SERVICE_TOKEN` presente em `infra/.env` e no container (len=64) |
| Conectividade autenticada | `GET /supplies/protheus-users/by-email` → **200** com token; **401** sem token |
| Health `delpi-core-api` | OK (`{"status":"Api rodando!"}`) |
| Logs | sem vazamento de token/secret no recorte pós-recreate |

### Homologação aba TOTVS (API = mesma superfície do Portal)

Conta controlada: Keycloak `user` / Portal e-mail `user@local.com` (JWT password grant `delpi-central`).

| Caso | Resultado |
|------|-----------|
| Carregar vínculo existente (GET) | **PASS** `USR_ID=000288`, código presente, `mapped`+`verified` |
| Atualizar (reload GET) | **PASS** |
| Sincronizar por e-mail (POST sync) | **PASS** e-mail `almoxarifado1-01@delpi.com.br`; `USR_ID`/`USR_CODIGO` estáveis; zeros à esquerda preservados |
| Sibling sync | **PASS** `almoxarifado@delpi.com.br` |
| Sem Authorization | **PASS** 401 |
| Integridade pós-sync | **PASS** 55 total / 55 verified / 55 mapped / 55 distinct / 55 leading zeros |

UI browser Portal não automatizada nesta sessão; endpoints admin usados pela aba TOTVS foram exercidos com JWT do usuário controlado.

## Pendências residuais

- Tabela legada `purchase_requests.user_protheus_mappings` **não** dropada (governança).
- Chamado **#1354** permanece aberto para aceite independente.
- Negativo de autorização (403 sem `rbac.manage`+`users.manage`) ficou **INCONCLUSIVE** nesta sessão (possível cache de effective permissions); não bloqueia conectividade Core→api-delpi nem sync.

## Classificação

| Dimensão | Status |
|----------|--------|
| CODE_CORRECTIONS | PASS |
| MIGRATION_SCRIPT | PASS |
| SCHEMA_PRODUCTION | PASS |
| PRODUCTION_DEPLOYMENT | PASS |
| DATA_INVENTORY | PASS |
| DATA_MIGRATION | PASS (55) |
| DATA_RECONCILIATION | PASS |
| CORE_OWNERSHIP | PASS (`PROTHEUS_IDENTITY_OWNER=core`) |
| CORE_DELPI_CONNECTIVITY | PASS |
| PORTAL_TOTVS_SYNC | PASS (API admin; UI browser TEST_NOT_RUN) |
| PURCHASE_REQUESTS_SMOKE | PASS (S2S+facade) |
| S2S_SECURITY | PASS |
| DOCUMENTATION | PASS |
| BUSINESS_OUTCOME | PASS |
