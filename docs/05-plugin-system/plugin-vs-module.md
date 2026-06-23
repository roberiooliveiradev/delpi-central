# Plugin vs Módulo — visão e arquitetura

> **Status:** especificação aprovada para implementação (jun/2026)  
> **Schema alvo:** [manifest-schema-1.1.0.md](./manifest-schema-1.1.0.md)  
> **Roadmap:** [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md)  
> **Compatível com:** manifests `schemaVersion: "1.0.0"` (sem mudança obrigatória)

---

## 1. Objetivo

Separar dois papéis na Minha DELPI:

| Conceito | Papel |
|----------|--------|
| **Plugin** | Aplicação autônoma com UI própria (`remoteEntry`), um domínio, tile no launcher |
| **Módulo** | Shell agregador: catálogo de rotas que aponta para views locais, outros plugins, iframes ou URLs externas |

O padrão informal já existe em **`maintenance`** (tile único no menu, sub-rotas `showInMenu: false`, `App.tsx` + `routeParser`, iframe GAS no código). Esta especificação **formaliza** esse padrão no manifesto, na Core API e no Portal.

**Caso de uso imediato:** `strategic-indicators` — rotas `/departments/{slug}` devem abrir dashboards departamentais (`dashboard-commercial`, etc.) em vez da página interna `DepartmentDetailsPage`.

---

## 2. Taxonomia de tipos no manifesto

### 2.1 Tipos de integração (`type`) — evolução 1.1.0

| `type` (1.1.0) | Descrição | `renderMode` típico |
|----------------|-----------|---------------------|
| **`plugin`** | App federado ou embedded autônomo | `federated` \| `embedded` \| `external` |
| **`module`** | Shell com roteamento declarativo (`routes[].target`) | `federated` |
| **`backend-only`** | Sem UI (inalterado) | — |

### 2.2 Aliases legados (1.0.0)

| `type` legado | Tratado como |
|---------------|--------------|
| `microfrontend` | `plugin` |
| `iframe` | `plugin` (`renderMode: embedded` ou `external`) |

Manifests `1.0.0` **continuam válidos** sem alteração.

### 2.3 O que não confundir

- **`permissions[].module`** — namespace RBAC (igual ao `id` do app). **Não** é o tipo módulo.
- **Submódulo de negócio** (ex.: mini-aplicadores) — rota/view dentro de um **módulo**, não um tipo de manifest.

---

## 3. Responsabilidades por camada

```text
┌─────────────────────────────────────────────────────────────────┐
│ Portal                                                          │
│  · Menu / launcher (rotas showInMenu)                             │
│  · RouteDelegate (target.kind: plugin → navigate ou embed)      │
│  · AppHost (monta remoteEntry do app/módulo dono da URL)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ GET /me/apps
┌───────────────────────────▼─────────────────────────────────────┐
│ Core API                                                        │
│  · Valida manifest 1.1.0 (plugin | module | backend-only)         │
│  · Persiste apps, app_routes, app_manifests, permissions         │
│  · Expõe routes[].target, menuGroup, ui.module                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ register
┌───────────────────────────▼─────────────────────────────────────┐
│ Manifest JSON                                                   │
└───────────────────────────┬─────────────────────────────────────┘
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   Plugin normal        Módulo            backend-only
   (dashboard-*)    (SI, maintenance)    (APIs)
```

| Responsabilidade | Plugin | Módulo |
|------------------|--------|--------|
| KPIs / regras de negócio | Sim | Não (delega) |
| `remoteEntry` próprio | Sim | Sim (shell) |
| Tile no launcher | Sim | Sim (1 entrada) |
| Rotas `showInMenu: false` | Opcional | Comum (deep links) |
| Apontar para outro plugin | Não | Sim (`target.kind: plugin`) |
| Iframe embutido | Pode (embedded) | Sim (`target.kind: iframe`) |
| Backend dedicado | Opcional | Opcional (ex.: SI API) |

---

## 4. Roteamento declarativo — `routes[].target`

Cada rota do módulo (ou plugin, quando aplicável) pode declarar um **destino**:

| `target.kind` | Comportamento |
|---------------|---------------|
| `local` | View React registrada no shell do módulo (`viewId`) |
| `plugin` | Navega ou embute outro plugin (`appId` + `path`) |
| `iframe` | Embute URL (ex.: Google Apps Script — padrão manutenção geral) |
| `external` | Abre em nova aba |
| `redirect` | Redirecionamento HTTP interno (`path` sob o portal) |

Exemplo — SI departamento comercial → dashboard:

```json
{
  "path": "/apps/strategic-indicators/departments/commercial",
  "label": "Comercial",
  "permission": "strategic-indicators.departments.view",
  "showInMenu": false,
  "target": {
    "kind": "plugin",
    "appId": "dashboard-commercial",
    "path": "/apps/dashboard-commercial",
    "requiredPermissions": ["dashboard-commercial.view"],
    "preserveQuery": ["branch", "start_date", "end_date"],
    "onDenied": "fallback"
  }
}
```

Detalhes do schema: [manifest-schema-1.1.0.md](./manifest-schema-1.1.0.md).

---

## 5. Configuração do módulo — `ui.module`

Somente quando `type: "module"`:

