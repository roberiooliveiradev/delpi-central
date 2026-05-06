# Minha DELPI — Modelo de Banco do Plugin System

> **Arquivo:** `docs/09-banco-de-dados/modelo-plugin-system.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** modelo relacional de apps, rotas, manifestos, versões e permissões de plugins

---

## 1. Objetivo

Este documento descreve o modelo de banco de dados que sustenta o **Plugin System** da Minha DELPI.

O Plugin System permite registrar apps, microfrontends, iframes e backends por manifesto JSON, persistindo suas informações centrais no banco `postgres-core`.

Este documento detalha:

- apps;
- rotas;
- manifestos vigentes;
- versões históricas;
- permissões de plugins;
- relacionamentos;
- fluxos de registro, atualização, rollback e remoção.

---

## 2. Tabelas envolvidas

As principais tabelas do Plugin System são:

```text
apps
app_routes
app_manifests
app_versions
permissions
```

Tabelas relacionadas:

```text
user_favorite_apps
role_permissions
user_permissions
```

---

## 3. Visão relacional

```text
apps
  ├── app_routes ───────── permissions
  ├── app_manifests
  └── app_versions

apps
  └── user_favorite_apps ─ users

permissions
  ├── role_permissions ─ roles
  └── user_permissions ─ users
```

---

## 4. Papel de cada tabela

| Tabela | Responsabilidade |
|---|---|
| `apps` | Cadastro principal do app/plugin |
| `app_routes` | Rotas navegáveis do app/plugin |
| `app_manifests` | Manifesto vigente do plugin |
| `app_versions` | Histórico versionado de manifestos |
| `permissions` | Permissões declaradas por plugins e sistema |
| `user_favorite_apps` | Favoritos de apps por usuário |

---

## 5. Tabela `apps`

A tabela `apps` representa a identidade principal de um app/plugin registrado.

Campos principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string | Identificador do app/plugin |
| `name` | string | Nome legível |
| `description` | text | Descrição |
| `base_path` | string | Caminho base do app |
| `icon` | string | Ícone do app |
| `type` | string | Tipo do plugin |
| `version` | string | Versão ativa |
| `active` | boolean | Indica se app está ativo |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Chave primária:

```text
id
```

Exemplos:

```text
dashboard-delpi
strategic-indicators
dashboard-lmps
api-delpi
```

---

## 6. Tipos de app/plugin

O campo `apps.type` deve refletir o tipo declarado no manifesto.

Tipos suportados:

```text
microfrontend
iframe
backend-only
```

| Tipo | Descrição |
|---|---|
| `microfrontend` | Plugin frontend integrado ao Portal |
| `iframe` | App renderizado por URL HTTP/HTTPS |
| `backend-only` | Serviço sem UI, usado para governança de backend/permissões |

---

## 7. Campo `active`

O campo `active` controla se o app é elegível para aparecer no fluxo comum do usuário.

Regra:

```text
active = true  → app pode ser retornado por /me/apps
active = false → app não deve aparecer para navegação comum
```

Operações relacionadas:

```text
SetAppActiveUseCase
SetPluginActiveUseCase
BulkSetPluginsActiveUseCase
BulkSetAdminAppsActiveUseCase
```

Eventos possíveis:

```text
app_activated
app_deactivated
plugin_activated
plugin_deactivated
```

---

## 8. Tabela `app_routes`

A tabela `app_routes` armazena as rotas navegáveis dos apps/plugins.

Campos principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador da rota |
| `app_id` | string | App dono da rota |
| `path` | string | Path da rota |
| `label` | string | Texto exibido no menu |
| `icon` | string | Ícone da rota |
| `order` | integer | Ordem de exibição |
| `show_in_menu` | boolean | Se aparece no menu |
| `active` | boolean | Se a rota está ativa |
| `permission_id` | UUID | Permissão exigida, opcional |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Relacionamentos:

```text
app_routes.app_id → apps.id
app_routes.permission_id → permissions.id
```

---

## 9. Rotas e menu dinâmico

As rotas são usadas pelo Portal para montar navegação.

Campos relevantes para o menu:

```text
path
label
icon
order
show_in_menu
permission_id
```

Regra:

```text
show_in_menu = true → rota aparece no menu
show_in_menu = false → rota pode existir, mas não aparece no menu
```

A autorização da rota depende de `permission_id`.

---

## 10. Rotas e permissões

Uma rota pode ter permissão associada.

```text
app_routes.permission_id → permissions.id
```

Se `permission_id` for `NULL`, a rota é considerada sem permissão específica.

Regra de autorização:

```text
permission_id NULL → rota permitida para usuário autenticado no contexto de /me/apps
permission_id definido → usuário precisa possuir a permission.code correspondente
```

A Core API retorna ao Portal o `permission_code`, não o UUID interno.

---

## 11. Tabela `app_manifests`

A tabela `app_manifests` armazena o manifesto vigente do plugin.

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `app_id` | string | PK e FK para `apps.id` |
| `manifest` | JSON | Manifesto vigente completo |
| `checksum` | string | SHA-256 do manifesto |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Chave primária:

```text
app_id
```

FK:

```text
app_id → apps.id ON DELETE CASCADE
```

Uso principal:

- obter `entry`;
- obter `ui.renderMode`;
- obter `routes[].entry`;
- preservar manifesto vigente completo;
- recalcular visão de apps para o Portal.

---

## 12. Manifesto vigente versus dados normalizados

O manifesto vigente é armazenado como JSON completo.

Mas a plataforma também normaliza partes dele em tabelas relacionais.

| Manifesto | Tabela relacional |
|---|---|
| `id`, `name`, `description`, `basePath`, `type`, `version`, `icon` | `apps` |
| `routes[]` | `app_routes` |
| `permissions[]` | `permissions` |
| manifesto completo | `app_manifests.manifest` |

Isso permite consultas relacionais eficientes e também preserva o contrato completo do plugin.

---

## 13. Tabela `app_versions`

A tabela `app_versions` armazena o histórico versionado dos manifestos.

Campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | bigint | Identificador interno |
| `app_id` | string | App/plugin dono da versão |
| `version` | string | Versão registrada |
| `manifest` | JSON | Snapshot completo do manifesto |
| `checksum` | string | SHA-256 do manifesto |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

Constraint única:

```text
app_id + version
```

Nome:

```text
uq_app_version
```

Índice:

```text
ix_app_versions_app_id
```

---

## 14. Uso de `app_versions`

A tabela `app_versions` é usada para:

- listar versões disponíveis;
- impedir registro duplicado de versão;
- executar rollback;
- manter histórico de contratos estruturais;
- preservar manifesto e checksum por versão.

Importante:

> Atualização não estrutural de manifesto não cria nova linha em `app_versions`.

---

## 15. Tabela `permissions` no contexto de plugins

Permissões de plugins são armazenadas na mesma tabela `permissions` usada pelo RBAC.

Campos importantes:

```text
code
name
description
module
```

Para plugins, a regra é:

```text
permissions.module = apps.id
```

Exemplo:

```text
apps.id = dashboard-lmps
permissions.module = dashboard-lmps
permissions.code = dashboard-lmps.access
```

Essa regra é fundamental para operações de lifecycle.

---

## 16. Por que `module` é importante

O campo `module` permite identificar permissões pertencentes a um plugin.

Operações que dependem disso:

```text
RegisterPluginUseCase em nova versão
RollbackPluginVersionUseCase
UnregisterPluginUseCase
BulkUnregisterPluginsUseCase
UpdatePluginManifestUseCase
```

Exemplo:

```text
Remover permissões do plugin dashboard-lmps:
DELETE FROM permissions WHERE module = 'dashboard-lmps';
```

Se `module` estiver errado, permissões podem não ser removidas ou podem ser removidas indevidamente.

---

## 17. Fluxo de registro — plugin novo

Quando um plugin novo é registrado:

```text
manifesto
  ↓
