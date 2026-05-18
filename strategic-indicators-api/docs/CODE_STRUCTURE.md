# Estrutura de código — `si_app`

Pacote Python da API SI, derivado e podado a partir da api-delpi.

## Entrypoint

| Arquivo | Função |
|---------|--------|
| `si_app/main.py` | FastAPI, CORS, JWT middleware, lifespan (migrations + warm-up) |
| `si_app/config.py` | Variáveis de ambiente (`Settings`) |

## Camadas

```text
interface/http/
  routes/strategic_indicators_routes.py   # Rotas HTTP
  si_read_route_support.py              # Log, Cache-Control, ETag, to_json_safe
  schemas/                              # Pydantic (settings, admin)

application/
  use_cases/strategic_indicators/       # Casos de uso (executive, trends, admin…)
  services/strategic_indicators/        # Snapshot, warm-up, cache compartilhado
  services/strategic_indicators/strategic_indicators_snapshot_models.py
  dto/strategic_indicators/             # DTOs e catalog_models

domain/
  services/strategic_indicators_calculator.py
  ports/strategic_indicators/           # Contratos (repos, measurements)

infrastructure/
  persistence/plugins/repositories/strategic_indicators/  # Postgres
  providers/strategic_indicators/         # Coletores TOTVS/Sheets/RH + medições
  cache/ttl_cache.py
  providers/database/                   # Pool TOTVS, Postgres plugins

composition/
  strategic_indicators_composer.py      # DI (factories dos use cases)
  financial_composer.py, commercial_composer.py, …  # Composers departamentais

startup/
  run_migrations_on_startup.py

shared/
  json_encoding.py                      # to_json_safe (Decimal → JSON)
```

## Núcleo do snapshot

1. `StrategicIndicatorsSnapshotService` — orquestra catálogo, medições, cálculo, cache, `period_scores`
2. `RealStrategicIndicatorsMeasurementsProvider` — agrega coletores por departamento
3. `StrategicIndicatorsCalculator` — scores, IGD, classificação
4. `PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository` — catálogo + metas

## Scripts (raiz do serviço)

| Script | Descrição |
|--------|-----------|
| `scripts/run_migrations.py` | Migrations V001–V010 |
| `scripts/warmup_si_snapshots.py` | Warm-up manual |
| `scripts/bench_si_routes.py` | Benchmark rotas de leitura |

## Dependência `shared/`

Pacote monorepo `shared/` (instalado com `pip install -e ./shared[fastapi]`):

- `delpi_auth` — JWT, `@require_permission`

## O que foi removido da api-delpi

Todo o grafo acima **não** deve existir em `api-delpi/app/` após a extração. A api-delpi mantém apenas composers departamentais para rotas `/financial`, `/commercial`, etc., e `application/shared/period_resolution.py` para resolução de competência.
