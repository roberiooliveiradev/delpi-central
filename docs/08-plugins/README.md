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

### Classificação plugin vs módulo (planejado)

| Papel | Descrição | Exemplos no monorepo |
|---|---|---|
| **Plugin** | App autônomo, tile no launcher, `remoteEntry` próprio | `dashboard-*`, `minha-delpi-chat`, `eficiencia-fabril`, … |
| **Módulo** | Shell agregador; rotas com `target` para views locais ou outros plugins | `strategic-indicators`, `maintenance` |

Especificação: [../05-plugin-system/plugin-vs-module.md](../05-plugin-system/plugin-vs-module.md) · Roadmap: [../05-plugin-system/roadmap-implementacao-plugin-modulo.md](../05-plugin-system/roadmap-implementacao-plugin-modulo.md).

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

**Legenda `papel`:** `plugin` = autônomo · `módulo` = shell agregador (alvo após manifest 1.1.0) · `—` = avaliar registro.

| Pasta | `id` (manifesto) | Tipo (hoje) | Papel (alvo) | `basePath` | Container Docker (dev) |
|---|---|---|---|---|---|
| `plugins/strategic-indicators` | `strategic-indicators` | microfrontend | **módulo** | `/apps/strategic-indicators` | `delpi-strategic-indicators` |
| `plugins/maintenance` | `maintenance` | microfrontend | **módulo** | `/apps/maintenance` | `delpi-maintenance` |
| `plugins/dashboard-commercial` | `dashboard-commercial` | microfrontend | plugin | `/apps/dashboard-commercial` | `delpi-dashboard-commercial` |
| `plugins/dashboard-production` | `dashboard-production` | microfrontend | plugin | `/apps/dashboard-production` | `delpi-dashboard-production` |
| `plugins/dashboard-financial` | `dashboard-financial` | microfrontend | plugin | `/apps/dashboard-financial` | `delpi-dashboard-financial` |
| `plugins/financeiro-centro-custo` | `financeiro-centro-custo` | microfrontend | plugin | `/apps/financeiro-centro-custo` | `delpi-financeiro-centro-custo` |
| `plugins/dashboard-hr` | `dashboard-hr` | microfrontend | plugin | `/apps/dashboard-hr` | `delpi-dashboard-hr` |
| `plugins/dashboard-supplies` | `dashboard-supplies` | microfrontend | plugin | `/apps/dashboard-supplies` | `delpi-dashboard-supplies` |
| `plugins/dashboard-engineering` | `dashboard-engineering` | microfrontend | plugin | `/apps/dashboard-engineering` | `delpi-dashboard-engineering` |
| `plugins/minha-delpi-chat` | `minha-delpi-chat` | microfrontend | plugin | `/apps/minha-delpi-chat` | `delpi-minha-delpi-chat` |
| `plugins/dashboard-lmps` | `dash-lmps` | iframe | plugin | `/dash-lmps` | `delpi-dashboard-lmps` |
| `plugins/dashboard-quality` | `dashboard-quality` | microfrontend | plugin | `/apps/dashboard-quality` | `delpi-dashboard-quality` |
| `plugins/eficiencia-fabril` | `eficiencia-fabril` | microfrontend | plugin | `/apps/eficiencia-fabril` | `delpi-eficiencia-fabril` |
| `plugins/pedidos-venda-abertos` | `pedidos-venda-abertos` | microfrontend | plugin | `/apps/pedidos-venda-abertos` | `delpi-pedidos-venda-abertos` |
| `plugins/auditoria-5s` | `auditoria-5s` | microfrontend | plugin | `/apps/auditoria-5s` | `delpi-auditoria-5s` |
| `plugins/cadastro-kaizen` | `cadastro-kaizen` | microfrontend | plugin | `/apps/cadastro-kaizen` | `delpi-cadastro-kaizen` |
| `plugins/inspecoes-entrada` | `inspecoes-entrada` | microfrontend | plugin | `/apps/inspecoes-entrada` | `delpi-inspecoes-entrada` |
| `plugins/central-agendamento` | `central-agendamento` | microfrontend | plugin | `/apps/central-agendamento` | `delpi-central-agendamento` |
| `plugins/propostas-comerciais` | (ver manifesto) | microfrontend | plugin | (ver manifesto) | (ver compose) |
| `plugins/cultura-delpi` | (ver manifesto) | microfrontend | plugin | (ver manifesto) | (ver compose) |
| `plugins/transformometro` | (ver manifesto) | microfrontend | plugin | (ver manifesto) | (ver compose) |
| `plugins/helpdesk` | (ver manifesto) | — | — | — | Pode ser externo / legado |
| `plugins/api-delpi-console` | `api-delpi-console` | microfrontend | plugin | `/apps/api-delpi-console` | `delpi-api-delpi-console` |
| `plugins/idd_production` | (ver manifesto) | — | — | — | Avaliar registro na Core API |
| `plugins/tv-dashboard` | `tv-dashboard` | microfrontend | plugin | `/apps/tv-dashboard` | `delpi-tv-dashboard` |
| `plugins/public-hub` | `public-hub` | microfrontend | plugin | `/p/*` (rotas públicas) | `delpi-public-hub` |
| `plugins/tv-dashboard-presentation` | — | biblioteca TS | — | (alias Vite nos MFEs) | — |

