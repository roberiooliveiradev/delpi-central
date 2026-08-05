# Planejamento Orçamentário (MFE)

Microfrontend federado para o ciclo de **Planejamento Orçamentário** — home do exercício, orientações institucionais com confirmação de leitura e área administrativa (exercícios, orientações, escopos).

## Fluxo

```text
Portal → planejamento-orcamentario (remoteEntry.js)
      → /apps/api-delpi/planejamento-orcamentario/*
      → /core-api/me (permissões admin)
      → @delpi/plugin-ui (Module Federation)
```

## Rotas UI

| Rota | Tela |
|------|------|
| `/apps/planejamento-orcamentario` | Home — status do exercício |
| `/apps/planejamento-orcamentario/orientacoes` | Orientações + confirmação de leitura |
| `/apps/planejamento-orcamentario/admin` | Administração (nav) |
| `/apps/planejamento-orcamentario/admin/exercicios` | CRUD de exercícios |
| `/apps/planejamento-orcamentario/admin/orientacoes` | Rascunho/publicação de orientações |
| `/apps/planejamento-orcamentario/admin/escopos` | Escopos + catálogo de CC |

## API consumida

Base: `/apps/api-delpi/planejamento-orcamentario`

| Método | Path |
|--------|------|
| GET | `/context` |
| GET | `/guidance/current` |
| POST | `/guidance/current/acknowledge` |
| GET | `/guidance/current/documents` |
| GET | `/guidance/current/documents/{id}/download` |
| GET/POST/PATCH | `/admin/exercises` … |
| GET/PUT/POST | `/admin/guidance/current` … |
| GET/POST/PATCH | `/admin/scopes` … |
| GET | `/admin/org-catalog/cost-centers` |

Envelope `{ success, data }` — unwrap em `src/api/httpClient.ts`.  
Header: `X-Delpi-Caller-App: planejamento-orcamentario`.

## Permissões (manifest)

- `planejamento-orcamentario.access`
- `planejamento-orcamentario.guidance.view`
- `planejamento-orcamentario.guidance.manage`
- `planejamento-orcamentario.scopes.manage`
- `planejamento-orcamentario.admin`

## Desenvolvimento

```bash
cd plugins/planejamento-orcamentario
npm install
npm run dev          # standalone
npm run test
npm run build
```

Module Federation: `preparePluginUiRemote()` no bootstrap; remotes via `plugins/vite/federation.shared.ts`.  
CSS escopado em `.dashboard-planejamento-orcamentario` — tokens `--delpi-ui-*` mapeados; **zero** CSS de componentes `.delpi-ui-*`.

## Docker

Build context: `plugins/` (ver `Dockerfile`). **Sem** `COPY plugin-ui` — depende do container `delpi-plugin-ui`.

## Registro no portal

```bash
TOKEN=<jwt-admin> ./scripts/register-manifest.sh
```

*(Não executar em produção sem revisar permissões e compose.)*

## Smoke

```bash
curl -I http://localhost/apps/planejamento-orcamentario/assets/remoteEntry.js
```

## Estrutura

```text
src/
  bootstrap.tsx      # mount / updateRoute / unmount
  App.tsx            # roteamento por pathname
  api/               # httpClient + budgetPlanningApi + meApi
  pages/             # Home, Orientações, Admin/*
  components/        # PageShell, uiKit (plugin-ui factories)
  hooks/usePermissions.ts
```
