# Minha DELPI — Core API: Controllers e Rotas HTTP

> **Arquivo:** `docs/04-core-api/controllers-e-rotas.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** controllers, endpoints HTTP, proteções e responsabilidades da Core API

---

## 1. Objetivo

Este documento descreve os controllers HTTP e as principais rotas da **Core API** da Minha DELPI.

A Core API é responsável pela governança da plataforma: autenticação recebida via JWT, usuário atual, RBAC, apps, plugins, rotas, favoritos, notificações e eventos administrativos.

Este documento organiza as rotas por controller e descreve:

- método HTTP;
- path;
- finalidade;
- proteção/autorização esperada;
- use case relacionado, quando conhecido;
- observações importantes.

---

## 2. Controllers principais

Controllers identificados:

```text
app/interfaces/http/health_controller.py
app/interfaces/http/me_controller.py
app/interfaces/http/apps_controller.py
app/interfaces/http/rbac_controller.py
app/interfaces/http/auth_middleware.py
```

Blueprints principais:

| Blueprint | Controller | Responsabilidade |
|---|---|---|
| `health_bp` | `health_controller.py` | Healthcheck |
| `me_bp` | `me_controller.py` | Usuário atual, apps, favoritos, notificações e dashboard |
| `admin_apps_bp` | `apps_controller.py` | Apps, plugins, manifestos, versões e rotas |
| `rbac_bp` | `rbac_controller.py` | Usuários, roles, groups, permissions e vínculos RBAC |

---

## 3. Middleware de autenticação

Arquivo:

```text
app/interfaces/http/auth_middleware.py
```

O middleware roda globalmente em `before_request`.

Fluxo:

```text
Requisição HTTP
  ↓
Lê Authorization: Bearer <token>
  ↓
Se não houver token, segue sem usuário
  ↓
Se houver token, valida JWT
  ↓
Sincroniza usuário local
  ↓
Resolve roles, groups e permissions
  ↓
Define g.current_user
```

Ponto importante:

> O middleware não bloqueia automaticamente endpoints sem token. A proteção real dos endpoints depende dos decorators nos controllers.

Decorators usados:

```text
require_auth
require_superadmin
require_permission
require_any_permission
require_all_permissions
```

---

## 4. Padrão de erro

Os controllers devem retornar erros no formato:

```json
{
  "errors": [
    {
      "code": "forbidden",
      "message": "Permission denied",
      "path": "_global"
    }
  ]
}
```

Helpers disponíveis:

```text
unauthorized
forbidden
not_found
bad_request
unprocessable
conflict
server_error
```

---

## 5. Health Controller

Arquivo:

```text
app/interfaces/http/health_controller.py
```

### 5.1 Healthcheck

```http
GET /health
```

Finalidade:

```text
Verificar se a Core API está respondendo.
```

Proteção:

```text
Público
```

Resposta conceitual:

```json
{
  "status": "Api rodando!"
}
```

Uso:

- validação local;
- gateway/proxy;
- monitoramento básico;
- troubleshooting.

---

## 6. Me Controller

Arquivo:

```text
app/interfaces/http/me_controller.py
```

Responsabilidade:

- dados do usuário autenticado;
- apps autorizados;
- favoritos;
- notificações;
- dashboard resumido.

Prefixo conceitual:

```text
/me
```

Todos os endpoints desta seção devem exigir usuário autenticado.

---

## 7. `GET /me`

```http
GET /me
```

Finalidade:

```text
Retornar dados do usuário atual autenticado.
```

Proteção:

```text
require_auth
```

Use case:

```text
GetMeUseCase
```

Resposta conceitual:

```json
{
  "id": "uuid",
  "name": "Nome do Usuário",
  "email": "usuario@empresa.com",
  "roles": ["admin"],
  "groups": ["ti"],
  "permissions": ["apps.view", "dashboard-lmps.access"],
  "is_superadmin": false
}
```

Uso pelo Portal:

- exibir usuário;
- verificar permissões para UX;
- habilitar áreas administrativas;
- iniciar estado autenticado.

---

## 8. `GET /me/apps`

```http
GET /me/apps
```

Finalidade:

```text
Retornar apps e rotas autorizados para o usuário atual.
```

Proteção:

```text
require_auth
```

Use case:

```text
ListUserAppsUseCase
```

Fluxo:

```text
Lista apps ativos com rotas
  ↓
Resolve permissões do usuário
  ↓
AppAuthorizationService filtra apps/rotas
  ↓
