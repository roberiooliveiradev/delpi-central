# Module runtime — pacote compartilhado

> **Status:** especificação (implementação pendente)  
> **Roadmap:** Fase 2 em [roadmap-implementacao-plugin-modulo.md](./roadmap-implementacao-plugin-modulo.md)

---

## 1. Objetivo

Evitar que cada **módulo** (`strategic-indicators`, `maintenance`, …) reimplemente:

- parser de pathname → view
- tiles de home
- embed de iframe
- navegação `pushState` / `popstate`
- integração com props do `AppHost`

Plugins **normais** não dependem deste pacote.

---

## 2. Localização proposta

```
shared/delpi-module-runtime/
  package.json          # @delpi/module-runtime
  src/
    index.ts
    ModuleRuntime.tsx
    ModuleRouter.tsx
    LocalViewRegistry.tsx
    PluginDelegate.tsx
    IframeEmbed.tsx
    TileMenu.tsx
    navigation.ts
    types.ts
  tests/
```

**Alternativa:** `plugins/_shared/module-runtime/` se o monorepo não tiver pasta `shared/` npm workspace ainda.

Consumo nos MFEs:

```json
{
  "dependencies": {
    "@delpi/module-runtime": "workspace:*"
  }
}
```

---

## 3. API pública

### 3.1 `ModuleRuntime`

```tsx
type ModuleRuntimeProps = {
  manifestId: string;
  pathname: string;
  search: string;
  getAccessToken?: () => string | undefined;
  localViews: LocalViewRegistry;
  routes: ManifestRoute[];      // do portal ou manifest
  moduleConfig?: ModuleConfig;
  routeTarget?: RouteTarget;    // rota resolvida atual
};

export function ModuleRuntime(props: ModuleRuntimeProps): JSX.Element;
```

**Responsabilidade:** ponto de entrada no `App.tsx` do módulo; substitui switches manuais como `maintenance/App.tsx` e `strategic-indicators/App.tsx`.

### 3.2 `LocalViewRegistry`

```tsx
type LocalViewComponent = React.ComponentType<LocalViewProps>;

type LocalViewProps = {
  pathname: string;
  search: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (path: string) => void;
};

export function createLocalViewRegistry(
  views: Record<string, LocalViewComponent>
): LocalViewRegistry;
```

### 3.3 `ModuleRouter`

Resolve `pathname` → rota do manifest → `target`:

| `target.kind` | Componente |
|---------------|------------|
| `local` | `localViews[viewId]` |
| `iframe` | `IframeEmbed` |
| `plugin` | `PluginDelegate` (navigate) ou null se portal já delegou |
| `external` | link / window.open |

### 3.4 `IframeEmbed`

Extraído de `plugins/maintenance/src/components/ManutencaoGeralFormEmbed.tsx`:

- loading state
- reload
- integração com shell (voltar, breadcrumb)

### 3.5 `TileMenu`

Home com tiles — padrão `maintenance/HomePage.tsx`:

- lê rotas com `showInMenu` ou config explícita
- agrupa por `menuGroup`
- `onNavigate(path)`

### 3.6 `navigation.ts`

```typescript
export function navigateModule(path: string): void;
export function normalizeModulePath(pathname: string, basePath: string): string;
```

Compatível com `BrowserRouter` do portal (`popstate`).

---

## 4. Integração com AppHost (portal)

O portal monta o remoteEntry do módulo e passa:

```typescript
{
  pathname,
  search,
  getAccessToken,
  basePath,
  routeTarget: resolveRouteTarget(matchedRoute),
  manifestRoutes: app.routes,
  moduleConfig: app.moduleConfig,
}
```

O bootstrap do MFE (`bootstrap.tsx`) repassa para `ModuleRuntime`.

---

## 5. Migração Manutenção

| Antes | Depois |
|-------|--------|
| `parseMaintenancePath` | `ModuleRouter` + manifest `target` |
| `ManutencaoGeralPage` + embed | `target.kind: iframe` |
| `HomePage` tiles | `TileMenu` + rotas manifest |
| `navigateMaintenance` | `navigateModule` |

Manter `routeParser.ts` fino só para **aliases legados** até deprecar paths antigos.

---

## 6. Migração Strategic Indicators

| Antes | Depois |
|-------|--------|
| `App.tsx` if chain | `ModuleRuntime` |
| `DepartmentDetailsPage` para departamentos | `target.kind: plugin` (portal delegate) |
| Views locais | registry: `executive-dashboard`, `departments-overview`, `indicators`, … |

---

## 7. Testes

| Teste | Escopo |
|-------|--------|
| `ModuleRouter` | pathname → componente correto |
| `buildDelegatedPath` | preserveQuery |
| `TileMenu` | render + navigate |
| `IframeEmbed` | smoke render |

Framework: Vitest + React Testing Library (alinhar ao plugin maintenance).

---

## 8. O que não fica no module-runtime

- Lógica de negócio (KPIs, API calls) — fica nas pages de cada módulo
- Module Federation config — cada MFE
- Decisão de permissão global — portal / Core API
- Carregar remoteEntry de **outro** plugin dentro do shell (Fase 1: portal faz `Navigate`; Fase futura: FederationEmbed opcional)

---

## 9. Dependências

- `react`, `react-dom` — peer
- Sem dependência de `react-router-dom` no pacote se navegação for via `history.pushState` (padrão atual dos plugins)
