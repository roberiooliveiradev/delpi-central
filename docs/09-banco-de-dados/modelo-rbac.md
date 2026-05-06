# Minha DELPI — Modelo de Banco do RBAC

> **Arquivo:** `docs/09-banco-de-dados/modelo-rbac.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** modelo relacional de usuários, grupos, roles, permissões e overrides

---

## 1. Objetivo

Este documento descreve o modelo de banco de dados usado pelo RBAC da **Minha DELPI**.

RBAC significa **Role-Based Access Control**, ou controle de acesso baseado em papéis.

Na Minha DELPI, o RBAC é mantido pela Core API e persistido no banco `postgres-core`.

Este documento detalha:

- usuários;
- roles;
- grupos;
- permissões;
- vínculos entre entidades;
- overrides individuais;
- resolução de permissões efetivas;
- impactos em apps, rotas e Portal.

---

## 2. Visão geral

O modelo RBAC da Minha DELPI combina quatro entidades principais:

```text
User
Group
Role
Permission
```

E cinco relações principais:

```text
User ↔ Role
User ↔ Group
Group ↔ Role
Role ↔ Permission
User ↔ Permission override
```

Visão lógica:

```text
Usuário
  ├── Roles diretas
  │     └── Permissões
  │
  ├── Grupos
  │     └── Roles do grupo
  │           └── Permissões
  │
  └── Overrides individuais
        ├── granted=true  → concede
        └── granted=false → remove
```

---

## 3. Tabelas do RBAC

Tabelas envolvidas:

```text
users
roles
groups
permissions
user_roles
user_groups
group_roles
role_permissions
user_permissions
```

---

## 4. Diagrama relacional conceitual

```text
users
  │
  ├── user_roles ───── roles ───── role_permissions ───── permissions
  │                       ▲
  │                       │
  ├── user_groups ──── groups ──── group_roles
  │
  └── user_permissions ─────────────────────────────────── permissions
```

---

## 5. Tabela `users`

Armazena os usuários locais da plataforma.

Campos principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador do usuário |
| `name` | string | Nome do usuário |
| `email` | string | Email único e indexado |
| `active` | boolean | Indica se o usuário está ativo |
| `is_superadmin` | boolean | Indica bypass administrativo |
| `last_login_at` | datetime | Último login processado pela Core API |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

O `id` normalmente corresponde ao `sub` do JWT emitido pelo Keycloak.

O usuário local é criado ou atualizado quando o usuário autenticado chama a Core API.

---

## 6. Tabela `roles`

Armazena papéis que agrupam permissões.

Campos principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador da role |
| `name` | string | Nome único da role |
| `description` | text | Descrição da role |
| `system_role` | boolean | Indica role de sistema |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Exemplos conceituais:

```text
Administrador de Apps
Gestor de Usuários
Analista LMP
Operações
```

Roles são atribuídas diretamente a usuários ou indiretamente via grupos.

---

## 7. Tabela `groups`

Armazena grupos de usuários.

Campos principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador do grupo |
| `name` | string | Nome único do grupo |
| `description` | text | Descrição |
| `active` | boolean | Indica se o grupo está ativo |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Exemplos conceituais:

```text
TI
Diretoria
Operações
Qualidade
RH
```

Grupos recebem roles. Usuários associados ao grupo herdam as permissões dessas roles.

---

## 8. Tabela `permissions`

Armazena permissões granulares.

Campos principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador da permissão |
| `code` | string | Código único da permissão |
| `name` | string | Nome legível |
| `description` | text | Descrição |
| `module` | string | Módulo dono da permissão |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Exemplos:

```text
rbac.manage
users.view
users.manage
apps.view
apps.manage
routes.manage
dashboard-lmps.access
```

Permissões do sistema usam normalmente:

```text
module = system
```

Permissões de plugins usam:

```text
module = <plugin_id>
```

---

## 9. Tabela `user_roles`

Associa usuários diretamente a roles.

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `user_id` | UUID | FK para `users.id` |
| `role_id` | UUID | FK para `roles.id` |

Chave primária composta:

```text
user_id + role_id
```

Uso:

```text
Conceder uma role diretamente a um usuário.
```

Exemplo:

```text
Usuário João recebe role Administrador de Apps.
```

---

## 10. Tabela `user_groups`

Associa usuários a grupos.

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `user_id` | UUID | FK para `users.id` |
| `group_id` | UUID | FK para `groups.id` |

Chave primária composta:

```text
user_id + group_id
```

Uso:

```text
Colocar usuário em um grupo organizacional ou funcional.
```

Exemplo:

```text
Usuário Maria pertence ao grupo Operações.
```

---

## 11. Tabela `group_roles`

Associa grupos a roles.

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `group_id` | UUID | FK para `groups.id` |
| `role_id` | UUID | FK para `roles.id` |

Chave primária composta:

```text
group_id + role_id
```

Uso:

```text
Conceder uma role a todos os usuários de um grupo.
```

Exemplo:

```text
Grupo Operações recebe role Analista LMP.
```

---

## 12. Tabela `role_permissions`

Associa roles a permissões.

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `role_id` | UUID | FK para `roles.id` |
| `permission_id` | UUID | FK para `permissions.id` |

Chave primária composta:

```text
role_id + permission_id
```

Uso:

```text
Definir quais permissões uma role concede.
```

Exemplo:

```text
Role Analista LMP recebe dashboard-lmps.access.
```

---

## 13. Tabela `user_permissions`

Associa usuários diretamente a permissões como override individual.

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `user_id` | UUID | FK para `users.id` |
| `permission_id` | UUID | FK para `permissions.id` |
| `granted` | boolean | Indica se concede ou remove |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Chave primária composta:

```text
user_id + permission_id
```

Regra:

```text
granted = true  → adiciona permissão
granted = false → remove permissão
```

Overrides são aplicados depois da composição por roles e grupos.

---

## 14. Cálculo de permissões efetivas

A Core API calcula permissões efetivas pelo `PermissionResolver`.

Fluxo lógico:

```text
1. Se usuário é superadmin:
     retornar todas as permissões.

