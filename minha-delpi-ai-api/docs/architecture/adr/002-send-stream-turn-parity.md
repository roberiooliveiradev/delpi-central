# ADR 002 — Paridade send/stream no turno

**Status:** Aceito (jun/2026)

## Contexto

`SendChatMessageUseCase` e `StreamChatMessageUseCase` tinham centenas de linhas duplicadas (preparação, montagem LLM, pós-LLM), com bugs que apareciam só em um modo.

## Decisão

Extrair serviços compartilhados em `app/application/services/chat_turn/`:

| Fase | Serviços |
|------|----------|
| Pré-LLM | `ChatTurnPreparationService` + delegates (`*_ingress`, `*_rag`, `*_tool_routing`, …) |
| Montagem | `ChatTurnLlmAssemblyService`, `ChatTurnUseCaseSupportService`, `ChatTurnSideEffectsService` |
| Stream | `ChatStreamTurnPrepareService`, `ChatStreamSessionTitleService`, `ChatStreamUserMessageService` |
| Pós-LLM | `ChatTurnCompletionService` |

Use cases delegam; stream adiciona apenas SSE, worker assíncrono e supressão de activity em turno simples.

## Consequências

- Send e stream < 500 linhas cada; mesma metadata de turno (exceto chunks).
- Testes de paridade e regressão em `chat_intelligence_regression_cases.py`.
- Activity headlines em `stream.json`; lógica de negócio fora do use case.