apps insert
  ↓
app_manifests insert
  ↓
app_versions insert
  ↓
permissions insert
  ↓
app_routes insert
```

Ordem importante:

1. App principal.
2. Manifesto vigente.
3. Versão histórica.
4. Permissões.
5. Rotas.

Rotas devem ser criadas depois das permissões para resolver `permission_id`.

---

## 18. Fluxo de registro — nova versão

Quando plugin existente recebe nova versão:

```text
Verifica versão duplicada
  ↓
apps.version update
  ↓
app_manifests update
  ↓
app_versions insert
  ↓
app_routes delete by app_id
  ↓
permissions delete by module
  ↓
permissions insert
  ↓
app_routes insert
```

Esse fluxo substitui o contrato estrutural do plugin.

---

## 19. Fluxo de atualização não estrutural

Atualização de manifesto sem nova versão:

```text
Valida manifesto
  ↓
Confere mesmo id
  ↓
Confere mesma version
  ↓
Confere mesmo basePath
  ↓
Confere mesmo conjunto de permissões
  ↓
Confere mesmo conjunto de rotas
  ↓
apps metadata update
  ↓
app_manifests update
  ↓
app_routes update label/icon/order/show_in_menu
```

Tabelas afetadas:

```text
apps
app_manifests
app_routes
```

Tabelas não afetadas:

```text
app_versions
permissions
```

---

## 20. Fluxo de rollback

Rollback para versão histórica:

```text
Busca app
  ↓
Busca app_versions por app_id + version
  ↓
Obtém manifest e checksum
  ↓
apps.version update
  ↓
app_manifests save
  ↓
app_routes delete by app_id
  ↓
permissions delete by module
  ↓
permissions insert do manifesto histórico
  ↓
