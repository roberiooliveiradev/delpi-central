# Migrations — Strategic Indicators

Scripts SQL versionados para o schema `strategic_indicators` no banco **postgres-plugins** (`PLUGINS_DB_*`).

Padrão de nome: `V001__descricao.sql`

## Comandos

Na raiz do monorepo (com `PLUGINS_DB_*` no ambiente):

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
python strategic-indicators-api/scripts/run_migrations.py status
python strategic-indicators-api/scripts/run_migrations.py up
```

No container:

```bash
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up
```

## Startup automático

`SI_RUN_MIGRATIONS_ON_STARTUP=true` aplica migrations pendentes antes do warm-up (recomendado em dev).

## Reset (cuidado)

```bash
python strategic-indicators-api/scripts/run_migrations.py reset
```

Remove o schema `strategic_indicators` inteiro.
