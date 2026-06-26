# Minha DELPI — Banco de Dados da Core API

> **Arquivo:** `docs/09-banco-de-dados/core-db.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** modelo de dados do banco `postgres-core`

---

## 1. Objetivo

Este documento descreve o banco de dados da **Core API** da Minha DELPI.

O banco da Core API armazena os dados de governança da plataforma, incluindo usuários, RBAC, apps, rotas, manifestos, versões de plugins, favoritos, notificações e auditoria.

Não cobre: TOTVS, Portal RH, `postgres-plugins` (operacional/RAG), `keycloak-db`.

**Índice da pasta:** [README.md](./README.md) · **RBAC:** [modelo-rbac.md](./modelo-rbac.md) · **Plugins:** [modelo-plugin-system.md](./modelo-plugin-system.md)

**Convenções SQLAlchemy** (classes, mixin, lista de arquivos em `models/`): [../04-core-api/modelos-de-banco.md](../04-core-api/modelos-de-banco.md).

**Schema versionado:** revision Alembic `7aa51b680332` (`core-api/migrations/versions/`).

---

## 2. Banco responsável

Serviço Docker:

```text
postgres-core
```

Container:

```text
delpi-postgres-core
```

Uso:

```text
Core API
```

Variáveis de conexão usadas pela Core API:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

---

## 3. Responsabilidade do banco Core

O banco Core é responsável por dados de governança da plataforma.

Pertence ao banco Core:

- usuários locais;
- roles;
- grupos;
- permissões;
- vínculos RBAC;
- apps/plugins registrados;
- rotas de apps;
- manifestos vigentes;
- versões históricas de manifestos;
- favoritos de usuário;
- notificações;
- logs de auditoria.

Não pertence ao banco Core:

- dados operacionais TOTVS;
- dados transacionais de módulos de negócio;
- dados internos do Keycloak;
- dados persistentes específicos de plugins de domínio;
- integrações externas que pertencem à API DELPI.

---

## 4. Tabelas principais

Tabelas atuais:

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
apps
app_routes
app_manifests
app_versions
user_favorite_apps
notifications
audit_logs
```

---

## 5. Visão por domínio

| Domínio | Tabelas |
|---|---|
| Identidade local | `users` |
| RBAC | `roles`, `groups`, `permissions`, `user_roles`, `user_groups`, `group_roles`, `role_permissions`, `user_permissions` |
| Plugin System | `apps`, `app_routes`, `app_manifests`, `app_versions` |
| Preferências | `user_favorite_apps` |
| Notificações | `notifications` |
| Auditoria | `audit_logs` |

---

## 6. Convenção de timestamps

Grande parte dos modelos usa `TimestampMixin`.

Campos:

```text
created_at
updated_at
```

Comportamento esperado:

- `created_at` recebe `now()` no banco;
- `updated_at` recebe `now()` no banco e é atualizado em alterações;
- ambos usam timezone quando configurado no model/migration.

---

## 7. Tabela `users`

Armazena usuários locais da plataforma.

Campos principais:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | Identificador do usuário, normalmente vindo do `sub` do JWT |
| `name` | string | Nome do usuário |
| `email` | string | Email único e indexado |
| `active` | boolean | Status ativo |
| `is_superadmin` | boolean | Bypass administrativo |
| `last_login_at` | datetime | Último login processado |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Índice:

```text
ix_users_email unique
```

Relacionamentos principais:

```text
users → user_roles
users → user_groups
users → user_permissions
users → user_favorite_apps
users → notifications
users → audit_logs
```

---

## 8. Tabela `roles`

Armazena papéis do RBAC.

Campos principais:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | Gerado pelo banco |
| `name` | string | Nome único |
| `description` | text | Descrição |
| `system_role` | boolean | Indica role de sistema |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Constraint:

```text
unique(name)
```

Relacionamentos:

```text
roles → user_roles
roles → group_roles
roles → role_permissions
```

