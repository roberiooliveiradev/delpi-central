# Minha DELPI — Consumo de plugins no Portal

> **Arquivo:** `docs/06-portal-frontend/consumo-de-plugins.md`  
> **Status:** documentação oficial (estado **atual** + evolução planejada)  
> **Implementação:** `portal/src/ui/AppHost.tsx`, `portal/src/ui/App.tsx`  
> **Evolução plugin/módulo:** [../05-plugin-system/portal-alteracoes.md](../05-plugin-system/portal-alteracoes.md)

---

## 0. Estado atual vs planejado (jun/2026)

| Capacidade | Hoje | Planejado (manifest 1.1.0) |
|---|---|---|
| Tipos consumidos | `microfrontend`, `iframe`, `backend-only` | + `plugin`, `module` (aliases legados mantidos) |
| Rotas React | Wildcard `basePath/*` → `AppHost` | Idem + `RouteDelegate` para `target.kind: plugin` |
| `routes[].entry` http em federated | `alternateEntry` (não redirect) | `target` declarativo substitui workaround |
| `menuGroup` | Ignorado | Agrupamento no sidebar |
| `routes[].target` | Não existe | `local` \| `plugin` \| `iframe` \| `external` \| `redirect` |
| Módulos (`type: module`) | Comportam-se como microfrontend | `@delpi/module-runtime` no MFE + props do host |

**POC prioritário:** `strategic-indicators` `/departments/commercial` → navegar para `dashboard-commercial` via `target.kind: plugin`.

---

## 1. Fonte de dados

```http
GET /core-api/me/apps
```

Cada item (`AppItem` em `coreApi.ts`):

| Campo | Uso |
|---|---|
| `id` | Identificador do plugin |
| `name`, `icon` | UI |
| `basePath` | Prefixo de URL do app |
| `type` | `microfrontend` \| `iframe` \| `backend-only` |
| `entryUrl` | URL do remote ou iframe |
| `renderMode` | `federated` \| `embedded` \| `external` |
| `routes[]` | Rotas React registradas dinamicamente |

---

## 2. Registro de rotas React

Em `App.tsx`, para cada `route` em `AuthContext.routes`:

```tsx
<Route
  path={route.path}
  element={
    <ProtectedRoute permission={route.permission}>
      <AppHost />
    </ProtectedRoute>
  }
/>
```

`route.path` deve coincidir com o path servido pelo gateway (ex.: `/apps/strategic-indicators`).

---

## 3. Resolução do app ativo (`AppHost`)

```typescript
apps.find((a) => {
  const base = normalize(a.basePath);
  return pathname === base || pathname.startsWith(base + "/");
});
```

Rota exata dentro do app:

```typescript
app.routes?.find((r) => r.path === location.pathname);
```

**Entry resolvido:** `route.entry` (prioridade) → `app.entryUrl`.

### 3.1 Tela de carregamento (`AppHostLoadingScreen`)

Enquanto iframe ou microfrontend não fica pronto, o host exibe overlay com ícone do app, nome, rota e animação suave.

| Arquivo | Responsabilidade |
|---|---|
| `ui/AppHostLoadingScreen.tsx` / `.css` | UI do loading (gradiente, shimmer, orbes) |
| `ui/useAppHostLoadingOverlay.ts` | Delay ~180ms antes de mostrar; mínimo ~450ms visível; fade ~340ms |
| `ui/AppHost.tsx` | `hostContentReady` — `true` após `iframe.onload` ou `mod.mount()` |

Comportamento:

- Carregamentos rápidos **não** piscam overlay (delay inicial).
- Conteúdo (`iframe` / mount federado) fica `opacity: 0` até pronto; entra com fade ~420ms.
- Troca de app/entry/reload reinicia ciclo via `hostLoadResetKey`.
- Transição entre rotas do mesmo app federado **não** remonta overlay (só `updateRoute`).
- `prefers-reduced-motion`: animações desligadas.

Transição de rota no shell: `appHostRouteTransition.ts` → classe `app-host--route-enter` (fade leve ~480ms).

---

## 4. Modos de renderização

### 4.1 Microfrontend (`type: microfrontend`, `renderMode: federated`)

1. `import(/* @vite-ignore */ entryUrl)` carrega `remoteEntry.js`
2. Container deve expor `.get()` (Module Federation)
3. Monta módulo exposto (ex. `./App`) em `federatedHostRef`
4. O MFE pai registra React no share scope ao inicializar o nested remote `plugin-ui` — **não** pré-semeie React no portal (`__federation_shared__`), senão o remote consome instância diferente da do bundle do MFE (React #321).

Gateway serve:

```text
/apps/<plugin-id>/assets/remoteEntry.js  → container delpi-<plugin-id>
/apps/<plugin-id>/assets/*              → cache longo
```

### 4.2 Iframe embutido (`renderMode: embedded`)

- Renderiza `<iframe src={entry + cacheBust}>`
- Após load, envia `postMessage({ type: "DELPI_AUTH", token }, targetOrigin)` e `DELPI_THEME` (`theme`, `resolved`)
- Reenvia `DELPI_THEME` ao mudar preferência no Sidebar (`DELPI_THEME_CHANGE`) ou `localStorage.theme` em outra aba
- Escuta `DELPI_REFRESH_REQUEST` → `refreshToken()` no Portal
- Apps Google: hook `useGoogleEmbeddedAppLogin` para fluxo de login embutido
- Classe CSS `portal-has-embedded-app` no `body` para layout full-height

### 4.3 Externo (`renderMode: external`)

- `useEffect` redireciona ou abre `window.open(resolvedEntry)` em nova aba
- Não mantém shell visível na rota

### 4.4 Backend-only

- Sem rotas no manifesto → não entra no menu
- Permissões existem para APIs e vínculos entre plugins

---

## 5. Token para plugins

| Canal | Mecanismo |
|---|---|
| Iframe | `postMessage` `DELPI_AUTH`, `DELPI_THEME`, `DELPI_NAVIGATE` (portal → filho); `DELPI_AUTH_READY`, `DELPI_EMBEDDED_ROUTE`, `DELPI_REFRESH_REQUEST` (filho → portal) |
| Microfrontend | Host pode passar token via props/context do remote (contrato do plugin) |
| API direta | Plugin chama `/apps/api-delpi` com `Authorization` próprio |

---

## 6. Recarregar após mudanças administrativas

`AuthContext` escuta `admin.changed` e chama `reload()` quando a entidade afeta menu ou permissões (`plugins`, `routes`, `roles`, etc.).

Se a rota atual deixar de existir após reload, redirecionar para `/` (comportamento recomendado — validar em `AppHost` / navegação).

---

## 7. Apps recentes

`pushRecentApp(app.id)` em `AppHost` persiste apps acessados (localStorage) para o launcher.

---

## 8. Documentos relacionados

- [menu-dinamico.md](./menu-dinamico.md)
- [app-authorization.md](./app-authorization.md)
- [../05-plugin-system/microfrontends.md](../05-plugin-system/microfrontends.md)
- [../05-plugin-system/iframe.md](../05-plugin-system/iframe.md)
- [../05-plugin-system/plugin-vs-module.md](../05-plugin-system/plugin-vs-module.md)
- [../05-plugin-system/portal-alteracoes.md](../05-plugin-system/portal-alteracoes.md)
- [../05-plugin-system/roadmap-implementacao-plugin-modulo.md](../05-plugin-system/roadmap-implementacao-plugin-modulo.md)
