# Minha DELPI — Menu dinâmico do Portal

> **Arquivo:** `docs/06-portal-frontend/menu-dinamico.md`  
> **Status:** documentação oficial  
> **Implementação:** `portal/src/layout/Sidebar.tsx`, `portal/src/state/AuthContext.tsx`

---

## 1. Fonte oficial

```http
GET /core-api/me/apps
```

No Portal:

```typescript
const derivedRoutes = appsResponse.flatMap((app) => app.routes ?? []);
setRoutes(derivedRoutes);
```

A Core API já remove apps sem nenhuma rota autorizada (`AppAuthorizationService`).

---

## 2. Agrupamento na Sidebar

O menu agrupa por **app** (`route.app` / metadados `app_name`, `app_icon`):

- Seções expansíveis por aplicativo
- Links `NavLink` para cada `route.path`
- Filtro: `showInMenu !== false`
- Ordenação: `order` ascendente (default 0)

Itens fixos do shell (não vêm de `/me/apps`):

| Item | Path | Condição |
|---|---|---|
| Início | `/` | Sempre |
| Produtos DELPI | `/delpi/products` | Implementação nativa |
| Health DELPI | `/delpi/health` | Implementação nativa |
| Administração | `/admin` | `rbac.manage` em `user.permissions` |
| Perfil | `/profile` | Menu usuário |

---

## 3. App Launcher

Componente `AppLauncher` / `AppLauncherCard`:

- Lista apps de `AuthContext.apps`
- Destaque para **favoritos** e **recentes** (`recentApps` localStorage)
- Navega para `basePath` ou primeira rota do app

---

## 4. Formato de rota (`RouteItem`)

```typescript
interface RouteItem {
  app: string;
  app_name?: string;
  app_icon?: string;
  path: string;
  permission?: string;
  icon?: string;
  label?: string;
  entry?: string;       // override do entryUrl do app
  showInMenu?: boolean;
  order?: number;
}
```

Campos `label` e `icon` na rota sobrescrevem exibição no menu; metadados do app preenchem fallback.

---

## 5. React Router

Cada rota autorizada gera `<Route path={route.path} element={<AppHost />} />`.

Paths devem ser absolutos a partir da raiz do Portal (ex.: `/apps/strategic-indicators` ou `/dash-lmps` para iframe), compatíveis com `basePath` do manifesto.

---

## 6. O que não fazer

- Hardcodar lista completa de plugins no frontend
- Inferir permissões só pelo JWT (usar `user.permissions` de `/me` para UX admin)
- Exibir rotas não retornadas pela API

---

## 7. Documentos relacionados

- [visao-geral-portal.md](./visao-geral-portal.md)
- [consumo-de-plugins.md](./consumo-de-plugins.md)
- [../04-core-api/visao-geral-core-api.md](../04-core-api/visao-geral-core-api.md) (seção `/me/apps`)
