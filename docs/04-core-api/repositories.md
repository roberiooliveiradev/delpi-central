# Minha DELPI — Core API: Repositories

> **Arquivo:** `docs/04-core-api/repositories.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** repositories, ports, persistência SQLAlchemy e consultas da Core API

---

## 1. Objetivo

Este documento descreve os **repositories** da Core API da Minha DELPI.

Repositories são responsáveis por encapsular acesso a dados e detalhes de persistência, permitindo que use cases trabalhem por meio de ports e Unit of Work sem depender diretamente de SQLAlchemy ou do banco.

---

## 2. Papel dos repositories

Repositories implementam operações de leitura e escrita em entidades do domínio.

Responsabilidades:

- consultar modelos SQLAlchemy;
- criar registros;
- atualizar registros;
- remover registros;
- resolver relacionamentos;
- aplicar filtros de paginação;
- expor consultas especializadas;
- esconder detalhes de banco da camada de aplicação.

Regra arquitetural:

> Use cases devem acessar dados por repositories expostos pelo Unit of Work, não diretamente por `db.session` ou models SQLAlchemy.

---

## 3. Ports e implementações

A Core API usa uma separação inspirada em Clean Architecture.

```text
domain/ports       → contratos
infrastructure     → implementações concretas
application        → usa ports via Unit of Work
```

Fluxo:

```text
Use case
  ↓
Unit of Work
  ↓
Repository port
  ↓
SQLAlchemy repository
  ↓
Models
  ↓
