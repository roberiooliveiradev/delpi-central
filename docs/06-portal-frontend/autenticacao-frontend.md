# Minha DELPI — Autenticação no Portal

> **Arquivo:** `docs/06-portal-frontend/autenticacao-frontend.md`  
> **Status:** documentação oficial  
> **Implementação:** `portal/src/data/keycloakClient.ts`, `portal/src/state/AuthContext.tsx`, `portal/src/data/apiClient.ts`

---

## 1. Princípio

```text
Keycloak autentica  →  JWT no Portal  →  Core API / API DELPI validam e autorizam
```

O Portal usa o access token apenas como credencial. Permissões efetivas vêm de `GET /core-api/me`.

---

## 2. Inicialização Keycloak

```typescript
// keycloakClient.ts
keycloak.init({
  onLoad: "check-sso",
  pkceMethod: "S256",
  checkLoginIframe: true,
});
```

- **check-sso:** tenta restaurar sessão sem redirect agressivo.
- **PKCE:** fluxo público do client SPA (sem client secret no browser).
- `initPromise` singleton evita dupla inicialização.

Variáveis obrigatórias em build:

```env
VITE_KC_URL=        # ex.: https://minhadelpi.com.br/auth
VITE_KC_REALM=
VITE_KC_CLIENT_ID=  # client público do Portal
```

---

## 3. Estados no `AuthContext`

| Estado | Significado |
|---|---|
| `initialized` | Keycloak terminou `init` |
| `isAuthenticated` | Sessão Keycloak ativa |
| `loading` | Carregando identidade |
| `coreLoaded` | `/me` e `/me/apps` concluídos (shell pode renderizar rotas protegidas) |
| `tokenRef` | Access token atual (não exposto em re-render desnecessário) |

Fluxo em `App.tsx`:

1. `!initialized || loading` → `<Loader />`
2. `!isAuthenticated` → apenas `/login`
3. Autenticado → `AppShell` com sidebar e rotas

---

## 4. Envio do token às APIs

`ApiClient` monta:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

Base URL vazia (`""`): endpoints são paths absolutos no mesmo origin do gateway (`/core-api/...`).

Opções do construtor:

```typescript
new ApiClient("", () => tokenRef.current, {
  refreshToken: refreshTokenSilently,  // keycloak.updateToken(60)
  onUnauthorized: handleUnauthorized, // keycloak.login()
});
```

### Tratamento de 401

1. Primeira resposta `401` → chama `refreshTokenSilently()`
2. Se refresh OK → repete a requisição **uma vez**
3. Se ainda falhar → `onUnauthorized` → redirect login Keycloak

---

## 5. Carga pós-login

Função `loadIdentityAndNavigation`:

```typescript
const [me, appsResponse] = await Promise.all([
  coreApi.getMe(),
  coreApi.getApps(),
]);
setRoutes(appsResponse.flatMap((app) => app.routes ?? []));
```

Outras cargas (paralelas após identidade):

- `loadFavoritesData` → `GET /core-api/me/apps/favorites`
- `loadNotificationsData` → `GET /core-api/me/notifications`
- `loadDashboardData` → `GET /core-api/me/dashboard`

Método público `reload()` reexecuta essas cargas (usado após `admin.changed`).

---

## 6. Refresh periódico

Intervalo configurado no `AuthContext` chama `keycloak.updateToken(60)` antes da expiração.

Plugins em iframe recebem token atualizado via `postMessage` (`DELPI_AUTH`) no `AppHost`.

Swagger da API DELPI usa o mesmo contrato (`DELPI_AUTH` / `DELPI_REFRESH_REQUEST`).

---

## 7. Logout

Sequência em `logout()`:

1. `runGlobalFrontChannelLogout()` — iframes para URLs configuradas (RH, controle MP, etc.)
2. `keycloak.logout({ redirectUri })`
3. `clearSessionState()` — zera apps, routes, user, token

URLs padrão embutidas; sobrescrever com:

```env
VITE_FRONT_CHANNEL_LOGOUT_URLS=https://app1/logout,https://app2/logout
```

---

## 8. Socket.IO

Após token válido:

```typescript
socket.auth = { token };
socket.connect();  // path /socket.io → core-api
```

Eventos: `notification`, `admin.changed`.

---

## 9. Segurança — checklist

- Não colocar `client_secret` em variáveis `VITE_*`
- Não usar JWT como única fonte de menu (sempre `/me/apps`)
- `ProtectedRoute` é UX; Core API deve bloquear no servidor
- Evitar token em query string de iframes (usar `postMessage`)

---

## 10. Documentos relacionados

- [visao-geral-portal.md](./visao-geral-portal.md)
- [menu-dinamico.md](./menu-dinamico.md)
- [../03-autenticacao-autorizacao/keycloak-sso.md](../03-autenticacao-autorizacao/keycloak-sso.md)
- [../03-autenticacao-autorizacao/jwt.md](../03-autenticacao-autorizacao/jwt.md)
