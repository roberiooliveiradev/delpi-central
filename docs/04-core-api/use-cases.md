# Minha DELPI — Core API: Use Cases

> **Arquivo:** `docs/04-core-api/use-cases.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** casos de uso da camada de aplicação da Core API

---

## 1. Objetivo

Este documento descreve os **use cases** da Core API da Minha DELPI.

Use cases concentram as regras de aplicação e orquestram repositories, services, validações, eventos e Unit of Work.

Eles representam ações de negócio como registrar plugin, listar apps do usuário, alterar roles, marcar notificação como lida ou executar rollback de plugin.

---

## 2. Papel dos use cases

Na arquitetura da Core API, controllers HTTP devem ser finos.

Fluxo esperado:

```text
Controller HTTP
  ↓
Valida entrada básica
  ↓
Cria Unit of Work
  ↓
Instancia use case
  ↓
Executa use case
  ↓
Retorna resposta HTTP
```

O use case deve concentrar:

- regra de aplicação;
- validações de negócio;
- chamadas a repositories;
- chamadas a services;
- coleta de eventos;
- formatação de resultado de aplicação quando necessário.

---

## 3. Relação com Unit of Work

Os use cases recebem um Unit of Work.

Exemplo conceitual:

```python
with SqlAlchemyUnitOfWork() as uow:
    use_case = RegisterPluginUseCase(uow)
    result = use_case.execute(manifest)
```

O Unit of Work disponibiliza repositories como:

```text
users
roles
groups
permissions
plugins
plugin_manifests
plugin_versions
plugin_routes
plugin_permissions
admin_apps
admin_routes
favorites
notifications
audit
```

E também permite coletar eventos:

```python
self.uow.collect_event(AdminChangedEvent(...))
```

---

## 4. Regra transacional recomendada

Regra recomendada:

> Use cases não devem chamar `commit()` diretamente. O commit deve ser responsabilidade do contexto externo do Unit of Work.

Fluxo preferencial:

```text
with uow:
  use_case.execute()

uow.__exit__
  ↓
commit
  ↓
publish events
```

Ponto de atenção:

> Alguns use cases administrativos atuais fazem `commit()` ou `rollback()` internamente. Isso deve ser tratado como inconsistência a revisar e padronizar.

---

## 5. Eventos em use cases

Use cases administrativos normalmente coletam eventos de domínio/aplicação.

Evento principal:

```python
AdminChangedEvent(
    entity="...",
    action="...",
    payload={...},
    target_user_id=None,
)
```

Eventos são publicados após commit pelo EventBus.

Fluxo:

```text
Use case coleta evento
  ↓
Unit of Work commita
  ↓
EventBus publica
  ↓
RbacEventHandler executa efeitos internos
  ↓
Socket.IO emite admin.changed
```

---

## 6. Use cases do usuário atual

### 6.1 `GetMeUseCase`

Responsabilidade:

```text
Retornar dados do usuário autenticado.
```

Usado por:

```http
GET /me
```

Dados esperados:

- id;
- name;
- email;
- roles;
- groups;
- permissions;
- is_superadmin.

---

### 6.2 `ListUserAppsUseCase`

Responsabilidade:

```text
Listar apps e rotas autorizados para o usuário atual.
```

Usado por:

```http
GET /me/apps
```

Fluxo:

```text
Busca apps ativos com rotas
  ↓
Recebe permissions/is_superadmin do usuário
  ↓
AppAuthorizationService filtra apps/rotas
  ↓
Retorna DTO para o Portal
```

Resultado inclui:

- id;
- name;
- basePath;
- icon;
- type;
- entryUrl;
- renderMode;
- routes.

---

## 7. Use cases de favoritos

### 7.1 `ListFavoriteAppsUseCase`

Responsabilidade:

```text
Listar apps favoritos do usuário, respeitando autorização atual.
```

Fluxo:

```text
Lista favoritos persistidos
  ↓
Lista apps ativos/autorizados
  ↓
