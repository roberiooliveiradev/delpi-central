# Minha DELPI — RBAC, Autenticação e Autorização

> **Arquivo:** `docs/03-autenticacao-autorizacao/rbac.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** autenticação, autorização, RBAC, permissões efetivas e superadmin

---

## 1. Objetivo

Este documento descreve como funciona a autenticação e autorização da **Minha DELPI**, com foco no modelo RBAC implementado pela Core API.

**Referência HTTP completa:** [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md) (seções `/me`, `/admin/apps`, `/admin/rbac`).

Ele explica:

- o papel do Keycloak;
- o papel da Core API;
- como usuários são sincronizados;
- como roles, groups e permissions se relacionam;
- como permissões efetivas são calculadas;
- como superadmin funciona;
- como apps e rotas são filtrados;
- como endpoints protegidos aplicam permissões;
- como eventos de RBAC atualizam cache e notificam o Portal.

---

## 2. Princípio central

A autenticação e a autorização são responsabilidades separadas.

```text
Keycloak → autentica
Core API → autoriza
```

O Keycloak é responsável por identificar o usuário e emitir o token JWT.

A Core API é responsável por validar o token, sincronizar o usuário local e calcular as permissões efetivas usadas pela Minha DELPI.

Regra importante:

> O JWT identifica o usuário. As permissões finais da plataforma são resolvidas internamente pela Core API.

---

## 3. Componentes envolvidos

| Componente | Responsabilidade |
|---|---|
| Keycloak | Autenticação, emissão de token, JWKS, issuer e audience |
| Portal | Inicia login, armazena token e chama APIs protegidas |
| Core API | Valida token, sincroniza usuário, resolve permissões e aplica RBAC |
| Banco Core | Persiste usuários, roles, groups, permissions e vínculos |
| Socket.IO | Notifica mudanças administrativas em tempo real |
| RBAC Cache | Cache em memória das permissões efetivas do usuário |

---

## 4. Fluxo geral de autenticação

```text
Usuário acessa Portal
  ↓
Portal redireciona para Keycloak
  ↓
Usuário autentica
  ↓
Keycloak emite access token JWT
  ↓
Portal chama Core API com Authorization Bearer
  ↓
Core API valida o JWT
  ↓
Core API sincroniza usuário local
  ↓
Core API carrega roles, groups e permissions
```

---

## 5. Middleware de autenticação da Core API

A Core API possui um middleware global executado antes das requisições.

Fluxo do middleware:

```text
Requisição HTTP
  ↓
Lê header Authorization
  ↓
Se não houver Bearer token, permite seguir como endpoint público
  ↓
Se houver token, valida JWT
  ↓
Extrai sub, email e name
  ↓
Valida UUID do sub
  ↓
Busca usuário local por email
  ↓
Cria usuário local se não existir
  ↓
Atualiza last_login_at
  ↓
Carrega roles, groups e permissions
  ↓
Define g.current_user
```

O usuário autenticado fica disponível em:

```python
g.current_user
```

Estrutura esperada:

```python
g.current_user = SimpleNamespace(
    id=str(user.id),
    email=user.email,
    name=user.name,
    roles=roles,
    groups=groups,
    permissions=permissions,
    is_superadmin=user.is_superadmin,
)
```

---

## 6. Endpoints públicos e protegidos

O middleware retorna `None` quando não há token.

Isso permite que endpoints públicos funcionem sem autenticação, desde que o controller não use decorators de proteção.

Para proteger endpoints, os controllers usam decorators como:

```python
@require_auth()
@require_permission("apps.view")
@require_all_permissions(["rbac.manage", "users.manage"])
@require_superadmin()
```

Portanto:

- ausência de token não bloqueia automaticamente todos os endpoints;
- endpoints sensíveis devem usar decorators;
- a segurança final depende do uso correto dos decorators.

---

## 7. Modelo RBAC

O RBAC da Minha DELPI é composto por:

```text
User
Group
Role
Permission
```

E pelas relações:

```text
User ↔ Role
User ↔ Group
Group ↔ Role
Role ↔ Permission
User ↔ Permission override
```

Visão lógica:

```text
User
 ├─ Roles diretas
 │   └─ Permissions
 │
 ├─ Groups
 │   └─ Roles
 │       └─ Permissions
 │
 └─ UserPermission overrides
     ├─ granted = true  → adiciona permissão
     └─ granted = false → remove permissão
