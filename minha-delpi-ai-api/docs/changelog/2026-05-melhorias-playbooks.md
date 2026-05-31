# Changelog — playbooks `docs/roadmap/melhorias` (maio/2026)

Implementação incremental dos playbooks além da Fase 5 de contexto/assertividade (`c432e742`).

## Contexto (`playbook_contexto_assertividade`)

| Entrega | Detalhe |
|---------|---------|
| Fase 2 (serviços) | `ChatFollowUpIntentService`, `ChatReferenceResolutionService` extraídos de `ChatWorkingMemoryService` |
| Fase 3 (UI) | `metadata.contextChips` + barra **Contexto ativo** no plugin (`ChatContextBar`) |
| Comportamento | Preferência «só versão final» em `ChatBehaviorInstructionService` |

**Fase 4:** tabela `ai_chat_session_memory` + `POST /chat/sessions/{id}/memory/clear`.

## Correções (problemas reportados em homologação)

| Problema | Correção |
|----------|----------|
| «Corrija» + anexo → «sem acesso a documentos» | Instrução textual explícita + policy; `text_task` com contexto de anexo no prompt |
| «Consulte estoque e escreva e-mail» sem e-mail | `ChatTextTaskComposerService` anexa rascunho após tools no turno misto |
| «E-mail com dados da tabela» → capacidades/RAG | `is_email_from_operational_data_request` + resposta direta com resumo da consulta |
| Roteiro 360° com `Operations=[{...}]` | `_format_guide_like_item` no presenter do analyser |
| «qual o estoque do produto X?» → «Sobre esta consulta» | `ChatCapabilitiesService` não confundia pergunta operacional com inquiry de capacidade |

## Playbook 07 — Anexos (início)

- `attachmentFollowUpSuggestions` no metadata do assistant quando a mensagem do usuário trouxe anexos.
- `ChatAttachmentWelcomeService` — resposta automática ao enviar anexo (mensagem vazia ou «segue anexo»).
- Correção de quebras de linha na extração CSV/XLSX/PDF (`ChatAttachmentTextExtractor`).
- Provider no agente via API (`PUT /chat/agents/{id}/providers`) ou `scripts/upsert_agent_provider.py` — **sem** migration de dados; local usa api-externa; «Ver vendas»/faturamento exige api-delpi habilitada na API.
- Chips: Resumir, Corrigir, Traduzir, Extrair pendências, Criar checklist (`personality_playbook.json`).

## Interatividade (`playbook_interatividade_botoes`)

| Entrega | Detalhe |
|---------|---------|
| Chips por outcome `text` | Após tarefas textuais (`followUpChips.text` no playbook) |
| Starters | Texto administrativo na home (`textHomeStarters` / `CHAT_TEXT_HOME_STARTERS`) |

| Menu por linha de tabela | `ChatTableRowMenu` + `buildTableRowMenuActions` (Fase 4 interatividade) |
| Menu por ponto de gráfico | `buildChartPointMenuActions` + clique em barra/fatia/ponto (`ChatRichChart`) |
| Preferência api-externa | `CHAT_PREFER_API_EXTERNA_PROVIDER` + smokes `SMOKE_REQUIRE_API_EXTERNA` |

## Playbook 08 — Segurança e confiança (início)

| Entrega | Detalhe |
|---------|---------|
| SQL seguro | `ChatSqlSafetyService` bloqueia DELETE/UPDATE/… no `ChatToolContextService` |
| Confiança UI | `metadata.trustSignals` + `ChatTrustBadges` no MFE |
| Textos | Seção `security` em `external_action_responses.json` |

| Falha de API | `ChatSecurityMessagingService` — não inventa dado quando consulta falha |
| Confirmação de escrita | `ChatWriteConfirmationService` bloqueia DELETE/escrita sem «confirmo» |

| Confirmação no MFE | `actionConfirmation` + `ChatActionConfirmationPanel` (Confirmar/Cancelar) |
| Permissão de tool | `ToolPermissionDeniedError` usa texto `security.actionNotPermitted` |

**Backlog:** badges em admin debug ampliado; menu em árvore/chip de contexto (interatividade).

## Atalhos «Próximos passos» vs chat comum

| Entrega | Detalhe |
|---------|---------|
| Agente padrão | `ChatPlatformDefaultAgentService` — sessão sem agente usa agente de sistema (nome/ID via env) |
| Chips condicionais | `ChatFollowUpSuggestionService` não sugere «Ver estoque» etc. sem `actionsEnabled` |
| Sem agentic em chip | `ChatFollowUpChipQueryService` + `should_skip_agentic_loop` para consultas explícitas dos atalhos |

## Infra local (gateway)

| Problema | Correção |
|----------|----------|
| 502 em `/core-api/*` após restart de containers | `gateway/nginx.dev.conf` — upstreams com variável + `resolver` (DNS dinâmico Docker) |

**Backlog interatividade:** menu em gráfico/chip de contexto, fluxos guiados (`ChatGuidedFlow`).

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
