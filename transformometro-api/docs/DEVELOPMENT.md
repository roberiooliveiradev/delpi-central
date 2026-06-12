# Desenvolvimento — Transformômetro API

## Docker (recomendado)

```bash
cd infra
docker compose -f docker-compose.dev.yml up -d transformometro-api transformometro
```

Health:

```bash
curl -s http://localhost/apps/transformometro-api/health
curl -s http://localhost/apps/transformometro-api/transformometro/health
```

## Migrations

Com `TM_RUN_MIGRATIONS_ON_STARTUP=true` (padrão no compose dev e prod), as migrations **V001–V018** são aplicadas no boot. Playbook 18: **V011–V018**.

Manual:

```bash
cd transformometro-api
export PLUGINS_DB_HOST=localhost PLUGINS_DB_PORT=5433 ...
python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

Ver tabela de versões em [migrations/README.md](../migrations/README.md).

## Cadastro JSON (export/import)

Baseline e restore **sem seed em migrations**:

```bash
set -a && source ../infra/.env && set +a
python scripts/import_cadastro_json.py export -o fixtures/cadastro/transformometro-cadastro.json
```

Detalhes: [fixtures/cadastro/README.md](../fixtures/cadastro/README.md) · [docs/json-backup.md](json-backup.md) · [docs/playbook-18-implementation-status.md](playbook-18-implementation-status.md).

## MFE

```bash
cd plugins/transformometro
npm run build
```

Deep link / sincronização com o portal: `src/hooks/useDelpiPortalBridge.ts`.
