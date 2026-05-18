# 09 — Deploy, migrations e schema audit

## Estado esperado em produção

```bash
flask --app app.main:app db current
flask --app app.main:app db heads
```

Ambos devem apontar para a mesma head, por exemplo:

```text
7c8d9e0f1a23 (head)
7c8d9e0f1a23 (head)
```

## Auditoria de schema

```bash
cd /app
python -m app.infrastructure.db.schema_audit
```

Resultado esperado:

```text
=== SCHEMA AUDIT ===
Models esperados: 17
Tabelas no banco: 18
Alembic banco: ['7c8d9e0f1a23']
Alembic heads: ['7c8d9e0f1a23']

STATUS: OK
```

## Deploy da `minha-delpi-ai-api`

```bash
cd ~/projetos/delpi-central/infra

docker compose -f docker-compose.yml --env-file .env up -d --build minha-delpi-ai-api

docker compose -f docker-compose.yml --env-file .env exec minha-delpi-ai-api \
  sh -lc "cd /app && flask --app app.main:app db upgrade"

docker compose -f docker-compose.yml --env-file .env exec minha-delpi-ai-api \
  sh -lc "cd /app && python -m app.infrastructure.db.schema_audit"

docker compose -f docker-compose.yml --env-file .env restart minha-delpi-ai-api
```

## Verificação rápida

```bash
docker compose -f docker-compose.yml --env-file .env exec minha-delpi-ai-api \
  sh -lc "cd /app && flask --app app.main:app db current && flask --app app.main:app db heads"
```

## Quando usar `stamp head`

Use `flask --app app.main:app db stamp head` somente quando:

1. O schema foi corrigido manualmente por hotfix SQL.
2. `python -m app.infrastructure.db.schema_audit` retorna `STATUS: OK`.
3. `flask db upgrade` falha por objetos já existentes, como `DuplicateTable`.

Exemplo:

```bash
docker compose -f docker-compose.yml --env-file .env exec minha-delpi-ai-api \
  sh -lc "cd /app && flask --app app.main:app db stamp head"
```

## Tabelas críticas recentes

| Tabela | Finalidade |
|---|---|
| `ai_external_action_providers` | Providers/API globais. |
| `ai_external_actions` | Rotas/actions importadas do OpenAPI. |
| `ai_external_action_schemas` | Schemas OpenAPI salvos. |
| `ai_chat_agent_action_providers` | Vínculo agente -> provider. |
| `ai_chat_agent_actions` | Overrides de rotas/actions por agente. |
| `ai_external_action_test_logs` | Logs de teste de rotas/actions. |
| `ai_chat_attachments` | Anexos de chat. |
