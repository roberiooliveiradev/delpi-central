# Memória de sessão (Playbook 01)

Camada transversal do chat base para contexto de sessão, preferências, lousa, ações e referências vagas.

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
  → ChatAdvancedContextService (contradição, esquecimento, grafo, segurança, debug)
  → workspaceContext.workingMemory + bloco no prompt
  → (turno) ChatSemanticMemoryService enriquece query RAG e registra hits
  → (turno) tools / LLM
  → ChatConversationMemoryService.build_post_turn
  → ChatEpisodicMemoryService.apply_post_turn (grava episódio quando couber)
  → contextSnapshot + contextChips + adminDebug.memory
  → metadata.activePending | metadata.activeQuery (parâmetro / sessão de consulta)
```

### Metadata transversal (jun/2026)

| Chave | Serviço | Uso |
|-------|---------|-----|
| `activePending` | `ChatActivePendingService` | Turno anterior pediu parâmetro; próxima mensagem curta resolve via `ChatIntentRouterService` |
| `activeQuery` | `ChatActiveQuerySessionService` | Última consulta bem-sucedida; continuar enviando só códigos/datas até mudar assunto |

Ver [`chat-intelligence-base.md`](./chat-intelligence-base.md) § Data obrigatória e sessão ativa.

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatConversationMemoryService` | Orquestra pré/pós-turno, chips, admin debug |
| `ChatConversationStateService` | `activeTopic`, `activeTask`, siga/próximo, correções, mudança de assunto (playbook memória §9) |
| `ChatEntityTrackerService` | Sinais do turno → `operationalFocus`, `referenceHints`, SQL recente (§10) |
| `ChatUserPreferenceManagerService` | `userPreferences` unificado (behavior, e-mail, texto, correção); revogação e reset por assunto (§13) |
| `ChatConversationSummarizerService` | Resumo estruturado extrativo (entidades, decisões, pendências) quando histórico ≥ 10 mensagens (§17) |
| `ChatContextCompressionService` | `compressedContext` no snapshot; bloco compactado no prompt (§18) |
| `ChatSemanticMemoryIntentService` | Detecta perguntas documentais/playbook para enriquecer RAG (§19) |
| `ChatSemanticMemoryRetrieverService` | Query enriquecida, hits ranqueados, `semanticMemoryHits` no snapshot |
| `ChatContextRankingService` | Ranking ponderado de trechos para o prompt (§22) |
| `ChatProceduralMemoryProviderService` | Hints de playbook/procedimento por tarefa ativa (§21) |
| `ChatSemanticMemoryService` | Ponte com `RagContextService` (híbrido + rerank já existentes) |
| `ChatEpisodicMemoryService` | Episódios no `contextSnapshot`, recall e gravação por tarefa (§20) |
| `ChatAdvancedContextService` | Orquestra Fase 7: contradição, safety, forgetting, grafo, debug |
| `ChatMemoryContradictionService` | Substitui preferências contraditórias (§32) |
| `ChatContextSafetyFilterService` | Gating de escrita e filtro sensível (§23) |
| `ChatLearnedForgettingService` | Poda contexto obsoleto (§33) |
| `ChatMemoryKnowledgeGraphService` | `memoryGraph` leve no snapshot |
| `ChatMemoryContextDebugService` | `memoryContextDebug` para admin |
| `ChatMemoryUxService` | `memoryUx` no metadata, chips UX, resposta «o que está usando» (Fase 8) |
| `ChatSessionMemoryAdminMetricsService` | Agregado admin `sessionMemoryAdminMetrics` (Fase 9) |
| `ChatMemoryContextLossAlertService` | `memoryContextAlerts` por turno (Fase 9) |
| `ChatManualContextPinService` | API de pin → grava `context_item` |
| `ChatSnapshotOperationalFocus` | Leitura/escrita de `operationalFocus` no snapshot |
| `ChatUserContextItemService` | Contexto do usuário + `sync_operational_focus` |
| `ChatWorkingMemoryService` | Pré/pós-turno, behavior, prompt block |
| `ChatConversationMemoryExtractor` | lastAction, lastPresentation, canvas, lastAttachment |
| `ChatActiveQuerySessionService` | `metadata.activeQuery` pós-turno — herança de tipo de consulta até mudança de assunto (jun/2026) |
| `ChatActivePendingService` | `metadata.activePending` — parâmetro faltante (código, data, filial) |
| `ChatReferenceResolutionService` | esse produto, mesmo período, essa tabela, faça o mesmo |
| `ChatSessionMemoryService` | Persistência ai_chat_session_memory, limpeza |
| `ChatSessionMemoryDirectAnswerService` | Ack preferência + ambiguidade |
| `ChatBehaviorInstructionService` | Preferências curtas (tabela, tom, resposta curta) |

## Validação

```bash
cd minha-delpi-ai-api && ./scripts/run_session_memory_validation.sh
```

## API de contexto manual

| Método | Rota | Uso |
|--------|------|-----|
| GET | `/chat/sessions/{id}/memory/context` | Chips, resumo, `usage` (modal memória) |
| POST | `/chat/sessions/{id}/memory/context-items` | Texto/arquivo ou `role`/`messageId`; par `question`+`answer` |
| DELETE | `/chat/sessions/{id}/memory/context-items/{itemId}` | Remove item (`itemId` = uuid do chip) |
| POST | `/chat/sessions/{id}/memory/clear` | Limpa overlay persistido |

Playbooks: [`playbook_memoria_sessao_preferencias`](../roadmap/melhorias/playbook_memoria_sessao_preferencias_minha_delpi_chat.md) (01) · [`playbook-memoria-e-contexto`](../roadmap/playbook-memoria-e-contexto.md) (Fases 1–9 + extensões jun/2026).

```bash
cd minha-delpi-ai-api && ./scripts/run_memory_context_validation.sh
```

Campos úteis no `adminDebug.memory`: `semanticMemory`, `episodicMemory`, `advancedContext` (`memoryContextDebug`, grafo, gating).

- `sessionMemoryMetrics`: snapshot por turno (`operationalFocus`, refs, follow-up, lousa)

Ver também: [`contexto-vs-entidades.md`](./contexto-vs-entidades.md).
