# Changelog — contexto, memória de turno e assertividade (maio/2026)

Entrega alinhada ao [playbook de contexto](../roadmap/melhorias/playbook_contexto_assertividade_minha_delpi_chat.md) (Fases 1–2 e 5) e correções correlatas de produto/presenter no chat base.

---

## 1. Memória de turno (Fase 1–2)

| Componente | Função |
|------------|--------|
| `ChatWorkingMemoryService` | Snapshot pré/pós-turno: `lastEntities`, follow-up, referências |
| `ChatBehaviorInstructionService` | Instruções de comportamento da sessão no contexto operacional |
| `ChatTurnPreparationService` | Injeta `workspaceContext.workingMemory` antes de tools/LLM |
| `ChatContextMetadataService` | Grava `contextSnapshot` e `contextAssertiveness` no metadata do assistant |

Policy global: `app/domain/prompt_policies/chat-context-memory.md` (registrada em `PromptPolicyService`).

---

## 2. Assertividade contextual (Fase 5)

| Componente | Função |
|------------|--------|
| `ChatContextAssertivenessService` | Score 0–100 e flags por turno |
| `ChatAdminDebugService.resolve_client_admin_debug` | Expõe memória + assertividade na resposta admin **após** attach do metadata |
| Plugin `ChatAdminDebugPanel` | Chips de score/flags; destaque quando score &lt; 70 |

Flags principais: `follow_up_entity_reused`, `follow_up_without_entity_reuse`, `unnecessary_code_request`, `humanized_none_fields`, `supplier_intent_used_analyser`, `stale_product_context`.

**Regressão:** `CONTEXT_ASSERTIVENESS_CASES` em `tests/fixtures/chat_intelligence_regression_cases.py`.

**CI:** `scripts/run_onda11_validation.sh` — pytest Fase 5 + `smoke_context_assertiveness_multiturn.py`.

---

## 3. Chips «Próximos passos»

| Alteração | Detalhe |
|-----------|---------|
| `ChatFollowUpSuggestionService` | Resolve `product_code` (memória, tools, histórico); omite chip sem código |
| `personality_playbook.json` | Queries explícitas com código do produto |
| Smoke | `scripts/smoke_follow_up_chips.py` |

Commit anterior dedicado: `ab0b843a`.

---

## 4. Correções operacionais (mesmo pacote)

| Área | Correção |
|------|----------|
| Estrutura / parents | `max_depth` limitado a 15 (evita 422) |
| Presenter analyser | `build_text_presentation` normaliza payload como `present()` |
| Intent produto | «onde o produto X é usado» → rota parents |
| MFE | Cancelamento de stream / «segundo plano»; quebra-gelos limitados (`agentIcebreakers.ts`) |

---

## 5. Feedback estruturado

Motivo **Perdeu o contexto** (`lost_context`) em `personality_playbook.json` e `chatFeedbackReasons.ts` (plugin).

---

## 6. Documentação

- [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) — seção memória/assertividade
- [`../api/02-chat-sessoes-mensagens.md`](../api/02-chat-sessoes-mensagens.md) — metadata `contextAssertiveness`, `adminDebug.memory`
- [`../roadmap/melhorias/README.md`](../roadmap/melhorias/README.md) — índice e status

## Backlog (playbook)

- **Fase 3:** chips de contexto ativo na UI, limpar contexto
- **Fase 4:** tabela `ai_chat_session_memory` persistida entre sessões
- Seleção de action para chip «Ver vendas» (WARN no smoke de chips)
