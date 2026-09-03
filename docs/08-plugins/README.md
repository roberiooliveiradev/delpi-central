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
| `plugins/production-control` | `production-control` | microfrontend | **módulo** | `/apps/production-control` | `delpi-production-control` |
| `plugins/financial` | `financial` | microfrontend | **módulo** | `/apps/financial` | `delpi-financial` |
| `plugins/travel-expenses` | `travel-expenses` | microfrontend | plugin | `/apps/travel-expenses` | `delpi-travel-expenses` |
| `plugins/production-pulse` | `production-pulse` | microfrontend | plugin | `/apps/production-pulse` | `delpi-production-pulse` |
| `plugins/dashboard-commercial` | `dashboard-commercial` | microfrontend | plugin | `/apps/dashboard-commercial` | `delpi-dashboard-commercial` |
| `plugins/dashboard-production` | `dashboard-production` | microfrontend | plugin | `/apps/dashboard-production` | `delpi-dashboard-production` |
| `plugins/dashboard-financial` | `dashboard-financial` | microfrontend | plugin | `/apps/dashboard-financial` | `delpi-dashboard-financial` |
| `plugins/financeiro-centro-custo` | `financeiro-centro-custo` | microfrontend | plugin | `/apps/financeiro-centro-custo` | `delpi-financeiro-centro-custo` |
| `plugins/dashboard-hr` | `dashboard-hr` | microfrontend | plugin | `/apps/dashboard-hr` | `delpi-dashboard-hr` |
| `plugins/dashboard-supplies` | `dashboard-supplies` | microfrontend | plugin | `/apps/dashboard-supplies` | `delpi-dashboard-supplies` |
| `plugins/dashboard-engineering` | `dashboard-engineering` | microfrontend | plugin | `/apps/dashboard-engineering` | `delpi-dashboard-engineering` |
| `plugins/minha-delpi-chat` | `minha-delpi-chat` | microfrontend | plugin | `/apps/minha-delpi-chat` | `delpi-minha-delpi-chat` |
| `plugins/dashboard-lmps` | `dashboard-lmps` | microfrontend | plugin | `/apps/dashboard-lmps` | `delpi-dashboard-lmps` |
| `plugins/dashboard-quality` | `dashboard-quality` | microfrontend | plugin | `/apps/dashboard-quality` | `delpi-dashboard-quality` |
| `plugins/eficiencia-fabril` | `eficiencia-fabril` | microfrontend | plugin | `/apps/eficiencia-fabril` | `delpi-eficiencia-fabril` |
| `plugins/pedidos-venda-abertos` | `pedidos-venda-abertos` | microfrontend | plugin | `/apps/pedidos-venda-abertos` | `delpi-pedidos-venda-abertos` |
| `plugins/commercial` | `commercial` | microfrontend | plugin | `/apps/commercial` | `delpi-commercial` |
| `plugins/auditoria-5s` | `auditoria-5s` | microfrontend | plugin | `/apps/auditoria-5s` | `delpi-auditoria-5s` |
| `plugins/kaizometro` | `kaizometro` | microfrontend | plugin | `/apps/kaizometro` | `delpi-kaizometro` |
| `plugins/customer-experience` | `customer-experience` | microfrontend | plugin | `/apps/customer-experience` | `delpi-customer-experience` |
| `plugins/inspecoes-entrada` | `inspecoes-entrada` | microfrontend | plugin | `/apps/inspecoes-entrada` | `delpi-inspecoes-entrada` |
| `plugins/lancamento-notas-fiscais` | `lancamento-notas-fiscais` | microfrontend | plugin | `/apps/lancamento-notas-fiscais` | `delpi-lancamento-notas-fiscais` |
| `plugins/invoice-issuance` | `invoice-issuance` | microfrontend | plugin | `/apps/invoice-issuance` | `delpi-invoice-issuance` |
| `plugins/inspecoes-processo` | `inspecoes-processo` | microfrontend | plugin | `/apps/inspecoes-processo` | `delpi-inspecoes-processo` |
| `plugins/controle-retrabalhos` | `controle-retrabalhos` | microfrontend | plugin | `/apps/controle-retrabalhos` | `delpi-controle-retrabalhos` |
| `plugins/my-requests` | `my-requests` | microfrontend | plugin | `/apps/my-requests` | `delpi-my-requests` |
| `plugins/cipa` | `cipa` | microfrontend | plugin | `/apps/cipa` | `delpi-cipa` |
| `plugins/comite-etica-conduta` | `comite-etica-conduta` | microfrontend | plugin | `/apps/comite-etica-conduta` | `delpi-comite-etica-conduta` |
| `plugins/scrap-monitoring` | `scrap-monitoring` | microfrontend | plugin | `/apps/scrap-monitoring` | `delpi-scrap-monitoring` |
| `plugins/estoque-seguranca` | `estoque-seguranca` | microfrontend | plugin | `/apps/estoque-seguranca` | `delpi-estoque-seguranca` |
| `plugins/materiais-terceiros` | `materiais-terceiros` | microfrontend | plugin | `/apps/materiais-terceiros` | `delpi-materiais-terceiros` |
| `plugins/production-appointments` | `production-appointments` | microfrontend | plugin | `/apps/production-appointments` | `delpi-production-appointments` |
| `plugins/canal-denuncia` | `canal-denuncia` | microfrontend | plugin | `/apps/canal-denuncia` | `delpi-canal-denuncia` |
| `plugins/codigo-etica` | `codigo-etica` | microfrontend | plugin | `/apps/codigo-etica` | `delpi-codigo-etica` |
| `plugins/mural-acessos` | `mural-acessos` | microfrontend | plugin | `/apps/mural-acessos` | `delpi-mural-acessos` |
| `plugins/reports` | `reports` | microfrontend | plugin | `/apps/reports` | `delpi-reports` |
| `plugins/central-agendamento` | `central-agendamento` | microfrontend | plugin | `/apps/central-agendamento` | `delpi-central-agendamento` |
| `plugins/propostas-comerciais` | (ver manifesto) | microfrontend | plugin | (ver manifesto) | (ver compose) |
| `plugins/cultura-delpi` | (ver manifesto) | microfrontend | plugin | (ver manifesto) | (ver compose) |
| `plugins/transformometro` | `transformometro` | microfrontend | plugin | `/apps/transformometro` | `delpi-transformometro` |
| `plugins/helpdesk` | (ver manifesto) | — | — | — | Pode ser externo / legado |
| `plugins/api-delpi-console` | `api-delpi-console` | microfrontend | plugin | `/apps/api-delpi-console` | `delpi-api-delpi-console` |
| `plugins/idd_production` | (ver manifesto) | — | — | — | Avaliar registro na Core API |
| `plugins/tv-dashboard` | `tv-dashboard` | microfrontend | plugin | `/apps/tv-dashboard` | `delpi-tv-dashboard` |
| `plugins/public-hub` | `public-hub` | microfrontend | plugin | `/p/*` (rotas públicas) | `delpi-public-hub` |
| `plugins/tv-dashboard-presentation` | — | biblioteca TS | — | (alias Vite nos MFEs) | — |
| `plugins/plugin-ui` | `plugin-ui` | remote MF + app catálogo | plugin (técnico) | `/apps/plugin-ui` | `delpi-plugin-ui` |
| `plugins/docker/` | — | docs Docker MFE | — | fragmento COPY bib. compartilhadas | — |

