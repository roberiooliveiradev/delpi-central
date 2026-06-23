# Manifesto — schema 1.1.0 (plugin e módulo)

> **Status:** especificação (implementação pendente)  
> **Visão:** [plugin-vs-module.md](./plugin-vs-module.md)  
> **Legado:** `schemaVersion: "1.0.0"` permanece suportado

---

## 1. Resumo das mudanças em relação a 1.0.0

| Área | 1.0.0 | 1.1.0 |
|------|-------|-------|
| `schemaVersion` | `"1.0.0"` | `"1.1.0"` |
| `type` | `microfrontend` \| `iframe` \| `backend-only` | + `plugin` \| `module`; legados aceitos |
| `routes[].target` | — | Destino declarativo da rota |
| `routes[].menuGroup` | No schema, não propagado | Propagado até o portal |
| `ui.module` | — | Config do shell (só `type: module`) |
| `dependencies` | Opcional (unregister) | Validação de `composedPlugins` |

---

## 2. `schemaVersion`

```json
{ "schemaVersion": "1.1.0" }
```

O resolvedor deve aceitar **1.0.0** e **1.1.0**. Versões futuras rejeitam até migração explícita.

---

## 3. Campo `type`

### 3.1 Valores

| Valor | Descrição |
|-------|-----------|
| `plugin` | Aplicação UI autônoma |
| `module` | Shell agregador com `routes[].target` |
| `backend-only` | Sem UI (inalterado) |

### 3.2 Aliases (entrada no validador)

| Manifest legado | Normalizado internamente |
|-----------------|--------------------------|
| `microfrontend` | `plugin` |
| `iframe` | `plugin` |

---

## 4. Plugin (`type: "plugin"`)

### 4.1 Obrigatório

- `entry` — `remoteEntry.js` (federated) ou URL raiz (embedded)
- `routes` — ≥ 1 rota
- `permissions` — ≥ 1 permissão
- `ui.renderMode` — `federated` \| `embedded` \| `external`

### 4.2 Exemplo mínimo

```json
{
  "schemaVersion": "1.1.0",
  "id": "dashboard-commercial",
  "name": "Dashboard Comercial",
  "version": "1.0.0",
  "type": "plugin",
  "basePath": "/apps/dashboard-commercial",
  "entry": "/apps/dashboard-commercial/assets/remoteEntry.js",
  "permissions": [
    {
      "code": "dashboard-commercial.view",
      "name": "Acessar dashboard comercial",
      "module": "dashboard-commercial"
    }
  ],
  "routes": [
    {
      "path": "/apps/dashboard-commercial",
      "label": "Comercial",
      "permission": "dashboard-commercial.view",
      "showInMenu": true,
      "order": 20
    }
  ],
  "ui": { "renderMode": "federated" }
}
```

### 4.3 Rotas aninhadas (detalhe OV, etc.)

Rotas adicionais sob `basePath` com `showInMenu: false` — padrão atual dos dashboards. `target` opcional; default implícito `kind: local` (roteamento interno do MFE).

---

## 5. Módulo (`type: "module"`)

### 5.1 Obrigatório

- Tudo de **plugin**, mais:
- `ui.module` — objeto de configuração
- `routes` com pelo menos uma rota `target` ou views locais explícitas

### 5.2 Exemplo — Indicadores Estratégicos (trecho)

```json
{
  "schemaVersion": "1.1.0",
  "id": "strategic-indicators",
  "name": "DELPI Indicadores",
  "version": "1.2.0",
  "type": "module",
  "basePath": "/apps/strategic-indicators",
  "entry": "/apps/strategic-indicators/assets/remoteEntry.js",
  "dependencies": [
    "dashboard-commercial",
    "dashboard-production",
    "dashboard-financial"
  ],
  "permissions": [
    {
      "code": "strategic-indicators.view",
      "name": "Acessar painel estratégico",
      "module": "strategic-indicators"
    },
    {
      "code": "strategic-indicators.departments.view",
      "name": "Visualizar departamentos",
      "module": "strategic-indicators"
    }
  ],
  "ui": {
    "renderMode": "federated",
    "module": {
      "menuStrategy": "tiles",
      "defaultRoute": "/apps/strategic-indicators",
      "composedPlugins": [
        "dashboard-commercial",
        "dashboard-production",
        "dashboard-financial",
        "dashboard-hr",
        "dashboard-quality",
        "dashboard-supplies",
        "dashboard-engineering"
      ]
    }
  },
  "routes": [
    {
      "path": "/apps/strategic-indicators",
      "label": "Painel Estratégico",
      "permission": "strategic-indicators.view",
      "showInMenu": true,
      "order": 10,
      "target": { "kind": "local", "viewId": "executive-dashboard" }
    },
    {
      "path": "/apps/strategic-indicators/departments",
      "label": "Departamentos",
      "permission": "strategic-indicators.departments.view",
      "showInMenu": true,
      "order": 11,
      "menuGroup": "Análise",
      "target": { "kind": "local", "viewId": "departments-overview" }
    },
    {
      "path": "/apps/strategic-indicators/departments/commercial",
      "label": "Comercial",
      "permission": "strategic-indicators.departments.view",
      "showInMenu": false,
      "order": 113,
      "target": {
        "kind": "plugin",
        "appId": "dashboard-commercial",
        "path": "/apps/dashboard-commercial",
        "requiredPermissions": ["dashboard-commercial.view"],
        "preserveQuery": ["branch", "start_date", "end_date"],
        "onDenied": "fallback"
      }
    }
  ]
}
```

