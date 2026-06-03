# Changelog — playbook memória e contexto (Fase 7)

## Contexto avançado

| Serviço | Função |
|---------|--------|
| `ChatMemoryContradictionService` | Detecta e substitui preferências contraditórias (§32, M10) |
| `ChatContextSafetyFilterService` | Bloqueia gravação com conteúdo sensível (§23, M18) |
| `ChatLearnedForgettingService` | Poda códigos/episódios/SQL obsoletos (§33, M19) |
| `ChatMemoryKnowledgeGraphService` | `memoryGraph` com nós de tópico, tarefa, entidade, ação |
| `ChatMemoryContextDebugService` | `memoryContextDebug` no snapshot/admin |
| `ChatAdvancedContextService` | Orquestra pré/pós-turno |

Validação: `test_chat_advanced_context.py` · casos M18–M19 em `MEMORY_CONTEXT_REGRESSION_CASES`.