2. Se não é superadmin:
     buscar cache.

3. Se cache não existe:
     buscar permissões por roles diretas.

4. Buscar permissões por roles herdadas via grupos.

5. Unir permissões.

6. Aplicar user_permissions:
     granted=true adiciona.
     granted=false remove.

7. Ordenar e cachear.
```

---

## 15. Exemplo de resolução

Usuário:

```text
Maria
```

Roles diretas:

```text
Gestor de Apps
```

Grupos:

```text
Operações
```

Roles do grupo Operações:

```text
Analista LMP
```

Permissões:

```text
Gestor de Apps → apps.view, apps.manage
Analista LMP   → dashboard-lmps.access
```

Overrides:

```text
granted=false para apps.manage
```

Resultado efetivo:

```text
apps.view
dashboard-lmps.access
```

A permissão `apps.manage` foi removida pelo override individual.

---

## 16. Superadmin

Usuário com:

```text
is_superadmin = true
```

recebe todas as permissões cadastradas.

Também possui bypass nos decorators de permissão, exceto em regras que exigem explicitamente `require_superadmin`.

Proteção especial:

> O sistema não permite remover o último superadmin.

---

## 17. Impacto em apps e rotas

Rotas de apps podem estar associadas a permissões.

```text
app_routes.permission_id → permissions.id
```

Quando o Portal chama `/me/apps`:

```text
Core API lista apps ativos
  ↓
lista rotas ativas
  ↓
filtra rotas por permissões efetivas
  ↓
