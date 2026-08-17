# Planejamento Orçamentário (MFE)

Microfrontend federado para o ciclo de **Planejamento Orçamentário** (V1.1): exercício, orientações com aceite, **elaboração unificada por centro de custo** (CAPEX + Pessoal na mesma tela), **aprovação CAPEX por investimento**, filas e consolidação, e administração.

## Playbook operacional (usuários)

Guia completo de fluxos, papéis, telas e FAQ:

[`docs/12-roadmap-e-evolucao/planejamento-orcamentario/35-playbook-usuario-v1.md`](../../docs/12-roadmap-e-evolucao/planejamento-orcamentario/35-playbook-usuario-v1.md)

Release V1: [`34-release-primeira-versao.md`](../../docs/12-roadmap-e-evolucao/planejamento-orcamentario/34-release-primeira-versao.md)

## Fluxo técnico

```text
Portal → planejamento-orcamentario (remoteEntry.js)
      → /apps/api-delpi/planejamento-orcamentario/*
      → /core-api/me (permissões)
      → @delpi/plugin-ui (Module Federation)
```

## Rotas UI (principais)

| Rota | Tela |
|------|------|
| `/apps/planejamento-orcamentario` | Home |
| `…/orientacoes` | Orientações + aceite |
| `…/gestao-aprovacoes` | Cockpit da diretoria (KPIs + CC) |
| `…/centros` | Orçamento por centro (lista + CAPEX/Pessoal) |
| `…/capex` e `…/pessoal` | Alias → `…/centros` |
| `…/capex/aprovacoes` | Fila CAPEX (avançada) |
| `…/capex/consolidacao` | Consolidação / Excel |
| `…/pessoal/aprovacoes` | Fila Pessoal (avançada) |
| `…/admin` | Administração |

Detalhe das aprovações e formulários de investimento ficam **fora do menu** (só via navegação interna).

## API consumida

Base: `/apps/api-delpi/planejamento-orcamentario`

Envelope `{ success, data }` — unwrap em `src/api/httpClient.ts`.  
Header: `X-Delpi-Caller-App: planejamento-orcamentario`.

Contratos e casos de uso: ver docs das fases 1–3C e o playbook §18.

## Permissões (manifest 0.4.0)

`access`, `guidance.view|manage`, `scopes.manage`, `admin`, `capex.submit|approve|consolidation.view|export`, `personnel.view|edit|submit|approve`.

Lista e agrupamento por perfil: playbook §3 e release §10.

## Desenvolvimento

```bash
cd plugins/planejamento-orcamentario
npm install
npm run dev
npm run test
npm run build
```

Module Federation: `preparePluginUiRemote()` no bootstrap.  
CSS escopado em `.dashboard-planejamento-orcamentario` — **zero** CSS de componentes `.delpi-ui-*`.

## Docker

Build context: `plugins/` (ver `Dockerfile`). Depende do remote `delpi-plugin-ui`.

## Registro no portal

```bash
TOKEN=<jwt-admin> ./scripts/register-manifest.sh
```

*(Importação manual preferida em produção — ver playbook e release.)*

## Smoke

```bash
curl -I http://127.0.0.1:9080/apps/planejamento-orcamentario/assets/remoteEntry.js
```

## Estrutura

```text
src/
  bootstrap.tsx
  App.tsx
  api/
  pages/          # Home, Orientações, CAPEX, Pessoal, Admin
  components/     # PageShell, workflow panels, uiKit
  hooks/
  utils/
```