Filtra favoritos contra apps autorizados
  ↓
Retorna favoritos visíveis
```

Ponto de atenção:

> A implementação conhecida abre `with self.uow:` internamente, enquanto o padrão predominante é o controller abrir o Unit of Work. Esse comportamento deve ser revisado para padronização.

---

### 7.2 `AddFavoriteAppUseCase`

Responsabilidade:

```text
Adicionar app aos favoritos do usuário.
```

Fluxo:

```text
Valida se app existe entre apps ativos
  ↓
Verifica duplicidade
  ↓
Se já existe, retorna ok
  ↓
Cria favorito
  ↓
Coleta evento favorite_added direcionado ao usuário
```

Evento:

```text
favorite_added
```

---

### 7.3 `RemoveFavoriteAppUseCase`

Responsabilidade:

```text
Remover app dos favoritos do usuário.
```

Fluxo:

```text
Remove vínculo user_id + app_id
  ↓
Coleta evento favorite_removed direcionado ao usuário
```

Evento:

```text
favorite_removed
```

---

## 8. Use cases de notificações

### 8.1 `ListUnreadNotificationsUseCase`

Responsabilidade:

```text
Listar notificações não lidas do usuário.
```

Usado por:

```http
GET /me/notifications
```

---

### 8.2 `NotifyUserUseCase`

Responsabilidade:

```text
Criar notificação para um usuário.
```

Fluxo:

```text
Cria registro em notifications
  ↓
Coleta evento de notificação
```

Evento conceitual:

```text
UserNotifiedEvent
```

---

### 8.3 `MarkNotificationReadUseCase`

Responsabilidade:

```text
Marcar uma notificação como lida.
```

Fluxo esperado:

```text
Busca notificação
  ↓
Valida se pertence ao usuário
  ↓
Atualiza read_at
  ↓
Coleta evento
```

Ponto de atenção:

> A implementação conhecida chama `self.uow.notifications.get(notification_id)`, mas o repository/port analisado anteriormente não expõe claramente esse método. Confirmar implementação final ou ajustar contrato.

---

### 8.4 `MarkAllNotificationsReadUseCase`

Responsabilidade:

```text
Marcar todas as notificações não lidas do usuário como lidas.
```

Evento conceitual:

```text
AllNotificationsMarkedReadEvent
```

---

## 9. Use cases de apps administrativos

### 9.1 `ListAdminAppsUseCase`

Responsabilidade:

```text
Listar apps/plugins de forma paginada para administração.
```

Usado por:

```http
GET /admin/apps
```

Usa paginação padronizada por:

```text
BaseListPaginatedUseCase
PaginatedResult
```

---

### 9.2 `UpdateAdminAppUseCase`

Responsabilidade:

```text
Atualizar metadata administrativa de um app.
```

Campos típicos:

- name;
- description;
- icon.

Evento:

```text
app_updated
```

---

### 9.3 `DeleteAdminAppUseCase`

Responsabilidade:

```text
Remover app administrativo.
```

Observação:

> Para plugins registrados por manifesto, o fluxo recomendado de remoção completa é `UnregisterPluginUseCase`, que remove versões, rotas, permissões, manifesto e app.

---

### 9.4 `SetAppActiveUseCase`

Responsabilidade:

```text
Ativar ou desativar app.
```

Eventos:

```text
app_activated
app_deactivated
```

---

### 9.5 `BulkSetAdminAppsActiveUseCase`

Responsabilidade:

```text
Ativar/desativar múltiplos apps administrativos.
```

Ponto de atenção:

> A implementação conhecida faz controle transacional interno. Revisar consistência com o padrão geral de Unit of Work.

---

### 9.6 `BulkDeleteAdminAppsUseCase`

Responsabilidade:

```text
Remover múltiplos apps administrativos.
```

Ponto de atenção:

> A implementação conhecida faz commit/rollback interno. Revisar padronização.

---

## 10. Use cases de rotas administrativas

### 10.1 `ListAppRoutesUseCase`

Responsabilidade:

```text
Listar rotas de um app.
```

---

### 10.2 `CreateAppRouteUseCase`

Responsabilidade:

```text
Criar rota administrativa para um app.
```

Fluxo:

```text
Valida app/entrada
  ↓