```

---

## 8. Tabelas principais

### 8.1 `users`

Armazena usuários locais da plataforma.

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID do usuário, normalmente vindo do `sub` do token |
| `name` | Nome do usuário |
| `email` | Email único e indexado |
| `active` | Indica se o usuário está ativo |
| `is_superadmin` | Indica bypass administrativo |
| `last_login_at` | Último login processado pela Core API |
| `created_at` | Criação do registro |
| `updated_at` | Última atualização |

---

### 8.2 `roles`

Representa papéis administrativos ou funcionais.

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID |
| `name` | Nome único da role |
| `description` | Descrição |
| `system_role` | Indica role de sistema |
| `created_at` | Criação |
| `updated_at` | Atualização |

---

### 8.3 `groups`

Representa grupos de usuários.

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID |
| `name` | Nome único do grupo |
| `description` | Descrição |
| `active` | Status ativo |
| `created_at` | Criação |
| `updated_at` | Atualização |

---

### 8.4 `permissions`

Representa permissões granulares da plataforma.

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID |
| `code` | Código único da permissão |
| `name` | Nome legível |
| `description` | Descrição |
| `module` | Módulo dono da permissão |
| `created_at` | Criação |
| `updated_at` | Atualização |

Exemplo de permission code:

```text
apps.view
rbac.manage
users.manage
dash-lmps.access
```

---

### 8.5 Tabelas associativas

| Tabela | Relação |
|---|---|
| `user_roles` | Usuários com roles diretas |
| `user_groups` | Usuários pertencentes a grupos |
| `group_roles` | Grupos com roles |
| `role_permissions` | Roles com permissões |
| `user_permissions` | Overrides individuais de permissão |

---

## 9. Permissões base do sistema

A Core API executa seed de permissões base ao iniciar, fora do modo de teste.

Permissões base atuais:

| Código | Nome | Módulo |
|---|---|---|
| `rbac.manage` | Gerenciar RBAC | `system` |
| `users.view` | Visualizar usuários | `system` |
| `users.manage` | Gerenciar usuários | `system` |
| `groups.manage` | Gerenciar grupos | `system` |
| `roles.manage` | Gerenciar papéis | `system` |
| `permissions.manage` | Gerenciar permissões | `system` |
| `apps.manage` | Gerenciar apps | `system` |
| `apps.view` | Visualizar apps | `system` |
| `routes.manage` | Gerenciar rotas | `system` |

O seed também remove permissões antigas sem `module`.

---

## 10. Permission Resolver

O `PermissionResolver` é o serviço de domínio responsável por calcular as permissões efetivas de um usuário.

Ele não conhece Flask, SQLAlchemy nem banco diretamente.

Dependências:

```text
PermissionQueryPort
PermissionCachePort opcional
```

Fluxo:

```text
resolve(user_id, is_superadmin)
  ↓
Se superadmin: retorna todas as permissões
  ↓
Se usuário comum: tenta cache
  ↓
Busca permissões por roles diretas
  ↓
Busca permissões por roles herdadas via grupos
  ↓
Une permissões
  ↓
Aplica user_permissions overrides
  ↓
Ordena resultado
  ↓
Salva no cache
  ↓
Retorna lista de permission codes
```

---

## 11. Bootstrap do primeiro superadmin (dev)

```env
INITIAL_SUPERADMIN_EMAIL=usuario@empresa.com.br
INITIAL_SUPERADMIN_NAME=Nome Exibido
```

No primeiro login com esse e-mail, a Core API promove `users.is_superadmin=true` (`bootstrap_service.py`). Criar o usuário no Keycloak com o **mesmo e-mail**.

Ver [configurar-keycloak.md](../10-guias-operacionais/configurar-keycloak.md).

---

## 12. Regra de superadmin

Superadmin possui bypass amplo na plataforma.

No cálculo de permissões:

```text
is_superadmin = true → todas as permissões cadastradas
```

Nos decorators de autorização:

```text
is_superadmin = true → bypass de require_permission, require_any_permission e require_all_permissions
```

O decorator `require_superadmin()` exige explicitamente que o usuário seja superadmin.

### Proteções para alteração de superadmin

A alteração da flag `is_superadmin` possui regras próprias.

Regras atuais:

1. Apenas um superadmin pode alterar outro superadmin.
2. O usuário alvo precisa existir.
3. Não é permitido remover o último superadmin do sistema.
4. Se não houver mudança real de valor, a operação retorna sucesso sem alteração.
5. Quando a alteração acontece, é publicado evento direcionado ao usuário alvo.

Fluxo:

```text
SetUserSuperadminUseCase
  ↓
Verifica se ator é superadmin
  ↓
Busca usuário alvo
  ↓
Se estiver removendo superadmin, conta superadmins
  ↓
Bloqueia remoção se for o último
  ↓
Atualiza flag
  ↓
