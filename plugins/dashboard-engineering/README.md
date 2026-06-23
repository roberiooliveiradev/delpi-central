# Dashboard Engenharia

Microfrontend (Module Federation) para o departamento **Engenharia** no escopo dos Indicadores Estratégicos:

| Indicador | Aba | Fonte |
|-----------|-----|--------|
| % projetos/LMPs no prazo | Visão geral + **LMPs no prazo** | TOTVS Protheus (`GET /engineering/lmps/dashboard`) |
| Ganhos TRANSFORMA+ | Visão geral + **TRANSFORMA+** | Postgres `transformometro` via `api-delpi` |

## Navegação

- `/apps/dashboard-engineering` — visão geral (KPIs + atalhos)
- `/apps/dashboard-engineering/lmp` — gráficos e tabela de LMPs (colunas **Revisão** e **Ciclo** alinhadas à política `work_month_lmp` da api-delpi)
- `/apps/dashboard-engineering/transforma` — ganhos e processos Transforma+

## API (`api-delpi`)

| Recurso | Endpoint |
|---------|----------|
| Dashboard LMP | `GET /engineering/lmps/dashboard` |
| Resumo Transforma+ | `GET /engineering/transforma-mais/processes/summary` |
| Processos | `GET /engineering/transforma-mais/processes` |

Base no gateway: `/apps/api-delpi/engineering`

Datas LMP: query em `YYYYMMDD`. Transforma+: `YYYY-MM-DD`.

### Listagem LMP — revisão e ciclo

A tabela consome os mesmos campos do dashboard LMPs dedicado (`homolog_revision`, `measurement_revision`, `cycle_index`). Quando a mesma OV aparece mais de uma vez no período (reabertura ou nova revisão com trabalho LMP no mês), cada linha traz **Revisão** e **Ciclo** para distinguir os registros. Ver auditoria: `api-delpi/docs/investigation/lmp-2026-rq060-vs-dashboard-auditoria.md` §6.1 e §14.

## Permissão

- `dashboard-engineering.view` (ou `api-delpi.access`)
- Rotas LMP e Transforma+ aceitam também `dashboard-lmps.view` por compatibilidade com o plugin legado

## Desenvolvimento

```bash
cd plugins/dashboard-engineering
npm install
npm run dev
```

## Deploy

```bash
cd infra
docker compose up -d --build dashboard-engineering api-delpi
docker compose restart gateway
```

Registro:

```bash
TOKEN=<jwt> ./plugins/dashboard-engineering/scripts/register-manifest.sh
```