---

## 9. Tabela `groups`

Armazena grupos de usuários.

Campos principais:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | Gerado pelo banco |
| `name` | string | Nome único |
| `description` | text | Descrição |
| `active` | boolean | Status ativo |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Constraint:

```text
unique(name)
```

Relacionamentos:

```text
groups → user_groups
groups → group_roles
```

---

## 10. Tabela `permissions`

Armazena permissões granulares.

Campos principais:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | Gerado pelo banco |
| `code` | string | Código único da permissão |
| `name` | string | Nome legível |
| `description` | text | Descrição |
| `module` | string | Módulo dono da permissão |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Constraints/índices:

```text
unique(code)
ix_permissions_module
```

**Permissões de sistema** (seed no boot — `permissions_seed.py`, `module: system`):

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

**Permissões de plugin** — criadas no `POST /admin/apps/register`; `module` = `id` do plugin (ex.: `strategic-indicators.view` com `module: strategic-indicators`).

---

## 11. Tabela `user_roles`

Associação muitos-para-muitos entre usuários e roles.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `user_id` | UUID | FK para `users.id` |
| `role_id` | UUID | FK para `roles.id` |

Chave primária composta:

```text
user_id + role_id
```

FKs com cascade:

```text
user_id → users.id ON DELETE CASCADE
role_id → roles.id ON DELETE CASCADE
```

Uso:

```text
Conceder roles diretamente a usuários.
```

---

## 12. Tabela `user_groups`

Associação muitos-para-muitos entre usuários e grupos.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `user_id` | UUID | FK para `users.id` |
| `group_id` | UUID | FK para `groups.id` |

Chave primária composta:

```text
user_id + group_id
```

Uso:

```text
Colocar usuários em grupos.
```

---

## 13. Tabela `group_roles`

Associação entre grupos e roles.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `group_id` | UUID | FK para `groups.id` |
| `role_id` | UUID | FK para `roles.id` |

Chave primária composta:

```text
group_id + role_id
```

Uso:

```text
Conceder roles a grupos.
```

Impacto:

```text
Usuários do grupo herdam permissões das roles do grupo.
```

---

## 14. Tabela `role_permissions`

Associação entre roles e permissões.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `role_id` | UUID | FK para `roles.id` |
| `permission_id` | UUID | FK para `permissions.id` |

Chave primária composta:

```text
role_id + permission_id
```

Uso:

```text
Definir quais permissões pertencem a cada role.
```

---

## 15. Tabela `user_permissions`

Overrides individuais de permissão por usuário.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `user_id` | UUID | FK para `users.id` |
| `permission_id` | UUID | FK para `permissions.id` |
| `granted` | boolean | Concede ou remove permissão |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Chave primária composta:

```text
user_id + permission_id
```

Regra:

```text
granted = true  → adiciona permissão efetiva
granted = false → remove permissão efetiva
```

Overrides são aplicados depois de roles diretas e roles herdadas por grupos.

---

## 16. Modelo lógico do RBAC

```text
users
  ├── user_roles ───── roles ───── role_permissions ───── permissions
  │
  ├── user_groups ──── groups ──── group_roles ────────── roles
  │
  └── user_permissions ────────────────────────────────── permissions
```

Fluxo de permissão efetiva:

```text
roles diretas
  + roles via grupos
  + user_permissions granted=true
  - user_permissions granted=false
  = permissões efetivas
```

---

## 17. Tabela `apps`

Armazena apps/plugins registrados na plataforma.

Campos principais:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | string | ID do plugin/app |
| `name` | string | Nome legível |
| `description` | text | Descrição |
| `base_path` | string | Base path do app |
| `icon` | string | Ícone |
| `type` | string | `microfrontend`, `iframe` ou `backend-only` |
| `version` | string | Versão ativa |
| `active` | boolean | Indica se app está ativo |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Chave primária:

```text
id
```

Exemplos de IDs:

