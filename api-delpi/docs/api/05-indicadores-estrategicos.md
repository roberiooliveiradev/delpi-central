# 05 — Indicadores Estratégicos (legado / redirecionamento)

> **As rotas deste módulo foram movidas para a API dedicada.**  
> Documentação oficial: **[strategic-indicators-api/docs/](../../strategic-indicators-api/docs/README.md)**

## Base URL atual

```text
/apps/strategic-indicators-api/strategic-indicators
```

Exemplos:

```text
GET /apps/strategic-indicators-api/strategic-indicators/executive-summary?competence=2026-05
GET /apps/strategic-indicators-api/strategic-indicators/trends?competence=2026-05&months=6
GET /apps/strategic-indicators-api/docs
```

A **api-delpi** (`/apps/api-delpi/`) **não** monta mais o prefixo `/strategic-indicators`.

## Ponte dashboard (api-delpi → SI)

Rotas envelope na api-delpi que consomem a Strategic Indicators API (S2S) e devolvem IDD / metas / realizado sem remontar o módulo SI:

| Rota api-delpi | `operationId` | Conteúdo |
|----------------|---------------|----------|
| `GET /dashboard/department-idd` | `get_dashboard_department_idd` | Nota IDD (score) de um departamento |
| `GET /dashboard/department-indicators` | `get_dashboard_department_indicators` | IDD + indicadores com `goals` (metas) e `realized` (realizado) |
| `GET /dashboard/departments-indicators` | `get_dashboard_departments_indicators` | Todos os departamentos com IDD e indicadores aninhados |
| `GET /dashboard/indicators/{indicator_id}/realized` | `get_si_indicator_*_realized` | Valor realizado escalar de um indicador ativo (TV KPI) |
| `GET /dashboard/indicators/{indicator_id}/meta` | `get_si_indicator_*_meta` | Meta comparável escalar do mesmo indicador (TV KPI) |

Query comum: `department_id` (quando aplicável), `competence` (`YYYY-MM`), `start_date` / `end_date`, `branch` (`01`/`02`).

As rotas por indicador são geradas a partir de `app/content/si_indicator_tv_catalog.json` (~32 indicadores ativos → ~64 `operationId`). Payload flat com `value` (shape `scalar`) para o picker «Fontes de dados» da TV. Sync: `scripts/sync_si_indicator_tv_catalog.py --check|--write|--sync-artifacts`.

Integrações SI correspondentes (token interno):

- `/strategic-indicators/integrations/dashboard-department-score`
- `/strategic-indicators/integrations/dashboard-department-indicators`
- `/strategic-indicators/integrations/dashboard-departments-indicators`
- `/strategic-indicators/integrations/dashboard-indicator-realized`
- `/strategic-indicators/integrations/dashboard-indicator-meta`

## Documentação completa do módulo SI

**Índice:** [strategic-indicators-api/docs/README.md](../../strategic-indicators-api/docs/README.md)

Inclui: visão geral, arquitetura, API, banco, fontes de dados, MFE, deploy, desenvolvimento, operação e performance.

## Migrations

Executar apenas via `strategic-indicators-api/scripts/run_migrations.py` — ver [migrations/README.md](../../strategic-indicators-api/migrations/README.md).

O diretório `api-delpi/migrations/plugins/strategic-indicators/` permanece como referência histórica; **não** adicionar novas versões lá.

## Permissões (inalteradas na plataforma)

| Permissão | Uso |
|-----------|-----|
| `strategic-indicators.view` | Painel, departments, indicators, presentation |
| `strategic-indicators.trends.view` | Trends |
| `strategic-indicators.settings.manage` | Settings, admin, metas, change requests |
