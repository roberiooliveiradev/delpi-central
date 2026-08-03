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
| `/apps/reports/{id}` | Editar params, destinatários, acompanhamentos, agenda, enviar agora, histórico |
| `/apps/reports/acompanhamentos` | Lista operacional (rupturas ativas) |
| `/apps/reports/acompanhamentos/{id}` | Acompanhamentos da definição (link do e-mail) |

## API

Base: `/apps/api-delpi/reports`

Doc: `api-delpi/docs/api/delpi-reports.md`

Provider atual: `safety_stock_shortage_30d`.

## Catálogo de providers

| `providerKey` | Nome | Params principais |
|---------------|------|-------------------|
| `safety_stock_shortage_30d` | Rupturas próximos 30 dias | `branch`, `horizonDays` |
| `management_revenue_monthly` | Relatório Gerencial — Faturamento | `customerLimit`, `asOfDate?` |

Playbook gerencial:  
[docs/…/PLAYBOOK-relatorio-gerencial-faturamento.md](../../docs/12-roadmap-e-evolucao/delpi-reports/PLAYBOOK-relatorio-gerencial-faturamento.md)

## Acompanhamentos (Observação)

Na definição, seção **Acompanhamentos**:

- Gravar comentário + previsão opcional por código de produto
- O texto entra na coluna Observação do e-mail (`Acompanhamento (Nome): …`)
- Itens **não** são ocultados do relatório

API: `GET/PUT/DELETE …/definitions/{id}/item-notes`

Testes (passo a passo):  
[docs/…/PLAYBOOK-testes-acompanhamento-observacao.md](../../docs/12-roadmap-e-evolucao/delpi-reports/PLAYBOOK-testes-acompanhamento-observacao.md)

## Agenda

Frequências em `scheduleKind`:

| Valor | UI | Comportamento |
|-------|-----|----------------|
| `daily` | Diário (todos os dias) | Inclui sábado e domingo |
| `weekdays` | Dias úteis (seg–sex) | Pula fim de semana (**não** considera feriados) |
| `weekly` | Semanal | Um dia da semana |
| `monthly` | Mensal (dia do mês) | Default dia 1 — Relatório Gerencial |

## Cron

```bash
./api-delpi/scripts/process-pending-report-schedules.sh
```

## Permissões

`reports.view`, `reports.manage`, **`reports.notes.manage`**, `reports.view.filial-sc/es`, `reports.manage.filial-sc/es`

| Perfil | Permissões | Abas no MFE |
|--------|------------|-------------|
| Operacional (só Observação) | `reports.notes.manage` + `reports.view.filial-*` | **somente** Acompanhamentos |
| Leitura / operação admin | `reports.view` (+ filial se escopo) | Visão geral, Relatórios, Acompanhamentos |
| Admin da definição | `reports.manage` (+ filial) | todas + gravar definição/agenda |

**Não** atribua `reports.view` a quem deve ver só acompanhamentos — essa permissão abre o menu «Delpi Reports» e as abas Visão geral / Relatórios.

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