Cria rota
  ↓
Resolve permission_code para permission_id quando aplicável
  ↓
Coleta evento route_created
```

Evento:

```text
route_created
```

---

### 10.3 `UpdateRouteUseCase`

Responsabilidade:

```text
Atualizar rota administrativa.
```

Evento:

```text
route_updated
```

---

### 10.4 `DeleteRouteUseCase`

Responsabilidade:

```text
Excluir rota administrativa.
```

Evento:

```text
route_deleted
```

---

### 10.5 `BulkDeleteRoutesUseCase`

Responsabilidade:

```text
Excluir múltiplas rotas.
```

Evento:

```text
routes_bulk_deleted
```

---

## 11. Use cases de Plugin System

### 11.1 `RegisterPluginUseCase`

Responsabilidade:

```text
Registrar plugin novo ou nova versão de plugin existente.
```

Fluxo para plugin novo:

```text
Valida manifesto
  ↓
Calcula checksum
  ↓
Cria app
  ↓
Salva manifesto
  ↓
Cria versão
  ↓
Cria permissões
  ↓
Cria rotas
  ↓
Coleta plugin_registered
```

Fluxo para plugin existente:

```text
Verifica versão duplicada
  ↓
Atualiza versão ativa
  ↓
Salva manifesto
  ↓
Cria nova versão
  ↓
Remove rotas/permissões antigas
  ↓
Recria permissões/rotas
  ↓
Coleta plugin_registered
```

Evento:

```text
plugin_registered
```

---

### 11.2 `GetPluginManifestUseCase`

Responsabilidade:

```text
Obter manifesto vigente de um plugin.
```

---

### 11.3 `UpdatePluginManifestUseCase`

Responsabilidade:

```text
Atualizar manifesto sem alterar estrutura nem versão.
```

Bloqueia:

- mudança de `id`;
- mudança de `version`;
- mudança de `basePath`;
- mudança no conjunto de permissões;
- mudança no conjunto de rotas.

Permite:

- metadata do app;
- label/icon/order/showInMenu de rotas existentes.

Evento:

```text
plugin_manifest_updated
```

---

### 11.4 `ListPluginVersionsUseCase`

Responsabilidade:

```text
Listar versões históricas de um plugin.
```

Consulta:

```text
app_versions
```

---

### 11.5 `RollbackPluginVersionUseCase`

Responsabilidade:

```text
Restaurar plugin para versão histórica.
```

Fluxo:

```text
Busca plugin
  ↓
Busca versão histórica
  ↓
Restaura apps.version
  ↓
Restaura app_manifests
  ↓
Remove rotas/permissões atuais
  ↓
Recria permissões/rotas do manifesto histórico
  ↓
Coleta plugin_version_rolled_back
```

Evento:

```text
plugin_version_rolled_back
```

---

### 11.6 `UnregisterPluginUseCase`

Responsabilidade:

```text
Remover completamente um plugin.
```

Fluxo:

```text
Busca plugin
  ↓
Verifica dependentes em manifestos
  ↓
Se houver dependentes, bloqueia
  ↓
Remove versões
  ↓
Remove rotas
  ↓
Remove permissões por module
  ↓
Remove manifesto
  ↓
Remove app
  ↓
Coleta plugin_unregistered
```

Evento:

```text
plugin_unregistered
```

---

### 11.7 `SetPluginActiveUseCase`

Responsabilidade:

```text
Ativar/desativar plugin.
```

Eventos:

```text
plugin_activated
plugin_deactivated
```

---

### 11.8 `BulkSetPluginsActiveUseCase`

Responsabilidade:

```text
Ativar/desativar múltiplos plugins.
```

Evento conceitual:

```text
plugins_activation_changed
```

---

### 11.9 `BulkUnregisterPluginsUseCase`

Responsabilidade:

```text
Remover múltiplos plugins.
```

Fluxo:

```text
Valida todos os plugins
  ↓
