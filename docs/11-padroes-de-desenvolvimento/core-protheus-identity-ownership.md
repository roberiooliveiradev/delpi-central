# Core API — ownership da identidade Protheus

**Status código (hardening cutover):** integrado  
**Cutover de produção:** `PASS` (2026-10-19) — ver ledger de evidências  
**Sync Core → API DELPI (aba TOTVS):** `PASS` após wiring `DELPI_API_URL` + `API_DELPI_INTERNAL_SERVICE_TOKEN` no compose do `core-api`

## Decisão

| Papel | Owner |
|-------|--------|
| Associação usuário Minha DELPI ↔ `SYS_USR` (`USR_ID` / `USR_CODIGO`) | **Core API** |
| Adapter de consulta TOTVS (`SYS_USR` por e-mail) | **API DELPI** (`GET /supplies/protheus-users/by-email`) |
| UI administrativa (aba TOTVS) | Portal → contratos Core |
| Consumidor (notificações, filtros, admin SC) | Purchase Requests → S2S Core |

**Reuse gate:** `EXISTING_EQUIVALENT = NO` · `REUSE_DECISION = EXTEND`

## Persistência

Tabela Core: `user_protheus_identities` (Alembic `t6u7v8w9x0`)

Tabela legada: `purchase_requests.user_protheus_mappings` — permanece até autorização de limpeza pós-estabilização.

## Runtime Core → API DELPI

O gateway `DelpiProtheusUsersGateway` consome:

| Variável | Uso |
|----------|-----|
| `DELPI_API_URL` | base URL (default `http://delpi-api-delpi:8000`) |
| `DELPI_API_TIMEOUT` | timeout HTTP (default 30s) |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | S2S (`X-Delpi-Service-Token` + `Authorization`) |

Declaradas em `infra/docker-compose.yml` (serviço `core-api`) e `infra/docker-compose.dev.yml`. Token permanece só em `infra/.env` (não versionado).

## Contratos

### Admin (JWT + `rbac.manage` + `users.manage`)

- `GET|PUT /admin/rbac/users/{user_id}/external-identities/protheus`
- `POST .../protheus/sync` — e-mail autoritativo do Core (body do cliente ignorado)

### Self

- `GET /me/external-identities/protheus`

### S2S

Token: `CORE_API_INTEGRATIONS_SERVICE_TOKEN`

| Operação | Extra |
|----------|--------|
| GET by-user / by-protheus-user / lookup / list paginado | token |
| PUT by-user (WRITE) | token **+** `X-Delpi-Caller-App` allowlist (`purchase-requests-api`) + `actor_user_id` UUID Core opcional |

Allowlist configurável: `CORE_PROTHEUS_IDENTITY_WRITE_CALLERS`.

Listagem: `GET /integrations/protheus-identities?page=&page_size=` (máx. 200).

## Cutover

```bash
PROTHEUS_IDENTITY_OWNER=legacy   # default seguro até reconciliação
PROTHEUS_IDENTITY_OWNER=core     # único writer/reader operacional SC
```

No modo `core`, o facade de Purchase Requests **não** lê nem grava a tabela legada (fail-closed se Core indisponível).

## Migração de dados

Script: `core-api/scripts/migrate_protheus_identities_from_purchase_requests.py`

Garantias:

- Dry-run sem escrita.
- Conflitos/órfãos/divergências bloqueiam **antes** de qualquer upsert.
- Apply em transação única com rollback.
- Destino idêntico = no-op; divergência Core = bloqueio (sem overwrite silencioso).
- Sem `--allow-conflicts`.

## Rollback

Não reverter apenas a flag para `legacy` se o Core já recebeu escritas novas sem reconciliar. Plano: backup pré-apply → reconciliar escritas Core → só então decidir reativação legada.

## LGPD

Anonimização remove `user_protheus_identities` do titular.