```text
strategic-indicators
dash-lmps
api-delpi
```

---

## 18. Tabela `app_routes`

Armazena rotas dos apps/plugins.

Campos principais:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | ID da rota |
| `app_id` | string | FK para `apps.id` |
| `path` | string | Path da rota |
| `label` | string | Nome exibido |
| `icon` | string | Ícone |
| `order` | integer | Ordem de exibição |
| `show_in_menu` | boolean | Exibe no menu |
| `active` | boolean | Status da rota |
| `permission_id` | UUID | FK opcional para `permissions.id` |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Relacionamentos:

```text
app_routes.app_id → apps.id
app_routes.permission_id → permissions.id
```

Uso:

```text
Montar menu e rotas autorizadas do Portal.
```

---

## 19. Tabela `app_manifests`

Armazena o manifesto vigente de cada app/plugin.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `app_id` | string | PK e FK para `apps.id` |
| `manifest` | JSON | Manifesto vigente completo |
| `checksum` | string | SHA-256 do manifesto |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Chave primária:

```text
app_id
```

FK:

```text
app_id → apps.id ON DELETE CASCADE
```

Uso:

```text
Consultar entry, renderMode, route.entry e metadados do plugin.
```

---

## 20. Tabela `app_versions`

Armazena histórico versionado de manifestos.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | bigint | ID interno |
| `app_id` | string | FK para `apps.id` |
| `version` | string | Versão registrada |
| `manifest` | JSON | Snapshot do manifesto |
| `checksum` | string | SHA-256 |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Constraint única:

```text
uq_app_version(app_id, version)
```

Índice:

```text
ix_app_versions_app_id
```

Uso:

- listar versões;
- impedir versão duplicada;
- executar rollback;
- preservar histórico de manifestos estruturais.

---

## 21. Modelo lógico do Plugin System

```text
apps
  ├── app_routes
  ├── app_manifests
  └── app_versions

app_routes
  └── permissions
```

Fluxo de registro:

```text
manifesto
  ↓
apps
  ↓
app_manifests
  ↓
app_versions
  ↓
permissions
  ↓
app_routes
```

---

## 22. Tabela `user_favorite_apps`

Armazena favoritos por usuário.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `user_id` | UUID | FK para `users.id` |
| `app_id` | string | FK para `apps.id` |
| `order_index` | integer | Ordem do favorito |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Chave primária composta:

```text
user_id + app_id
```

Uso:

```text
Favoritos do Portal por usuário.
```

---

## 23. Tabela `notifications`

Armazena notificações de usuário.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | UUID | ID da notificação |
| `user_id` | UUID | Usuário destino |
| `title` | string | Título opcional |
| `message` | string | Mensagem |
| `type` | string | Tipo da notificação |
| `read_at` | datetime | Data de leitura |
| `created_at` | datetime | Data de criação |

Índice:

```text
ix_notifications_user_id
```

Uso:

- listar notificações não lidas;
- marcar uma como lida;
- marcar todas como lidas;
- emitir eventos de notificação.

Ponto de atenção:

> O modelo atual de migration não possui FK explícita de `notifications.user_id` para `users.id`, apesar de semanticamente representar vínculo com usuário.

---

## 24. Tabela `audit_logs`

Armazena logs de auditoria.

Campos:

| Campo | Tipo | Observação |
|---|---|---|
| `id` | integer | ID interno |
| `user_id` | UUID | Usuário associado, opcional |
| `action` | string | Ação executada |
| `entity_type` | string | Tipo da entidade |
| `entity_id` | string | ID da entidade |
| `payload` | JSON | Dados adicionais |
| `ip_address` | string | IP da origem |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Atualização |

Índices:

```text
ix_audit_logs_action
ix_audit_logs_user_id
```

FK:

```text
audit_logs.user_id → users.id
```

---

## 25. Índices e constraints relevantes

