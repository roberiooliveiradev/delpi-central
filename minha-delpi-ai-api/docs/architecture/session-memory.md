# Memória de sessão (Playbook 01)

Camada transversal do chat base para entidades, preferências, lousa, ações e referências vagas.

## Pipeline

```
Histórico + mensagem
  → ChatConversationMemoryService.build_pre_turn
  → ChatSessionMemoryService (overlay persistido)
  → ChatConversationMemoryExtractor (action, canvas, anexo, período)
  → ChatReferenceResolutionService.resolve_from_snapshot
  → workspaceContext.workingMemory + bloco no prompt
  → (turno) tools / LLM
  → ChatConversationMemoryService.build_post_turn
  → contextSnapshot + contextChips + adminDebug.memory
```

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatConversationMemoryService` | Orquestra pré/pós-turno, chips, admin debug |
| `ChatWorkingMemoryService` | Entidades, behavior, prompt block |
| `ChatConversationMemoryExtractor` | lastAction, lastPresentation, canvas, lastAttachment |
| `ChatReferenceResolutionService` | esse produto, mesmo período, essa tabela, faça o mesmo |
| `ChatSessionMemoryService` | Persistência ai_chat_session_memory, limpeza |
| `ChatSessionMemoryDirectAnswerService` | Ack preferência + ambiguidade |
| `ChatBehaviorInstructionService` | Preferências curtas (tabela, tom, resposta curta) |

## Validação

```bash
cd minha-delpi-ai-api && ./scripts/run_session_memory_validation.sh
```

Playbook: `docs/roadmap/melhorias/playbook_memoria_sessao_preferencias_minha_delpi_chat.md`.

- `sessionMemoryMetrics`: snapshot por turno (entidades, refs, follow-up, lousa)
