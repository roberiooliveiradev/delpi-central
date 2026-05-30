# Changelog — playbooks `docs/roadmap/melhorias` (maio/2026)

Implementação incremental dos playbooks além da Fase 5 de contexto/assertividade (`c432e742`).

## Contexto (`playbook_contexto_assertividade`)

| Entrega | Detalhe |
|---------|---------|
| Fase 2 (serviços) | `ChatFollowUpIntentService`, `ChatReferenceResolutionService` extraídos de `ChatWorkingMemoryService` |
| Fase 3 (UI) | `metadata.contextChips` + barra **Contexto ativo** no plugin (`ChatContextBar`) |
| Comportamento | Preferência «só versão final» em `ChatBehaviorInstructionService` |

**Backlog:** tabela `ai_chat_session_memory` (Fase 4).

## Interatividade (`playbook_interatividade_botoes`)

| Entrega | Detalhe |
|---------|---------|
| Chips por outcome `text` | Após tarefas textuais (`followUpChips.text` no playbook) |
| Starters | Texto administrativo na home (`textHomeStarters` / `CHAT_TEXT_HOME_STARTERS`) |

**Backlog:** menus por linha de tabela, fluxos guiados (`ChatGuidedFlow`).

## Admin textos (`playbook_assistente_administrativo_textos`)

| Entrega | Detalhe |
|---------|---------|
| Fase 1–2 | Policy `administrative-writing.md`, `ChatTextTaskIntentService`, estágio `text_task` no turn prep (sem tools/RAG) |

**Backlog:** templates no input (Fase 3), skill registry dedicada, testes E2E com LLM.

## Descontraído (`playbook_chat_interativo_descontraido`)

| Entrega | Detalhe |
|---------|---------|
| Parcial | Starters e chips de texto alinhados ao `personality_playbook.json` |

**Backlog:** ampliar `stream.json` / variantes por outcome.

## Testes

- `test_chat_text_task_intent_service.py` (T1/T6/T7 lógica)
- `test_chat_reference_resolution_service.py`
- `test_chat_follow_up_intent_service.py`
- Inclusão em `run_onda11_validation.sh`