**`@delpi/plugin-ui`:** componentes React compartilhados (tooltips, labels, abas), servidos como **remote Module Federation** (`delpi-plugin-ui`). Também registra o app **Catálogo UI** (`./App`, permissão `plugin-ui.view`) para prévia visual. Doc: [plugins/plugin-ui/README.md](../../plugins/plugin-ui/README.md) · MF: [plugins/plugin-ui/docs/module-federation.md](../../plugins/plugin-ui/docs/module-federation.md) · **Novo MFE:** [../05-plugin-system/novo-plugin-mfe-checklist.md](../05-plugin-system/novo-plugin-mfe-checklist.md).

**Bibliotecas compartilhadas no Docker:** manifesto [plugins/shared-libraries.manifest.json](../../plugins/shared-libraries.manifest.json) · gate `scripts/ci/check_plugin_docker_shared_libraries.py`.

**Painéis TV:** gestão em `/apps/tv-dashboard`; apresentação pública em `/p/tv-dashboard/present/{token}` (sem login). API dedicada: `/apps/tv-dashboard-api/*`. Playbook: [../12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md](../12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-EXCELENCIA.md).
**Experiência do Cliente:** admin `/apps/customer-experience`; público `/p/customer-experience/thanks/{token}` e `/form/{token}`. API: `/apps/customer-experience-api/*`. [README do plugin](../../plugins/customer-experience/README.md) · [roadmap](../12-roadmap-e-volucao/customer-experience/).
**Portal PCP:** `/apps/production-control` (gestão à vista + demanda + carga máquina + análise de problemas + materiais). API: `/apps/production-control-api/*`. Destino do módulo: **Portal de Produção**, PCP como primeira área — [recado no roadmap](../12-roadmap-e-evolucao/production-control/README.md). [README do plugin](../../plugins/production-control/README.md) · [API](../../production-control-api/README.md).
**Portal Financeiro:** `/apps/financial` (gestão à vista + faturamento/ROL + inadimplência + despesas por CC + IDD/IGD). API: `/apps/financial-api/*`. Plugins legados permanecem. [README do plugin](../../plugins/financial/README.md) · [API](../../financial-api/README.md) · [spec](../12-roadmap-e-evolucao/financial/README.md).
**Despesas de Viagem:** `/apps/travel-expenses` (prestação, cupons e pacote). API: `/apps/travel-expenses-api/*`. [README](../../plugins/travel-expenses/README.md) · [API](../../travel-expenses-api/README.md) · [playbook](../12-roadmap-e-evolucao/travel-expenses/PLAYBOOK.md).
**Pulso de Produção:** `/apps/production-pulse` (dispositivos IoT + modo operador). API: `/apps/production-pulse-api/*`. [README](../../plugins/production-pulse/README.md) · [API](../../production-pulse-api/README.md) · [roadmap](../12-roadmap-e-evolucao/production-pulse/ROADMAP.md).
**CIPA SIPAT:** admin `/apps/cipa/filial-{01|02}/sipat`; público `/p/cipa/sipat/{token}`. API: `/apps/cipa-api/public/sipat/*`.


