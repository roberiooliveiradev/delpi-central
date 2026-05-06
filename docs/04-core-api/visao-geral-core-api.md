# Minha DELPI — Visão Geral da Core API

> **Arquivo:** `docs/04-core-api/visao-geral-core-api.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** visão técnica da Core API

---

## 1. Objetivo

Este documento descreve a **Core API** da Minha DELPI, explicando seu papel na arquitetura, suas responsabilidades, organização interna, principais fluxos, modelos, endpoints e integrações.

A Core API é o núcleo de governança da plataforma. Ela não é a API operacional de negócio; essa responsabilidade pertence à API DELPI.

---

## 2. Papel da Core API

A Core API é responsável pela governança central da Minha DELPI.

Responsabilidades principais:

- validar tokens JWT emitidos pelo Keycloak;
- sincronizar usuários autenticados no banco local;
- manter usuários, roles, groups e permissions;
- resolver permissões efetivas;
- proteger endpoints administrativos;
- gerenciar apps cadastrados na plataforma;
- gerenciar rotas de apps;
- registrar plugins por manifesto;
- validar manifestos;
- versionar plugins;
- executar rollback de plugins;
- ativar/desativar apps e plugins;
- gerenciar favoritos de usuário;
- gerenciar notificações;
- emitir eventos administrativos via Socket.IO;
- manter auditoria.

Regra de separação:

```text
Core API  → governança da plataforma
API DELPI → dados e regras operacionais de negócio
```

---

## 3. Stack técnica

A Core API usa:

```text
Python
Flask
Flask-SQLAlchemy
Flask-Migrate
Alembic
PostgreSQL
Socket.IO
Eventlet
Keycloak JWT validation
```

Serviço Docker:

```text
core-api
```

Container:

```text
delpi-core-api
```

Banco:

```text
postgres-core
```

---

## 4. Estrutura geral

Estrutura conceitual:

```text
core-api/
  app/
    application/
      services/
      use_cases/
      validators/
      event_handlers/
      event_bus.py
      unit_of_work.py

    domain/
      dto/
      events/
      plugins/
      ports/
      services/

    infrastructure/
      cache/
      config/
      db/
      persistence/
      plugins/
      security/
      seeds/
      socket/

    interfaces/
      http/
      socket/

    extensions/
      db.py
      migrate.py
      socket.py

    create_app.py
    main.py
```

---

## 5. Camadas internas

| Camada | Responsabilidade |
|---|---|
| `interfaces` | Controllers HTTP, middlewares e socket handlers |
| `application` | Use cases, validators, event bus e serviços de aplicação |
| `domain` | Ports, eventos, serviços de domínio, regras e DTOs |
| `infrastructure` | SQLAlchemy, cache, socket, schemas, seeds e detalhes técnicos |
| `extensions` | Instâncias Flask compartilhadas: db, migrate e socket |

---

## 6. Bootstrap da aplicação

A aplicação é criada por:

```text
app/create_app.py
```

Fluxo de inicialização:

```text
create_app(config_name)
  ↓
Cria Flask app
  ↓
Carrega Config ou TestingConfig
  ↓
Inicializa db
  ↓
Inicializa migrate
  ↓
Inicializa socketio
  ↓
Registra middleware global de autenticação
  ↓
Registra blueprints
  ↓
Executa seed de permissões base
  ↓