PostgreSQL
```

---

## 4. Localização conceitual

Ports ficam no domínio:

```text
app/domain/ports/
```

Implementações SQLAlchemy ficam na infraestrutura:

```text
app/infrastructure/persistence/sqlalchemy/
```

| Implementação | Domínio |
|---|---|
| `user_repository` | Usuários |
| `role_repository`, `group_repository` | RBAC entidades |
| `user_role_repository`, `user_group_repository`, `group_role_repository` | Vínculos |
| `role_permission_repository`, `permission_repository` | Permissões |
| `permission_query_repository`, `rbac_query_repository` | `PermissionResolver` |
| `plugin_*_repository` | Apps, manifestos, versões, rotas, permissões |
| `admin_app_repository`, `admin_route_repository` | Admin |
| `app_query_repository` | `/me/apps` |
| `favorite_app_repository`, `notification_repository`, `audit_repository` | Favoritos, notificações, auditoria |

Models ficam em:

```text
app/infrastructure/db/models/
```

---

## 5. Repositories expostos pelo Unit of Work

Repositories conhecidos expostos pelo Unit of Work:

```text
users
roles
groups
permissions
user_roles
user_groups
group_roles
role_permissions
rbac_query
admin_apps
admin_routes
app_query
plugins
plugin_manifests
plugin_permissions
plugin_routes
plugin_versions
favorites
notifications
audit
```

Também podem existir aliases de compatibilidade para nomes antigos ou transições de arquitetura.

---

## 6. Grupos de repositories

Os repositories podem ser agrupados por domínio.

| Domínio | Repositories |
|---|---|
| Usuários/RBAC | `users`, `roles`, `groups`, `permissions`, `user_roles`, `user_groups`, `group_roles`, `role_permissions`, `rbac_query` |
| Apps administrativos | `admin_apps`, `admin_routes` |
| Apps para Portal | `app_query` |
| Plugin System | `plugins`, `plugin_manifests`, `plugin_permissions`, `plugin_routes`, `plugin_versions` |
| Favoritos | `favorites` |
| Notificações | `notifications` |
| Auditoria | `audit` |

---

## 7. Repository `users`

Responsável por usuários locais da plataforma.

Tabela principal:

```text
users
```

Operações esperadas:

- buscar usuário por ID;
- buscar usuário por email;
- criar usuário;
- atualizar dados do usuário;
- atualizar `last_login_at`;
- listar usuários com paginação;
- alterar status ativo;
- alterar flag `is_superadmin`;
- contar superadmins;
- excluir usuário.

Uso principal:

- middleware de autenticação;
- listagens administrativas;
- RBAC;
- superadmin;
- sincronização local a partir do JWT.

---

## 8. Repository `roles`

Responsável por roles.

Tabela principal:

```text
roles
```

Operações esperadas:

- criar role;
- buscar role;
- buscar por nome;
- atualizar role;
- excluir role;
- listar roles com paginação;
- verificar duplicidade;
- listar roles por usuário;
- listar roles por grupo.

Use cases relacionados:

```text
CreateRoleUseCase
UpdateRoleUseCase
DeleteRoleUseCase
ListRolesUseCase
ListUserRolesUseCase
ListGroupRolesUseCase
```

---

## 9. Repository `groups`

Responsável por grupos.

Tabela principal:

```text
groups
```

Operações esperadas:

- criar grupo;
- buscar grupo;
- buscar por nome;
- atualizar grupo;
- excluir grupo;
- listar grupos com paginação;
- listar grupos do usuário;
- listar usuários de um grupo.

Use cases relacionados:

```text
ListGroupsUseCase
DeleteGroupUseCase
ListUserGroupsUseCase
ListGroupUsersUseCase
```

Ponto de atenção:

> Use cases de criação/atualização de grupo devem ser confirmados nos arquivos reais caso ainda não tenham sido analisados.

---

## 10. Repository `permissions`

Responsável por permissões.

Tabela principal:

```text
permissions
```

Operações esperadas:

- buscar permissão por ID;
- buscar permissão por code;
- criar permissão;
- listar permissões;
- listar permissões com paginação;
- listar permissões por module;
- remover permissões por module;
- listar todas as permissões para superadmin;
- consultar uso de permissão.

Uso principal:

- RBAC;
- seed de permissões base;
- registro de plugins;
- rollback;
- unregister.

---

## 11. Repositories associativos de RBAC

Repositories:

```text
user_roles
user_groups
group_roles
role_permissions
```

Responsabilidades:

- criar vínculos;
- remover vínculos;
- substituir conjuntos;
- verificar existência;
- limpar vínculos antes de delete;
- listar IDs relacionados.

Tabelas:

```text
user_roles
user_groups
group_roles
role_permissions
```

Use cases relacionados:

```text
AddRoleToUserUseCase
RemoveRoleFromUserUseCase
ReplaceUserRolesUseCase
AddGroupToUserUseCase
RemoveGroupFromUserUseCase
ReplaceUserGroupsUseCase
AddGroupRolesUseCase
RemoveGroupRolesUseCase
ReplaceGroupRolesUseCase
AddPermissionToRoleUseCase
RemovePermissionFromRoleUseCase
ReplaceRolePermissionsUseCase
```

---

## 12. Repository `rbac_query`

Repository especializado para consultas agregadas de RBAC.

Responsabilidades esperadas:

- consultar roles de usuário;
- consultar grupos de usuário;
- consultar permissões efetivas por relações;
- consultar usuários impactados por mudança de role;
- consultar usuários impactados por mudança de grupo;
- apoiar `RbacEventHandler`;
- apoiar `PermissionResolver` por meio de `PermissionQueryPort`.

Uso:

```text
PermissionResolver
RbacEventHandler
ListPermissionUsageUseCase
```

---

## 13. Repository `admin_apps`

Responsável por operações administrativas de apps.

Tabela principal:

```text
apps
```

Operações esperadas:

- listar apps paginados;
- buscar app por ID;
- atualizar metadata;
- ativar/desativar app;
- excluir app;
- operações em lote.

Use cases relacionados:

```text
ListAdminAppsUseCase
UpdateAdminAppUseCase
DeleteAdminAppUseCase
SetAppActiveUseCase
BulkSetAdminAppsActiveUseCase
BulkDeleteAdminAppsUseCase
```

---

## 14. Repository `admin_routes`

Responsável por rotas administrativas de apps.

Tabela principal:

```text
app_routes
```

Operações esperadas:

- listar rotas por app;
- criar rota;
- atualizar rota;
- excluir rota;
- excluir múltiplas rotas;
- resolver permission code para permission_id;
- ativar/desativar rota.

Use cases relacionados:

```text
ListAppRoutesUseCase
CreateAppRouteUseCase
UpdateRouteUseCase
DeleteRouteUseCase
BulkDeleteRoutesUseCase
```

---

## 15. Repository `app_query`

Repository especializado para consulta de apps disponíveis ao Portal.

Responsabilidade:

```text
Listar apps ativos com rotas para posterior filtragem por autorização.
```

Usado por:

```text
ListUserAppsUseCase
ListFavoriteAppsUseCase
AddFavoriteAppUseCase
```

Fluxo:

```text
app_query lista apps ativos com rotas
  ↓
