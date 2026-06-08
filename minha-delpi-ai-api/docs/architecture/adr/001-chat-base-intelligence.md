# ADR 001 — Inteligência no chat base

**Status:** Aceito (jun/2026)

## Contexto

Agentes, projetos e simulação admin reutilizam o mesmo fluxo de mensagens. Regras duplicadas em use cases ou prompts de agente geravam divergência send≠stream e regressões por perfil.

## Decisão

Toda inteligência transversal (intenção, tools, RAG, apresentação, direct answers) evolui na **camada base** (`ChatIntelligencePipelineService`, `ChatToolContextService`, `ChatTurnPreparationService`, domain services). Agentes **filtram** actions/skills e acrescentam identidade — não reimplementam o pipeline.

## Consequências

- Melhorias beneficiam chat comum, agentes e preview/simulate automaticamente.
- Use cases (`SendChatMessageUseCase`, `StreamChatMessageUseCase`) permanecem finos (orquestração + I/O).
- Novas policies globais em `domain/prompt_policies/`; texto de UI em JSON (ADR 003).
