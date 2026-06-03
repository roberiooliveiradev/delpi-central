# Memória de sessão (Playbook 01)

Camada transversal do chat base para entidades, preferências, lousa, ações e referências vagas.

## Pipeline

```
Histórico + mensagem
  → ChatConversationMemoryService.build_pre_turn
  → ChatSessionMemoryService (overlay persistido)
  → ChatConversationMemoryExtractor (action, canvas, anexo, período)
  → ChatReferenceResolutionService.resolve_from_snapshot
  → ChatContextCompressionService (histórico ≥ 10 mensagens)
  → ChatSemanticMemoryRetrieverService (intenção documental/playbook)
  → ChatEpisodicMemoryService.apply_pre_turn (recall de episódios)
  → workspaceContext.workingMemory + bloco no prompt
  → (turno) ChatSemanticMemoryService enriquece query RAG e registra hits
  → (turno) tools / LLM
  → ChatConversationMemoryService.build_post_turn
  → ChatEpisodicMemoryService.apply_post_turn (grava episódio quando couber)
  → contextSnapshot + contextChips + adminDebug.memory
```

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatConversationMemoryService` | Orquestra pré/pós-turno, chips, admin debug |
| `ChatConversationStateService` | `activeTopic`, `activeTask`, siga/próximo, correções, mudança de assunto (playbook memória §9) |
| `ChatEntityTrackerService` | `activeEntities`, `referenceHints`, `previousProductCodes`, SQL recente (playbook memória §10) |
| `ChatUserPreferenceManagerService` | `userPreferences` unificado (behavior, e-mail, texto, correção); revogação e reset por assunto (§13) |
| `ChatConversationSummarizerService` | Resumo estruturado extrativo (entidades, decisões, pendências) quando histórico ≥ 10 mensagens (§17) |
| `ChatContextCompressionService` | `compressedContext` no snapshot; bloco compactado no prompt (§18) |
| `ChatSemanticMemoryIntentService` | Detecta perguntas documentais/playbook para enriquecer RAG (§19) |
| `ChatSemanticMemoryRetrieverService` | Query enriquecida, hits ranqueados, `semanticMemoryHits` no snapshot |
| `ChatContextRankingService` | Ranking ponderado de trechos para o prompt (§22) |
| `ChatProceduralMemoryProviderService` | Hints de playbook/procedimento por tarefa ativa (§21) |
| `ChatSemanticMemoryService` | Ponte com `RagContextService` (híbrido + rerank já existentes) |
| `ChatEpisodicMemoryService` | Episódios no `contextSnapshot`, recall e gravação por tarefa (§20) |
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

Playbooks: [`playbook_memoria_sessao_preferencias`](../roadmap/melhorias/playbook_memoria_sessao_preferencias_minha_delpi_chat.md) (01, concluído) · [`playbook-memoria-e-contexto`](../roadmap/playbook-memoria-e-contexto.md) (Fases 1–6).

```bash
cd minha-delpi-ai-api && ./scripts/run_memory_context_validation.sh
```

Campos úteis no `adminDebug.memory` (Fases 5–6): `semanticMemory` (hits, intent), `episodicMemory` (contagem, recall).

- `sessionMemoryMetrics`: snapshot por turno (entidades, refs, follow-up, lousa)
