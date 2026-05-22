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

Com `TM_RUN_MIGRATIONS_ON_STARTUP=true` (padrão no compose dev), as migrations V001–V005 são aplicadas no boot.

Manual:

```bash
cd transformometro-api
export PLUGINS_DB_HOST=localhost PLUGINS_DB_PORT=5433 ...
python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

Ver tabela de versões em [migrations/README.md](../migrations/README.md).

## Notificações de workflow (opcional)

No `infra/.env`:

```env
TM_NOTIFICATIONS_ENABLED=true
TM_CORE_API_URL=http://core-api:8000
# CORE_API_INTEGRATIONS_SERVICE_TOKEN já definido para a Core API
TM_WORKFLOW_APPROVER_EMAILS=seu-email@delpi.com.br
```

Recriar o container da API após mudar o `.env`. Documentação: [NOTIFICACOES-WORKFLOW.md](../../docs/12-roadmap-e-evolucao/transformometro-app/NOTIFICACOES-WORKFLOW.md).

## MFE

```bash
cd plugins/transformometro
npm run build
```

Deep link / sincronização com o portal: `src/hooks/useDelpiPortalBridge.ts`.
