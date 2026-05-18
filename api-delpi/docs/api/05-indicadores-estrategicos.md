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