**Painéis TV:** gestão em `/apps/tv-dashboard`; apresentação pública em `/p/tv-dashboard/present/{token}` (sem login). API dedicada: `/apps/tv-dashboard-api/*`. Playbook: [../12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md](../12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md).

**Atenção:** o `id` na URL de assets (`/apps/{id}/`) deve coincidir com o sufixo do container `delpi-{id}` no Nginx. Manifestos com `basePath` fora de `/apps/...` ainda precisam de rotas React no Portal compatíveis com o path registrado na Core API.

---

## 3. Backends consumidos pelos plugins

| Plugin | API principal |
|---|---|
| Indicadores Estratégicos | `/apps/strategic-indicators-api/strategic-indicators/*` |
| Dashboard LMPs | `/apps/api-delpi/engineering/lmps/*` |
| Eficiência Fabril | `/apps/api-delpi/production/eficiencia-fabril/*` |
| Dashboard Qualidade | `/apps/api-delpi/quality/*` (Kaizen/5S: **Google Sheets**; PPM/NC: TOTVS) |
| Cadastro de Kaizens | `/apps/api-delpi/quality/kaizens/records` (**PostgreSQL**); importação da planilha via `POST .../import-from-sheet` |
| Inspeções de Entrada | `/apps/api-delpi/inspecoes-entrada/*` (TOTVS views) |
| Minha DELPI Chat | `/apps/minha-delpi-ai/api/*` (não é Core API) |
| Central de Agendamento | `/apps/api-delpi/scheduling/*` |
| Dashboard DELPI | `/apps/api-delpi/products/*` (consultas produto) |
| Despesas por Centro de Custo | `/apps/api-delpi/financeiro/despesas-centro-custo/*` |
| Painéis TV | `/apps/tv-dashboard-api/*` (programações + payload público); agregadores nativos via api-delpi |

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

Implementado em `plugins/*/src/api/httpClient.ts`.

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
| api-delpi-console | `api-delpi-console` |
| eficiencia-fabril | `eficiencia-fabril` |
| central-agendamento | `central-agendamento` |
| cadastro-kaizen | `cadastro-kaizen` |
| inspecoes-entrada | `inspecoes-entrada` |

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
| inspecoes-entrada | `inspecoes-entrada.view`, `inspecoes-entrada.view.filial-01`, `inspecoes-entrada.view.filial-02` |
| cadastro-kaizen | `cadastro-kaizen.view`, `cadastro-kaizen.manage` |

Lista completa: seed + manifestos em `plugins/*/`.

---

## 6. Documentação por plugin

| Plugin | Doc específica |
|---|---|
| Chat / IA | **[API docs](../../minha-delpi-ai-api/docs/README.md)** · [Doc plataforma](./minha-delpi-chat/documentacao-tecnica.md) · [Plugin README](../../plugins/minha-delpi-chat/README.md) · [Status](../12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md) |
| Indicadores | [Documentação SI (completa)](../../strategic-indicators-api/docs/README.md) |
| API operacional | [api-delpi/docs/api/](../../api-delpi/docs/api/README.md) |
| Console API DELPI | [Plugin README](../../plugins/api-delpi-console/README.md) · [Playbook](../../api-delpi/docs/roadmaps/playbook-api-delpi-console.md) |
| Dashboard Qualidade | [plugins/dashboard-quality/docs/ROADMAP.md](../../plugins/dashboard-quality/docs/ROADMAP.md) |
| Central de Agendamento | [Plugin README](../../plugins/central-agendamento/README.md) |
| Cadastro de Kaizens | [Plugin README](../../plugins/cadastro-kaizen/README.md) · [Roadmap](../../docs/12-roadmap-e-volucao/cadastro-kaizen/ROADMAP.md) · [Revisões (spec)](../../docs/12-roadmap-e-volucao/cadastro-kaizen/ESPECIFICACAO-REVISOES.md) · [Doc técnica](../../plugins/cadastro-kaizen/docs/DOCUMENTACAO.md) |
| Inspeções de Entrada | [Plugin README](../../plugins/inspecoes-entrada/README.md) · [Roadmap](../../docs/12-roadmap-e-volucao/inspecoes-entrada/ROADMAP.md) · [Status](../../docs/12-roadmap-e-volucao/inspecoes-entrada/status-atual.md) · [Doc técnica](../../plugins/inspecoes-entrada/docs/DOCUMENTACAO.md) · [API](../../api-delpi/docs/api/inspecoes-entrada.md) |

---

## 7. Criar novo plugin

1. Copiar estrutura de um **plugin** (`dashboard-commercial`, `minha-delpi-chat`) ou de um **módulo** (`maintenance`) conforme o papel desejado — ver [plugin-vs-module.md](../05-plugin-system/plugin-vs-module.md).
2. Definir `delpi.manifest.json` (schema `1.0.0` hoje; `1.1.0` quando a Fase 0 do roadmap estiver em produção).
3. Build → registrar na Core API.
4. Adicionar serviço `delpi-<id>` no `docker-compose.dev.yml`.
5. Validar `remoteEntry.js` via gateway.

Guia operacional: [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md).
