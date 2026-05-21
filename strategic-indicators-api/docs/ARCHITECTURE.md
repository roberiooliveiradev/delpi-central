# Arquitetura — Strategic Indicators

**Última atualização:** 2026-05-18

## Visão geral

```text
Portal (shell)
  └── MFE plugins/strategic-indicators
        └── GET /apps/strategic-indicators-api/strategic-indicators/*
              └── strategic-indicators-api (FastAPI, si_app)
                    ├── Postgres plugins (catálogo, metas, settings, period_scores)
                    ├── TOTVS / SQL Server (medições operacionais)
                    ├── Google Sheets (Transforma+, etc.)
                    └── Portal RH (quando aplicável)
```

A **api-delpi** não monta mais o router `/strategic-indicators`. Toda leitura e admin do módulo passam pelo serviço dedicado.

## Componentes

| Componente | Container (dev) | Responsabilidade |
|------------|-----------------|------------------|
| MFE | `delpi-strategic-indicators` | UI React (Module Federation) |
| API SI | `delpi-strategic-indicators-api` | Snapshots, cálculo IGD/IDD, admin |
| Gateway | `delpi-gateway` | Proxy `/apps/strategic-indicators-api/` e `/apps/strategic-indicators/` |
| Postgres plugins | `delpi-postgres-plugins` | Schema `strategic_indicators` |

## Pacote `si_app`

Código derivado da api-delpi, podado para o grafo alcançável a partir de `main.py`:

- `interface/http/routes/strategic_indicators_routes.py` — rotas
- `composition/strategic_indicators_composer.py` — DI
- `application/services/strategic_indicators/` — snapshots, warm-up, cache
- `infrastructure/providers/strategic_indicators/` — coletores TOTVS/Sheets/RH
- `infrastructure/persistence/plugins/repositories/strategic_indicators/` — Postgres

Modelos de snapshot (`StrategicIndicatorsPeriodSnapshot`, etc.) ficam em `strategic_indicators_snapshot_models.py` para evitar import circular com `period_scores_serialization`.

## Fluxo de leitura (painel)

1. **Catálogo estrutural** (Postgres): departamentos, indicadores, pesos.
2. **Metas resolvidas** por competência (`list_resolved_goals_map`); fallback para meta ativa mais recente se o ano da competência não tiver meta cadastrada (`list_latest_active_goals_map`).
3. **Medições** (TOTVS/Sheets/RH) por período — paralelo seguro por departamento e, quando aplicável, por período com `measurements_port_factory`.
4. **Cálculo** (`StrategicIndicatorsCalculator`) → scores, IGD, classificação.
5. **Cache** in-process (TTL) + opcional **`si_period_scores`** (Postgres) para séries em trends.

## Metas em séries históricas

O seed padrão (V009) cadastra metas para o ano corrente (ex.: 2026). Trends com `months=6` podem incluir competências de 2025.

| Comportamento | Descrição |
|---------------|-----------|
| Meta do `goal_year` da competência | Preferência quando existe |
| Fallback | Meta ativa mais recente do indicador (log `si_goal_year_fallback`) |
| Sem meta alguma | Indicador omitido do catálogo resolvido (log `si_goal_missing`) |

Recomendação de negócio: duplicar metas para anos anteriores via admin (`duplicate-year`) em vez de depender só do fallback.

## Cache e invalidação

| Camada | Onde | TTL / notas |
|--------|------|-------------|
| Medições / catálogo in-process | `snapshot_shared_cache.py` | `SI_SNAPSHOT_CACHE_TTL_SECONDS` (default 600s) |
| Coletores (Transforma+, LMP, etc.) | providers | TTL próprio por fonte |
| HTTP leitura | `Cache-Control`, `ETag` | 300s (`si_read_route_support`) |
| `period_scores` | Postgres V010 | Persiste snapshot calculado por competência/escopo |

Mutações em **settings**, **metas** ou estrutura admin chamam `invalidate_strategic_indicators_snapshot_cache()` (limpa cache in-process e apaga `period_scores` + `calculation_snapshots` no Postgres).

## Warm-up

Com `SI_WARMUP_ON_STARTUP=true`, uma thread em background após o boot:

- Executive-summary (competência atual)
- Trends (`SI_WARMUP_TRENDS_MONTHS`, default 6)

Script manual: `scripts/warmup_si_snapshots.py`.

## Paralelismo seguro

```text
SEGURO:
  - 7 departamentos em paralelo dentro de um período
  - N períodos em paralelo COM measurements_port_factory() (instância por thread)

PROIBIDO:
  - N períodos compartilhando o mesmo RealStrategicIndicatorsMeasurementsProvider
```

Detalhes e checklist: [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md).

## Migrations

Runner próprio: `scripts/run_migrations.py`. SQL em `migrations/V001`–`V010`.  
**Não** adicionar novas versões em `api-delpi/migrations/plugins/strategic-indicators/` (apenas referência histórica).