Retorna app
```

O entrypoint principal é:

```text
app/main.py
```

Ele cria o app e executa via Socket.IO:

```python
socketio.run(
    app,
    host="0.0.0.0",
    port=8000,
    debug=False,
    use_reloader=False,
)
```

---

## 7. Configuração

Arquivo principal:

```text
app/infrastructure/config/settings.py
```

A configuração carrega variáveis de ambiente usando `dotenv`.

Variáveis de banco da Core API:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

URI montada:

```python
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
```

Configuração de teste:

```text
postgresql://delpi:delpi123@postgres-core-test:5432/delpi_core_test
```

---

## 8. Extensões Flask

A Core API centraliza extensões em `app/extensions`.

### 8.1 SQLAlchemy

Arquivo:

```text
app/extensions/db.py
```

Conteúdo:

```python
db = SQLAlchemy()
```

---

### 8.2 Flask-Migrate

Arquivo:

```text
app/extensions/migrate.py
```

Conteúdo:

```python
migrate = Migrate()
```

---

### 8.3 Socket.IO

Arquivo:

```text
app/extensions/socket.py
```

Configuração:

```python
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=False,
    engineio_logger=False,
)
```

---

## 9. Blueprints registrados

A aplicação registra os seguintes blueprints:

| Blueprint | Arquivo | Responsabilidade |
|---|---|---|
| `health_bp` | `health_controller.py` | Healthcheck |
| `rbac_bp` | `rbac_controller.py` | Administração RBAC |
| `admin_apps_bp` | `apps_controller.py` | Administração de apps/plugins/rotas |
| `me_bp` | `me_controller.py` | Usuário atual, apps, favoritos, notificações e dashboard |

---

## 10. Middleware de autenticação

Arquivo:

```text
app/interfaces/http/auth_middleware.py
```

O middleware é registrado globalmente em `before_request`.

Fluxo:

```text
Requisição chega
  ↓
Se TESTING, ignora autenticação
  ↓
Lê Authorization header
  ↓
Se não houver Bearer token, retorna None
  ↓
Valida JWT
  ↓
Extrai sub, email e name
  ↓
Valida sub como UUID
  ↓
Busca usuário por email
  ↓
Cria usuário se não existir
  ↓
Atualiza last_login_at
  ↓
Busca roles, groups e permissions
  ↓
