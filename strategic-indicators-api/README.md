# Strategic Indicators API

Serviço FastAPI dedicado a **`/strategic-indicators/*`** (código derivado da api-delpi, pacote `si_app` com imports `from si_app...`).

O **`si_app/main.py`** expõe **`/health`**, **`/docs`** e o router **`/strategic-indicators/*`**.

O repositório `si_app/` foi **poado**: mantêm-se só módulos alcançáveis a partir de `main.py` → `strategic_indicators_routes` → `strategic_indicators_composer` → composers departamentais (comercial, produção, qualidade, engenharia, financeiro, suprimentos, RH) e respetiva infra (TOTVS, Google Sheets, Portal RH, Postgres plugins para catálogo/metas/settings).

## Variáveis de ambiente

Igual à api-delpi para dados operacionais: `PLUGINS_*`, TOTVS, Google Sheets, Portal RH, Keycloak/JWT, etc. (ver `si_app/config.py`).

| Variável | Descrição |
|----------|-----------|
| `SI_API_ROOT_PATH` | Prefixo atrás do gateway (predefinição `/apps/strategic-indicators-api`). |
| `STRATEGIC_INDICATORS_API_PORT` | Porta do processo (fallback para `PORT`). |
| `TOTVS_POOL_ENABLED` | Reutilizar conexões SQL Server (`true` por padrão). |
| `TOTVS_POOL_MAX_SIZE` | Tamanho do pool TOTVS (padrão `8`). |
| `SI_SNAPSHOT_CACHE_TTL_SECONDS` | TTL do cache in-process de snapshots (padrão `600`). |
| `SI_WARMUP_ON_STARTUP` | Aquece executive + trends em background no boot (`true` no Compose). |
| `SI_WARMUP_TRENDS_MONTHS` | Meses carregados no warm-up (padrão `6`). |
| `SI_PERIOD_SCORES_ENABLED` | Persiste scores por competência no Postgres para trends (padrão `true`). |
| `SI_RUN_MIGRATIONS_ON_STARTUP` | Aplica migrations pendentes no boot (padrão `false`; `true` no Compose dev). |

## Migrations (Postgres plugins)

Arquivos em **`migrations/`** (V001–V010). Runner dedicado desta API — não depende mais da api-delpi.

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
# Requer PLUGINS_DB_HOST, PLUGINS_DB_PORT, PLUGINS_DB_NAME, PLUGINS_DB_USER, PLUGINS_DB_PASSWORD
python strategic-indicators-api/scripts/run_migrations.py up
python strategic-indicators-api/scripts/run_migrations.py status
```

Detalhes: [migrations/README.md](migrations/README.md).

## Desenvolvimento local

Na raiz do monorepo:

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

## Integração

O MFE chama **`/apps/strategic-indicators-api/strategic-indicators`** através do gateway; a **api-delpi** já não monta estas rotas.

## Performance (implementação)

Roadmap e checklist de otimização das rotas de leitura: **[docs/PERFORMANCE_IMPLEMENTATION.md](docs/PERFORMANCE_IMPLEMENTATION.md)**.
