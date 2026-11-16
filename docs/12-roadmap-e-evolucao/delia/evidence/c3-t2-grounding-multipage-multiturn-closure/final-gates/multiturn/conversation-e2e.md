# WS-3 — Continuidade real same-conversation

```yaml
CONVERSATION_CORRELATION: or-qwen14b-00bb3f24aebb
CONTEXT_SOURCE: live_turn1_published_response
TURN_1_ID: INT2_R6_clarification_needed
TURN_2_ID: INT2_R6_same_conversation_recovery
SAME_SUBJECT_SESSION: true
AGENTS: DELIA_TWO_AGENT_EXPERIMENT=true (eval only)
```

## Turno 1

- Pedido: "Quero ver a estrutura de um produto."
- Clarificação publicada (live): pede o código
- MCP: nenhum
- Grounding: NON_GROUNDED
- Limitations: agent_requested_clarification

## Turno 2

- Resposta do usuário: "90260921"
- Prior: user turn-1 + **assistant = resposta publicada do turn-1**
- Objetivo recuperado; obrigação SATISFIED
- MCP: get_context×2 + read
- Grounding: GROUNDED
- Resposta: estrutura CHICOTE DE LIGACAO / 90260921

## Role filtering

`_prior_turns_blob` autoriza só `TurnKind.USER_INPUT` (`DELIA_RESULT`
fail-closed) — códigos inventados pelo modelo não autorizam lookups
posteriores.
