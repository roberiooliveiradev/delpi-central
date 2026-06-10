# Minha DELPI — Visão geral do Portal

> **Arquivo:** `docs/06-portal-frontend/visao-geral-portal.md`  
> **Status:** documentação oficial  
> **Código:** `portal/`  
> **Stack:** React 19, Vite 7, TypeScript, React Router 7, Keycloak JS 26, Socket.IO client

---

## 1. Papel do Portal

O Portal é o **shell** da Minha DELPI: autentica via Keycloak, consome a **Core API** para identidade e navegação, e renderiza **plugins** (microfrontends e iframes) nas rotas autorizadas.

O Portal **não** calcula permissões efetivas — usa `GET /core-api/me` e `GET /core-api/me/apps` já filtrados pelo backend.

---

## 2. Estrutura do projeto

```text
portal/src/
├── main.tsx                 Bootstrap React
├── ui/
│   ├── App.tsx              Rotas do shell (home, admin, plugins, login)
│   ├── AppHost.tsx          Renderização de plugin (federated / iframe / external)
│   ├── HomePage.tsx
│   ├── LoginPage.tsx
│   ├── MyProfile.tsx
│   └── admin/               Área administrativa (RBAC + apps)
├── state/
│   └── AuthContext.tsx      Sessão Keycloak + carga Core API + Socket.IO
├── data/
│   ├── keycloakClient.ts    Instância Keycloak (check-sso, PKCE)
│   ├── apiClient.ts         HTTP com retry 401 + refresh token
│   ├── coreApi.ts           /me, apps, favoritos, notificações
│   └── adminApi.ts          /admin/rbac/* e /admin/apps/*
├── layout/
│   └── Sidebar.tsx          Menu dinâmico, favoritos, notificações, logo → home
├── tour/                    Descubra o portal (painel, card home, gamificação)
│   ├── PortalTour.tsx
│   └── PortalTourHomeEntry.tsx
├── routes/
│   └── ProtectedRoute.tsx   Guard de rota por permissão (UX)
├── hooks/
│   ├── useSocket.ts
│   ├── useTheme.ts
│   └── useGoogleEmbeddedAppLogin.ts
└── pages/                   Telas nativas do shell (ex.: produtos, health)
```

---

## 3. Fluxo de bootstrap

```text
main.tsx
  ↓
AuthProvider (AuthContext)
  ↓
initKeycloak() — onLoad: check-sso, PKCE S256
  ↓
Se autenticado: token em tokenRef
  ↓
Promise.all paralelo:
  - GET /core-api/me
  - GET /core-api/me/apps  → apps + routes (flatMap)
  - GET /core-api/me/apps/favorites
  - GET /core-api/me/notifications
  - GET /core-api/me/dashboard (opcional)
  ↓
coreLoaded = true → App.tsx renderiza shell
  ↓
useSocket conecta com auth: { token }
```

Arquivo central: `portal/src/state/AuthContext.tsx`.

---

## 4. Rotas do shell (nativas)

Além das rotas vindas de plugins (`routes` do contexto), o Portal define rotas fixas em `App.tsx`:

| Path | Componente | Proteção |
|---|---|---|
| `/login` | `LoginPage` | Público (não autenticado) |
| `/` | `HomePage` | Autenticado |
| `/profile` | `MyProfile` | Autenticado |
| `/admin` | `AdminPage` | `rbac.manage` |
| `/delpi/products` | `ProductsPage` | Autenticado |
| `/delpi/health` | `DelpiHealthPage` | Autenticado |
| `/unauthorized` | `Unauthorized` | — |
| `{route.path}` | `AppHost` | `route.permission` (se definida) |

Cada rota de plugin registrada na Core API vira um `<Route>` dinâmico com `ProtectedRoute` + `AppHost`.

---

## 5. Clientes HTTP

### Core API (`coreApi.ts`)

Base path relativo ao origin do Portal (mesmo host do gateway):