| Tabela | Índice/constraint | Uso |
|---|---|---|
| `users` | unique index `email` | Buscar/sincronizar usuário por email |
| `roles` | unique `name` | Evitar role duplicada |
| `groups` | unique `name` | Evitar grupo duplicado |
| `permissions` | unique `code` | Evitar permissão duplicada |
| `permissions` | index `module` | Buscar permissões por módulo/plugin |
| `app_versions` | unique `app_id + version` | Evitar versão duplicada |
| `app_versions` | index `app_id` | Listar versões por plugin |
| `notifications` | index `user_id` | Listar notificações do usuário |
| `audit_logs` | index `user_id` | Consultar auditoria por usuário |
| `audit_logs` | index `action` | Consultar auditoria por ação |

---

## 26. Migrations

A Core API usa Flask-Migrate/Alembic.

Arquivos principais:

```text
app/extensions/migrate.py
migrations/env.py
migrations/versions/7aa51b680332_initial_clean_schema_from_current_models.py
```

A migration inicial cria todo o schema da Core API a partir dos modelos atuais.

---

## 27. Cascades e exclusões

Algumas FKs possuem `ON DELETE CASCADE`.

Exemplos:

```text
app_manifests.app_id → apps.id ON DELETE CASCADE
app_versions.app_id → apps.id ON DELETE CASCADE
user_favorite_apps.app_id → apps.id ON DELETE CASCADE
user_favorite_apps.user_id → users.id ON DELETE CASCADE
user_roles.user_id → users.id ON DELETE CASCADE
user_roles.role_id → roles.id ON DELETE CASCADE
user_groups.user_id → users.id ON DELETE CASCADE
user_groups.group_id → groups.id ON DELETE CASCADE
role_permissions.role_id → roles.id ON DELETE CASCADE
role_permissions.permission_id → permissions.id ON DELETE CASCADE
group_roles.group_id → groups.id ON DELETE CASCADE
group_roles.role_id → roles.id ON DELETE CASCADE
```

Mesmo com cascades, alguns use cases removem vínculos explicitamente antes de remover entidades.

Exemplo:

```text
DeleteRoleUseCase remove role_permissions, user_roles, group_roles antes de remover role.
```

---

## 28. Regras de manutenção

1. Alterações no schema devem ser feitas por migration.
2. Models e migration devem permanecer alinhados.
3. Não alterar banco manualmente em produção sem migration formal.
4. Permissões de plugin devem manter `module = plugin_id`.
5. Rotas de plugin devem manter `app_id = plugin_id`.
6. Não misturar dados operacionais no banco Core.
7. Não acessar diretamente `keycloak-db` pela aplicação.
8. Não usar `postgres-core` para dados de domínio de plugins.

---

## 29. Pontos de atenção

1. `postgres-core` é banco de governança, não de operação.
2. `apps.id` é string, não UUID.
3. `app_manifests.app_id` é PK e FK.
4. `app_versions` preserva histórico estrutural, mas update não estrutural de manifesto não cria nova versão.
5. `permissions.module` é essencial para plugins.
6. `user_permissions` aplica overrides efetivos.
7. `notifications.user_id` é indexado, mas na migration inicial não aparece como FK para users.
8. `order` em `app_routes` é palavra comum; observar compatibilidade de SQLAlchemy/banco.
9. Alguns deletes são feitos explicitamente mesmo com cascade.
10. Schema físico deve ser validado contra migrations antes de produção.

---

## 30. Documentos relacionados

- [README.md](./README.md)
- [modelo-rbac.md](./modelo-rbac.md)
- [modelo-plugin-system.md](./modelo-plugin-system.md)
- [../02-infraestrutura/bancos-de-dados.md](../02-infraestrutura/bancos-de-dados.md) (inclui `postgres-plugins`)
- [../04-core-api/modelos-de-banco.md](../04-core-api/modelos-de-banco.md)
- [../04-core-api/migrations.md](../04-core-api/migrations.md)

