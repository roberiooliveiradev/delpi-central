# Core API — ownership da identidade Protheus

**Status:** implementação de código pronta para review  
**Cutover de produção:** `PENDING` (requer inventário, backup, dry-run, autorização)

## Decisão

| Papel | Owner |
|-------|--------|
| Associação usuário Minha DELPI ↔ `SYS_USR` (`USR_ID` / `USR_CODIGO`) | **Core API** |
| Adapter de consulta TOTVS (`SYS_USR` por e-mail) | **API DELPI** (`GET /supplies/protheus-users/by-email`) |
| UI administrativa (aba TOTVS) | Portal → contratos Core |
| Consumidor (notificações, filtros SC) | Purchase Requests → S2S Core |

**Reuse gate**

- `EXISTING_EQUIVALENT = NO` (Core não tinha identidade externa Protheus)
- `REUSE_DECISION = EXTEND` (gestão de usuários Core + lookup api-delpi existente)

## Persistência

Tabela Core: `user_protheus_identities`

- PK/FK `user_id` → `users.id` (CASCADE)
- `protheus_user_id` (TEXT, zeros à esquerda preservados)
- `protheus_user_code`, `mapping_status`, `mapping_source`, `verified`
- Índice único parcial em `protheus_user_id` quando `mapping_status='mapped'`
- Migration Alembic: `t6u7v8w9x0_user_protheus_identities`

A tabela legada `purchase_requests.user_protheus_mappings` **não é dropada** nesta entrega.

## Contratos Core

### Admin (JWT + `rbac.manage` + `users.manage`)

- `GET /admin/rbac/users/{user_id}/external-identities/protheus`
- `PUT /admin/rbac/users/{user_id}/external-identities/protheus`
- `POST /admin/rbac/users/{user_id}/external-identities/protheus/sync`  
  — e-mail autoritativo vem do Core; o body do cliente **não** define a identidade.

### Self

- `GET /me/external-identities/protheus` — somente o usuário autenticado

### S2S (`X-Delpi-Service-Token` / Bearer = `CORE_API_INTEGRATIONS_SERVICE_TOKEN`)

- `GET /integrations/protheus-identities/by-user/{user_id}`
- `GET /integrations/protheus-identities/by-protheus-user/{protheus_user_id}`
- `POST /integrations/protheus-identities/lookup` (`user_ids` e/ou `protheus_user_ids`, máx. 50)
- `PUT /integrations/protheus-identities/by-user/{user_id}` — compatibilidade de escrita no cutover

## Cutover

| Estado | Writer | Reader SC | Portal |
|--------|--------|-----------|--------|
| A (legado) | purchase-requests | local | SC rbac |
| B (prep) | ainda legado | local | **Core** (novo) |
| C (cutover) | **Core** (`PROTHEUS_IDENTITY_OWNER=core`) | Core S2S | Core |
| D (estabilização) | Core | Core | Core — remoção tabela legada só com autorização |

Env de cutover no purchase-requests-api:

```bash
PROTHEUS_IDENTITY_OWNER=core
```

Default atual do código: `legacy` (seguro até migração de dados).

## Migração de dados

Script (dry-run por padrão):

`core-api/scripts/migrate_protheus_identities_from_purchase_requests.py`

Não executar em produção sem backup + autorização operacional.

## LGPD

Anonimização de usuário no Core remove a linha em `user_protheus_identities`.
