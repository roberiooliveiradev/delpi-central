# Portal — alterações para plugin e módulo

> **Status:** especificação (implementação pendente)  
> **Roadmap:** [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md)  
> **Estado atual:** [../06-portal-frontend/consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md)

---

## 1. Escopo

Alterações no pacote **`portal/`** para consumir manifests 1.1.0: tipos plugin/módulo, `routes[].target`, `menuGroup`, delegate para outros apps e runtime de módulo.

---

## 2. Estado atual (baseline)

| Comportamento | Onde |
|---------------|------|
| `GET /me/apps` → `AuthContext.apps` | `state/AuthContext.tsx` |
| Rotas federated: wildcard `basePath/*` | `ui/App.tsx` |
| App ativo por prefixo de `basePath` | `ui/AppHost.tsx` |
| Rota ativa: maior prefixo | `ui/appHostEntry.ts` → `resolveMatchingRoute` |
| `routes[].entry` http em federated → `alternateEntry` | `resolveRouteAlternateUrl` |
| Menu por `app.id`, filtra `showInMenu` | `layout/Sidebar.tsx` |
| `menuGroup` | **Não usado** |
| `target` | **Não existe** |

---

## 3. Tipos TypeScript (`src/data/coreApi.ts`)

### 3.1 Novos tipos

```typescript
export type AppType =
  | "plugin"
  | "module"
  | "microfrontend"  // legado
  | "iframe"         // legado
  | "backend-only";

export type RouteTargetKind =
  | "local"
  | "plugin"
  | "iframe"
  | "external"
  | "redirect";

export type RouteTargetOnDenied = "fallback" | "hide" | "error";

export interface RouteTarget {
  kind: RouteTargetKind;
  viewId?: string;
  appId?: string;
  path?: string;
  url?: string;
  title?: string;
  requiredPermissions?: string[];
  preserveQuery?: string[];
  onDenied?: RouteTargetOnDenied;
}

export interface ModuleConfig {
  menuStrategy?: "tiles" | "sidebar" | "mixed";
  defaultRoute?: string;
  composedPlugins?: string[];
}
```

### 3.2 Alterações em interfaces

```typescript
export interface RouteItem {
  // ... existentes
  menuGroup?: string;
  target?: RouteTarget;
}

export interface AppItem {
  type: AppType;
  moduleConfig?: ModuleConfig;
  // entryUrl, renderMode, routes — inalterados
}
```

---

## 4. Resolução de rotas (`ui/appHostEntry.ts`)

### 4.1 Funções novas

| Função | Responsabilidade |
|--------|------------------|
| `normalizeAppType(type)` | `microfrontend`/`iframe` → `plugin` |
| `resolveRouteTarget(route)` | Retorna `route.target` ou `{ kind: "local" }` implícito |
| `resolveDelegatedApp(apps, target)` | Encontra `AppItem` por `target.appId` |
| `buildDelegatedPath(target, search, preserveQuery)` | Monta URL com query |
| `canAccessTarget(target, permissions)` | Checa `requiredPermissions` |

### 4.2 Funções existentes (mantidas)

- `resolveMatchingRoute` — maior prefixo
- `resolveFederationEntry` — sempre `app.entryUrl`
- `resolveRouteAlternateUrl` — legado http em `route.entry`

---

## 5. RouteDelegate (novo componente)

**Arquivo sugerido:** `portal/src/ui/RouteDelegate.tsx`

Inserido em `App.tsx` **antes** ou **dentro** de `AppHost` quando a rota matched tem `target`:

```text
pathname + matching route
  → target.kind === "plugin" && canAccess
      → <Navigate to={delegatedPath} replace />
  → target.kind === "plugin" && !canAccess
      → onDenied: fallback / error UI
  → target.kind === "redirect"
      → <Navigate />
  → demais kinds
      → AppHost (module runtime trata local/iframe)
```

**Importante:** evitar loop A → B → A; validar na Core API e no portal.

---

## 6. AppHost (`ui/AppHost.tsx`)

### 6.1 Props para MFE módulo

```typescript
{
  getAccessToken,
  basePath,
  pathname,
  search,
  routeLabel,
  alternateEntry,      // legado
  routeTarget,         // novo
  manifestRoutes,      // novo — catálogo completo do app
  moduleConfig,        // novo
}
```

### 6.2 Comportamento

| `app.type` normalizado | Ação |
|------------------------|------|
| `plugin` | Comportamento atual |
| `module` | Monta remoteEntry do módulo; passa `routeTarget` para `ModuleRuntime` no MFE |
| `backend-only` | Não monta AppHost |

### 6.3 `target.kind: iframe`

Opção A: `AppHost` renderiza iframe quando `routeTarget.kind === iframe` (sem carregar lógica no MFE).