**Atenção:** o `id` na URL de assets (`/apps/{id}/`) deve coincidir com o sufixo do container `delpi-{id}` no Nginx. Manifestos com `basePath` fora de `/apps/...` ainda precisam de rotas React no Portal compatíveis com o path registrado na Core API.

---

## 3. Backends consumidos pelos plugins

| Plugin | API principal |
|---|---|
| Indicadores Estratégicos | `/apps/strategic-indicators-api/strategic-indicators/*` |
| Dashboard LMPs | `/apps/api-delpi/engineering/lmps/*` |
| Eficiência Fabril | `/apps/api-delpi/production/eficiencia-fabril/*` |
| Dashboard Qualidade | `/apps/api-delpi/quality/*` (Kaizen/5S: **Google Sheets**; PPM/NC: TOTVS) |
| Kaizômetro | `/apps/api-delpi/quality/kaizens/records` (**PostgreSQL**); importação Sheets; sugestão pública `POST /public/kaizen/suggestions` + form `/p/kaizen/sugestao/aberto` |
| Inspeções de Entrada | `/apps/api-delpi/inspecoes-entrada/*` (TOTVS views) |
| Lançamento de Notas Fiscais | `/apps/api-delpi/lancamento-notas-fiscais/*` (Postgres plugins + SF1/SA2) |
| Emissão de Notas Fiscais | `/apps/api-delpi/invoice-issuance/*` (Postgres plugins + SA1/SA2/SB1/SB2) |
| Inspeções de Processo | `/apps/api-delpi/inspecoes-processo/*` (TOTVS views + auditoria QPR/QP*) |
| Controle de Retrabalhos | `/apps/api-delpi/retrabalhos/*` (TOTVS view BI RT) |
| Estoque de Segurança | `/apps/api-delpi/supplies/safety-stock/*` (TOTVS SBZ/SB2/SC7/SD4/SD3; UI: monitoramento + `/analise-consumo`) — [README](../../plugins/estoque-seguranca/README.md) · [API](../../api-delpi/docs/api/estoque-seguranca.md) |
| Materiais de Terceiros | `/apps/api-delpi/supplies/third-party-materials/*` (TOTVS SB6 / VW_PD3_BENEF_RETORNOS) — [README](../../plugins/materiais-terceiros/README.md) · [API](../../api-delpi/docs/api/materiais-terceiros.md) |
| Portal Comercial | `/apps/commercial-api/*` + `/apps/api-delpi/pedidos-venda-abertos/*`, `/commercial/*`, `/commercial-proposals/*`, `/products/*` e `/production/*` — [README](../../plugins/commercial/README.md) · [wireframes](../12-roadmap-e-evolucao/commercial/WIREFRAMES.md) |
| Minha DELPI Chat | `/apps/minha-delpi-ai/api/*` (não é Core API) |
| Central de Agendamento | `/apps/api-delpi/scheduling/*` |
| Dashboard DELPI | `/apps/api-delpi/products/*` (consultas produto) |
| Despesas por Centro de Custo | `/apps/api-delpi/financeiro/despesas-centro-custo/*` |
| Experiência do Cliente | `/apps/customer-experience-api/*` (participantes + formulários; público por token) |
| Portal PCP | `/apps/production-control-api/*` (subplugins + demanda + carga máquina + análise de problemas + materiais; TOTVS via api-delpi) |
| Portal Financeiro | `/apps/financial-api/*` (subplugins + overview + faturamento + inadimplência + centros de custo + IDD/IGD; TOTVS via api-delpi, SI direto) |
| Despesas de Viagem | `/apps/travel-expenses-api/*` (prestações, cupons, PDF; Postgres plugins) |
| Pulso de Produção | `/apps/production-pulse-api/*` (devices, bindings, readings, poll, operador; Postgres plugins; CT via api-delpi gateway) |
| Painéis TV | `/apps/tv-dashboard-api/*` (programações + payload público); agregadores nativos via api-delpi |
| Transformômetro | `/apps/transformometro-api/transformometro/*` (Postgres; atas + Kimi) — [README](../../plugins/transformometro/README.md) · [atas](../../plugins/transformometro/docs/atas.md) · [Kimi](../../transformometro-api/docs/atas-kimi.md) |
| Comitê de Ética e Conduta | `/apps/comite-etica-conduta-api/*` (Postgres; atas + membros) — [README](../../plugins/comite-etica-conduta/README.md) · [API](../../comite-etica-conduta-api/README.md) · [roadmap](../12-roadmap-e-evolucao/comite-etica-conduta/) |
| CIPA | `/apps/cipa-api/*` (atas, membros, SIPAT); público `/p/cipa/sipat/{token}` — [README](../../plugins/cipa/README.md) · [API](../../cipa-api/README.md) · [playbook](../12-roadmap-e-evolucao/cipa/PLAYBOOK.md) |
| Mural de Acessos | `/apps/api-delpi/mural-acessos/*` + público `/public/mural-acessos/*` — [README](../../plugins/mural-acessos/README.md) · [API](../../api-delpi/docs/api/mural-acessos.md) |

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
| kaizometro | `kaizometro` |
| inspecoes-entrada | `inspecoes-entrada` |
| lancamento-notas-fiscais | `lancamento-notas-fiscais` |
| invoice-issuance | `invoice-issuance` |
| inspecoes-processo | `inspecoes-processo` |
| controle-retrabalhos | `controle-retrabalhos` |
| my-requests | `my-requests` (API: `requests-api`; não chama api-delpi no browser) |
| scrap-monitoring | `scrap-monitoring` |
| estoque-seguranca | `estoque-seguranca` |
| materiais-terceiros | `materiais-terceiros` |
| production-appointments | `production-appointments` |
| canal-denuncia | `canal-denuncia` |
| mural-acessos | `mural-acessos` |
| reports | `reports` |
| commercial | `commercial` |
| financial | `financial` (BFF; não chama api-delpi no browser) |
| travel-expenses | `travel-expenses` (API própria; não chama api-delpi no browser) |

