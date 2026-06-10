# Portal — documentação frontend

> **Código:** `portal/` · **Stack:** React 19, Vite 7, TypeScript, Keycloak JS, Socket.IO

Shell da Minha DELPI: login SSO, menu dinâmico, admin RBAC/apps, carregamento de plugins.

---

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [visao-geral-portal.md](./visao-geral-portal.md) | Estrutura `src/`, bootstrap, rotas |
| [autenticacao-frontend.md](./autenticacao-frontend.md) | Keycloak, PKCE, token, `apiClient` |
| [menu-dinamico.md](./menu-dinamico.md) | `/me/apps`, Sidebar |
| [app-authorization.md](./app-authorization.md) | Guards, permissões na UI |
| [consumo-de-plugins.md](./consumo-de-plugins.md) | AppHost, loading overlay, Module Federation, iframe |
| [favoritos.md](./favoritos.md) | `/me/apps/favorites`, reorder, pin |
| [app-launcher-cards.md](./app-launcher-cards.md) | `AppLauncherCard`, grid, drag na sidebar |
| [portal-tour.md](./portal-tour.md) | Tour gamificado v6, persistência core-api, botão Dica, admin exploradores |
| [playbook-portal-tour-gamificacao.md](./playbook-portal-tour-gamificacao.md) | Roadmap XP, celebrações, conquistas (Fases A–D) |
| [notificacoes.md](./notificacoes.md) | Sino, `/notifications`, preferências |
| [admin-estatisticas.md](./admin-estatisticas.md) | Aba Estatísticas no `/admin` |

---

## APIs consumidas

| Cliente | Base path |
|---|---|
| `coreApi.ts` | `/core-api/me`, favoritos, notificações |
| `adminApi.ts` | `/core-api/admin/rbac/*`, `/core-api/admin/apps/*`, `/admin/statistics` |
| Plugins | `/apps/api-delpi/*`, `/apps/minha-delpi-ai/api/*` |

---

## Relacionados

- [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md)
- [../08-plugins/README.md](../08-plugins/README.md)
- [../03-autenticacao-autorizacao/jwt.md](../03-autenticacao-autorizacao/jwt.md)