### 5.3 Exemplo — Manutenção (trecho)

```json
{
  "schemaVersion": "1.1.0",
  "id": "maintenance",
  "type": "module",
  "basePath": "/apps/maintenance",
  "ui": {
    "renderMode": "federated",
    "module": {
      "menuStrategy": "tiles",
      "defaultRoute": "/apps/maintenance"
    }
  },
  "routes": [
    {
      "path": "/apps/maintenance",
      "label": "Manutenção",
      "permission": "maintenance.view",
      "showInMenu": true,
      "target": { "kind": "local", "viewId": "home" }
    },
    {
      "path": "/apps/maintenance/filial-01/manutencao-geral",
      "permission": "maintenance.manutencao-geral.view.filial-01",
      "showInMenu": false,
      "target": {
        "kind": "iframe",
        "url": "https://script.google.com/macros/s/.../exec",
        "title": "Manutenção geral"
      }
    },
    {
      "path": "/apps/maintenance/mini-aplicadores",
      "permission": "maintenance.mini-applicators.view.filial-01",
      "showInMenu": false,
      "target": { "kind": "local", "viewId": "mini-aplicadores" }
    }
  ]
}
```

---

## 6. `routes[].target` — especificação

### 6.1 Campos comuns

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `kind` | string | `local` \| `plugin` \| `iframe` \| `external` \| `redirect` |
| `onDenied` | string | `fallback` \| `hide` \| `error` (default: `error`) |

### 6.2 `kind: local`

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `viewId` | Sim | Chave no `LocalViewRegistry` do MFE módulo |

### 6.3 `kind: plugin`

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `appId` | Sim | `id` do plugin destino (registrado) |
| `path` | Sim | `basePath` ou rota inicial do destino |
| `requiredPermissions` | Não | Permissões adicionais além da rota |
| `preserveQuery` | Não | Query params repassados na navegação |

**Validação:** `appId` deve existir em `apps`; se `ui.module.composedPlugins` declarado, `appId` deve estar na lista.

### 6.4 `kind: iframe`

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `url` | Sim | URL `https://` |
| `title` | Não | Título acessível do embed |
| `sandbox` | Não | Lista de flags sandbox (opcional) |

### 6.5 `kind: external`

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `url` | Sim | URL `https://` |

### 6.6 `kind: redirect`

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `path` | Sim | Path interno do portal |

---

## 7. `routes[].menuGroup`

String opcional para agrupar entradas no menu/launcher **dentro do mesmo app**.

```json
{
  "path": "/apps/strategic-indicators/trends",
  "label": "Tendências",
  "menuGroup": "Análise",
  "order": 13
}
```

Propagado em `GET /me/apps` → `routes[].menuGroup`.

---

## 8. `routes[].entry` (legado)

Comportamento **inalterado** em 1.1.0:

| `renderMode` | `routes[].entry` |
|--------------|------------------|
| `federated` | Se URL `http(s)://` → `alternateEntry` no MFE (não troca remote) |
| `embedded` / `external` | Override de URL de carregamento |

Preferir `target.kind: iframe` em módulos novos em vez de `entry` http em rotas federated.

---

## 9. Regras de validação (domínio)

| Regra | Erro sugerido |
|-------|---------------|
| `type: module` sem `ui.module` | `module_config_required` |
| `target.appId` não registrado | `target_app_not_found` |
| `target.appId` fora de `composedPlugins` | `target_app_not_composed` |
| Ciclo módulo → módulo → mesmo id | `target_cycle_forbidden` |
| `path` da rota fora de `basePath` | `route_outside_base_path` (existente) |
| `iframe` / `external` sem `https://` | `target_url_invalid` |
| `backend-only` com rotas ou `ui.module` | regras existentes |

---

## 10. Persistência na Core API

### Fase 1 (recomendada)

| Dado | Onde |
|------|------|
| `target`, `menuGroup`, `ui.module` | JSON em `app_manifests.manifest` |
| `path`, `label`, `permission`, `show_in_menu`, `order` | `app_routes` (como hoje) |
| Leitura `/me/apps` | Merge manifest + `app_routes` (como `routes[].entry` hoje) |

### Fase 2 (opcional)

```sql
ALTER TABLE app_routes ADD COLUMN menu_group VARCHAR(100);
ALTER TABLE app_routes ADD COLUMN target_json JSONB;
```

Permite CRUD admin de `target` sem re-register. Ver [core-api-alteracoes.md](./core-api-alteracoes.md).

---

## 11. Update manifest vs nova versão

| Alteração | Via `PUT .../manifest` | Via `POST .../register` (nova versão) |
|-----------|------------------------|--------------------------------------|
| `name`, `description`, `icon` | Sim | Sim |
| `routes[].label/icon/order/showInMenu` | Sim | Sim |
| `routes[].target` | **Não** | Sim |
| `ui.module`, `composedPlugins` | **Não** | Sim |
| `type` plugin → module | **Não** | Sim |
| Novas rotas / paths | **Não** | Sim |

Alinhado a [atualizacao-de-manifesto.md](./atualizacao-de-manifesto.md).

---

## 12. Arquivo JSON Schema (implementação)

Na implementação, estender:

`core-api/app/infrastructure/plugins/schemas/delpi.manifest.schema.json`

- Novo arquivo paralelo `delpi.manifest.schema-1.1.0.json` **ou** `oneOf` por `schemaVersion`
- `ManifestVersionResolver` roteia para o schema correto
