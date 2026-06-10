# Minha DELPI — Documentação da plataforma

Documentação técnica do monorepo **delpi-central** (produto **Minha DELPI**).

Última revisão alinhada ao código: **jun/2026**.

---

## Comece por aqui

| Ordem | Documento | Para quem |
|---:|---|---|
| 1 | [00-visao-geral/minha-delpi-visao-geral.md](./00-visao-geral/minha-delpi-visao-geral.md) | Visão de produto |
| 2 | [00-visao-geral/mapa-da-plataforma.md](./00-visao-geral/mapa-da-plataforma.md) | Mapa de serviços e links |
| 3 | [00-visao-geral/glossario.md](./00-visao-geral/glossario.md) | Termos |

---

## Índice por pasta

| Pasta | README | Conteúdo principal |
|---|---|---|
| [00-visao-geral/](./00-visao-geral/) | — | Visão, mapa, glossário |
| [01-arquitetura/](./01-arquitetura/) | [README](./01-arquitetura/README.md) | Camadas, fluxos, monorepo |
| [02-infraestrutura/](./02-infraestrutura/) | — | Docker, gateway, env, bancos |
| [03-autenticacao-autorizacao/](./03-autenticacao-autorizacao/) | — | Keycloak, JWT, RBAC |
| [04-core-api/](./04-core-api/) | [README](./04-core-api/README.md) | Governança Flask |
| [05-plugin-system/](./05-plugin-system/) | [README](./05-plugin-system/README.md) | Manifestos |
| [06-portal-frontend/](./06-portal-frontend/) | [README](./06-portal-frontend/README.md) | Portal React |
| [07-api-delpi/](./07-api-delpi/) | [README](./07-api-delpi/README.md) | Visão API operacional |
| [08-plugins/](./08-plugins/) | [README](./08-plugins/README.md) | Inventário plugins |
| [09-banco-de-dados/](./09-banco-de-dados/) | [README](./09-banco-de-dados/README.md) | Schema `postgres-core` |
| [10-guias-operacionais/](./10-guias-operacionais/) | — | Runbooks |
| [11-padroes-de-desenvolvimento/](./11-padroes-de-desenvolvimento/) | [README](./11-padroes-de-desenvolvimento/README.md) | Padrões de código |
| [12-roadmap-e-evolucao/](./12-roadmap-e-evolucao/) | [README](./12-roadmap-e-evolucao/README.md) | Status, pendências |
| [13-auditoria-lgpd/](./13-auditoria-lgpd/) | — | ROPA, relatórios LGPD, rastreamento de uso |

---

## Serviços e APIs (fonte de verdade HTTP)

| Serviço | Documentação de rotas |
|---|---|
| **Core API** | [04-core-api/controllers-e-rotas.md](./04-core-api/controllers-e-rotas.md) |
| **API DELPI** | [api-delpi/docs/api/README.md](../api-delpi/docs/api/README.md) |
| **Minha DELPI AI API** | [minha-delpi-ai-api/docs/api/README.md](../minha-delpi-ai-api/docs/api/README.md) |

---

## Base URL pública (gateway)

| Path | Destino |
|---|---|
| `/` | Portal |
| `/core-api/*` | Core API |
| `/auth/*` | Keycloak |
| `/socket.io/*` | Core API (WebSocket) |
| `/apps/api-delpi/*` | API DELPI |
| `/apps/minha-delpi-ai/api/*` | AI API |
| `/apps/<plugin-id>/*` | Assets MFE |
| `/dash-lmps` | Plugin iframe LMPs |

---

## Infra e operação

| Documento | Conteúdo |
|---|---|
| [subir-ambiente-dev.md](./10-guias-operacionais/subir-ambiente-dev.md) | Stack local |
| [configurar-keycloak.md](./10-guias-operacionais/configurar-keycloak.md) | SSO |
| [troubleshooting.md](./10-guias-operacionais/troubleshooting.md) | Diagnóstico |
| [rastreamento-uso-apps.md](./04-core-api/rastreamento-uso-apps.md) | Uso de apps, api-delpi, LGPD |
| [12-testes-sem-totvs-google-sheets.md](../api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md) | api-delpi sem VPN TOTVS |
| [reset-banco-dev.md](./10-guias-operacionais/reset-banco-dev.md) | Reset DB |
| [registrar-plugin.md](./10-guias-operacionais/registrar-plugin.md) | Plugins |
| [conectar-aplicacao-iframe.md](./10-guias-operacionais/conectar-aplicacao-iframe.md) | Tutorial app iframe + SSO + notificações |
| [docker-compose.md](./02-infraestrutura/docker-compose.md) | Compose |
| [gateway-nginx.md](./02-infraestrutura/gateway-nginx.md) | Nginx |
| [variaveis-de-ambiente.md](./02-infraestrutura/variaveis-de-ambiente.md) | `.env` |

---

## Nomenclatura

- **Minha DELPI** — nome oficial do produto.
- **DELPI Central** — legado (repositório `delpi-central`, client Keycloak `delpi-central`).
- **Plugin LMPs** — `id` **`dash-lmps`** no manifesto (pasta do repo: `plugins/dashboard-lmps`).

---

## Roadmap

- [status-atual.md](./12-roadmap-e-evolucao/status-atual.md)
- [pendencias-tecnicas.md](./12-roadmap-e-evolucao/pendencias-tecnicas.md)
- [decisoes-tecnicas.md](./12-roadmap-e-evolucao/decisoes-tecnicas.md)
