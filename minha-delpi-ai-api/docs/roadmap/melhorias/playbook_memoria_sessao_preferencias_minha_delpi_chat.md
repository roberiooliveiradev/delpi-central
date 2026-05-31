# Playbook 01 — Memória de Sessão e Preferências

**Projeto:** Minha DELPI Chat IA  
**Escopo:** chat comum, agentes, lousa, anexos, respostas textuais e consultas operacionais  
**Status implementação:** Fases **1–5** concluídas (maio/2026)

**Código:** `ChatConversationMemoryService`, `ChatConversationMemoryExtractor`, `ChatWorkingMemoryService`, `ChatReferenceResolutionService`, `ChatSessionMemoryService`, `ChatBehaviorInstructionService`

**Validação:** `./scripts/run_session_memory_validation.sh` · **Arquitetura:** [`../../architecture/session-memory.md`](../../architecture/session-memory.md)

| Fase | Escopo | Status |
|------|--------|--------|
| 1 | Produto, filial, período, referências operacionais | Concluída |
| 2 | Preferências (curto, formal, tabela, correção, e-mail) | Concluída |
| 3 | Lousa e anexo no snapshot | Concluída |
| 4 | Última action e apresentação | Concluída |
| 5 | Admin debug e regressão M1–M12 | Concluída |

**Métricas por turno:** `sessionMemoryMetrics` + feedback §21 (motivos memory_*). **Backlog:** agregado §20, UI §18 expandida.

---

## 1. Objetivo

Memória de sessão para o chat lembrar produto, período, última resposta, preferências e lousa — permitindo «E os fornecedores?» após consultar estoque sem repetir o código.

## 2–3. Problemas e princípio

Memória **curta, estruturada, auditável** — não guardar tudo, só o útil para o próximo passo.

## 4–6. Tipos e estrutura

Implementado em `workingMemory` / `contextSnapshot`:

- `lastEntities` (productCode, branch, period)
- `behaviorInstructions` + `emailPreferences` + `textCorrectionPreferences`
- `lastAction`, `lastPresentation`, `canvas`, `lastAttachment`
- `resolvedReferences`, `preferencesApplied`, `memoryUsed`

## 5–7. Serviços

- **`ChatConversationMemoryService`** — orquestra pré/pós-turno (playbook §5)
- **`ChatReferenceResolutionService.resolve_from_snapshot`** — §7 (esse produto, mesmo período, essa tabela, faça o mesmo)

## 8–9. Preferências de sessão

`ChatBehaviorInstructionService` + serviços de e-mail/correção; persistência via `ChatSessionMemoryService`.

## 10–11. Limpeza e expiração

- Total: «limpe o contexto», «começar do zero», `POST .../memory/clear`
- Seletiva: «esqueça esse produto» → `selectiveMemoryCleared`
- Troca de agente: `agentContextReset` limpa `lastAction`

## 12–16. Ambiguidade, agentes, permissões, lousa, anexos

- `memoryAmbiguity` quando «compare com o anterior» sem candidatos claros
- Contexto lembrado **não é autorização** (§14)
- Lousa/anexo no extractor (§15–16)

## 17. Admin debug

`adminDebug.memory`: `memoryUsed`, `resolvedReferences`, `preferencesApplied`, `lastAction`, `canvas`, `persisted`.

## 18. UI

`contextChips` + `ChatContextBar` (MFE) — produto, filial, período, lousa, preferências.

## 19. Testes

`tests/unit/domain/services/test_chat_session_memory.py` — casos M1–M12 (regressão).

## 20–22. Métricas, feedback, anti-padrões

- **Por turno:** `ChatSessionMemoryMetricsService` → `sessionMemoryMetrics`
- **Feedback:** motivos `memory_*` no `personality_playbook.json`
- **Agregado admin:** backlog

## 23. Roadmap

Fases 1–5: **concluídas** neste pacote.

## 24. Resumo

Memória boa = contexto útil + preferência respeitada + possibilidade de limpar.

**Relacionado:** [playbook_contexto_assertividade_minha_delpi_chat.md](./playbook_contexto_assertividade_minha_delpi_chat.md)
