# Minha DELPI — Core API: controllers e rotas HTTP

> **Arquivo:** `docs/04-core-api/controllers-e-rotas.md`  
> **Status:** documentação oficial (maio/2026)  
> **Código:** `core-api/app/interfaces/http/`  
> **Base URL (gateway):** `/core-api`

Todas as rotas abaixo são relativas ao prefixo público `/core-api`. Exemplo: `GET /core-api/me`.

---

## 1. Autenticação

| Item | Detalhe |
|---|---|
| Header | `Authorization: Bearer <JWT>` |
| Middleware | `auth_middleware.authenticate` em todo `before_request` |
| Proteção efetiva | Decorators `@require_auth`, `@require_permission`, etc. |

Sem token: `g.current_user` fica vazio; endpoints com `@require_auth` retornam **401**.

---

## 2. Formato de erro

```json
{
  "errors": [
    { "code": "forbidden", "message": "...", "path": "_global" }
  ]
}
```

Helpers: `app/interfaces/http/utils/errors.py`.

---

## 3. Health

| Método | Path | Auth | Resposta |
|---|---|---|---|
| GET | `/health` | Público | `{ "status": "Api rodando!" }` |

Arquivo: `health_controller.py`.

---

## 4. Usuário atual (`me_bp`)

Arquivo: `me_controller.py` — todas exigem `@require_auth()`.

| Método | Path | Descrição |
|---|---|---|
| GET | `/me` | Perfil + `roles`, `groups`, `permissions`, `is_superadmin` |
| GET | `/me/apps` | Apps ativos com rotas **já filtradas** por permissão |
| GET | `/me/apps/favorites` | Favoritos (somente apps autorizados) |
| POST | `/me/apps/favorites/{app_id}` | Adiciona favorito → `{ "ok": true }` |
| DELETE | `/me/apps/favorites/{app_id}` | Remove favorito |
| GET | `/me/notifications` | Não lidas (array) |
| GET | `/me/notifications/history` | Histórico paginado (`status`, `category`, `important`, `limit`, `offset`) |
| POST | `/me/notifications/{id}/read` | Marca como lida |
| POST | `/me/notifications/read-all` | Marca todas |
| DELETE | `/me/notifications/{id}` | Soft delete |
| PATCH | `/me/notifications/{id}/important` | `{ "isImportant": bool }` |
| GET/PATCH | `/me/notifications/preferences` | Categorias silenciadas |
| POST | `/me/notifications/test` | Teste (403 se `FLASK_ENV=production`) |
| GET | `/me/dashboard` | `{ "appsCount", "apps" }` |

Admin notificações (`notifications_controller.py`, superadmin): `POST /admin/notifications`, `GET/PUT /admin/notifications/dispatches/:id`, `GET /admin/notifications/dispatches`, `POST .../process-pending`, templates CRUD — ver [notificacoes.md](./notificacoes.md).

### GET /me — exemplo

```json
{
  "id": "uuid",
  "name": "Nome",
  "email": "user@empresa.com",
  "roles": ["..."],
  "groups": ["..."],
  "permissions": ["rbac.manage", "apps.view"],
  "is_superadmin": false
}
```

### GET /me/apps — item conceitual

```json
{
  "id": "strategic-indicators",
  "name": "Indicadores Estratégicos",
  "basePath": "/apps/strategic-indicators",
    "type": "microfrontend",
  "entryUrl": "/apps/strategic-indicators/assets/remoteEntry.js",
    "renderMode": "federated",
    "routes": [
      {
      "app": "strategic-indicators",
      "path": "/apps/strategic-indicators",
      "permission": "strategic-indicators.view",
      "label": "...",
        "showInMenu": true,
      "order": 1
    }
  ]
}
```

Use case: `ListUserAppsUseCase` + `AppAuthorizationService`.

---

## 5. Apps e plugins (`admin_apps_bp`)