Publica admin.changed target_user_id=usuário alvo
```

---

## 13. Overrides individuais de permissão

A tabela `user_permissions` permite ajustar permissões diretamente no usuário.

Campos:

| Campo | Descrição |
|---|---|
| `user_id` | Usuário |
| `permission_id` | Permissão |
| `granted` | Indica se concede ou remove |

Regra:

```text
granted = true  → adiciona permissão efetiva
granted = false → remove permissão efetiva
```

Os overrides são aplicados depois das permissões por role e grupo.

---

## 14. Cache de permissões

A Core API possui um cache em memória para permissões efetivas.

Implementação:

```text
RBACCache
```

Estrutura:

```python
_cache: Dict[str, List[str]]
```

Operações:

```text
get(user_id)
set(user_id, permissions)
invalidate_user(user_id)
invalidate(user_id)
clear()
```

O cache usa `RLock` para proteger acesso concorrente.

Atenção:

> O cache é em memória do processo. Em múltiplas réplicas da Core API, será necessário considerar invalidação distribuída ou cache externo.

---

## 15. Invalidação de cache

Quando alterações administrativas impactam RBAC, eventos são publicados e tratados pelo `RbacEventHandler`.

O handler invalida o cache de usuários impactados e recalcula permissões quando necessário.

Eventos tratados incluem:

```text
permission_added_to_role
permission_removed_from_role
role_permissions_replaced
role_added_to_group
role_removed_from_group
group_roles_replaced
```

Também existem eventos direcionados ao usuário, como:

```text
role_added_to_user
role_removed_from_user
groups_replaced
roles_replaced
user_superadmin_updated
```

---

## 16. Decorators de autorização

A Core API possui decorators para proteger endpoints HTTP.

### 16.1 `require_auth()`

Exige usuário autenticado em `g.current_user`.

Uso:

```python
@require_auth()
def get_me():
    ...
```

---

### 16.2 `require_superadmin()`

Exige que o usuário autenticado seja superadmin.

Uso:

```python
@require_superadmin()
def delete_user(user_id):
    ...
```

---

### 16.3 `require_permission(permission_code)`

Exige uma permissão específica.

Superadmin possui bypass.

Uso:

```python
@require_permission("apps.view")
def list_apps():
    ...
```

---

### 16.4 `require_any_permission(permission_codes)`

Exige pelo menos uma permissão da lista.

Uso:

```python
@require_any_permission(["apps.view", "apps.manage"])
def some_route():
    ...
```

---

### 16.5 `require_all_permissions(permission_codes)`

Exige todas as permissões da lista.

Uso:

```python
@require_all_permissions(["rbac.manage", "users.manage"])
def update_user():
    ...
```

---

## 17. Policy Engine

Além dos decorators diretos por permissão, existe um `PolicyEngine` para regras mais complexas.

Responsabilidades:

- manter registry de policies;
- avaliar policy pelo nome;
- acessar `g.current_user`;
- aplicar bypass de superadmin;
- retornar `unauthorized` quando não há usuário;
- retornar `forbidden` quando a policy nega acesso.

Policies registradas atualmente:

| Policy | Regra |
|---|---|
| `can_manage_rbac` | Exige `rbac.manage` |
| `can_manage_users` | Exige `users.manage` |
| `can_delete_user` | Exige `users.manage` e impede deletar a si mesmo |
| `can_manage_groups` | Exige `groups.manage` |
| `can_manage_roles` | Exige `roles.manage` |

Uso conceitual:

```python
@policy("can_delete_user")
def delete_user(user_id):
    ...
```

---

## 18. Autorização de apps e rotas

A autorização de apps para o Portal é feita pelo `AppAuthorizationService`.

Ele recebe:

```text
apps
permissions
is_superadmin
```

Regra:

- se for superadmin, retorna todos os apps;
- se não for superadmin, filtra rotas;
- rota sem `permission_code` é permitida;
- rota com `permission_code` exige permissão correspondente;
- app só é retornado se tiver pelo menos uma rota autorizada.

Fluxo:

```text
ListUserAppsUseCase
  ↓
AppQueryRepository lista apps ativos com rotas
  ↓
AppAuthorizationService filtra por permissão
  ↓
Core API retorna apps e rotas autorizados
  ↓
