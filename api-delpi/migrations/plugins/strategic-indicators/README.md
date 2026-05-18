# Migrations movidas

As migrations do Strategic Indicators passaram a ser mantidas e executadas pela API dedicada:

- **SQL:** `strategic-indicators-api/migrations/`
- **Runner:** `python strategic-indicators-api/scripts/run_migrations.py up`

Use `PLUGINS_DB_*` (mesmo banco `postgres-plugins`). O schema continua `strategic_indicators`.

Este diretório permanece apenas como referência histórica; não adicione novas versões aqui.