```text
/core-api/me
/core-api/me/apps
/core-api/me/apps/favorites
/core-api/me/notifications
/core-api/me/dashboard
```

### Admin (`adminApi.ts`)

```text
/core-api/admin/apps/*
/core-api/admin/rbac/*
```

### API DELPI (`delpiApi.ts`)

Consultas operacionais diretas ao gateway:

```text
/apps/api-delpi/...
```

Usado por páginas nativas do shell (ex. busca de produtos), não pelo menu de plugins.

---

## 6. Autenticação e token

- **Keycloak:** `portal/src/data/keycloakClient.ts`
- **Refresh:** `keycloak.updateToken(60)` a cada intervalo configurado no `AuthContext`
- **401 nas APIs:** `ApiClient` tenta refresh uma vez; se falhar, `onUnauthorized` → `keycloak.login()`
- **Logout global:** iframes ocultos (`VITE_FRONT_CHANNEL_LOGOUT_URLS`) para apps Google/embed antes do logout Keycloak

Variáveis Vite:

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=          # opcional conforme deploy
VITE_FRONT_CHANNEL_LOGOUT_URLS=  # opcional, CSV de URLs
```

---

## 7. Menu dinâmico

O `Sidebar` agrupa `routes` por `app` (nome e ícone do manifesto), exibe itens com `showInMenu !== false`, ordena por `order`, e integra:

- **App launcher** (grade de apps)
- **Favoritos** (`/me/apps/favorites`)
- **Notificações** (lista + marcar lida)
- Link **Admin** se `user.permissions` incluir `rbac.manage`

Fonte: `AuthContext.routes` derivado de `apps[].routes`.

---

## 8. Plugins (`AppHost`)

| `type` | `renderMode` | Comportamento |
|---|---|---|
| `microfrontend` | `federated` | Dynamic import de `entryUrl` (Module Federation) |
| `iframe` | `embedded` | `<iframe>` + `postMessage` `DELPI_AUTH` / `DELPI_LOGOUT` |
| `iframe` | `external` | Abre URL em nova aba |
| `backend-only` | — | Sem UI; não aparece no menu |

Detalhes: [consumo-de-plugins.md](./consumo-de-plugins.md).

---

## 9. Tempo real (Socket.IO)

- Cliente: `useSocket.ts` — conecta em `/` com `path: /socket.io`
- Autenticação: `socket.auth = { token }` após login
- Eventos escutados: `notification`, `admin.changed`
- O `AuthContext` recarrega apps/RBAC/favoritos quando recebe `admin.changed` relevante

O gateway encaminha `/socket.io/` para o container `core-api`.

---

## 10. Área administrativa

`AdminPage` + abas (`AppsTab`, `RolesTab`, `GroupsTab`, `PermissionsTab`, `RbacTab`) consomem `adminApi.ts`.

Permissões típicas no backend:

| Permissão | Uso |
|---|---|
| `rbac.manage` | Usuários, roles, groups, permissions |
| `apps.view` | Listar apps/plugins |
| `apps.manage` | Registrar manifesto, rotas, rollback |

O Portal só exibe `/admin` com `ProtectedRoute permission="rbac.manage"`; endpoints admin de apps exigem permissões adicionais no backend.

---

## 11. Build e deploy

| Ambiente | Dockerfile | Observação |
|---|---|---|
| Dev | `portal/Dockerfile.dev` | Volume `../portal:/app` |
| Prod | `portal/Dockerfile.prod` | Build estático + nginx interno |

Build args / env de produção: variáveis `VITE_KC_*` embutidas no bundle.

---

## 12. Documentos relacionados

- [autenticacao-frontend.md](./autenticacao-frontend.md)
- [menu-dinamico.md](./menu-dinamico.md)
- [app-authorization.md](./app-authorization.md)
- [favoritos.md](./favoritos.md)
- [consumo-de-plugins.md](./consumo-de-plugins.md)
- [../04-core-api/visao-geral-core-api.md](../04-core-api/visao-geral-core-api.md)