Define g.current_user
```

Observação importante:

> A ausência de token não bloqueia automaticamente a requisição. Endpoints protegidos devem usar decorators como `@require_auth()`, `@require_permission()` ou `@require_superadmin()`.

---

## 11. Controllers HTTP

### 11.1 Health

Arquivo:

```text
app/interfaces/http/health_controller.py
```

Endpoint:

```http
GET /health
```

Resposta:

```json
{
  "status": "Api rodando!"
}
```

---

### 11.2 Me

Arquivo:

```text
app/interfaces/http/me_controller.py
```

Responsabilidades:

- dados do usuário atual;
- apps disponíveis;
- favoritos;
- notificações;
- dashboard básico.

Endpoints principais:

```http
GET    /me
GET    /me/apps
GET    /me/apps/favorites
POST   /me/apps/favorites/<app_id>
DELETE /me/apps/favorites/<app_id>
GET    /me/notifications
POST   /me/notifications/<notification_id>/read
POST   /me/notifications/read-all
POST   /me/notifications/test
GET    /me/dashboard
```

---

### 11.3 Apps e plugins

Arquivo:

```text
app/interfaces/http/apps_controller.py
```

Prefixo:

```text
/admin/apps
```

Responsabilidades:

- listar apps/plugins;
- atualizar metadata;
- obter manifesto;
- registrar plugin;
- atualizar manifesto;
- listar versões;
- rollback;
- unregister;
- ativar/desativar plugin;
- operações em lote;
- gerenciar rotas de apps.

---

### 11.4 RBAC

Arquivo:

```text
app/interfaces/http/rbac_controller.py
```

Responsabilidades:

- roles;
- groups;
- permissions;
- usuários;
- vínculos usuário-role;
- vínculos usuário-grupo;
- vínculos grupo-role;
- vínculos role-permission;
- uso de permissões;
- superadmin.

---

## 12. Padrão de resposta de erro

Arquivo:

```text
app/interfaces/http/utils/errors.py
```

Formato padrão:

```json
{
  "errors": [
    {
      "code": "validation_error",
      "message": "Campo obrigatório.",
      "path": "name"
    }
  ]
}
```

Helpers disponíveis:

```text
api_error
error_response
unauthorized
forbidden
not_found
bad_request
unprocessable
conflict
server_error
```

---

## 13. Banco de dados da Core API

A Core API usa o banco:

```text
postgres-core
```

Modelos registrados:

```text
User
Group
Role
Permission
user_roles
role_permissions
user_groups
group_roles
UserPermission
UserFavoriteApp
App
AppRoute
AppManifest
AppVersion
Notification
AuditLog
```

Tabelas principais:

```text
users
groups
roles
permissions
user_roles
user_groups
group_roles
role_permissions
user_permissions
apps
app_routes
app_manifests
app_versions
user_favorite_apps
notifications
audit_logs
```

---

## 14. Modelos de plataforma

### 14.1 User

Tabela:

```text
users
```

Campos principais:

```text
id
name
email
active
is_superadmin
last_login_at
created_at
updated_at
```

---

### 14.2 RBAC

Tabelas:

```text
roles
groups
permissions
user_roles
user_groups
group_roles
role_permissions
user_permissions
```

Essas tabelas sustentam o cálculo de permissões efetivas.

---

### 14.3 Apps e plugins

Tabelas:

```text
apps
app_routes
app_manifests
app_versions
```

Responsabilidades:

- `apps`: cadastro principal do app/plugin;
- `app_routes`: rotas navegáveis vinculadas ao app;
- `app_manifests`: manifesto vigente;
- `app_versions`: histórico versionado de manifestos.

---

### 14.4 Favoritos

Tabela:

```text
user_favorite_apps
```

Chave composta:

```text
user_id + app_id
```

---

### 14.5 Notificações

Tabela:

```text
notifications
```

Campos principais:

```text
id
user_id
title
message
type
read_at
created_at
```

---

### 14.6 Auditoria

Tabela:

```text
audit_logs
```

Campos principais:

```text
id
user_id
action
entity_type
entity_id
payload
ip_address
created_at
updated_at
```

---

## 15. Migrations

A Core API usa Flask-Migrate/Alembic.

Arquivos principais:

```text
app/extensions/migrate.py
migrations/env.py
migrations/versions/<revision>.py
```

A migration inicial cria a estrutura principal:

```text
apps
groups
notifications
permissions
roles
users
app_manifests
app_routes
app_versions
audit_logs
group_roles
role_permissions
user_favorite_apps
user_groups
user_permissions
user_roles
```

O `env.py` do Alembic usa o engine da aplicação Flask e evita gerar revisão vazia em autogenerate quando não há mudanças.

---

## 16. Unit of Work

A Core API usa Unit of Work para agrupar repositories, controlar transação e publicar eventos após commit.

Arquivos:

```text
app/application/unit_of_work.py
app/infrastructure/persistence/sqlalchemy/unit_of_work.py
```

Responsabilidades:

- disponibilizar repositories;
- controlar commit;
- controlar rollback;
- coletar eventos de domínio;
- publicar eventos após commit;
- fornecer aliases de compatibilidade.

Fluxo esperado:

```python
with SqlAlchemyUnitOfWork() as uow:
    uc = SomeUseCase(uow)
    result = uc.execute(...)
```

Ao sair do contexto sem erro:

```text
commit
  ↓
