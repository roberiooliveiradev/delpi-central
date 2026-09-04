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
  tests/unit/domain/services/test_chat_intent_router_service.py::test_classify_system_metadata_columns_and_indexes_not_sql_generate \
  tests/unit/domain/services/test_chat_data_insight_service.py::test_build_system_tables_search_skips_similarity_ratio_total \
  tests/unit/domain/services/test_chat_data_insight_service.py::test_build_system_columns_uses_catalog_total_not_generic_numeric \
  tests/unit/domain/services/test_chat_presentation_profile_service.py::test_prose_delivery_mode_system_metadata_is_template \
  -q
```

Regressões F06 cobertas:

| Critério | Fix canônico |
|----------|----------------|
| R1 — colunas/índices sem `sql_generate` | Predicado `systemMetadataQuestion` no pipeline de sub-intent (+ `excludeIfSqlConversation`) |
| R4 — sem «Total de similarity_ratio» / lista genérica | `suppressGenericInsightFallback` + highlightRules `searchHitCount`/`catalogTotal` |
| R4 — lead na bolha (não só título) | prosa `template` + preferir markdown autorizado / `dataAnswer` |
| R4 — tabela no MFE | remover suppress por path em `visualSegmentCollector` (só `sqlSchemaPrefetch` / `suppressClientPresentation`) |
| R8 — prosa sem LLM pesado | `proseDeliveryByProfile.system` / entidades `protheus_*` = `template` + `dataAnswerLeadAlignment: inject` |

## Diagnóstico rápido (DB timeout)

Logs do `api-delpi`:

```text
Login timeout expired (SQLDriverConnect)
```

Confirme VPN/rede até `TOTVS_DB_HOST` e credenciais em `infra/.env`.