O middleware da api-delpi repassa o valor à Core API para rastreamento agregado (consentimento `usage_tracking`). Ver [rastreamento-uso-apps.md](../04-core-api/rastreamento-uso-apps.md).

---

## 5. Permissões típicas (exemplos)

Declaradas no manifesto e persistidas na Core API:

| Plugin | Permissões (exemplos) |
|---|---|
| strategic-indicators | `strategic-indicators.view`, `strategic-indicators.settings.manage`, … |
| dashboard-lmps | `dashboard-lmps.view`, `dashboard-lmps.nc.write` |
| dashboard-quality | `dashboard-quality.view` (+ `api-delpi.quality.access` na API) |
| minha-delpi-chat | `minha-delpi.chat.access`, `minha-delpi.chat.ask`, … |
| central-agendamento | `central-agendamento.view.filial-es|sc`, `central-agendamento.manage.filial-es|sc`, `central-agendamento.approve.filial-es|sc` |
| inspecoes-entrada | `inspecoes-entrada.view`, `inspecoes-entrada.view.filial-01`, `inspecoes-entrada.view.filial-02` |
| lancamento-notas-fiscais | `lancamento-notas-fiscais.access`, `.create`, `.view`, `.process`, `.manage` |
| invoice-issuance | `invoice-issuance.access`, `.create`, `.view`, `.view.filial-01/02`, `.process`, `.manage` |
| inspecoes-processo | `inspecoes-processo.view`, `inspecoes-processo.view.filial-01`, `inspecoes-processo.view.filial-02` |
| controle-retrabalhos | `controle-retrabalhos.view.filial-sc`, `.view.filial-es`, `.view`, `.access`, `.export` |
| my-requests | `my-requests.access`, `.view-all`, `.manage`, `.view.filial-*`, `.invoice-issuance.create/process`, `.raw-material-creation.create/process` |
| scrap-monitoring | `scrap-monitoring.view.filial-sc`, `.view.filial-es`, `.view`, `.access` |
| estoque-seguranca | `estoque-seguranca.access`, `.view.filial-sc`, `.view.filial-es` |
| materiais-terceiros | `materiais-terceiros.access`, `.view.filial-sc`, `.view.filial-es`, `.export` |
| production-appointments | `production-appointments.view.filial-sc`, `.view.filial-es`, `.view`, `.access` |
| canal-denuncia | `canal-denuncia.access` |
| mural-acessos | `mural-acessos.access`, `mural-acessos.manage` |
| reports | `reports.view`, `reports.manage`, `reports.*.filial-sc/es` |
| kaizometro | `kaizometro.view`, `kaizometro.manage`, `kaizometro.notify-suggestions`, `kaizometro.branch-01`, `kaizometro.branch-02` |
| financial | `financial.access`, `.delinquency.view`, `.cost-centers.view`, `.indicators.view`, `.export`, `.view.filial-01/02` |
| travel-expenses | `travel-expenses.view`, `.write`, `.manage`, `.admin`, `.unit.filial-01/02` |
| production-pulse | `production-pulse.access`, `.devices.view`, `.devices.manage`, `.devices.command`, `.operator`, `.view.filial-01/02`, `.admin` |

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
| Kaizômetro | [Plugin README](../../plugins/kaizometro/README.md) · [Roadmap](../../docs/12-roadmap-e-volucao/kaizometro/ROADMAP.md) · [Revisões (spec)](../../docs/12-roadmap-e-volucao/kaizometro/ESPECIFICACAO-REVISOES.md) · [Doc técnica](../../plugins/kaizometro/docs/DOCUMENTACAO.md) |
| Inspeções de Entrada | [Plugin README](../../plugins/inspecoes-entrada/README.md) · [Roadmap](../../docs/12-roadmap-e-evolucao/inspecoes-entrada/ROADMAP.md) · [Status](../../docs/12-roadmap-e-volucao/inspecoes-entrada/status-atual.md) · [Doc técnica](../../plugins/inspecoes-entrada/docs/DOCUMENTACAO.md) · [API](../../api-delpi/docs/api/inspecoes-entrada.md) |
| Lançamento de Notas Fiscais | [Plugin README](../../plugins/lancamento-notas-fiscais/README.md) · [Playbook](../12-roadmap-e-evolucao/lancamento-notas-fiscais/PLAYBOOK.md) · [Roadmap](../12-roadmap-e-evolucao/lancamento-notas-fiscais/ROADMAP.md) · [API](../../api-delpi/docs/api/lancamento-notas-fiscais.md) |
| Emissão de Notas Fiscais | [Plugin README](../../plugins/invoice-issuance/README.md) · [Playbook](../12-roadmap-e-evolucao/invoice-issuance/PLAYBOOK.md) · [Roadmap](../12-roadmap-e-evolucao/invoice-issuance/ROADMAP.md) · [API](../../api-delpi/docs/api/invoice-issuance.md) |
| Inspeções de Processo | [Plugin README](../../plugins/inspecoes-processo/README.md) · [Auditoria](../../docs/12-roadmap-e-evolucao/inspecoes-processo/ESPECIFICACAO-AUDITORIA-APONTAMENTOS.md) · [API](../../api-delpi/docs/api/inspecoes-processo.md) |
| Controle de Retrabalhos | [Plugin README](../../plugins/controle-retrabalhos/README.md) · [Roadmap](../../docs/12-roadmap-e-evolucao/controle-retrabalhos/README.md) · [API](../../api-delpi/docs/api/controle-retrabalhos.md) |
| Acompanhamento de Refugos | [Plugin README](../../plugins/scrap-monitoring/README.md) · [API](../../api-delpi/docs/api/scrap-monitoring.md) |
| Apontamento de Produção | [Plugin README](../../plugins/production-appointments/README.md) · [API](../../api-delpi/docs/api/production-appointments.md) |
| Canal de Denúncia | [Plugin README](../../plugins/canal-denuncia/README.md) · [API](../../api-delpi/docs/api/canal-denuncia.md) · [público `/p/canal-denuncia/denuncia/aberto`](../../plugins/public-hub/README.md) |
| Código de Ética | [Plugin README](../../plugins/codigo-etica/README.md) · [público `/p/codigo-etica/codigo/aberto`](../../plugins/public-hub/README.md) |
| Mural de Acessos | [Plugin README](../../plugins/mural-acessos/README.md) · [API](../../api-delpi/docs/api/mural-acessos.md) · [público `/p/mural-acessos/menu/{token}`](../../plugins/public-hub/README.md) |
| Delpi Reports | [Plugin README](../../plugins/reports/README.md) · [Roadmap](../12-roadmap-e-evolucao/delpi-reports/README.md) |
| Portal Comercial | [Plugin README](../../plugins/commercial/README.md) · [Wireframes e rotas](../12-roadmap-e-evolucao/commercial/WIREFRAMES.md) · [Perfis e permissões](../12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md) |
| Portal Financeiro | [Plugin README](../../plugins/financial/README.md) · [API](../../financial-api/README.md) · [Spec](../12-roadmap-e-evolucao/financial/README.md) |
| Despesas de Viagem | [Plugin README](../../plugins/travel-expenses/README.md) · [API](../../travel-expenses-api/README.md) · [Playbook](../12-roadmap-e-evolucao/travel-expenses/PLAYBOOK.md) · [Wireframes](../12-roadmap-e-evolucao/travel-expenses/WIREFRAMES.md) |
| Pulso de Produção | [Plugin README](../../plugins/production-pulse/README.md) · [API](../../production-pulse-api/README.md) · [Roadmap](../12-roadmap-e-evolucao/production-pulse/ROADMAP.md) · [Homologação ESP](../12-roadmap-e-evolucao/production-pulse/HOMOLOGACAO-E6-S2.md) · [Wireframes](../12-roadmap-e-evolucao/production-pulse/WIREFRAMES.md) |

