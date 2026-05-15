# Minha DELPI — Core API: Modelos de Banco

> **Arquivo:** `docs/04-core-api/modelos-de-banco.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** models SQLAlchemy da Core API e relação com o schema `postgres-core`

---

## 1. Objetivo

Este documento descreve os modelos de banco da **Core API** da Minha DELPI.

Os models SQLAlchemy representam o schema do banco `postgres-core`, usado para governança da plataforma: usuários, RBAC, apps, plugins, rotas, manifestos, versões, favoritos, notificações e auditoria.

- Banco: [../09-banco-de-dados/core-db.md](../09-banco-de-dados/core-db.md)
- Rotas que persistem dados: [controllers-e-rotas.md](./controllers-e-rotas.md)

**Nota:** o model `App` está em `app_module.py` (tabela `apps`).

### Onde ler o quê

| Precisa de… | Documento |
|---|---|
| Tabelas, FKs, índices e visão relacional do `postgres-core` | [../09-banco-de-dados/core-db.md](../09-banco-de-dados/core-db.md) |
| RBAC só no modelo de dados | [../09-banco-de-dados/modelo-rbac.md](../09-banco-de-dados/modelo-rbac.md) |
| Plugin System só no modelo de dados | [../09-banco-de-dados/modelo-plugin-system.md](../09-banco-de-dados/modelo-plugin-system.md) |
| Arquivos `.py` dos models, mixin, boas práticas Alembic | este arquivo |

---

## 2. Localização dos models

Os models ficam em:

```text
core-api/app/infrastructure/db/models/
```

Eles são carregados no bootstrap da aplicação para garantir que SQLAlchemy e Alembic conheçam todas as tabelas.

Ponto de atenção:

> O bootstrap pode usar import amplo dos models para garantir registro no metadata do SQLAlchemy. Em refatorações, é importante não quebrar esse registro, pois migrations dependem dele.

---

## 3. Extensão SQLAlchemy

A instância global do SQLAlchemy fica em:

```text
app/extensions/db.py
```

Conteúdo conceitual:

```python
db = SQLAlchemy()
```

Todos os models da Core API usam essa instância.

---

## 4. Mixin de timestamps

Vários models usam um mixin de timestamps.

Campos comuns:

```text
created_at
updated_at
```

Comportamento esperado:

- `created_at` preenchido na criação;
- `updated_at` atualizado em alterações;
- valores gerados por `now()`/função equivalente.

Esses campos aparecem em tabelas como:

```text
users
roles
groups
permissions
apps
app_routes
app_manifests
app_versions
user_favorite_apps
audit_logs
```

---

## 5. Lista de models principais

Models principais da Core API:

```text
User
Group
Role
Permission
UserPermission
UserFavoriteApp
App
AppRoute
AppManifest
AppVersion
Notification
AuditLog
```

Tabelas associativas:

```text
user_roles
role_permissions
user_groups
group_roles
```

---

## 6. Organização por domínio

| Domínio | Models/tabelas |
|---|---|
| Identidade local | `User` |
| RBAC | `Role`, `Group`, `Permission`, `UserPermission`, associativas |
| Plugin System | `App`, `AppRoute`, `AppManifest`, `AppVersion` |
| Favoritos | `UserFavoriteApp` |
| Notificações | `Notification` |
| Auditoria | `AuditLog` |

---

## 7. Model `User`

Tabela:

```text
users
```

Responsabilidade:

```text
Representar o usuário local da plataforma.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID do usuário |
| `name` | Nome |
| `email` | Email único |
| `active` | Status ativo |
| `is_superadmin` | Bypass administrativo |
| `last_login_at` | Último login processado |
| `created_at` | Criação |
| `updated_at` | Atualização |

Uso:

- sincronização a partir do JWT;
- RBAC;
- favoritos;
- notificações;
- auditoria;
- controle de superadmin.

---

## 8. Model `Role`

Tabela:

```text
roles
```

Responsabilidade:

```text
Representar papel RBAC que agrupa permissões.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID |
| `name` | Nome único |
| `description` | Descrição |
| `system_role` | Role de sistema |
| `created_at` | Criação |
| `updated_at` | Atualização |

Relacionamentos:

```text
Role ↔ User via user_roles
Role ↔ Group via group_roles
Role ↔ Permission via role_permissions
```

---

## 9. Model `Group`

Tabela:

```text
groups
```

Responsabilidade:

```text
Representar grupo de usuários.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID |
| `name` | Nome único |
| `description` | Descrição |
| `active` | Status ativo |
| `created_at` | Criação |
| `updated_at` | Atualização |

Relacionamentos:

```text
Group ↔ User via user_groups
Group ↔ Role via group_roles
```

---

## 10. Model `Permission`

Tabela:

```text
permissions
```

