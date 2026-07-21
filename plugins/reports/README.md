# Delpi Reports

Plugin para **cadastrar, agendar e enviar relatórios por e-mail** aos colaboradores.

## Fluxo

```text
Portal → /apps/reports (MFE federado)
       → api-delpi /reports/*
       → Postgres schema reports
       → Microsoft Graph (GRAPH_REPORTS_MAIL_SENDER)
```

## Rotas UI

| Path | Uso |
|------|-----|
| `/apps/reports` | Lista de definições |
| `/apps/reports/new` | Criar definição |
| `/apps/reports/{id}` | Editar params, destinatários, agenda, enviar agora, histórico |

## API

Base: `/apps/api-delpi/reports`

Doc: `api-delpi/docs/api/delpi-reports.md`

Provider atual: `safety_stock_shortage_30d`.

## Cron

```bash
./api-delpi/scripts/process-pending-report-schedules.sh
```

## Permissões

`reports.view`, `reports.manage`, `reports.view.filial-sc/es`, `reports.manage.filial-sc/es`

## Dev

```bash
cd plugins/reports && npm install && npm run build

# Compose (dev)
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build reports

# Manifest
TOKEN=... bash plugins/reports/scripts/register-manifest.sh
```

## Roadmap

[docs/12-roadmap-e-evolucao/delpi-reports/](../../docs/12-roadmap-e-evolucao/delpi-reports/)
