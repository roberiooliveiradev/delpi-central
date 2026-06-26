# Minha DELPI — Mapa da plataforma

> **Arquivo:** `docs/00-visao-geral/mapa-da-plataforma.md`  
> **Status:** documentação oficial  
> **Índice geral:** [docs/README.md](../README.md)

---

## 1. Componentes

| Componente | Pasta / serviço | Função |
|---|---|---|
| Gateway | `gateway/` | Proxy Nginx, porta 80 |
| Portal | `portal/` | Shell React (login, menu, plugins) |
| Core API | `core-api/` | RBAC, apps, plugins, favoritos, Socket.IO |
| Keycloak | `keycloak` | SSO / JWT |
| API DELPI | `api-delpi/` | TOTVS, métricas, produtos |
| Minha DELPI AI API | `minha-delpi-ai-api/` | Chat, agentes, RAG |
| PostgreSQL Core | `postgres-core` | Governança |
| PostgreSQL Plugins | `postgres-plugins` | Domínios de plugins, RAG (AI API) |
| Ollama | `ollama` | LLM local (dev / chat) |
| Plugins | `plugins/*` | Microfrontends buildados |

---

## 2. Stack Docker (dev)

Serviços em `infra/docker-compose.dev.yml` (principais):

```text
postgres-core, keycloak-db, keycloak
core-api, portal, api-delpi
postgres-plugins
ollama, minha-delpi-ai-api
strategic-indicators, dash-lmps, minha-delpi-chat
gateway
```

Rede: `delpi-network` · Entrada: **gateway:80**

---

## 3. Rotas públicas (gateway)

| Path | Serviço |
|---|---|
| `/` | Portal |
| `/core-api/` | Core API REST |
| `/socket.io/` | Core API WebSocket |
| `/auth/` | Keycloak |
| `/apps/api-delpi/` | API DELPI |
| `/apps/minha-delpi-ai/api/` | AI API |
| `/apps/<id>/assets/` | Plugin (remoteEntry + chunks) |

---

## 4. Fluxo Portal ↔ Core API

```text
Keycloak login
  → token no AuthContext (portal)
  → GET /core-api/me
  → GET /core-api/me/apps  (menu + rotas React)
  → GET /core-api/me/apps/favorites
  → GET /core-api/me/notifications
  → Socket.IO (admin.changed, notification)
  → AppHost renderiza plugin na rota
```

Código: `portal/src/state/AuthContext.tsx`, `portal/src/ui/AppHost.tsx`.

---

## 5. Fluxo administrativo

```text
Admin Portal (/admin)
  → adminApi.ts → /core-api/admin/rbac/*
  → adminApi.ts → /core-api/admin/apps/*
  → Manifesto JSON → POST /admin/apps/register
  → Eventos → Socket → Portal reload()
```

---

## 6. Documentação por área

### Visão e arquitetura

- [minha-delpi-visao-geral.md](./minha-delpi-visao-geral.md)
- [glossario.md](./glossario.md)
- [../01-arquitetura/arquitetura-geral.md](../01-arquitetura/arquitetura-geral.md)

### Portal (atualizado maio/2026)

- [../06-portal-frontend/visao-geral-portal.md](../06-portal-frontend/visao-geral-portal.md)
- [../06-portal-frontend/autenticacao-frontend.md](../06-portal-frontend/autenticacao-frontend.md)
- [../06-portal-frontend/menu-dinamico.md](../06-portal-frontend/menu-dinamico.md)
- [../06-portal-frontend/app-authorization.md](../06-portal-frontend/app-authorization.md)
- [../06-portal-frontend/consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md)
- [../06-portal-frontend/favoritos.md](../06-portal-frontend/favoritos.md)
- [../06-portal-frontend/descubra-o-portal.md](../06-portal-frontend/descubra-o-portal.md)

### Core API

- [../04-core-api/README.md](../04-core-api/README.md) · [controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md) · [visao-geral-core-api.md](../04-core-api/visao-geral-core-api.md)

### Plugins

- [../08-plugins/README.md](../08-plugins/README.md)
- [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md)

### APIs de domínio

- [../07-api-delpi/visao-geral-api-delpi.md](../07-api-delpi/visao-geral-api-delpi.md)
- [../../api-delpi/docs/api/README.md](../../api-delpi/docs/api/README.md)
- [../../minha-delpi-ai-api/docs/api/README.md](../../minha-delpi-ai-api/docs/api/README.md)

### Infra e operação

- [../02-infraestrutura/docker-compose.md](../02-infraestrutura/docker-compose.md)
- [../02-infraestrutura/gateway-nginx.md](../02-infraestrutura/gateway-nginx.md)
- [../02-infraestrutura/variaveis-de-ambiente.md](../02-infraestrutura/variaveis-de-ambiente.md)
- [../09-banco-de-dados/README.md](../09-banco-de-dados/README.md)
- [../10-guias-operacionais/subir-ambiente-dev.md](../10-guias-operacionais/subir-ambiente-dev.md)
- [../10-guias-operacionais/troubleshooting.md](../10-guias-operacionais/troubleshooting.md)

---

## 7. Caminhos de leitura

**Novo no time (frontend):** visão geral → portal → consumo de plugins → autenticação.

**Novo no time (backend governança):** visão geral → core-api visão geral → controllers-e-rotas → RBAC.

**Integração ERP / dashboards:** api-delpi docs → 07-api-delpi visão geral.

**Chat / IA:** minha-delpi-ai-api docs.

---

## 8. Roadmap e pendências

- [../12-roadmap-e-evolucao/status-atual.md](../12-roadmap-e-evolucao/status-atual.md)
- [../12-roadmap-e-evolucao/pendencias-tecnicas.md](../12-roadmap-e-evolucao/pendencias-tecnicas.md)
- [../12-roadmap-e-evolucao/roadmap.md](../12-roadmap-e-evolucao/roadmap.md)

Rotas HTTP canônicas: [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md) e [api-delpi/docs/api/README.md](../../api-delpi/docs/api/README.md).