AppAuthorizationService filtra por permissions/is_superadmin
  ↓
Portal recebe DTO autorizado
```

Este repository deve retornar dados suficientes para montar:

- id;
- name;
- basePath;
- icon;
- type;
- entryUrl;
- renderMode;
- routes.

---

## 16. Repository `plugins`

Responsável pelo registro principal de plugins na tabela `apps`.

Tabela principal:

```text
apps
```

Operações esperadas:

- buscar plugin/app por ID;
- criar plugin;
- atualizar versão ativa;
- atualizar metadata;
- ativar/desativar;
- remover app;
- validar existência.

Use cases relacionados:

```text
RegisterPluginUseCase
RollbackPluginVersionUseCase
UnregisterPluginUseCase
SetPluginActiveUseCase
BulkUnregisterPluginsUseCase
```

---

## 17. Repository `plugin_manifests`

Responsável pelo manifesto vigente.

Tabela principal:

```text
app_manifests
```

Operações esperadas:

- buscar manifesto por app_id;
- salvar manifesto vigente;
- atualizar checksum;
- remover manifesto;
- listar manifestos para checar dependências.

Uso:

```text
GetPluginManifestUseCase
RegisterPluginUseCase
UpdatePluginManifestUseCase
RollbackPluginVersionUseCase
UnregisterPluginUseCase
```

---

## 18. Repository `plugin_versions`

Responsável pelo histórico de versões.

Tabela principal:

```text
app_versions
```

Operações esperadas:

- criar versão;
- verificar versão duplicada;
- buscar versão específica;
- listar versões por app;
- remover versões por app;
- retornar manifesto/checksum histórico.

Uso:

```text
RegisterPluginUseCase
ListPluginVersionsUseCase
RollbackPluginVersionUseCase
UnregisterPluginUseCase
```

---

## 19. Repository `plugin_permissions`

Responsável por permissões declaradas por plugins.

Tabela principal:

```text
permissions
```

Operações esperadas:

- criar permissões do manifesto;
- remover permissões por module;
- listar permissões por module;
- buscar permissão por code;
- validar conjunto de permissões na atualização de manifesto.

Regra crítica:

```text
permissions.module = plugin_id
```

Uso:

```text
RegisterPluginUseCase
UpdatePluginManifestUseCase
RollbackPluginVersionUseCase
UnregisterPluginUseCase
BulkUnregisterPluginsUseCase
```

---

## 20. Repository `plugin_routes`

Responsável por rotas declaradas por plugins.

Tabela principal:

```text
app_routes
```

Operações esperadas:

- criar rotas do manifesto;
- remover rotas por app_id;
- listar rotas por app_id;
- atualizar campos não estruturais;
- validar conjunto de paths na atualização de manifesto.

Campos não estruturais atualizáveis:

```text
label
icon
order
show_in_menu
```

Uso:

```text
RegisterPluginUseCase
UpdatePluginManifestUseCase
RollbackPluginVersionUseCase
UnregisterPluginUseCase
BulkUnregisterPluginsUseCase
```

---

## 21. Repository `favorites`

Responsável por favoritos de apps por usuário.

Tabela principal:

```text
user_favorite_apps
```

Operações esperadas:

- listar favoritos por usuário;
- verificar se favorito existe;
- adicionar favorito;
- remover favorito;
- preservar `order_index`;
- filtrar favoritos conforme apps autorizados em conjunto com outros services.

Use cases relacionados:

```text
ListFavoriteAppsUseCase
AddFavoriteAppUseCase
RemoveFavoriteAppUseCase
```

---

## 22. Repository `notifications`

Responsável por notificações de usuário.

Tabela principal:

```text
notifications
```

Operações esperadas:

- criar notificação;
- listar não lidas por usuário;
- marcar uma como lida;
- marcar todas como lidas;
- buscar notificação por ID.

Use cases relacionados:

```text
ListUnreadNotificationsUseCase
NotifyUserUseCase
MarkNotificationReadUseCase
MarkAllNotificationsReadUseCase
```

Ponto de atenção:

> Confirmar se o método `get(notification_id)` existe no repository concreto e no port correspondente, pois `MarkNotificationReadUseCase` depende dele.

---

## 23. Repository `audit`

Responsável por logs de auditoria.

Tabela principal:

```text
audit_logs
```

Operação principal conhecida:

```text
log(data)
```

Dados auditáveis:

- user_id;
- action;
- entity_type;
- entity_id;
- payload;
- ip_address.

---

## 24. Repositories e paginação

Listagens administrativas usam padrão comum.

Parâmetros:

```text
q
page
page_size
sort
direction
```

Repositories devem retornar:

```text
items
total
```

O use case transforma isso em:

```text
PaginatedResult
```

Use cases paginados:

```text
ListUsersUseCase
ListRolesUseCase
ListGroupsUseCase
ListPermissionsUseCase
ListAdminAppsUseCase
```

---

## 25. Repositories e eventos

Repositories não devem publicar eventos diretamente.

Fluxo correto:

```text
Repository executa persistência
  ↓
