# Transformômetro — OpenAPI para agente de chat

Rotas de leitura sobre o cache materializado (`dashboard_calculos`), sem expor CRUD de escrita.

## Arquivo OpenAPI

`docs/openapi-snapshot-chat.json` — 4 rotas:

| operationId | Path |
|-------------|------|
| `get_dashboard_snapshot_meta` | `GET /transformometro/dashboard/snapshot/meta` |
| `get_dashboard_snapshot_resumo` | `GET /transformometro/dashboard/snapshot/resumo` |
| `get_dashboard_snapshot_processos` | `GET /transformometro/dashboard/snapshot/processos` |
| `get_dashboard_snapshot_linhas` | `GET /transformometro/dashboard/snapshot/linhas` |

## Provider no agente

| Campo | Valor |
|-------|-------|
| `providerKey` | `transformometro-api` |
| `baseUrl` | `https://<host>/apps/transformometro-api` |
| `authMode` | `user_token` (JWT do usuário) |
| `allowRead` | `true` |
| `allowWrite` | `false` |

Importe o schema inline (`openapi-snapshot-chat.json`) na criação do provider.

## Sync pós-deploy

No container `minha-delpi-ai-api`:

```bash
python scripts/sync_transformometro_openapi.py
```

Gera catálogo em `minha-delpi-ai-api/docs/knowledge/_generated/transformometro-openapi-catalog.md`.

## RAG do agente

Indexar: `minha-delpi-ai-api/docs/knowledge/domains/agents/transformometro/transformometro-snapshot-rotas-agente.md`

## Variáveis

| Variável | Default | Efeito |
|----------|---------|--------|
| `TM_DASHBOARD_AUTO_RECALC` | `true` | CRUD atualiza cache automaticamente |
