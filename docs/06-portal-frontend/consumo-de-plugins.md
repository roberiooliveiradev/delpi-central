# Minha DELPI — Consumo de plugins no Portal

> **Arquivo:** `docs/06-portal-frontend/consumo-de-plugins.md`  
> **Status:** documentação oficial  
> **Implementação:** `portal/src/ui/AppHost.tsx`, `portal/src/ui/App.tsx`

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

---

## 4. Modos de renderização

### 4.1 Microfrontend (`type: microfrontend`, `renderMode: federated`)

1. `import(/* @vite-ignore */ entryUrl)` carrega `remoteEntry.js`
2. Container deve expor `.get()` (Module Federation)
3. Monta módulo exposto (ex. `./App`) em `federatedHostRef`
4. Compartilha escopo via `window.__federation_shared__` quando disponível

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