EventBus.publish(events)
```

---

## 17. Repositories

A infraestrutura implementa repositories SQLAlchemy para os ports do domínio.

Exemplos:

```text
SqlAlchemyUserRepository
SqlAlchemyRoleRepository
SqlAlchemyGroupRepository
SqlAlchemyPermissionRepository
SqlAlchemyRbacQueryRepository
SqlAlchemyAppQueryRepository
SqlAlchemyAdminAppRepository
SqlAlchemyAdminRouteRepository
SqlAlchemyPluginRepository
SqlAlchemyPluginManifestRepository
SqlAlchemyPluginVersionRepository
SqlAlchemyPluginRouteRepository
SqlAlchemyPluginPermissionRepository
SqlAlchemyFavoriteAppRepository
SqlAlchemyNotificationRepository
SqlAlchemyAuditRepository
```

Regra arquitetural:

> Use cases dependem de ports e Unit of Work. Repositories concretos pertencem à infraestrutura.

---

## 18. Use cases

Os use cases implementam as ações da aplicação.

Grupos principais:

### 18.1 Usuário atual

```text
GetMeUseCase
ListUserAppsUseCase
ListFavoriteAppsUseCase
AddFavoriteAppUseCase
RemoveFavoriteAppUseCase
ListUnreadNotificationsUseCase
MarkNotificationReadUseCase
MarkAllNotificationsReadUseCase
NotifyUserUseCase
```

---

### 18.2 RBAC

```text
CreateRoleUseCase
UpdateRoleUseCase
DeleteRoleUseCase
ListRolesUseCase
ListGroupsUseCase
ListUsersUseCase
ListPermissionsUseCase
SetUserSuperadminUseCase
AddRoleToUserUseCase
RemoveRoleFromUserUseCase
ReplaceUserRolesUseCase
AddGroupToUserUseCase
RemoveGroupFromUserUseCase
ReplaceUserGroupsUseCase
AddRoleToGroupUseCase
RemoveRoleFromGroupUseCase
ReplaceGroupRolesUseCase
AddPermissionToRoleUseCase
RemovePermissionFromRoleUseCase
ReplaceRolePermissionsUseCase
ListPermissionUsageUseCase
```

---

### 18.3 Apps, rotas e plugins

```text
ListAdminAppsUseCase
UpdateAdminAppUseCase
DeleteAdminAppUseCase
CreateAppRouteUseCase
UpdateRouteUseCase
DeleteRouteUseCase
BulkDeleteRoutesUseCase
RegisterPluginUseCase
UpdatePluginManifestUseCase
RollbackPluginVersionUseCase
UnregisterPluginUseCase
SetPluginActiveUseCase
BulkSetPluginsActiveUseCase
BulkUnregisterPluginsUseCase
GetPluginManifestUseCase
ListPluginVersionsUseCase
```

---

## 19. RBAC na Core API

A Core API resolve permissões efetivas por meio do `PermissionResolver`.

Fontes de permissões:

```text
roles diretas do usuário
roles herdadas por grupos
overrides individuais
superadmin
```

Fluxo:

```text
PermissionResolver.resolve(user_id, is_superadmin)
  ↓
Se superadmin, lista todas as permissões
  ↓
Se usuário comum, tenta cache
  ↓
Busca permissões diretas
  ↓
Busca permissões por grupos
  ↓
Aplica overrides
  ↓
Salva no cache
```

---

## 20. Autorização HTTP

Decorators principais:

```text
require_auth
require_superadmin
require_permission
require_any_permission
require_all_permissions
```

Exemplos:

```python
@require_auth()
@require_permission("apps.view")
@require_all_permissions(["rbac.manage", "users.manage"])
@require_superadmin()
```

Além disso, existe `PolicyEngine` para regras contextuais.

---

## 21. Apps autorizados para o Portal

O endpoint `/me/apps` usa `ListUserAppsUseCase`.

Fluxo:

```text
AppQueryRepository lista apps ativos com rotas
  ↓
AppAuthorizationService filtra rotas por permissão
  ↓
Apps sem rota autorizada são removidos
  ↓
