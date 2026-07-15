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

MFE com filtros (período, CT, OP, produto), KPIs, série temporal e uma tabela com modos de visualização (por CT, apontamentos, por OP).

## UI (`@delpi/plugin-ui`)

Alinhado ao padrão canônico de [controle-retrabalhos](../controle-retrabalhos/README.md) e tabelas do [dashboard-commercial](../dashboard-commercial/README.md):

- Factories: header, KPI, ChartCard, filtros, `createDashboardDataTableKit`, detalhe e Excel
- **CSS estrutural** de DataTable / Pagination / DetailCard vive em `@delpi/plugin-ui/styles` (`data-table.css`, `pagination.css`, `detail-card.css`) — o MFE só aplica tokens `--delpi-ui-*` e branding
- Filtros auto-aplicados; detalhe da OP em `/apps/production-appointments/{sc|es}/op/:op`
- Ajuda em `src/content/helpTooltips.ts`

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
