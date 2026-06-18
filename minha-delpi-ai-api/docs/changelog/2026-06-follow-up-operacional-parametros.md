# Follow-up operacional, parâmetros e fontes de projeto (jun/2026)

## Motivação

Homologação do roteiro de treinamento expôs follow-ups («e a expedição?», exclusividade «desse produto») e follow-up de fontes («resuma o primeiro arquivo») que falhavam por classificação capabilities, parâmetros HTTP fora do schema ou `text_task` genérico.

## Entregas

| Fase | Área | Mudança |
|------|------|---------|
| P0 | Follow-up | `ChatFollowUpIntentService` — expedição/exclusividade |
| P0 | Contexto | `resolve_product_code` herda código em follow-up operacional |
| P0 | Matcher | escopo de produto + `product_query_intent.json` |
| P0 | Capabilities | Gate operacional antes de self_help |
| P0 | Parâmetros | `filter_parameters_to_schema` |
| P1.0 | Data | `collect_recent_playbook_date_parameters` |
| P1.1 | Roteamento | `operational_follow_up_routing.json` + `ChatOperationalFollowUpRoutingService` |
| P1.2 | Fallback | Bloqueio semântico com herança de produto + match parcial |
| P1.3–P1.4 | Treinamento | Roteiro + `TRAINING_AGENT_*` regressão |
| P2 | Fontes | `lastProjectSourcesInventory` + slot ordinal + RAG por `documentId` |

## Playbook

[`playbook-follow-up-operacional-desacoplado-jun2026.md`](../roadmap/melhorias/playbook-follow-up-operacional-desacoplado-jun2026.md)

## Testes

- `test_chat_follow_up_intent_service.py`
- `test_chat_capabilities_service.py`
- `test_chat_operational_follow_up_routing_service.py`
- `test_chat_project_source_slot_resolver_service.py`
- `test_chat_project_sources_slot_rag.py`
- `OPERATIONAL_FOLLOW_UP_SELECTION_CASES` em `production_operational_regression_cases.py`
- `PROJECT_SOURCES_INTENT_CASES` + `TRAINING_AGENT_*` em `chat_intelligence_regression_cases.py`