remove apps sem rotas autorizadas
```

Portanto, o RBAC afeta diretamente o menu e os apps visíveis no Portal.

---

## 18. Permissões de plugins

Quando um plugin é registrado, permissões declaradas no manifesto são criadas em `permissions`.

Exemplo:

```json
{
  "code": "dashboard-lmps.access",
  "name": "Acessar Dashboard LMPs",
  "module": "dashboard-lmps"
}
```

Regra importante:

```text
permissions.module = plugin_id
```

Isso permite remover/recriar permissões do plugin por módulo durante register, rollback ou unregister.

---

## 19. Seeds de permissões base

A Core API possui seed de permissões base do sistema.

Permissões atuais:

```text
rbac.manage
users.view
users.manage
groups.manage
roles.manage
permissions.manage
apps.manage
apps.view
routes.manage
```

Essas permissões têm `module = system`.

---

## 20. Operações administrativas comuns

### 20.1 Atribuir role a usuário

Tabelas afetadas:

```text
user_roles
```

Evento esperado:

```text
role_added_to_user
```

---

### 20.2 Remover role de usuário

Tabelas afetadas:

```text
user_roles
```

Evento esperado:

```text
role_removed_from_user
```

---

### 20.3 Substituir roles do usuário

Tabelas afetadas:

```text
user_roles
```

Evento esperado:

```text
roles_replaced
```

---

### 20.4 Atribuir grupo a usuário

Tabelas afetadas:

```text
user_groups
```

Evento esperado:

```text
group_added_to_user
```

---

### 20.5 Substituir roles do grupo

Tabelas afetadas:

```text
group_roles
```

Evento esperado:

```text
group_roles_replaced
```

---

### 20.6 Substituir permissões da role

Tabelas afetadas:

```text
role_permissions
```

Evento esperado:

```text
role_permissions_replaced
```

---

## 21. Invalidação de cache

Alterações de RBAC devem invalidar cache de permissões.

Eventos podem ser:

- direcionados a um usuário;
- globais, quando múltiplos usuários podem ser impactados.

Exemplos:

```text
role_added_to_user → usuário específico
group_roles_replaced → usuários do grupo
role_permissions_replaced → usuários com a role direta ou herdada
```

---

## 22. Consultas úteis

### 22.1 Permissões de um usuário por role direta

```sql
SELECT p.code
FROM user_roles ur
JOIN role_permissions rp ON rp.role_id = ur.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE ur.user_id = :user_id;
```

---

### 22.2 Permissões de um usuário por grupos

```sql
SELECT p.code
FROM user_groups ug
JOIN group_roles gr ON gr.group_id = ug.group_id
JOIN role_permissions rp ON rp.role_id = gr.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE ug.user_id = :user_id;
```

---

### 22.3 Overrides de usuário

```sql
SELECT p.code, up.granted
FROM user_permissions up
JOIN permissions p ON p.id = up.permission_id
WHERE up.user_id = :user_id;
```

---

## 23. Regras de integridade

1. `permissions.code` deve ser único.
2. `roles.name` deve ser único.
3. `groups.name` deve ser único.
4. Tabelas associativas usam chave composta para evitar duplicidade.
5. Permissões de plugin devem ter `module = plugin_id`.
6. Usuário não deve ficar sem possibilidade de administração global se for o último superadmin.
7. Remoção de roles/groups/users deve limpar vínculos.
8. Mudanças de permissão devem invalidar cache.

---

## 24. Pontos de atenção

1. `user_permissions` pode remover permissões herdadas por role/grupo.
2. Superadmin ignora o fluxo comum e recebe todas as permissões.
3. AppAuthorizationService usa permissões efetivas já resolvidas.
4. Permissões sem vínculo com roles não dão acesso a usuários comuns.
5. Rotas sem `permission_id` são liberadas para usuários autenticados que receberam o app/rota.
6. Remover permissão de plugin pode afetar roles existentes.
7. Recriação de permissões em register/rollback deve preservar coerência de roles.
8. Cache atual é em memória e exige atenção em múltiplas réplicas.
9. Alguns repositories agregados podem consultar parte do RBAC; a fonte conceitual completa é o PermissionResolver.
10. Alterações administrativas devem publicar eventos.

---

## 25. Documentos relacionados

```text
docs/09-banco-de-dados/core-db.md
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/permission-resolver.md
docs/04-core-api/modelos-de-banco.md
docs/04-core-api/repositories.md
docs/05-plugin-system/manifesto-plugin.md
```