---

## 7. Criar novo plugin

### Microfrontend (padrão jul/2026)

Siga o checklist técnico completo: **[../05-plugin-system/novo-plugin-mfe-checklist.md](../05-plugin-system/novo-plugin-mfe-checklist.md)**.

Resumo:

1. Copiar estrutura de **`controle-retrabalhos`** ou **`dashboard-commercial`** (Module Federation + `@delpi/plugin-ui` remote).
2. `vite.config.ts`: `pluginUiRemote()` + `FEDERATION_SHARED_REACT`; `bootstrap.tsx`: `await preparePluginUiRemote()`.
3. Dockerfile: `context: ../plugins`, `COPY vite ./vite` — **sem** `COPY plugin-ui`.
4. Compose: anchor `<<: *plugin-ui-federated` + `container_name: delpi-<id>`.
5. Manifesto `type: microfrontend`, `ui.renderMode: federated`, `entry` → `remoteEntry.js`.
6. Build → registrar na Core API → RBAC.
7. **Documentar** — regra `plugins-documentation.mdc` (README + doc API + entrada neste inventário).
8. Deploy: `./infra/scripts/up-prod-sequential.sh` (fase `remote` → `mfe` → `core`).
9. Validar `remoteEntry.js` do MFE **e** de `plugin-ui` via gateway.

### Outros tipos

- **Módulo** shell: copiar `maintenance` ou `strategic-indicators` — [plugin-vs-module.md](../05-plugin-system/plugin-vs-module.md).
- **iframe** / **backend-only**: ver [microfrontends.md](../05-plugin-system/microfrontends.md) e manifesto.

Guia operacional de registro: [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md).
