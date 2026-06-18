# Follow-up operacional e parâmetros estritos (jun/2026)

## Motivação

Homologação do roteiro de treinamento expôs follow-ups («e a expedição?», exclusividade «desse produto») que falhavam por classificação capabilities ou parâmetros HTTP fora do schema OpenAPI.

## Entregas (P0)

| Área | Mudança |
|------|---------|
| Follow-up | `ChatFollowUpIntentService` — padrões expedição/exclusividade |
| Contexto | `resolve_product_code` herda código em follow-up operacional |
| Matcher | `_has_product_scope` reconhece follow-up como escopo de produto |
| Capabilities | Gate operacional antes de self_help (referência anafórica + tópicos) |
| Parâmetros | `filter_parameters_to_schema` — remove `limit` e outros fora do schema |
| Rotas | Segmentos playbook em `ChatRouteContextService` |

## Playbook

[`playbook-follow-up-operacional-desacoplado-jun2026.md`](../roadmap/melhorias/playbook-follow-up-operacional-desacoplado-jun2026.md)

## Testes

- `test_chat_follow_up_intent_service.py`
- `test_chat_capabilities_service.py`
- `test_external_action_product_route_catalog_service.py`
- `OPERATIONAL_FOLLOW_UP_SELECTION_CASES` em `production_operational_regression_cases.py`
