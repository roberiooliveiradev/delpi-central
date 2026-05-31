# Homologação — metadados Protheus (`/system`)

Pergunta de referência: **«qual a tabela de produtos?»** → `GET /system/tables/search?description=produtos`.

## Pré-requisitos

| Item | Verificação |
|------|-------------|
| Gateway | `SMOKE_BASE_URL=http://localhost` (ou `http://delpi-gateway`) |
| Login | Keycloak `rober` / `1234` (dev) |
| Agente | Provider **api-delpi** habilitado no agente oficial |
| OpenAPI | `POST /chat/agents/{id}/providers/api-delpi/import` ou `scripts/sync_api_delpi_openapi.py` |
| ERP | `TOTVS_DB_HOST` acessível da rede do container `api-delpi` (porta 1433) |

Se o SQL Server estiver indisponível, o chat ainda deve:

- classificar `subIntent: system_metadata`;
- chamar a tool `/system/tables/search` com `description=produtos`;
- responder com mensagem `systemMetadataQueryFailed` (sem inventar SB1).

Com ERP online, a resposta deve listar tabelas (ex.: **SB1** — cadastro de produtos).

## Smoke automatizado

```bash
cd minha-delpi-ai-api
SMOKE_BASE_URL=http://localhost \
SMOKE_USER=rober \
SMOKE_PASSWORD=1234 \
PYTHONPATH=. python3 scripts/smoke_system_table_routing.py
```

Camadas validadas:

1. **Unit** — `ExternalActionSelectionService` → `tables-search` + `description=produtos`
2. **API** — rota gateway `/apps/api-delpi/system/tables/search` (WARN se DB off)
3. **Chat E2E** — mensagem na sessão com tool e intent corretos

## Testes unitários

```bash
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app -w /app minha-delpi-ai-api \
  python -m pytest \
  tests/unit/application/services/test_external_action_selection_service.py::test_select_system_table_search_with_article_qual_a_tabela \
  tests/unit/domain/services/test_external_action_result_presenter_system.py \
  tests/unit/domain/services/test_chat_security_messaging_service.py \
  tests/unit/domain/services/test_chat_intent_router_service.py::test_classify_system_metadata_table_question \
  -q
```

## Diagnóstico rápido (DB timeout)

Logs do `api-delpi`:

```text
Login timeout expired (SQLDriverConnect)
```

Confirme VPN/rede até `TOTVS_DB_HOST` e credenciais em `infra/.env`.
