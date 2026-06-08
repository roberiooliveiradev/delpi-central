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
  gateways/delpi_*_gateway.py             # Adapters HTTP para api-delpi
  http/auth_header.py                     # bearer_authorization_from_context()
  persistence/plugins/repositories/strategic_indicators/  # Postgres
  providers/strategic_indicators/         # Coletores Sheets/RH + medições
  cache/ttl_cache.py
  providers/database/                   # Pool Postgres plugins

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
5. `PostgresStrategicIndicatorsIndicatorGoalsRepository` — resolução por `goal_scope_branch` e vigência

Metas por filial: ver [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md).

## Scripts (raiz do serviço)

| Script | Descrição |
|--------|-----------|
| `scripts/run_migrations.py` | Migrations V001–V025+ |
| `scripts/refresh_period_scores.py` | Materializa `period_scores` (consolidado + filiais) |
| `scripts/warmup_si_snapshots.py` | Warm-up manual |
| `scripts/bench_si_routes.py` | Benchmark rotas de leitura |

## Testes relevantes

| Arquivo | Cobertura |
|---------|-----------|
| `tests/test_branch_scoped_goals.py` | Metas/realizado por filial, valor consolidado sem meta na filial |
| `tests/test_goal_scope_helpers.py` | `indicator_uses_branch_unit_measurement`, resolução estrita |
| `tests/test_commercial_production_scoring.py` | Curva mensal, Comercial/Produção sem nota 0 indevida |
| `tests/test_goal_value_policy.py` | `goal_value` zerado em metas Curva |
| `tests/test_goal_curve_validation.py` | Pontos da curva por periodicidade |
| `tests/test_indicator_goals_sql_param_order.py` | Ordem dos parâmetros SQL em metas por filial |
| `tests/test_goal_scope_validation.py` | Validação de escopo no admin |

Serviços de metas: `goal_value_policy.py`, `goal_curve_validation.py`. Bundle admin: `postgres_admin_config_bundle_repository.py`. Ver [ADMIN_GOALS_AND_CONFIG.md](./ADMIN_GOALS_AND_CONFIG.md).

## Dependência `shared/`

Pacote monorepo `shared/` (instalado com `pip install -e ./shared[fastapi]`):

- `delpi_auth` — JWT, `@require_permission`
- `delpi_api_client` — HTTP client para api-delpi (`DelpiApiClient`)

## Legado removido (fase 1 — jun/2026)

Ver [LEGACY_CLEANUP.md](./LEGACY_CLEANUP.md).

- Removidos: `persistence/totvs/`, `providers/totvs/`, `persistence/google_sheets/`, `providers/google_sheets/`, `pyodbc`.
- Mantidos: gateways HTTP (`delpi_*_gateway.py`), use cases e snapshot services consumindo api-delpi.

A api-delpi mantém composers departamentais para rotas `/financial`, `/commercial`, etc.
