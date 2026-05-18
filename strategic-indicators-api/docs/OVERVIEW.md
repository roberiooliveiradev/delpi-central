# Visão geral — Indicadores Estratégicos

**Última atualização:** 2026-05-18

## O que é

O módulo **Indicadores Estratégicos (SI)** consolida KPIs departamentais em um painel executivo com:

- **IGD** (índice global da diretoria)
- **IDDs** por departamento (Financeiro, Comercial, Produção, Qualidade, Suprimentos, Engenharia, RH)
- Comparativo mês atual vs anterior
- Tendências históricas (2–12 meses)
- Alertas, modo apresentação e administração de metas

## Componentes no monorepo

| Peça | Repositório / pasta | URL (gateway) |
|------|---------------------|---------------|
| API | `strategic-indicators-api/` (`si_app`) | `/apps/strategic-indicators-api/` |
| Rotas de negócio | prefixo `/strategic-indicators` | `/apps/strategic-indicators-api/strategic-indicators/*` |
| MFE (UI) | `plugins/strategic-indicators/` | `/apps/strategic-indicators/` |
| Postgres | schema `strategic_indicators` em `postgres-plugins` | `PLUGINS_DB_*` |
| Medições operacionais | TOTVS, Google Sheets, Portal RH | via coletores na API |

## O que não é mais a api-delpi

Até a extração do serviço, parte do SI vivia em `api-delpi`. Hoje:

- **Painel SI** → apenas `strategic-indicators-api`
- **api-delpi** → rotas departamentais de **dados diretos** (ex.: `GET /financial/rol`, métricas comercial/produção) para outros consumidores

Documentação legada da api-delpi: [api-delpi/docs/api/05-indicadores-estrategicos.md](../../api-delpi/docs/api/05-indicadores-estrategicos.md) (redireciona para aqui).

## Fluxo do usuário

```text
Portal MinhaDelpi
  → Core API (apps, permissões, menu)
  → Carrega MFE strategic-indicators (Module Federation)
  → JWT no header Authorization
  → GET /apps/strategic-indicators-api/strategic-indicators/executive-summary?competence=2026-05
  → API monta snapshot (Postgres + TOTVS/Sheets/RH)
  → UI renderiza IGD, departamentos, prefetch trends
```

## Conceitos de domínio

| Termo | Significado |
|-------|-------------|
| **Competência** | Mês de referência `YYYY-MM` (ex.: `2026-05`) |
| **Visão consolidada** | Todas as filiais agregadas (`branch` omitido) |
| **Visão por filial** | `branch=01`, `02`, … |
| **Catálogo estrutural** | Departamentos, indicadores, pesos (Postgres) |
| **Meta resolvida** | Meta ativa do indicador para o ano da competência |
| **Snapshot** | Medições + cálculo de scores + IGD para um período |
| **period_scores** | Snapshot persistido no Postgres para séries (trends) |

## Permissões (Core API / manifesto)

Declaradas em `plugins/strategic-indicators/strategic-indicators.manifest.json`:

| Código | Uso |
|--------|-----|
| `strategic-indicators.view` | Painel executivo |
| `strategic-indicators.departments.view` | Departamentos e sub-rotas |
| `strategic-indicators.indicators.view` | Lista de indicadores |
| `strategic-indicators.trends.view` | Tendências |
| `strategic-indicators.alerts.view` | Alertas |
| `strategic-indicators.presentation.view` | Modo apresentação |
| `strategic-indicators.settings.manage` | Settings, admin, metas, change requests |

## Documentação relacionada

| Doc | Tópico |
|-----|--------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Diagramas, cache, paralelismo |
| [API.md](./API.md) | Referência HTTP completa |
| [DATABASE.md](./DATABASE.md) | Schema Postgres |
| [DATA_SOURCES.md](./DATA_SOURCES.md) | TOTVS, planilhas, RH |
| [MFE.md](./MFE.md) | Plugin React |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Docker, env, produção |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Dev local |
| [OPERATIONS.md](./OPERATIONS.md) | Logs, warm-up, bench |
| [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md) | Performance |
