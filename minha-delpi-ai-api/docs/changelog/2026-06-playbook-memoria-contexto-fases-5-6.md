# Changelog — playbook memória e contexto (Fases 5–6)

Entrega alinhada a [`playbook-memoria-e-contexto.md`](../roadmap/playbook-memoria-e-contexto.md) §81 e [`session-memory.md`](../architecture/session-memory.md).

**Commits:** `da03bf0b` (Fase 5) · `bf17fada` (Fase 6)

---

## Fase 5 — Memória semântica

| Componente | Função |
|------------|--------|
| `ChatSemanticMemoryIntentService` | Detecta documentação/playbook; não dispara em consulta operacional pura |
| `ChatProceduralMemoryProviderService` | Hints de procedimento por `activeTask` |
| `ChatContextRankingService` | Ranking ponderado (§22) |
| `ChatSemanticMemoryRetrieverService` | Query enriquecida, `semanticMemoryHits`, bloco no prompt |
| `ChatSemanticMemoryService` | Ponte com `RagContextService` / `SearchKnowledgeUseCase` |
| `ChatTurnPreparationService` | Estágio `semantic_memory`; merge de bloco pós-RAG |

Infraestrutura reutilizada (sem duplicar): embeddings, busca vetorial, híbrida, rerank (`CHAT_RAG_*`).

**Regressão:** M16 · `tests/unit/domain/services/test_chat_semantic_memory.py`

---

## Fase 6 — Memória episódica

| Componente | Função |
|------------|--------|
| `ChatEpisodicMemoryService` | `episodicMemory` no `contextSnapshot` (máx. 8 episódios) |
| Recall | «playbook anterior», «continue de onde», «mesmo padrão», … |
| Gravação | Pós-turno com tarefa ativa e resposta substantiva |
| Exclusão | Pedido explícito do usuário |
| `ChatSessionMemoryDirectAnswerService` | Clarificação quando recall ausente |

**Regressão:** M17 · `tests/unit/domain/services/test_chat_episodic_memory_service.py`

---

## Validação

```bash
cd minha-delpi-ai-api && ./scripts/run_memory_context_validation.sh
```

Casos registrados: `MEMORY_CONTEXT_REGRESSION_CASES` (M1–M17) em `tests/fixtures/memory_context_regression_cases.py`.