Retorna DTO normalizado ao Portal
```

Resposta conceitual:

```json
[
  {
    "id": "dashboard-lmps",
    "name": "Dashboard LMPs",
    "basePath": "/apps/dashboard-lmps",
    "icon": "bar-chart3",
    "type": "microfrontend",
    "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
    "renderMode": "federated",
    "routes": [
      {
        "path": "/apps/dashboard-lmps",
        "permission": "dashboard-lmps.access",
        "label": "Dashboard LMPs",
        "showInMenu": true,
        "order": 1,
        "entry": null
      }
    ]
  }
]
```

---

## 9. `GET /me/apps/favorites`

```http
GET /me/apps/favorites
```

Finalidade:

```text
Listar apps favoritos do usuário atual.
```

Proteção:

```text
require_auth
```

Use case:

```text
ListFavoriteAppsUseCase
```

Regra:

```text
Favoritos são filtrados contra apps autorizados.
```

---

## 10. `POST /me/apps/favorites/<app_id>`

```http
POST /me/apps/favorites/<app_id>
```

Finalidade:

```text
Adicionar app aos favoritos do usuário atual.
```

Proteção:

```text
require_auth
```

Use case:

```text
AddFavoriteAppUseCase
```

Resposta:

```json
{
  "ok": true
}
```

Evento:

```text
favorite_added
```

Observação:

```text
Operação idempotente quando o favorito já existe.
```

---

## 11. `DELETE /me/apps/favorites/<app_id>`

```http
DELETE /me/apps/favorites/<app_id>
```

Finalidade:

```text
Remover app dos favoritos do usuário atual.
```

Proteção:

```text
require_auth
```

Use case:

```text
RemoveFavoriteAppUseCase
```

Resposta:

```json
{
  "ok": true
}
```

Evento:

```text
favorite_removed
```

---

## 12. `GET /me/notifications`

```http
GET /me/notifications
```

Finalidade:

```text
Listar notificações não lidas do usuário atual.
```

Proteção:

```text
require_auth
```

Use case:

```text
ListUnreadNotificationsUseCase
```

---

## 13. `POST /me/notifications/<notification_id>/read`

```http
POST /me/notifications/<notification_id>/read
```

Finalidade:

```text
Marcar uma notificação como lida.
```

Proteção:

```text
require_auth
```

Use case:

```text
MarkNotificationReadUseCase
```

Ponto de atenção:

> O use case conhecido chama `notifications.get(notification_id)`. É necessário garantir que o repository concreto implemente esse método.

---

## 14. `POST /me/notifications/read-all`

```http
POST /me/notifications/read-all
```

Finalidade:

```text
Marcar todas as notificações do usuário como lidas.
```

Proteção:

```text
require_auth
```

Use case:

```text
MarkAllNotificationsReadUseCase
```

---

## 15. `POST /me/notifications/test`

```http
POST /me/notifications/test
```

Finalidade:

```text
Criar notificação de teste para o usuário atual.
```

Proteção:

```text
require_auth
```

Use case provável:

```text
NotifyUserUseCase
```

Observação:

> Endpoint útil para desenvolvimento/teste. Avaliar se deve existir em produção.

---

## 16. `GET /me/dashboard`

```http
GET /me/dashboard
```

Finalidade:

```text
Retornar dados resumidos do dashboard do usuário atual.
```

Proteção:

```text
require_auth
```

Observação:

> O conteúdo exato depende da implementação vigente do controller.

---

## 17. Apps Controller

Arquivo:

```text
app/interfaces/http/apps_controller.py
```

Prefixo:

```text
/admin/apps
```

Responsabilidade:

- administração de apps;
- registro de plugins;
- manifestos;
- versões;
- rollback;
- ativação/desativação;
- rotas;
- operações em lote.

---

## 18. `GET /admin/apps`

```http
GET /admin/apps
```

Finalidade:

```text
Listar apps/plugins para administração.
```

Proteção esperada:

```text
apps.view
```

Use case:

```text
ListAdminAppsUseCase
```

Query params comuns:

```text
q
page
page_size
sort
direction
```

Resposta:

```text
PaginatedResult
```

---

## 19. `PUT /admin/apps/<plugin_id>`

```http
PUT /admin/apps/<plugin_id>
```

Finalidade:

```text
Atualizar metadata administrativa do app.
```

Proteção esperada:

```text
apps.manage
```

Use case:

```text
UpdateAdminAppUseCase
```

Campos esperados:

```json
{
  "name": "Novo Nome",
  "description": "Descrição",
  "icon": "icon-name"
}
```

Evento:

```text
app_updated
```

---

## 20. `GET /admin/apps/<plugin_id>/manifest`

```http
GET /admin/apps/<plugin_id>/manifest
```

Finalidade:

```text
Obter manifesto vigente de um plugin.
```

Proteção esperada:

```text
apps.view
```

Use case:

```text
GetPluginManifestUseCase
```

---

## 21. `POST /admin/apps/register`

```http
POST /admin/apps/register
```

Finalidade:

```text
Registrar plugin novo ou nova versão de plugin existente.
```

Proteção:

```text
apps.manage
```

Use case:

```text
RegisterPluginUseCase
```

Body:

```text
Manifesto JSON completo
```

Fluxo:

```text
Valida manifesto
Calcula checksum
Cria/atualiza app
Salva manifesto
Cria versão
Cria permissões
Cria rotas
Publica plugin_registered
```

---

## 22. `PUT /admin/apps/<plugin_id>/manifest`

```http
PUT /admin/apps/<plugin_id>/manifest
```

Finalidade:

```text
Atualizar manifesto sem alterar estrutura ou versão.
```

Proteção:

```text
apps.manage
```

Use case:

```text
UpdatePluginManifestUseCase
```

Permitido:

- nome;
- descrição;
- ícone;
- label/icon/order/showInMenu de rotas.

Bloqueado:

- mudar version;
- mudar basePath;
- adicionar/remover permissões;
- adicionar/remover rotas.

Evento:

```text
plugin_manifest_updated
```

---

## 23. `GET /admin/apps/<plugin_id>/versions`

```http
GET /admin/apps/<plugin_id>/versions
```

Finalidade:

```text
Listar versões históricas de um plugin.
```

Proteção esperada:

```text
apps.view
```

Use case:

```text
ListPluginVersionsUseCase
```

---

## 24. `POST /admin/apps/<plugin_id>/rollback`

```http
POST /admin/apps/<plugin_id>/rollback
```

Finalidade:

```text
Restaurar plugin para uma versão histórica.
```

Proteção:

```text
apps.manage
```

Use case:

```text
RollbackPluginVersionUseCase
```

Body:

```json
{
  "version": "1.0.0"
}
```

Evento:

```text
plugin_version_rolled_back
```

---

## 25. `DELETE /admin/apps/<plugin_id>`

```http
DELETE /admin/apps/<plugin_id>
```

Finalidade:

```text
Remover completamente um plugin.
```

Proteção:

```text
apps.manage
```

Use case:

```text
UnregisterPluginUseCase
```

Fluxo:

```text
Verifica dependentes
Remove versões
Remove rotas
Remove permissões
Remove manifesto
Remove app
```

Evento:

```text
plugin_unregistered
```

---

## 26. `POST /admin/apps/<plugin_id>/active`

```http
POST /admin/apps/<plugin_id>/active
```

Finalidade:

```text
Ativar ou desativar plugin/app.
```

Proteção esperada:

```text
apps.manage
```

Use case:

```text
SetPluginActiveUseCase
ou SetAppActiveUseCase
```

Body conceitual:

```json
{
  "active": true
}
```

Eventos:

```text
plugin_activated
plugin_deactivated
app_activated
app_deactivated
```

---

## 27. `POST /admin/apps/bulk-activate`

```http
POST /admin/apps/bulk-activate
```

Finalidade:

```text
Ativar/desativar múltiplos plugins/apps.
```

Proteção esperada:

```text
apps.manage
```

Use cases possíveis:

```text
BulkSetPluginsActiveUseCase
BulkSetAdminAppsActiveUseCase
```

Body conceitual:

```json
{
  "ids": ["dashboard-lmps"],
  "active": true
}
```

---

## 28. `POST /admin/apps/bulk-unregister`

```http
POST /admin/apps/bulk-unregister
```

Finalidade:

```text
Remover múltiplos plugins.
```

Proteção esperada:

```text
apps.manage
```

Use case:

```text
BulkUnregisterPluginsUseCase
```

Body conceitual:

```json
{
  "ids": ["plugin-a", "plugin-b"]
}
```

---

## 29. Rotas administrativas de app routes

### 29.1 `GET /admin/apps/<app_id>/routes`

```http
GET /admin/apps/<app_id>/routes
```

Finalidade:

```text
Listar rotas de um app.
```

Proteção esperada:

```text
apps.view ou routes.manage
```

Use case:

```text
ListAppRoutesUseCase
```

---

### 29.2 `POST /admin/apps/<app_id>/routes`

```http
POST /admin/apps/<app_id>/routes
```

Finalidade:

```text
Criar rota administrativa para um app.
```

Proteção esperada:

```text
routes.manage
```

Use case:

```text
CreateAppRouteUseCase
```

Evento:

```text
route_created
```

---

### 29.3 `PUT /admin/apps/routes/<route_id>`

```http
PUT /admin/apps/routes/<route_id>
```

Finalidade:

```text
Atualizar rota administrativa.
```

Proteção esperada:

```text
routes.manage
```

Use case:

```text
UpdateRouteUseCase
```

Evento:

```text
route_updated
```

---

### 29.4 `DELETE /admin/apps/routes/<route_id>`

```http
DELETE /admin/apps/routes/<route_id>
```

Finalidade:

```text
Excluir rota administrativa.
```

Proteção esperada:

```text
routes.manage
```

Use case:

```text
DeleteRouteUseCase
```

Evento:

```text
route_deleted
```

---

### 29.5 `POST /admin/apps/routes/bulk-delete`

```http
POST /admin/apps/routes/bulk-delete
```

Finalidade:

```text
Excluir múltiplas rotas.
```

Proteção esperada:

```text
routes.manage
```

Use case:

```text
BulkDeleteRoutesUseCase
```

Evento:

```text
routes_bulk_deleted
```

---

## 30. RBAC Controller

Arquivo:

```text
app/interfaces/http/rbac_controller.py
```

Responsabilidade:

- usuários;
- roles;
- groups;
- permissions;
- vínculos entre entidades;
- superadmin;
- uso de permissões;
- rotas legadas de compatibilidade.

Prefixo principal:

```text
/admin/rbac
```

---

## 31. Roles

### 31.1 `GET /admin/rbac/roles`

```http
GET /admin/rbac/roles
```

Finalidade:

```text
Listar roles paginadas.
```

Proteção esperada:

```text
rbac.manage
```

Use case:

```text
ListRolesUseCase
```

---

### 31.2 `POST /admin/rbac/roles`

```http
POST /admin/rbac/roles
```

Finalidade:

```text
Criar role.
```

Proteção esperada:

```text
rbac.manage + roles.manage
```

Use case:

```text
CreateRoleUseCase
```

Evento:

```text
role_created
```

---

### 31.3 `PUT /admin/rbac/roles/<role_id>`

```http
PUT /admin/rbac/roles/<role_id>
```

Finalidade:

```text
Atualizar role.
```

Proteção esperada:

```text
rbac.manage + roles.manage
```

Use case:

```text
UpdateRoleUseCase
```

Evento:

```text
role_updated
```

---

### 31.4 `DELETE /admin/rbac/roles/<role_id>`

```http
DELETE /admin/rbac/roles/<role_id>
```

Finalidade:

```text
Excluir role.
```

Proteção esperada:

```text
rbac.manage + roles.manage
```

Use case:

```text
DeleteRoleUseCase
```

Observação:

```text
Remove vínculos com permissões, usuários e grupos antes de excluir.
```

---

## 32. Role permissions

### 32.1 `GET /admin/rbac/roles/<role_id>/permissions`

```http
GET /admin/rbac/roles/<role_id>/permissions
```

Finalidade:

```text
Listar permissões de uma role.
```

Use case:

```text
ListRolePermissionsUseCase
```

---

### 32.2 `PUT /admin/rbac/roles/<role_id>/permissions`

```http
PUT /admin/rbac/roles/<role_id>/permissions
```

Finalidade:

```text
Substituir conjunto de permissões da role.
```

Use case:

```text
ReplaceRolePermissionsUseCase
```

Evento:

```text
role_permissions_replaced
```

---

### 32.3 `POST /admin/rbac/roles/<role_id>/permissions`

```http
POST /admin/rbac/roles/<role_id>/permissions
```

Finalidade:

```text
Adicionar permissão a uma role.
```

Use case:

```text
AddPermissionToRoleUseCase
```

Evento:

```text
permission_added_to_role
```

---

### 32.4 `DELETE /admin/rbac/roles/<role_id>/permissions/<permission_id>`

```http
DELETE /admin/rbac/roles/<role_id>/permissions/<permission_id>
```

Finalidade:

```text
Remover permissão de uma role.
```

Use case:

```text
RemovePermissionFromRoleUseCase
```

Evento:

```text
permission_removed_from_role
```

---

## 33. Role users

### 33.1 `GET /admin/rbac/roles/<role_id>/users`

```http
GET /admin/rbac/roles/<role_id>/users
```

Finalidade:

```text
Listar usuários vinculados a uma role.
```

Use case:

```text
ListRoleUsersUseCase
```

---

### 33.2 `POST /admin/rbac/roles/<role_id>/users/<user_id>`

```http
POST /admin/rbac/roles/<role_id>/users/<user_id>
```

Finalidade:

```text
Adicionar role a usuário.
```

Use case:

```text
AddRoleToUserUseCase
```

Evento:

```text
role_added_to_user
```

---

### 33.3 `DELETE /admin/rbac/roles/<role_id>/users/<user_id>`

```http
DELETE /admin/rbac/roles/<role_id>/users/<user_id>
```

Finalidade:

```text
Remover role de usuário.
```

Use case:

```text
RemoveRoleFromUserUseCase
```

Evento:

```text
role_removed_from_user
```

---

## 34. Groups

### 34.1 `GET /admin/rbac/groups`

```http
GET /admin/rbac/groups
```

Finalidade:

```text
Listar grupos paginados.
```

Use case:

```text
ListGroupsUseCase
```

---

### 34.2 `POST /admin/rbac/groups`

```http
POST /admin/rbac/groups
```

Finalidade:

```text
Criar grupo.
```

Use case:

```text
CreateGroupUseCase
```

Observação:

> O arquivo do use case de criação de grupo ainda deve ser confirmado se não estiver entre os analisados.

---

### 34.3 `PUT /admin/rbac/groups/<group_id>`

```http
PUT /admin/rbac/groups/<group_id>
```

Finalidade:

```text
Atualizar grupo.
```

Use case:

```text
UpdateGroupUseCase
```

Observação:

> O arquivo do use case de atualização de grupo ainda deve ser confirmado se não estiver entre os analisados.

---

### 34.4 `DELETE /admin/rbac/groups/<group_id>`

```http
DELETE /admin/rbac/groups/<group_id>
```

Finalidade:

```text
Excluir grupo.
```

Use case:

```text
DeleteGroupUseCase
```

---

## 35. Group roles

### 35.1 `GET /admin/rbac/groups/<group_id>/roles`

```http
GET /admin/rbac/groups/<group_id>/roles
```

Finalidade:

```text
Listar roles de um grupo.
```

Use case:

```text
ListGroupRolesUseCase
```

---

### 35.2 `PUT /admin/rbac/groups/<group_id>/roles`

```http
PUT /admin/rbac/groups/<group_id>/roles
```

Finalidade:

```text
Substituir roles de um grupo.
```

Use case:

```text
ReplaceGroupRolesUseCase
```

Evento:

```text
group_roles_replaced
```

---

### 35.3 `POST /admin/rbac/groups/<group_id>/roles/<role_id>`

```http
POST /admin/rbac/groups/<group_id>/roles/<role_id>
```

Finalidade:

```text
Adicionar role a grupo.
```

Use case:

```text
AddGroupRolesUseCase
```

Evento:

```text
role_added_to_group
```

---

### 35.4 `DELETE /admin/rbac/groups/<group_id>/roles/<role_id>`

```http
DELETE /admin/rbac/groups/<group_id>/roles/<role_id>
```

Finalidade:

```text
Remover role de grupo.
```

Use case:

```text
RemoveGroupRolesUseCase
```

Evento:

```text
role_removed_from_group
```

---

## 36. Group users

### 36.1 `GET /admin/rbac/groups/<group_id>/users`

```http
GET /admin/rbac/groups/<group_id>/users
```

Finalidade:

```text
Listar usuários de um grupo.
```

Use case:

```text
ListGroupUsersUseCase
```

---

### 36.2 `POST /admin/rbac/groups/<group_id>/users/<user_id>`

```http
POST /admin/rbac/groups/<group_id>/users/<user_id>
```

Finalidade:

```text
Adicionar usuário a grupo.
```

Use case:

```text
AddGroupToUserUseCase
```

Evento:

```text
group_added_to_user
```

---

### 36.3 `DELETE /admin/rbac/groups/<group_id>/users/<user_id>`

```http
DELETE /admin/rbac/groups/<group_id>/users/<user_id>
```

Finalidade:

```text
Remover usuário de grupo.
```

Use case:

```text
RemoveGroupFromUserUseCase
```

Evento:

```text
group_removed_from_user
```

---

## 37. Users

### 37.1 `GET /admin/rbac/users`

```http
GET /admin/rbac/users
```

Finalidade:

```text
Listar usuários paginados.
```

Proteção esperada:

```text
rbac.manage + users.view
```

Use case:

```text
ListUsersUseCase
```

---

### 37.2 `PUT /admin/rbac/users/<user_id>`

```http
PUT /admin/rbac/users/<user_id>
```

Finalidade:

```text
Atualizar dados/status/superadmin de usuário conforme implementação do controller.
```

Proteção esperada:

```text
rbac.manage + users.manage
```

Use cases possíveis:

```text
SetUserSuperadminUseCase
ReplaceUserRolesUseCase
ReplaceUserGroupsUseCase
```

---

### 37.3 `DELETE /admin/rbac/users/<user_id>`

```http
DELETE /admin/rbac/users/<user_id>
```

Finalidade:

```text
Excluir usuário.
```

Proteção esperada:

```text
require_superadmin
```

Use case:

```text
DeleteUserUseCase
```

---

## 38. User roles e groups por usuário

Rotas antigas de compatibilidade:

```http
GET    /admin/users/<user_id>/roles
PUT    /admin/users/<user_id>/roles
POST   /admin/users/<user_id>/roles/<role_id>
DELETE /admin/users/<user_id>/roles/<role_id>
GET    /admin/users/<user_id>/groups
PUT    /admin/users/<user_id>/groups
POST   /admin/users/<user_id>/groups/<group_id>
DELETE /admin/users/<user_id>/groups/<group_id>
```

Finalidade:

```text
Compatibilidade com frontend ou rotas administrativas antigas.
```

Use cases relacionados:

```text
ListUserRolesUseCase
ReplaceUserRolesUseCase
AddRoleToUserUseCase
RemoveRoleFromUserUseCase
ListUserGroupsUseCase
ReplaceUserGroupsUseCase
AddGroupToUserUseCase
RemoveGroupFromUserUseCase
```

Ponto de atenção:

> Avaliar padronização futura para manter apenas prefixo `/admin/rbac`.

---

## 39. Permissions

### 39.1 `GET /admin/rbac/permissions`

```http
GET /admin/rbac/permissions
```

Finalidade:

```text
Listar permissões paginadas.
```

Proteção esperada:

```text
rbac.manage
```

Use case:

```text
ListPermissionsUseCase
```

---

### 39.2 `GET /admin/rbac/permissions/<permission_id>/usage`

```http
GET /admin/rbac/permissions/<permission_id>/usage
```

Finalidade:

```text
Listar uso de uma permissão por roles e grupos.
```

Use case:

```text
ListPermissionUsageUseCase
```

Resposta conceitual:

```json
{
  "permission": {},
  "roles": [],
  "groups": []
}
```

---

## 40. Paginação administrativa

Listagens administrativas usam padrão comum:

```text
q
page
page_size
sort
direction
```

Use cases:

```text
ListUsersUseCase
ListRolesUseCase
ListGroupsUseCase
ListPermissionsUseCase
ListAdminAppsUseCase
```

Resposta:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## 41. Eventos por controller

Controllers administrativos geralmente executam use cases que coletam `AdminChangedEvent`.

Fluxo:

```text
Controller
  ↓
Use case
  ↓
Unit of Work coleta evento
  ↓
Commit
  ↓
EventBus
  ↓
Socket.IO admin.changed
```

Eventos podem ser globais ou direcionados ao usuário.

---

## 42. Pontos de atenção

1. Confirmar rotas exatas diretamente no controller sempre que houver divergência.
2. Algumas rotas antigas existem para compatibilidade.
3. Alguns use cases citados podem ainda precisar confirmação de arquivo real.
4. O middleware não bloqueia endpoint sem decorator.
5. Endpoints administrativos devem usar permissões específicas.
6. Operações de plugin podem impactar menu em tempo real.
7. Operações RBAC podem mudar apps visíveis durante a sessão.
8. Respostas de erro devem seguir `{ errors: [...] }`.
9. Bulk use cases podem ter controle transacional próprio; revisar consistência.
10. Controllers devem permanecer finos e delegar regra a use cases.

---

## 43. Documentos relacionados

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/use-cases.md
docs/04-core-api/unit-of-work.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/registro-de-plugin.md
docs/06-portal-frontend/menu-dinamico.md
```

