# Migrations — Transformômetro

Padrão de nome: `V001__descricao.sql`

```bash
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
```

Variáveis: `PLUGINS_DB_HOST`, `PLUGINS_DB_PORT`, `PLUGINS_DB_NAME`, `PLUGINS_DB_USER`, `PLUGINS_DB_PASSWORD`.