Responsabilidade:

```text
Representar permissão granular do sistema ou plugin.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID |
| `code` | Código único |
| `name` | Nome legível |
| `description` | Descrição |
| `module` | Módulo dono |
| `created_at` | Criação |
| `updated_at` | Atualização |

Exemplos:

```text
rbac.manage
apps.view
apps.manage
dash-lmps.access
```

Regra para plugins:

```text
module = plugin_id
```

---

## 11. Tabela associativa `user_roles`

Associação:

```text
User ↔ Role
```

Tabela:

```text
user_roles
```

Campos:

```text
user_id
role_id
```

Chave primária composta:

```text
user_id + role_id
```

Uso:

```text
Conceder roles diretamente ao usuário.
```

---

## 12. Tabela associativa `role_permissions`

Associação:

```text
Role ↔ Permission
```

Tabela:

```text
role_permissions
```

Campos:

```text
role_id
permission_id
```

Chave primária composta:

```text
role_id + permission_id
```

Uso:

```text
Definir permissões de uma role.
```

---

## 13. Tabela associativa `user_groups`

Associação:

```text
User ↔ Group
```

Tabela:

```text
user_groups
```

Campos:

```text
user_id
group_id
```

Chave primária composta:

```text
user_id + group_id
```

Uso:

```text
Incluir usuários em grupos.
```

---

## 14. Tabela associativa `group_roles`

Associação:

```text
Group ↔ Role
```

Tabela:

```text
group_roles
```

Campos:

```text
group_id
role_id
```

Chave primária composta:

```text
group_id + role_id
```

Uso:

```text
Conceder roles a grupos.
```

---

## 15. Model `UserPermission`

Tabela:

```text
user_permissions
```

Responsabilidade:

```text
Representar override individual de permissão por usuário.
```

Campos:

| Campo | Descrição |
|---|---|
| `user_id` | Usuário |
| `permission_id` | Permissão |
| `granted` | Concede ou remove |
| `created_at` | Criação |
| `updated_at` | Atualização |

Regra:

```text
granted = true  → adiciona permissão efetiva
granted = false → remove permissão efetiva
```

---

## 16. Model `App`

Tabela:

```text
apps
```

Responsabilidade:

```text
Representar app/plugin registrado na plataforma.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | ID string do app/plugin |
| `name` | Nome |
| `description` | Descrição |
| `base_path` | Caminho base |
| `icon` | Ícone |
| `type` | Tipo do plugin/app |
| `version` | Versão ativa |
| `active` | Status ativo |
| `created_at` | Criação |
| `updated_at` | Atualização |

Tipos suportados:

```text
microfrontend
iframe
backend-only
```

---

## 17. Model `AppRoute`

Tabela:

```text
app_routes
```

Responsabilidade:

```text
Representar rota navegável de um app/plugin.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID da rota |
| `app_id` | App dono |
| `path` | Path da rota |
| `label` | Label de menu |
| `icon` | Ícone |
| `order` | Ordem |
| `show_in_menu` | Se aparece no menu |
| `active` | Status ativo |
| `permission_id` | Permissão exigida |
| `created_at` | Criação |
| `updated_at` | Atualização |

Relacionamentos:

```text
AppRoute → App
AppRoute → Permission opcional
```

Uso pelo Portal:

- menu dinâmico;
- roteamento de plugins;
- controle de acesso por rota.

---

## 18. Model `AppManifest`

Tabela:

```text
app_manifests
```

Responsabilidade:

```text
Armazenar manifesto vigente de um plugin.
```

Campos:

| Campo | Descrição |
|---|---|
| `app_id` | App/plugin dono |
| `manifest` | JSON completo vigente |
| `checksum` | SHA-256 do manifesto |
| `created_at` | Criação |
| `updated_at` | Atualização |

Relacionamento:

```text
AppManifest → App
```

Chave:

```text
app_id
```

---

## 19. Model `AppVersion`

Tabela:

```text
app_versions
```

Responsabilidade:

```text
Armazenar histórico versionado dos manifestos.
```

Campos:

| Campo | Descrição |
|---|---|
| `id` | ID interno |
| `app_id` | App/plugin dono |
| `version` | Versão registrada |
| `manifest` | Snapshot do manifesto |
| `checksum` | SHA-256 |
| `created_at` | Criação |
| `updated_at` | Atualização |

Constraint:

```text
app_id + version único
```

Uso:

- listar versões;
- impedir versão duplicada;
- rollback.

---

## 20. Model `UserFavoriteApp`

Tabela:

```text
user_favorite_apps
```

Responsabilidade:

```text
Representar app favorito de um usuário.
```

Campos:

| Campo | Descrição |
|---|---|
| `user_id` | Usuário |
| `app_id` | App favoritado |
| `order_index` | Ordem de exibição |
| `created_at` | Criação |
| `updated_at` | Atualização |

Chave primária composta:

```text
user_id + app_id
```

---

## 21. Model `Notification`

Tabela:

```text
notifications
```

Responsabilidade:

```text
Representar notificação enviada a um usuário.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | UUID |
| `user_id` | Usuário destino |
| `title` | Título opcional |
| `message` | Mensagem |
| `type` | Tipo |
| `read_at` | Data de leitura |
| `created_at` | Criação |