Core API retorna payload para o Portal
```

Formato conceitual:

```json
[
  {
    "id": "dashboard-lmps",
    "name": "Dashboard LMPs",
    "basePath": "/apps/dashboard-lmps",
    "icon": "bar-chart3-icon",
    "type": "microfrontend",
    "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
    "renderMode": "federated",
    "routes": [
      {
        "app": "dashboard-lmps",
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

## 22. Plugin System na Core API

A Core API possui um sistema de plugins baseado em manifesto JSON.

Principais responsabilidades:

- validar manifesto;
- normalizar manifesto;
- resolver versão do schema;
- aplicar JSON Schema;
- aplicar strategy por tipo;
- aplicar regras de domínio;
- calcular checksum;
- criar ou atualizar app;
- salvar manifesto vigente;
- criar versão histórica;
- criar permissões;
- criar rotas;
- publicar eventos.

Tipos suportados:

```text
microfrontend
iframe
backend-only
```

Schema suportado:

```text
1.0.0
```

---

## 23. Registro de plugin

Endpoint:

```http
POST /admin/apps/register
```

Proteção:

```text
apps.manage
```

Fluxo:

```text
Recebe manifesto
  ↓
Valida manifesto
  ↓
Calcula checksum
  ↓
Se plugin não existe:
    cria app
    salva manifesto
    cria versão
    cria permissões
    cria rotas
  ↓
Se plugin existe:
    bloqueia versão duplicada
    atualiza versão ativa
    salva manifesto
    cria nova versão
    remove permissões/rotas antigas
    recria permissões/rotas
  ↓
Publica plugin_registered
```

---

## 24. Atualização de manifesto

Endpoint:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Proteção:

```text
apps.manage
```

Regra central:

> Atualização de manifesto não pode alterar estrutura do plugin.

Permitido:

- alterar `name`;
- alterar `description`;
- alterar `icon`;
- alterar `label` de rotas;
- alterar `icon` de rotas;
- alterar `order` de rotas;
- alterar `showInMenu` de rotas.

Bloqueado:

- alterar `id`;
- alterar `version`;
- alterar `basePath`;
- adicionar/remover permissões;
- adicionar/remover rotas.

Mudanças estruturais exigem novo registro de versão.

---

## 25. Rollback de plugin

Endpoint:

```http
POST /admin/apps/<plugin_id>/rollback
```

Proteção:

```text
apps.manage
```

Fluxo:

```text
Recebe version alvo
  ↓
Busca plugin
  ↓
Busca versão no histórico
  ↓
Restaura manifesto e checksum
  ↓
Atualiza versão ativa
  ↓
Remove rotas e permissões atuais
  ↓
Recria permissões e rotas do manifesto restaurado
  ↓
Publica plugin_version_rolled_back
```

---

## 26. Unregister de plugin

Endpoint:

```http
DELETE /admin/apps/<plugin_id>
```

Proteção:

```text
apps.manage
```

Fluxo:

```text
Verifica existência
  ↓
Verifica se outros plugins dependem dele
  ↓
Se houver dependentes, bloqueia
  ↓
Remove versões
  ↓
Remove rotas
  ↓
Remove permissões por módulo
  ↓
Remove manifesto
  ↓
Remove app
  ↓
Publica plugin_unregistered
```

---

## 27. Notificações

A Core API possui suporte a notificações por usuário.

Endpoints principais:

```http
GET  /me/notifications
POST /me/notifications/<notification_id>/read
POST /me/notifications/read-all
POST /me/notifications/test
```

Tabela:

```text
notifications
```

Eventos:

```text
UserNotifiedEvent
NotificationMarkedReadEvent
AllNotificationsMarkedReadEvent
```

Ponto de atenção:

> O use case `MarkNotificationReadUseCase` chama `notifications.get(notification_id)`. É necessário garantir que o repository concreto implemente esse método ou ajustar o use case.

---

## 28. Eventos administrativos

Evento principal:

```python
AdminChangedEvent(
    entity="...",
    action="...",
    payload={...},
    target_user_id=None,
)
```

Fluxo:

```text
Use case coleta evento
  ↓
Unit of Work commita
  ↓
EventBus publica
  ↓
RbacEventHandler executa efeitos de domínio
  ↓
SocketIOEventDispatcher emite evento
```

Eventos podem ser:

- globais;
- direcionados a um usuário.

---

## 29. Socket.IO

Socket handlers ficam em:

```text
app/interfaces/socket/socket_handlers.py
```

Conexão:

```text
socket connect
  ↓
recebe auth.token ou query token
  ↓
valida JWT
  ↓
extrai sub
  ↓
join_room(sub)
```

Dispatcher:

```text
app/infrastructure/socket/socket_event_dispatcher.py
```

Eventos `AdminChangedEvent` são emitidos como:

```text
admin.changed
```

Se houver `target_user_id`, o evento vai para a sala daquele usuário.

Se não houver, é broadcast.

---

## 30. Auditoria

A Core API possui model e repository de auditoria.

Tabela:

```text
audit_logs
```

Campos:

```text
user_id
action
entity_type
entity_id
payload
ip_address
created_at
updated_at
```

Repository:

```text
SqlAlchemyAuditRepository
```

Método principal:

```text
log(data)
```

---

## 31. Endpoints principais

### 31.1 Health

```http
GET /health
```

---

### 31.2 Usuário atual

```http
GET    /me
GET    /me/apps
GET    /me/apps/favorites
POST   /me/apps/favorites/<app_id>
DELETE /me/apps/favorites/<app_id>
GET    /me/notifications
POST   /me/notifications/<notification_id>/read
POST   /me/notifications/read-all
POST   /me/notifications/test
GET    /me/dashboard
```

---

### 31.3 Apps, plugins e rotas

```http
GET    /admin/apps
PUT    /admin/apps/<plugin_id>
GET    /admin/apps/<plugin_id>/manifest
POST   /admin/apps/register
PUT    /admin/apps/<plugin_id>/manifest
GET    /admin/apps/<plugin_id>/versions
POST   /admin/apps/<plugin_id>/rollback
DELETE /admin/apps/<plugin_id>
POST   /admin/apps/<plugin_id>/active
POST   /admin/apps/bulk-activate
POST   /admin/apps/bulk-unregister
GET    /admin/apps/<app_id>/routes
POST   /admin/apps/<app_id>/routes
PUT    /admin/apps/routes/<route_id>
DELETE /admin/apps/routes/<route_id>
POST   /admin/apps/routes/bulk-delete
```

---

### 31.4 RBAC

```http
POST   /admin/rbac/roles
GET    /admin/rbac/roles
PUT    /admin/rbac/roles/<role_id>
DELETE /admin/rbac/roles/<role_id>
POST   /admin/rbac/roles/bulk-delete
GET    /admin/rbac/roles/<role_id>/permissions
PUT    /admin/rbac/roles/<role_id>/permissions
POST   /admin/rbac/roles/<role_id>/permissions
DELETE /admin/rbac/roles/<role_id>/permissions/<permission_id>
GET    /admin/rbac/roles/<role_id>/users
POST   /admin/rbac/roles/<role_id>/users/<user_id>
DELETE /admin/rbac/roles/<role_id>/users/<user_id>
GET    /admin/rbac/groups
POST   /admin/rbac/groups
PUT    /admin/rbac/groups/<group_id>
DELETE /admin/rbac/groups/<group_id>
POST   /admin/rbac/groups/bulk-delete
GET    /admin/rbac/groups/<group_id>/roles
PUT    /admin/rbac/groups/<group_id>/roles
POST   /admin/rbac/groups/<group_id>/roles/<role_id>
DELETE /admin/rbac/groups/<group_id>/roles/<role_id>
GET    /admin/rbac/groups/<group_id>/users
POST   /admin/rbac/groups/<group_id>/users/<user_id>
DELETE /admin/rbac/groups/<group_id>/users/<user_id>
GET    /admin/rbac/users
PUT    /admin/rbac/users/<user_id>
DELETE /admin/rbac/users/<user_id>
POST   /admin/rbac/users/bulk-delete
GET    /admin/rbac/permissions
GET    /admin/rbac/permissions/<permission_id>/usage
```

---

### 31.5 Rotas antigas de compatibilidade

O controller RBAC mantém rotas antigas usadas pelo frontend:

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

Essas rotas devem ser documentadas como compatibilidade e avaliadas futuramente para padronização.

---

## 32. Pontos de atenção técnicos

1. O middleware não bloqueia automaticamente endpoints sem token; controllers devem usar decorators.
2. Algumas rotas antigas de compatibilidade ainda existem.
3. Alguns use cases fazem commit/rollback interno, divergindo do padrão principal do Unit of Work.
4. O cache RBAC é em memória e não distribuído.
5. `MarkNotificationReadUseCase` depende de método `get` no repository de notificações.
6. Alguns ports podem estar incompletos em relação às implementações concretas.
7. O termo DELPI Central ainda pode aparecer em variáveis, docs ou clients antigos.
8. O schema de manifesto aceita pré-release, mas a regra de domínio SemVer é mais restritiva.
9. A Core API não deve receber responsabilidades operacionais que pertencem à API DELPI.
10. O uso de `from app.infrastructure.db.models import *` em bootstrap existe para garantir registro dos models, mas deve ser tratado com cuidado em refatorações.

---

## 33. Documentos relacionados

```text
docs/04-core-api/bootstrap-da-aplicacao.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/use-cases.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/repositories.md
docs/04-core-api/modelos-de-banco.md
docs/04-core-api/migrations.md
docs/04-core-api/erros-api.md
docs/04-core-api/notificacoes.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/manifesto-plugin.md
```

