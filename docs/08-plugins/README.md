# Minha DELPI — Plugins do monorepo

> **Status:** documentação oficial  
> **Código:** `plugins/`  
> **Registro:** Core API `POST /core-api/admin/apps/register`

---

## 1. Como um plugin entra na plataforma

```text
Manifesto JSON (delpi.manifest.json)
  → POST /core-api/admin/apps/register
  → Core API cria app, permissões, rotas, versão
  → GET /core-api/me/apps (usuários autorizados)
  → Portal monta menu + AppHost
  → Gateway serve /apps/<id>/assets/*
```

Documentação do contrato: [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md).

**CI (build):**

- `./scripts/ci/build-dashboard-quality.sh` — lint + build do plugin Qualidade.
- `./scripts/ci/build-eficiencia-fabril.sh` — lint + build do plugin Eficiência Fabril.
- `./scripts/ci/build-auditoria-5s.sh` — lint + build do plugin Auditoria 5S.
- `./scripts/ci/build-central-agendamento.sh` — lint + build do plugin Central de Agendamento.
- `./scripts/ci/build-pedidos-venda-abertos.sh` — lint + build do plugin Pedidos de Venda em Aberto.

**Homologação:**

- `./scripts/homologacao/check-dashboard-quality.sh` — smoke HTTP (assets + API com `TOKEN`).
- `./scripts/homologacao/check-eficiencia-fabril.sh` — smoke HTTP (`remoteEntry.js` + API `/dashboard`; defina `TOKEN` para validar JWT).
- `./scripts/homologacao/check-auditoria-5s.sh` — smoke HTTP (`remoteEntry.js` + API critérios 5S).
- `./scripts/homologacao/check-central-agendamento.sh` — smoke HTTP (`remoteEntry.js` + API recursos ES).
- `./scripts/homologacao/check-scheduling-api.sh` — homologação **Fase 2** (curl: recurso → reserva → conflito 409 → cancelar; requer `TOKEN` com permissão manage).
- `./scripts/homologacao/check-audit-5s-api.sh` — homologação **Fase 2** (curl: área → auditoria → 48 notas → concluir avaliação; requer `TOKEN`).
- `./scripts/homologacao/check-eficiencia-fabril-fase0.sh` — validação da view TOTVS (container `delpi-api-delpi`).

---

## 2. Inventário no repositório

| Pasta | `id` (manifesto) | Tipo | `basePath` | Container Docker (dev) |
|---|---|---|---|---|
| `plugins/strategic-indicators` | `strategic-indicators` | microfrontend | `/apps/strategic-indicators` | `delpi-strategic-indicators` |
| `plugins/minha-delpi-chat` | `minha-delpi-chat` | microfrontend | `/apps/minha-delpi-chat` | `delpi-minha-delpi-chat` |
| `plugins/dashboard-lmps` | `dash-lmps` | iframe | `/dash-lmps` | `delpi-dashboard-lmps` |
| `plugins/dashboard-quality` | `dashboard-quality` | microfrontend | `/apps/dashboard-quality` | `delpi-dashboard-quality` |
| `plugins/eficiencia-fabril` | `eficiencia-fabril` | microfrontend | `/apps/eficiencia-fabril` | `delpi-eficiencia-fabril` |
| `plugins/pedidos-venda-abertos` | `pedidos-venda-abertos` | microfrontend | `/apps/pedidos-venda-abertos` | `delpi-pedidos-venda-abertos` |
| `plugins/auditoria-5s` | `auditoria-5s` | microfrontend | `/apps/auditoria-5s` | `delpi-auditoria-5s` |
| `plugins/central-agendamento` | `central-agendamento` | microfrontend | `/apps/central-agendamento` | `delpi-central-agendamento` |
| `plugins/dashboard-delpi` | (ver manifesto) | microfrontend | `/apps/dashboard-delpi` | `delpi-dashboard-delpi` |
| `plugins/helpdesk` | (ver manifesto) | — | — | Pode ser externo / legado |
| `plugins/api-delpi-console` | `api-delpi-console` | microfrontend | `/apps/api-delpi-console` | `delpi-api-delpi-console` |
| `plugins/idd_production` | (ver manifesto) | — | — | Avaliar registro na Core API |

**Atenção:** o `id` na URL de assets (`/apps/{id}/`) deve coincidir com o sufixo do container `delpi-{id}` no Nginx. Manifestos com `basePath` fora de `/apps/...` ainda precisam de rotas React no Portal compatíveis com o path registrado na Core API.

---

## 3. Backends consumidos pelos plugins