Uso:

- listar notificações não lidas;
- marcar como lida;
- marcar todas como lidas;
- criar notificação.

Ponto de atenção:

> A migration inicial indica índice em `user_id`, mas deve-se confirmar se há FK explícita para `users.id` no model final.

---

## 22. Model `AuditLog`

Tabela:

```text
audit_logs
```

Responsabilidade:

```text
Registrar ações auditáveis.
```

Campos principais:

| Campo | Descrição |
|---|---|
| `id` | ID interno |
| `user_id` | Usuário relacionado |
| `action` | Ação executada |
| `entity_type` | Tipo da entidade |
| `entity_id` | ID da entidade |
| `payload` | JSON com dados adicionais |
| `ip_address` | IP da origem |
| `created_at` | Criação |
| `updated_at` | Atualização |

Uso:

```text
Auditoria administrativa e operacional da plataforma.
```

---

## 23. Relacionamentos principais

### 23.1 RBAC

```text
User ↔ Role
User ↔ Group
Group ↔ Role
Role ↔ Permission
User ↔ Permission override
```

### 23.2 Plugin System

```text
App → AppRoute
App → AppManifest
App → AppVersion
AppRoute → Permission
```

### 23.3 Preferências

```text
User → UserFavoriteApp → App
```

### 23.4 Notificações

```text
User → Notification
```

### 23.5 Auditoria

```text
User → AuditLog
```

---

## 24. Como os models participam dos fluxos

### 24.1 Login

```text
JWT validado
  ↓
User buscado/criado
  ↓
last_login_at atualizado
  ↓
roles/groups/permissions carregados
```

Models:

```text
User
Role
Group
Permission
```

---

### 24.2 Listagem de apps do usuário

```text
App + AppRoute + AppManifest
  ↓
Permission
  ↓
AppAuthorizationService
  ↓
DTO para Portal
```

Models:

```text
App
AppRoute
AppManifest
Permission
```

---

### 24.3 Registro de plugin

```text
App
AppManifest
AppVersion
Permission
AppRoute
```

Ordem:

```text
apps
app_manifests
app_versions
permissions
app_routes
```

---

### 24.4 RBAC

```text
User
Role
Group
Permission
UserPermission
associativas
```

---

## 25. Alinhamento com migrations

Models devem permanecer alinhados com migrations.

Arquivos relacionados:

```text
migrations/env.py
migrations/versions/*.py
```

Regra:

> Toda alteração em model persistente deve gerar migration correspondente.

---

## 26. Boas práticas para novos models

1. Definir nome de tabela explicitamente.
2. Usar UUID quando fizer sentido para entidades internas.
3. Usar string estável quando a entidade for identificada por contrato externo, como `apps.id`.
4. Adicionar timestamps quando o registro for auditável.
5. Definir índices para campos de busca frequente.
6. Definir constraints únicas para evitar duplicidade lógica.
7. Definir relacionamentos com cascade somente quando a exclusão for segura.
8. Atualizar migrations.
9. Atualizar repositories.
10. Atualizar documentação.

---

## 27. Pontos de atenção

1. `apps.id` é string, não UUID.
2. `permissions.module` é crítico para Plugin System.
3. `app_manifests` tem um manifesto vigente por app.
4. `app_versions` tem histórico por app e version.
5. `user_permissions` aplica overrides depois das roles.
6. `Notification.user_id` deve ser validado quanto à FK no model final.
7. Rotas dependem de permissões opcionais.
8. Tabelas associativas usam chaves compostas.
9. Models precisam estar importados para Alembic autogenerate.
10. Alterações no model sem migration quebram ambientes.

---

## 28. Documentos relacionados

- [../09-banco-de-dados/README.md](../09-banco-de-dados/README.md)
- [../09-banco-de-dados/core-db.md](../09-banco-de-dados/core-db.md)
- [../09-banco-de-dados/modelo-rbac.md](../09-banco-de-dados/modelo-rbac.md)
- [../09-banco-de-dados/modelo-plugin-system.md](../09-banco-de-dados/modelo-plugin-system.md)
- [migrations.md](./migrations.md)
- [repositories.md](./repositories.md)
- [../03-autenticacao-autorizacao/rbac.md](../03-autenticacao-autorizacao/rbac.md)
- [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md)