Prefixo blueprint: `/admin/apps`  
Arquivo: `apps_controller.py`

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/apps` | `apps.view` |
| PUT | `/admin/apps/{plugin_id}` | `apps.manage` |
| GET | `/admin/apps/{plugin_id}/manifest` | `apps.view` |
| POST | `/admin/apps/register` | `apps.manage` |
| PUT | `/admin/apps/{plugin_id}/manifest` | `apps.manage` |
| GET | `/admin/apps/{plugin_id}/versions` | `apps.manage` |
| POST | `/admin/apps/{plugin_id}/rollback` | `apps.manage` |
| DELETE | `/admin/apps/{plugin_id}` | `apps.manage` |
| POST | `/admin/apps/{plugin_id}/active` | `apps.manage` |
| POST | `/admin/apps/bulk-activate` | `apps.manage` |
| POST | `/admin/apps/bulk-unregister` | `apps.manage` |
| GET | `/admin/apps/{app_id}/routes` | `apps.view` |
| POST | `/admin/apps/{app_id}/routes` | `apps.manage` |
| PUT | `/admin/apps/routes/{route_id}` | `apps.manage` |
| DELETE | `/admin/apps/routes/{route_id}` | `apps.manage` |
| POST | `/admin/apps/routes/bulk-delete` | `apps.manage` |

### Listagem paginada

`GET /admin/apps?page=1&page_size=10&q=&sort=name&direction=asc`

```json
{
  "data": [],
  "pagination": { "page": 1, "page_size": 10, "total": 0, "total_pages": 0 }
}
```

### Registro de plugin

`POST /admin/apps/register` — corpo = manifesto JSON completo. Validação: `ManifestValidator`.

Atualização **não estrutural**: `PUT /admin/apps/{id}/manifest` (nome, ícone, labels de rotas). Mudança de versão/basePath exige novo registro.

---

## 6. RBAC (`rbac_bp`)

Arquivo: `rbac_controller.py`  
Prefixo: `/admin/rbac`

Legenda de permissões:

- **RBAC** = `rbac.manage`
- **Roles** = `rbac.manage` + `roles.manage`
- **Groups** = `rbac.manage` + `groups.manage`
- **Users R** = `rbac.manage` + `users.view`
- **Users W** = `rbac.manage` + `users.manage`
- **SA** = `@require_superadmin()`

### Roles

| Método | Path | Permissão |
|---|---|---|
| POST | `/admin/rbac/roles` | Roles |
| GET | `/admin/rbac/roles` | RBAC |
| PUT | `/admin/rbac/roles/{role_id}` | Roles |
| DELETE | `/admin/rbac/roles/{role_id}` | Roles |
| POST | `/admin/rbac/roles/bulk-delete` | Roles |
| GET | `/admin/rbac/roles/{role_id}/permissions` | RBAC |
| PUT | `/admin/rbac/roles/{role_id}/permissions` | Roles |
| POST | `/admin/rbac/roles/{role_id}/permissions` | Roles |
| DELETE | `/admin/rbac/roles/{role_id}/permissions/{permission_id}` | Roles |
| GET | `/admin/rbac/roles/{role_id}/users` | RBAC |
| POST | `/admin/rbac/roles/{role_id}/users/{user_id}` | Roles |
| DELETE | `/admin/rbac/roles/{role_id}/users/{user_id}` | Roles |

### Groups

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/rbac/groups` | RBAC |
| POST | `/admin/rbac/groups` | Groups |
| PUT | `/admin/rbac/groups/{group_id}` | Groups |
| DELETE | `/admin/rbac/groups/{group_id}` | Groups |
| POST | `/admin/rbac/groups/bulk-delete` | Groups |
| GET | `/admin/rbac/groups/{group_id}/roles` | RBAC |
| PUT | `/admin/rbac/groups/{group_id}/roles` | Groups |
| POST | `/admin/rbac/groups/{group_id}/roles/{role_id}` | Groups |
| DELETE | `/admin/rbac/groups/{group_id}/roles/{role_id}` | Groups |
| GET | `/admin/rbac/groups/{group_id}/users` | RBAC |
| POST | `/admin/rbac/groups/{group_id}/users/{user_id}` | Groups |
| DELETE | `/admin/rbac/groups/{group_id}/users/{user_id}` | Groups |

### Users

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/rbac/users` | Users R |
| PUT | `/admin/rbac/users/{user_id}` | Users W — `roleIds`, `groupIds`, `birthDate`, `is_superadmin` |
| DELETE | `/admin/rbac/users/{user_id}` | SA |
| POST | `/admin/rbac/users/bulk-delete` | SA |
| GET | `/admin/rbac/users/{user_id}/roles` | RBAC |
| PUT | `/admin/rbac/users/{user_id}/roles` | Users W |
| POST | `/admin/rbac/users/{user_id}/roles/{role_id}` | Users W |
| DELETE | `/admin/rbac/users/{user_id}/roles/{role_id}` | Users W |
| GET | `/admin/rbac/users/{user_id}/groups` | Users R |
| PUT | `/admin/rbac/users/{user_id}/groups` | Users W |
| POST | `/admin/rbac/users/{user_id}/groups/{group_id}` | Users W |
| DELETE | `/admin/rbac/users/{user_id}/groups/{group_id}` | Users W |

### Permissions

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/rbac/permissions` | RBAC |
| GET | `/admin/rbac/permissions/{permission_id}/usage` | RBAC |

---

## 7. Admin — estatísticas e presença

Arquivos: `admin_statistics_controller.py`, `presence_controller.py`.

| Método | Path | Permissão | Descrição |
|---|---|---|---|
| GET | `/admin/statistics` | `rbac.manage` | Snapshot agregado: usuários, apps, papéis, grupos, permissões, vínculos RBAC, campanhas de notificação, online, uso de apps |
| GET | `/admin/users/presence` | Superadmin | Usuários com portal conectado (Socket.IO) |
| GET | `/admin/apps/usage` | `rbac.manage` | Apps em uso agora, ranking 30 dias, apps fantasmas |

`GET /admin/statistics` retorna contagens e rankings (ex.: papéis/grupos mais usados, apps por tipo, logins 7/30 dias). Campo `users.online` integra o store de presença; `apps.usage` integra uso de plugins. Ver [event-driven-e-socket.md](../01-arquitetura/event-driven-e-socket.md) §12.1 e §12.2.

---

## 8. Socket.IO

| Item | Valor |
|---|---|
| Path público | `/socket.io/` (gateway → `core-api:8000`) |
| Handshake | `auth.token` ou query token |
| Sala | `sub` do JWT (UUID usuário) |
| Eventos emitidos | `admin.changed`, `notification` |

Cliente Portal: `portal/src/hooks/useSocket.ts`.

---

## 9. Consumo pelo Portal

| Cliente | Arquivo |
|---|---|
| `/me`, apps, favoritos, notificações | `portal/src/data/coreApi.ts` |
| Admin RBAC + apps | `portal/src/data/adminApi.ts` |

Paths usados pelo admin batem com as tabelas acima (prefixo `/core-api/admin/rbac`).

---

## 10. Documentos relacionados

- [README.md](./README.md)
- [visao-geral-core-api.md](./visao-geral-core-api.md)
- [../03-autenticacao-autorizacao/rbac.md](../03-autenticacao-autorizacao/rbac.md)
- [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md)
- [../06-portal-frontend/autenticacao-frontend.md](../06-portal-frontend/autenticacao-frontend.md)