| Plugin | API principal |
|---|---|
| Indicadores Estratégicos | `/apps/strategic-indicators-api/strategic-indicators/*` |
| Dashboard LMPs | `/apps/api-delpi/engineering/lmps/*` |
| Eficiência Fabril | `/apps/api-delpi/production/eficiencia-fabril/*` |
| Dashboard Qualidade | `/apps/api-delpi/quality/*` (Kaizen/5S: **Google Sheets**; PPM/NC: TOTVS) |
| Minha DELPI Chat | `/apps/minha-delpi-ai/api/*` (não é Core API) |
| Central de Agendamento | `/apps/api-delpi/scheduling/*` |
| Dashboard DELPI | `/apps/api-delpi/products/*` (consultas produto) |

---

## 4. Build e assets

Cada plugin com UI gera build em `dist/` (Vite). O gateway expõe:

```text
GET /apps/<plugin-id>/assets/remoteEntry.js   # sem cache
GET /apps/<plugin-id>/assets/<chunk>.js       # cache longo
```

Module Federation: `renderMode: "federated"` + `entryUrl` apontando para `remoteEntry.js`.

---

## 4.1 Header `X-Delpi-Caller-App` (api-delpi)

Plugins que consomem a **api-delpi** devem identificar sua origem no HTTP client:

```typescript
const DELPI_CALLER_APP = "dashboard-commercial"; // id do manifesto

headers["X-Delpi-Caller-App"] = DELPI_CALLER_APP;
```

Implementado em `plugins/*/src/api/httpClient.ts` (e `dashboard-delpi/src/data/apiClient.ts`).

| Plugin | Valor do header |
|--------|-----------------|
| dashboard-commercial | `dashboard-commercial` |
| dashboard-production | `dashboard-production` |
| dashboard-financial | `dashboard-financial` |
| dashboard-quality | `dashboard-quality` |
| dashboard-supplies | `dashboard-supplies` |
| dashboard-engineering | `dashboard-engineering` |
| dashboard-hr | `dashboard-hr` |
| dashboard-lmps | `dashboard-lmps` |
| dashboard-delpi | `dashboard-delpi` |
| api-delpi-console | `api-delpi-console` |
| eficiencia-fabril | `eficiencia-fabril` |
| central-agendamento | `central-agendamento` |

O middleware da api-delpi repassa o valor à Core API para rastreamento agregado (consentimento `usage_tracking`). Ver [rastreamento-uso-apps.md](../04-core-api/rastreamento-uso-apps.md).

---

## 5. Permissões típicas (exemplos)

Declaradas no manifesto e persistidas na Core API:

| Plugin | Permissões (exemplos) |
|---|---|
| strategic-indicators | `strategic-indicators.view`, `strategic-indicators.settings.manage`, … |
| dash-lmps | `dash-lmps.access` |
| dashboard-quality | `dashboard-quality.view` (+ `api-delpi.quality.access` na API) |
| minha-delpi-chat | `minha-delpi.chat.access`, `minha-delpi.chat.ask`, … |
| central-agendamento | `central-agendamento.view.filial-es|sc`, `central-agendamento.manage.filial-es|sc` |

Lista completa: seed + manifestos em `plugins/*/`.

---

## 6. Documentação por plugin

| Plugin | Doc específica |
|---|---|
| Chat / IA | [Plugin README](../../plugins/minha-delpi-chat/README.md) · [API](../../minha-delpi-ai-api/docs/api/README.md) · [Status](../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md) |
| Indicadores | [Documentação SI (completa)](../../strategic-indicators-api/docs/README.md) |
| API operacional | [api-delpi/docs/api/](../../api-delpi/docs/api/README.md) |
| Console API DELPI | [Plugin README](../../plugins/api-delpi-console/README.md) · [Playbook](../../api-delpi/docs/roadmaps/playbook-api-delpi-console.md) |
| Dashboard Qualidade | [plugins/dashboard-quality/docs/ROADMAP.md](../../plugins/dashboard-quality/docs/ROADMAP.md) |
| Central de Agendamento | [Plugin README](../../plugins/central-agendamento/README.md) |

---

## 7. Criar novo plugin

1. Copiar estrutura de `plugins/strategic-indicators` ou `minha-delpi-chat`.
2. Definir `delpi.manifest.json` (schema `1.0.0`).
3. Build → registrar na Core API.
4. Adicionar serviço `delpi-<id>` no `docker-compose.dev.yml`.
5. Validar `remoteEntry.js` via gateway.

Guia operacional: [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md).
