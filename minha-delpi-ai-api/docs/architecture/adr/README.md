# Architecture Decision Records — minha-delpi-ai-api

Registro curto de decisões estruturais do chat. Formato: **contexto → decisão → consequências**.

| ADR | Título | Status |
|-----|--------|--------|
| [001](001-chat-base-intelligence.md) | Inteligência no chat base | Aceito |
| [002](002-send-stream-turn-parity.md) | Paridade send/stream no turno | Aceito |
| [003](003-assistant-content-json.md) | Textos de UI em JSON | Aceito |
| [004](004-repository-ports-composition-root.md) | Ports e composition root | Aceito |
| [005](005-http-routes-modular-facade.md) | HTTP modular com facade | Aceito |
| [006](006-hardcoded-pt-strings-baseline-gate.md) | Gate de strings PT (baseline) | Aceito |

**Quando criar um ADR:** mudança que afeta pipeline do chat, contrato de camadas, bundles de conteúdo ou política de testes/CI — não para cada feature de produto.

**Referências:** [`chat-intelligence-base.md`](../chat-intelligence-base.md), [`playbook-11-clean-architecture-chat-api.md`](../../roadmap/playbook-11-clean-architecture-chat-api.md).
