# Desenvolvimento local

## Pré-requisitos

- Python 3.11+
- Acesso a `postgres-plugins`, TOTVS (ou mocks), Keycloak (via stack Docker)
- Monorepo com `shared/` instalado

## API sem Docker

Na raiz do monorepo:

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
pip install -r strategic-indicators-api/requirements.txt
pip install -e ./shared[fastapi]

# Copiar variáveis de infra/.env ou exportar PLUGINS_DB_*, DB_*, KEYCLOAK_*
python -m uvicorn si_app.main:app --reload --app-dir strategic-indicators-api --port 8010
```

Swagger local (sem gateway):

```text
http://127.0.0.1:8010/docs
```

Com gateway (stack completa):

```text
http://localhost/apps/strategic-indicators-api/docs
```

## Stack Docker (recomendado)

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d strategic-indicators-api strategic-indicators gateway
```

Logs:

```bash
docker logs -f delpi-strategic-indicators-api
```

## MFE

```bash
cd plugins/strategic-indicators
npm install
npm run dev          # HMR local (ajustar proxy se necessário)
npm run build        # dist/ para o container delpi-strategic-indicators
```

Base URL da API no build: `VITE_STRATEGIC_INDICATORS_API_BASE` (opcional; default no código aponta para o gateway).

## Migrations

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
python strategic-indicators-api/scripts/run_migrations.py up
```

## Benchmark

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
python strategic-indicators-api/scripts/bench_si_routes.py --competence 2026-05
```

Com token:

```bash
python strategic-indicators-api/scripts/bench_si_routes.py \
  --competence 2026-05 \
  --base-url http://localhost/apps/strategic-indicators-api/strategic-indicators \
  --token "$ACCESS_TOKEN"
```

## Warm-up e materialização

```bash
docker exec delpi-strategic-indicators-api python3 scripts/warmup_si_snapshots.py
docker exec delpi-strategic-indicators-api python3 -u scripts/refresh_period_scores.py
```

## Testes

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
pip install pytest  # se ainda não instalado
pytest strategic-indicators-api/tests/test_branch_scoped_goals.py \
       strategic-indicators-api/tests/test_indicator_goals_sql_param_order.py \
       strategic-indicators-api/tests/test_goal_scope_validation.py -q
```

## Dicas

- Volume dev monta `/app` — alterações em `si_app/` recarregam com `--reload` se rodar uvicorn local; no container, reiniciar o serviço.
- Primeira carga de executive/trends pode levar ~10–20s (TOTVS); segunda carga usa cache TTL.
- Ver [OPERATIONS.md](./OPERATIONS.md) para erros comuns.
