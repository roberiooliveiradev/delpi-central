# Strategic Indicators API

Serviço **FastAPI** dedicado ao módulo **Indicadores Estratégicos** (`/strategic-indicators/*`).

- Pacote: `si_app` (imports `from si_app...`)
- Entrypoint: `si_app/main.py` — `/health`, `/docs`, router estratégico
- Código podado a partir da api-delpi: apenas composers e infra usados pelo painel SI

## Documentação

| Doc | Descrição |
|-----|-----------|
| [docs/README.md](docs/README.md) | Índice da documentação |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Gateway, fontes de dados, cache, paralelismo |
| [docs/API.md](docs/API.md) | Rotas, permissões, query params |
| [docs/PERFORMANCE_IMPLEMENTATION.md](docs/PERFORMANCE_IMPLEMENTATION.md) | Performance (fases 0–5), benchmark |
| [migrations/README.md](migrations/README.md) | Migrations Postgres |

MFE: [plugins/strategic-indicators/README.md](../plugins/strategic-indicators/README.md)

## URL no gateway

```text
/apps/strategic-indicators-api/strategic-indicators/*
```

A **api-delpi** não expõe mais estas rotas.

## Variáveis de ambiente

Ver `si_app/config.py`. Principais:

| Variável | Descrição |
|----------|-----------|
| `SI_API_ROOT_PATH` | Prefixo atrás do gateway (padrão `/apps/strategic-indicators-api`) |
| `PORT` / `STRATEGIC_INDICATORS_API_PORT` | Porta do processo |
| `PLUGINS_DB_*` | Postgres (schema `strategic_indicators`) |
| `DB_*` / `TOTVS_*` | SQL Server Protheus |
| `TOTVS_POOL_ENABLED`, `TOTVS_POOL_MAX_SIZE` | Pool pyodbc (padrão `true` / `8`) |
| `SI_SNAPSHOT_CACHE_TTL_SECONDS` | Cache in-process de snapshots (padrão `600`) |
| `SI_WARMUP_ON_STARTUP` | Warm-up executive + trends no boot |
| `SI_WARMUP_TRENDS_MONTHS` | Meses do warm-up (padrão `6`) |
| `SI_PERIOD_SCORES_ENABLED` | Persistir scores por competência (trends) |
| `SI_RUN_MIGRATIONS_ON_STARTUP` | Aplicar migrations no boot (`true` em dev Compose) |

Exemplo: [../infra/env.strategic-indicators.example](../infra/env.strategic-indicators.example)

## Migrations

SQL em `migrations/V001`–`V010`. Runner: `scripts/run_migrations.py`.

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
python strategic-indicators-api/scripts/run_migrations.py status
python strategic-indicators-api/scripts/run_migrations.py up
```

## Desenvolvimento local

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
pip install -r strategic-indicators-api/requirements.txt
pip install -e ./shared[fastapi]
python -m uvicorn si_app.main:app --reload --app-dir strategic-indicators-api --port 8010
```

Docker (contexto = raiz do monorepo):

```bash
docker build -f strategic-indicators-api/Dockerfile -t strategic-indicators-api:dev .
```

Compose dev: serviço `strategic-indicators-api` em `infra/docker-compose.dev.yml`.

## Scripts úteis

| Script | Uso |
|--------|-----|
| `scripts/run_migrations.py` | `up`, `status`, `reset` |
| `scripts/warmup_si_snapshots.py` | Aquecer cache manualmente |
| `scripts/bench_si_routes.py` | Medir latência das rotas de leitura |

## Performance (resumo)

Baseline medido: executive-summary ~19s → ~10s; trends 3 meses ~28s → ~9–10s.

Detalhes, checklist e regras de paralelismo: [docs/PERFORMANCE_IMPLEMENTATION.md](docs/PERFORMANCE_IMPLEMENTATION.md).