Opção B: MFE módulo renderiza via `ModuleRuntime`.

**Recomendação Fase 2:** Opção B (paridade Manutenção); Fase 1 POC só `plugin` delegate no portal.

---

## 7. App.tsx — rotas React

### 7.1 Estrutura atual (manter)

- `federatedAppHosts`: `${basePath}/*` → `AppHost`
- `embeddedAppHosts`: idem embedded
- `staticPluginRoutes`: rotas fora do basePath do app federated

### 7.2 Alteração

Envolver `AppHost`:

```tsx
<ProtectedRoute permission={route.permission}>
  <RouteDelegate apps={apps} route={matchedRoute}>
    <AppHost />
  </RouteDelegate>
</ProtectedRoute>
```

Permissão de `target.requiredPermissions`: segunda camada em `RouteDelegate` ou `ProtectedRoute` estendido.

---

## 8. Menu e launcher

### 8.1 Sidebar (`layout/Sidebar.tsx`)

- Agrupar rotas por `menuGroup` (fallback: grupo único por app)
- Ordenar por `order`
- Ocultar rotas com `target.onDenied === "hide"` quando sem permissão de destino

### 8.2 `hooks/useRoutesByApp.ts`

- Sort: `menuGroup` (localeCompare) → `order` → `label`
- Expor `menuGroup` nos itens

### 8.3 `utils/launchableApps.ts`

- Filtrar `backend-only` (inalterado)
- Opcional: ocultar plugins que só aparecem via módulo (`displayInLauncher: false` no manifest)

### 8.4 Componentes

- `components/AppLauncher.tsx`
- `components/AppLauncherCard.tsx`
- `components/SidebarFavoritesList.tsx`
- `ui/HomePage.tsx` — favoritos/recentes

---

## 9. Admin — registro de manifesto

### 9.1 Arquivos

| Arquivo | Alteração |
|---------|-----------|
| `ui/admin/modals/ManifestRegisterModal.tsx` | Tipo plugin/module; editor `target`; `menuGroup` |
| `ui/admin/modals/base/UIBaseFields.tsx` | Seção Module |
| `ui/admin/modals/base/ModuleBaseFields.tsx` | **Novo** |
| `ui/admin/modals/base/RouteTargetFields.tsx` | **Novo** |
| `ui/admin/modals/base/MicrofoentendBaseFields.tsx` | Renomear/alinhar a Plugin |
| `ui/admin/tabs/AppsTab.tsx` | Coluna tipo plugin/module |
| `ui/admin/modals/ManifestRegisterModal_2.tsx` | **Remover** após consolidar |

### 9.2 Validação client-side

- `module` exige `ui.module`
- `target.kind: plugin` exige `appId` + `path`
- `target.kind: iframe` exige `url` https

---

## 10. AuthContext

**Arquivo:** `state/AuthContext.tsx`

Sem mudança de endpoint. Consumir campos novos de `/me/apps` quando Core API Fase 1 estiver pronta.

`derivedRoutes` flatMap — incluir `menuGroup` e `target` em cada item.

---

## 11. Testes

| Tipo | Arquivo | Casos |
|------|---------|-------|
| Unit | `ui/appHostEntry.test.ts` | `resolveRouteTarget`, delegate path, permissions |
| Unit | `ui/RouteDelegate.test.tsx` | Navigate, onDenied |
| E2E | (playwright/cypress se existir) | SI → commercial |

---

## 12. Lista de arquivos

```
portal/src/data/coreApi.ts
portal/src/ui/appHostEntry.ts
portal/src/ui/RouteDelegate.tsx                    (novo)
portal/src/ui/App.tsx
portal/src/ui/AppHost.tsx
portal/src/ui/appHostRouteTransition.ts
portal/src/state/AuthContext.tsx
portal/src/layout/Sidebar.tsx
portal/src/hooks/useRoutesByApp.ts
portal/src/utils/launchableApps.ts
portal/src/components/AppLauncher.tsx
portal/src/components/AppLauncherCard.tsx
portal/src/routes/ProtectedRoute.tsx
portal/src/ui/admin/modals/ManifestRegisterModal.tsx
portal/src/ui/admin/modals/base/ModuleBaseFields.tsx      (novo)
portal/src/ui/admin/modals/base/RouteTargetFields.tsx     (novo)
portal/src/ui/admin/tabs/AppsTab.tsx
```

---

## 13. Documentação a atualizar após implementar

- [../06-portal-frontend/consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md) — wildcard, RouteDelegate, tipos
- [plugin-vs-module.md](./plugin-vs-module.md) — marcar decisões fechadas

---

## 14. Compatibilidade

Portal deployado antes da Core API Fase 1: campos novos ignorados — **sem regressão**.

Portal Fase 1 + Core API legada: `target` ausente — comportamento idêntico ao hoje.