Portal monta menu dinâmico
```

---

## 19. Endpoints protegidos por RBAC

Exemplos de proteções atuais:

### Apps

| Endpoint | Permissão |
|---|---|
| `GET /admin/apps` | `apps.view` |
| `PUT /admin/apps/<plugin_id>` | `apps.manage` |
| `POST /admin/apps/register` | `apps.manage` |
| `PUT /admin/apps/<plugin_id>/manifest` | `apps.manage` |
| `DELETE /admin/apps/<plugin_id>` | `apps.manage` |

---

### RBAC

| Endpoint | Permissão |
|---|---|
| `GET /admin/rbac/roles` | `rbac.manage` |
| `POST /admin/rbac/roles` | `rbac.manage` + `roles.manage` |
| `PUT /admin/rbac/roles/<role_id>` | `rbac.manage` + `roles.manage` |
| `GET /admin/rbac/users` | `rbac.manage` + `users.view` |
| `PUT /admin/rbac/users/<user_id>` | `rbac.manage` + `users.manage` |
| `DELETE /admin/rbac/users/<user_id>` | superadmin |
| `GET /admin/rbac/permissions` | `rbac.manage` |

---

### Usuário atual

| Endpoint | Proteção |
|---|---|
| `GET /me` | autenticado |
| `GET /me/apps` | autenticado |
| `GET /me/apps/favorites` | autenticado |
| `GET /me/notifications` | autenticado |
| `GET /me/dashboard` | autenticado |

---

## 20. Eventos de RBAC

Alterações RBAC geram eventos `AdminChangedEvent`.

Estrutura:

```python
AdminChangedEvent(
    entity="rbac",
    action="...",
    payload={...},
    target_user_id="..." | None,
)
```

Exemplos de actions:

```text
role_created
role_updated
role_added_to_user
role_removed_from_user
roles_replaced
group_added_to_user
group_removed_from_user
groups_replaced
role_added_to_group
role_removed_from_group
group_roles_replaced
permission_added_to_role
permission_removed_from_role
role_permissions_replaced
user_superadmin_updated
```

Eventos com `target_user_id` são direcionados para a sala Socket.IO do usuário.

Eventos sem `target_user_id` são broadcast.

---

## 21. Socket.IO e RBAC

O Socket.IO exige token no handshake.

O token pode vir em:

```text
auth.token
```

ou, como fallback:

```text
query string token
```

Após validar o token, o socket usa o claim `sub` para colocar o cliente em uma sala:

```text
room = sub
```

Isso permite eventos direcionados a um usuário específico.

---

## 22. Padrão de erro de autorização

A Core API usa o formato padronizado:

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

Códigos comuns:

| Código | HTTP | Significado |
|---|---:|---|
| `unauthorized` | 401 | Usuário ausente ou não autenticado |
| `forbidden` | 403 | Usuário autenticado sem permissão |
| `invalid_token` | 401 | Token inválido |
| `invalid_claims` | 401 | Claims obrigatórias ausentes |
| `invalid_uuid` | 401 | `sub` inválido para UUID |

---

## 23. Regras de desenvolvimento

Ao criar novo endpoint protegido:

1. Definir se o endpoint é público ou autenticado.
2. Se autenticado, usar `@require_auth()`.
3. Se administrativo, usar permissão específica.
4. Se exigir múltiplas permissões, usar `@require_all_permissions()`.
5. Se exigir alternativa de permissões, usar `@require_any_permission()`.
6. Se for operação crítica global, avaliar `@require_superadmin()`.
7. Se a regra for contextual, criar policy.
8. Evitar regras de autorização espalhadas dentro do controller.

---

## 24. Regras para novas permissões

Permission codes devem ser claros, estáveis e hierárquicos.

Formato recomendado:

```text
<module>.<resource>.<action>
```

Exemplos:

```text
crm.leads.read
crm.leads.write
dash-lmps.access
apps.manage
users.view
```

Regras:

- usar lowercase;
- não usar espaços;
- não usar acentos;
- evitar nomes genéricos demais;
- manter o `module` coerente com o dono da permissão;
- permissões de plugins devem ser declaradas no manifesto.

---

## 25. Pontos de atenção

1. O middleware permite requisição sem token seguir adiante; a proteção real depende dos decorators.
2. O Keycloak autentica, mas não é a fonte final de autorização da plataforma.
3. Superadmin tem bypass amplo, mas algumas operações exigem explicitamente `require_superadmin()`.
4. A remoção do último superadmin é bloqueada.
5. O cache RBAC atual é em memória do processo.
6. Em ambiente com múltiplas réplicas, cache local pode causar inconsistência sem invalidação distribuída.
7. A autorização de apps depende das rotas autorizadas; app sem rota autorizada não aparece para usuário comum.
8. Permissões de plugins devem ser recriadas com cuidado durante update/register/rollback.
9. Alterações RBAC devem gerar eventos para invalidar cache e atualizar usuários impactados.
10. Algumas implementações atuais podem usar métodos não declarados nos ports; revisar contratos ao evoluir.

---

## 26. Documentos relacionados

- [jwt.md](./jwt.md)
- [keycloak-sso.md](./keycloak-sso.md)
- [permission-resolver.md](./permission-resolver.md)
- [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md)
- [../09-banco-de-dados/modelo-rbac.md](../09-banco-de-dados/modelo-rbac.md)
- [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md)