Remove versões, rotas, permissões, manifestos e apps
  ↓
Coleta plugins_unregistered
```

Evento:

```text
plugins_unregistered
```

---

## 12. Use cases de roles

### 12.1 `ListRolesUseCase`

Responsabilidade:

```text
Listar roles com paginação.
```

Base:

```text
BaseListPaginatedUseCase
```

---

### 12.2 `CreateRoleUseCase`

Responsabilidade:

```text
Criar role.
```

Validações comuns:

- nome obrigatório;
- evitar duplicidade.

Evento:

```text
role_created
```

---

### 12.3 `UpdateRoleUseCase`

Responsabilidade:

```text
Atualizar role.
```

Evento:

```text
role_updated
```

---

### 12.4 `DeleteRoleUseCase`

Responsabilidade:

```text
Excluir role e limpar vínculos.
```

Vínculos envolvidos:

```text
role_permissions
user_roles
group_roles
```

---

## 13. Use cases de permissões de role

### 13.1 `ListRolePermissionsUseCase`

Responsabilidade:

```text
Listar permissões de uma role.
```

---

### 13.2 `AddPermissionToRoleUseCase`

Responsabilidade:

```text
Adicionar permissão a uma role.
```

Evento:

```text
permission_added_to_role
```

---

### 13.3 `RemovePermissionFromRoleUseCase`

Responsabilidade:

```text
Remover permissão de uma role.
```

Evento:

```text
permission_removed_from_role
```

---

### 13.4 `ReplaceRolePermissionsUseCase`

Responsabilidade:

```text
Substituir todas as permissões de uma role.
```

Evento:

```text
role_permissions_replaced
```

---

## 14. Use cases de grupos

### 14.1 `ListGroupsUseCase`

Responsabilidade:

```text
Listar grupos com paginação.
```

---

### 14.2 `DeleteGroupUseCase`

Responsabilidade:

```text
Excluir grupo e limpar vínculos.
```

Vínculos envolvidos:

```text
user_groups
group_roles
```

---

### 14.3 Use cases de criação/atualização de grupo

Os controllers indicam operações de criação e atualização de grupos, mas os arquivos específicos ainda devem ser confirmados se não estiverem presentes entre os analisados.

Nomes esperados:

```text
CreateGroupUseCase
UpdateGroupUseCase
```

---

## 15. Use cases de roles de grupo

### 15.1 `ListGroupRolesUseCase`

Responsabilidade:

```text
Listar roles de um grupo.
```

---

### 15.2 `AddGroupRolesUseCase`

Responsabilidade:

```text
Adicionar role a grupo.
```

Evento:

```text
role_added_to_group
```

---

### 15.3 `RemoveGroupRolesUseCase`

Responsabilidade:

```text
Remover role de grupo.
```

Evento:

```text
role_removed_from_group
```

---

### 15.4 `ReplaceGroupRolesUseCase`

Responsabilidade:

```text
Substituir roles de um grupo.
```

Evento:

```text
group_roles_replaced
```

---

## 16. Use cases de usuários

### 16.1 `ListUsersUseCase`

Responsabilidade:

```text
Listar usuários com paginação.
```

---

### 16.2 `DeleteUserUseCase`

Responsabilidade:

```text
Excluir usuário.
```

Proteção esperada:

```text
superadmin
```

---

### 16.3 `SetUserSuperadminUseCase`

Responsabilidade:

```text
Alterar flag is_superadmin de um usuário.
```

Regras:

- ator precisa ser superadmin;
- usuário alvo deve existir;
- não pode remover o último superadmin;
- se não houver mudança real, retorna ok sem alteração.

Evento:

```text
user_superadmin_updated
```

---

## 17. Use cases de roles do usuário

### 17.1 `ListUserRolesUseCase`

Responsabilidade:

```text
Listar roles de um usuário.
```

---

### 17.2 `AddRoleToUserUseCase`

Responsabilidade:

```text
Adicionar role a usuário.
```

Evento direcionado:

```text
role_added_to_user
```

---

### 17.3 `RemoveRoleFromUserUseCase`

Responsabilidade:

```text
Remover role de usuário.
```

Evento direcionado:

```text
role_removed_from_user
```

---

### 17.4 `ReplaceUserRolesUseCase`

Responsabilidade:

```text
Substituir todas as roles diretas de um usuário.
```

Evento direcionado:

```text
roles_replaced
```

---

## 18. Use cases de grupos do usuário

### 18.1 `ListUserGroupsUseCase`

Responsabilidade:

```text
Listar grupos de um usuário.
```

---

### 18.2 `AddGroupToUserUseCase`

Responsabilidade:

```text
Adicionar usuário a grupo.
```

Evento direcionado:

```text
group_added_to_user
```

---

### 18.3 `RemoveGroupFromUserUseCase`

Responsabilidade:

```text
Remover usuário de grupo.
```

Evento direcionado:

```text
group_removed_from_user
```

---

### 18.4 `ReplaceUserGroupsUseCase`

Responsabilidade:

```text
Substituir todos os grupos de um usuário.
```

Evento direcionado:

```text
groups_replaced
```

---

## 19. Use cases de consultas auxiliares RBAC

### 19.1 `ListRoleUsersUseCase`

Responsabilidade:

```text
Listar usuários associados a uma role.
```

---

### 19.2 `ListGroupUsersUseCase`

Responsabilidade:

```text
Listar usuários associados a um grupo.
```

---

### 19.3 `ListPermissionsUseCase`

Responsabilidade:

```text
Listar permissões com paginação.
```

---

### 19.4 `ListPermissionUsageUseCase`

Responsabilidade:

```text
Listar uso de uma permissão por roles e grupos.
```

Retorna:

- permissão;
- roles que possuem a permissão;
- grupos que recebem essas roles;
- indicação de via roles.

---

## 20. Base de paginação

### 20.1 `BaseListPaginatedUseCase`

Responsabilidade:

```text
Padronizar listagens paginadas.
```

Recebe parâmetros como:

```text
page
page_size
q
sort
direction
```

---

### 20.2 `PaginatedResult`

Estrutura conceitual:

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

## 21. Padrão para criar novo use case

Novo use case deve seguir este padrão:

```python
class SomeUseCase:
    def __init__(self, uow):
        self.uow = uow

    def execute(self, ...):
        # valida entrada
        # chama repositories/services
        # coleta eventos se necessário
        # retorna DTO/resultado
```

Recomendações:

- não depender de Flask diretamente;
- não acessar `request` ou `g` dentro do use case;
- receber dados necessários como argumentos;
- usar ports/repositories via Unit of Work;
- não fazer commit diretamente, salvo exceções legadas;
- coletar eventos sem publicar diretamente;
- retornar dados simples/serializáveis.

---

## 22. Pontos de atenção

1. Controllers devem permanecer finos.
2. Use cases devem conter regra de aplicação.
3. Unit of Work deve controlar transação e publicação de eventos.
4. Alguns use cases atuais fazem commit/rollback interno; revisar.
5. Alguns use cases esperados de grupos precisam confirmação se não estiverem nos arquivos analisados.
6. `MarkNotificationReadUseCase` depende de método `notifications.get` a confirmar.
7. Eventos devem ser coletados antes do commit e publicados depois.
8. Use cases não devem conhecer detalhes HTTP.
9. Use cases devem depender de ports, não de SQLAlchemy diretamente.
10. Alterações RBAC devem gerar eventos para invalidação de cache e atualização do Portal.

---

## 23. Documentos relacionados

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/repositories.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/versionamento-e-rollback.md
```