app_routes insert do manifesto histórico
```

Rollback não cria nova versão histórica.

---

## 21. Fluxo de unregister

Remoção completa de plugin:

```text
Busca plugin
  ↓
Verifica dependentes em app_manifests.manifest.dependencies
  ↓
Se houver dependentes, bloqueia
  ↓
app_versions delete by app_id
  ↓
app_routes delete by app_id
  ↓
permissions delete by module
  ↓
app_manifests delete
  ↓
apps delete
```

A verificação de dependentes percorre manifestos salvos e procura o plugin alvo em `dependencies`.

---

## 22. Relação com favoritos

Favoritos usam `apps.id`.

Tabela:

```text
user_favorite_apps
```

Relacionamento:

```text
user_favorite_apps.app_id → apps.id ON DELETE CASCADE
```

Quando um app é removido, favoritos associados devem ser removidos pelo cascade.

Quando um app é desativado, favoritos podem continuar persistidos, mas não devem aparecer se o app não for retornado como autorizado.

---

## 23. Relação com o Portal

O Portal não lê essas tabelas diretamente.

Fluxo:

```text
Portal chama /me/apps
  ↓
Core API consulta apps, app_routes, permissions e app_manifests
  ↓
Core API filtra por autorização
  ↓
Portal recebe DTO normalizado
```

O DTO contém:

```text
id
name
basePath
icon
type
entryUrl
renderMode
routes[]
```

---

## 24. Relação com o Gateway

`apps.base_path` e `app_routes.path` devem ser coerentes com o Gateway.

Exemplo:

```text
base_path = /apps/dashboard-lmps
route.path = /apps/dashboard-lmps
entry = /apps/dashboard-lmps/assets/remoteEntry.js
```

Se o Gateway não servir esse path, o app pode aparecer no Portal, mas falhar ao carregar.

---

## 25. Constraints e índices relevantes

| Tabela | Constraint/índice | Finalidade |
|---|---|---|
| `apps` | PK `id` | Identidade do plugin |
| `app_manifests` | PK `app_id` | Um manifesto vigente por app |
| `app_versions` | unique `app_id + version` | Impedir versão duplicada |
| `app_versions` | index `app_id` | Listar versões por plugin |
| `permissions` | unique `code` | Impedir permissão duplicada |
| `permissions` | index `module` | Operações por plugin/módulo |
| `app_routes` | FK `app_id` | Rotas por app |
| `app_routes` | FK `permission_id` | Autorização da rota |

---

## 26. Regras de integridade de manifesto no banco

Embora parte das regras seja validada antes de persistir, o banco depende de consistência mantida pela aplicação.

Regras que a aplicação deve garantir:

1. `apps.id` igual a `manifest.id`.
2. `apps.base_path` igual a `manifest.basePath`.
3. `apps.version` igual à versão ativa.
4. `permissions.module` igual a `apps.id`.
5. `app_routes.app_id` igual a `apps.id`.
6. `app_routes.path` começa com `apps.base_path`.
7. `app_routes.permission_id` aponta para permissão declarada pelo plugin, quando aplicável.
8. `app_manifests.manifest` representa o manifesto vigente.
9. `app_versions` preserva snapshots versionados.

---

## 27. Consultas úteis

### 27.1 Apps ativos com rotas

```sql
SELECT a.id, a.name, a.base_path, a.type, r.path, r.label
FROM apps a
JOIN app_routes r ON r.app_id = a.id
WHERE a.active = true
  AND r.active = true;
```

---

### 27.2 Permissões de um plugin

```sql
SELECT code, name, module
FROM permissions
WHERE module = :plugin_id
ORDER BY code;
```

---

### 27.3 Versões de um plugin

```sql
SELECT version, checksum, created_at
FROM app_versions
WHERE app_id = :plugin_id
ORDER BY created_at DESC;
```

---

### 27.4 Manifesto vigente

```sql
SELECT manifest, checksum
FROM app_manifests
WHERE app_id = :plugin_id;
```

---

## 28. Pontos de atenção

1. `apps.id` é string e deve seguir o `id` do manifesto.
2. `app_manifests` armazena apenas o manifesto vigente.
3. `app_versions` armazena histórico, mas update não estrutural não cria versão.
4. `permissions.module` é crítico para lifecycle de plugin.
5. Rotas dependem de permissões já criadas.
6. Rollback remove e recria permissões/rotas.
7. Unregister verifica dependências em manifestos salvos.
8. App registrado pode falhar no Portal se o Gateway não servir seu `entry`.
9. Favoritos podem persistir mesmo se app for desativado, mas não devem aparecer sem autorização.
10. O Portal consome DTO normalizado, não o banco nem o manifesto bruto.

---

## 29. Documentos relacionados

```text
docs/09-banco-de-dados/core-db.md
docs/09-banco-de-dados/modelo-rbac.md
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/06-portal-frontend/consumo-de-plugins.md
```