Use case decide evento
  ↓
Use case chama uow.collect_event
  ↓
UoW publica após commit
```

Motivo:

- repository não deve conhecer Socket.IO;
- repository não deve conhecer regra de frontend;
- evento deve refletir regra de negócio, não apenas operação SQL;
- publicação deve ocorrer após commit.

---

## 26. Repositories e erros

Repositories podem lançar exceções técnicas, mas erros de negócio devem preferencialmente ser tratados no use case.

Exemplo:

```text
Repository: retorna None se app não existe.
Use case: transforma em plugin.not_found.
```

Regra:

> Repositories devem evitar retornar respostas HTTP ou estruturas `{ errors: [...] }`. Isso pertence aos controllers/use cases.

---

## 27. Regras para criar novo repository

Ao criar novo repository:

1. Definir claramente o domínio.
2. Criar port no domínio, se aplicável.
3. Implementar classe SQLAlchemy na infraestrutura.
4. Registrar no Unit of Work.
5. Usar somente via use cases.
6. Manter métodos pequenos e específicos.
7. Evitar lógica de negócio extensa no repository.
8. Escrever testes de consultas importantes.

---

## 28. O que evitar

Evitar em repositories:

```text
Chamar Socket.IO.
Publicar eventos.
Acessar request/g do Flask.
Retornar jsonify/Response.
Resolver regra de autorização complexa de usuário.
Executar commit por conta própria.
Abrir nova sessão fora do UoW.
Misturar múltiplos domínios sem necessidade.
```

---

## 29. Pontos de atenção

1. Use cases devem acessar repositories via Unit of Work.
2. Repositories concretos pertencem à infraestrutura.
3. Ports pertencem ao domínio.
4. Alguns ports podem estar defasados em relação às implementações; revisar contratos.
5. `notifications.get` precisa ser confirmado no port/repository.
6. `permissions.module` é essencial para plugin lifecycle.
7. `app_query` deve retornar dados suficientes para `/me/apps`.
8. Repositories não devem publicar eventos diretamente.
9. Commits devem ser responsabilidade do Unit of Work.
10. Evitar lógica HTTP nos repositories.

---

## 30. Documentos relacionados

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/use-cases.md
docs/04-core-api/modelos-de-banco.md
docs/09-banco-de-dados/core-db.md
docs/09-banco-de-dados/modelo-rbac.md
docs/09-banco-de-dados/modelo-plugin-system.md
```

