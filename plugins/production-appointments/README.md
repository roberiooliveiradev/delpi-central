# Apontamento de Produção

Plugin id: **`production-appointments`**. Título no portal: **Apontamento de Produção**.

Painel multi-filial (SC/ES) de apontamentos de OP por centro de trabalho (`SH6` → `SH1` → `SHB`).

## Rotas da UI

| Path | Permissão | Filial TOTVS |
|------|-----------|--------------|
| `/apps/production-appointments/sc` | `production-appointments.view.filial-sc` | `01` |
| `/apps/production-appointments/es` | `production-appointments.view.filial-es` | `02` |

Permissão ampla: `production-appointments.view` · acesso ao app: `production-appointments.access`.

## API

Base: `/apps/api-delpi` (gateway). Header: `X-Delpi-Caller-App: production-appointments`.

| Endpoint | Uso |
|----------|-----|
| `GET /production/appointments/work-centers` | Catálogo de CTs |
| `GET /production/appointments/summary` | KPIs + ranking por CT |
| `GET /production/appointments/series` | Série diária |
| `GET /production/appointments` | Lista paginada |
| `GET /production/appointments/by-op` | Agregado por OP |

Doc: [api-delpi/docs/api/production-appointments.md](../../api-delpi/docs/api/production-appointments.md) · Spec: [docs/12-roadmap-e-evolucao/production-appointments/](../../docs/12-roadmap-e-evolucao/production-appointments/).

## Estado desta entrega

MFE com filtros (período, CT, OP, produto), KPIs, série temporal, tabela por CT, lista de apontamentos e agregado por OP.

## UI (`@delpi/plugin-ui`)

Alinhado ao padrão canônico de [controle-retrabalhos](../controle-retrabalhos/README.md):

- `createDashboardPageHeader` / `createSimpleKpiCard` / `ChartCard`
- `createFilterBarShell` + `FilterInputField` / `FilterSelectField`
- `CompactPagination`, `LoadingActivityCard`, empty/error states
- Textos de ajuda em `src/content/helpTooltips.ts` (não no pacote plugin-ui)
- Tokens `--delpi-ui-*` no escopo `.dashboard-production-appointments`

## Dev

```bash
cd plugins/production-appointments
npm install
npm test
npm run build
```

Docker (scripts sequenciais):

```bash
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build production-appointments
```

Registrar o manifesto no portal após o primeiro deploy.