```json
{
  "ui": {
    "renderMode": "federated",
    "module": {
      "menuStrategy": "tiles",
      "defaultRoute": "/apps/strategic-indicators",
      "composedPlugins": [
        "dashboard-commercial",
        "dashboard-production",
        "dashboard-financial"
      ]
    }
  },
  "dependencies": [
    "dashboard-commercial",
    "dashboard-production"
  ]
}
```

| Campo | Descrição |
|-------|-----------|
| `menuStrategy` | `tiles` \| `sidebar` \| `mixed` — layout da home do módulo |
| `defaultRoute` | Rota ao abrir o tile do módulo |
| `composedPlugins` | Plugins que o módulo pode referenciar em `target.kind: plugin` |
| `dependencies` | Validação no register; bloqueia unregister se dependente |

---

## 6. Referência: Manutenção (hub informal hoje)

| Aspecto | Implementação atual | Após 1.1.0 |
|---------|---------------------|------------|
| Menu portal | 1 rota `showInMenu: true` | Igual |
| Sub-rotas | Manifest + `routeParser.ts` | Manifest + `routes[].target` |
| Mini-aplicadores | `view: mini-aplicadores` no código | `target: { kind: "local", viewId: "mini-aplicadores" }` |
| Manutenção geral | `ManutencaoGeralPage` + iframe hardcoded | `target: { kind: "iframe", url: "..." }` |
| Filiais | Paths `/filial-XX` no parser | Rotas no manifest com `target` local |

Arquivos de referência:

- `plugins/maintenance/maintenance.manifest.json`
- `plugins/maintenance/src/App.tsx`
- `plugins/maintenance/src/utils/routeParser.ts`

---

## 7. Referência: Indicadores Estratégicos (primeiro módulo com delegate)

| Rota SI | Destino proposto |
|---------|------------------|
| `/apps/strategic-indicators` | `local` → executive dashboard |
| `/apps/strategic-indicators/departments` | `local` → departments overview |
| `/apps/strategic-indicators/departments/commercial` | `plugin` → `dashboard-commercial` |
| `/apps/strategic-indicators/departments/production` | `plugin` → `dashboard-production` |
| `/apps/strategic-indicators/departments/financial` | `plugin` → `dashboard-financial` |
| `/apps/strategic-indicators/departments/hr` | `plugin` → `dashboard-hr` |
| `/apps/strategic-indicators/departments/quality` | `plugin` → `dashboard-quality` |
| `/apps/strategic-indicators/departments/supplies` | `plugin` → `dashboard-supplies` |
| `/apps/strategic-indicators/departments/engineering` | `plugin` → `dashboard-engineering` *(ou `dashboard-lmps` — decisão de produto)* |
| `/apps/strategic-indicators/indicators`, `/trends`, … | `local` (páginas SI atuais) |

---

## 8. Runtime compartilhado

Módulos não devem duplicar parser/iframe/tiles em cada MFE. Pacote canônico:

**[module-runtime.md](./module-runtime.md)** — `@delpi/module-runtime` (caminho TBD: `shared/delpi-module-runtime/`).

Plugins normais **não** dependem desse pacote.

---

## 9. Permissões

| Camada | Permissão |
|--------|-----------|
| Abrir rota no módulo | `routes[].permission` (ex.: `strategic-indicators.departments.view`) |
| Destino plugin | `target.requiredPermissions` (ex.: `dashboard-commercial.view`) |
| Negado | `onDenied`: `fallback` (view local legada), `hide` (some do menu), `error` (mensagem) |

O módulo **não substitui** RBAC dos plugins filhos.

---

## 10. Telemetria (`app-usage`)

Decisão pendente (fechar na Fase 1):

- Registrar abertura no **módulo** pai, no **plugin** filho, ou ambos.
- Recomendação: evento no **plugin efetivamente renderizado** + metadata `delegatedFrom: strategic-indicators`.

---

## 11. Decisões em aberto

| # | Tema | Opções | Recomendação |
|---|------|--------|--------------|
| 1 | Onde executar `target.kind: plugin` | Portal vs só MFE | **Portal** (`RouteDelegate`) |
| 2 | Plugin filho no launcher | Visível / oculto | Manter visível; opcional `ui.displayInLauncher: false` no plugin |
| 3 | `target` no PUT manifest cosmético | Sim / exige re-register | **Exige nova versão** (estrutural) |
| 4 | Engenharia no SI | `dashboard-engineering` / `dashboard-lmps` | Produto |
| 5 | Persistir `target` | Só manifest / coluna `app_routes` | Fase 1: **só manifest**; Fase 2: coluna JSONB |

---

## 12. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [manifest-schema-1.1.0.md](./manifest-schema-1.1.0.md) | Contrato JSON completo |
| [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md) | Fases, arquivos, testes |
| [core-api-alteracoes.md](./core-api-alteracoes.md) | Endpoints, use cases, validação |
| [portal-alteracoes.md](./portal-alteracoes.md) | AppHost, menu, admin |
| [module-runtime.md](./module-runtime.md) | Pacote compartilhado MFE |
| [manifesto-plugin.md](./manifesto-plugin.md) | Contrato 1.0.0 (legado) |
| [../08-plugins/README.md](../08-plugins/README.md) | Inventário plugin vs módulo |
| [../06-portal-frontend/consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md) | Consumo no portal |
