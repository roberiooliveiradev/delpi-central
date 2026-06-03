# Especialista em textos (editor textual DELPI)

**Playbook:** [`../roadmap/playbook-especialista-editor-textos.md`](../roadmap/playbook-especialista-editor-textos.md) — **Concluído (03/06/2026)**, Fases 1–7.

## Status de entrega

| Fase (§49) | Escopo | Estado |
|------------|--------|--------|
| 1 | Núcleo textual, roteamento `text_task`, templates | Concluído |
| 2 | E-mails, cartas, comunicados, chips | Concluído |
| 3 | Atas, relatórios, documentação, lousa | Concluído |
| 4 | Explicação, ELI5, adaptação de público | Concluído |
| 5 | Contexto, preferências de sessão | Concluído |
| 6 | Anexos e lousa | Concluído |
| 7 | Qualidade, feedback admin, regressão T1–T32 | Concluído |

**Pós-MVP:** `TextArtifactService` (§37); smoke HTTP/E2E LLM estável no ambiente docker com gateway.

## Princípio

**Texto bom = contexto entendido + sentido preservado + tom adequado + clareza + zero invenção.**

Tarefa textual pura não aciona API, SQL, RAG ou web (ver também [intent-routing.md](./intent-routing.md)).

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatTextTaskIntentService` | Detecção e categoria (`correct`, `email`, `minutes`, …) |
| `ChatTextTaskService` | Subtipos, supplement de prompt, `textTask` metadata |
| `ChatTextQualityValidator` | Validação pós-resposta → `textTaskQuality` |
| `ChatTextTaskFollowUpService` | Chips `textTaskFollowUpSuggestions` |
| `ChatTextTaskPreferenceService` | Preferências de sessão (merge persistente, «de agora em diante») |
| `ChatTextTaskMixedTurnService` | Turno misto: dados consultados + rascunho de e-mail |
| `ChatTextTaskCanvasService` | Atualização da lousa + histórico `textCanvasVersions` |
| `ChatTextTaskAdminMetricsService` | Snapshot em auditoria e agregado admin |
| `ChatTextTaskComposerService` | Rascunho operacional após tools (turno misto) |
| `ChatTextEditorSupplementService` | Templates por subtipo (carta, ata, ELI5, documentação, …) |
| `ChatTextContextResolverService` | Texto fonte inline, anexo, lousa e resposta anterior |

## Policies

- `administrative-writing.md` — regras gerais
- `text-specialist.md` — templates (e-mail, ata, checklist, comunicado)
- `text-correction.md` / `email-writing.md` — quando aplicável

## Admin

- `GET /admin/metrics/text-tasks/summary?hours=168` — uso (`textTaskMetrics`) + feedback textual agregado
- MFE: `AdminTextTaskMetrics` na aba Métricas

## Metadata

- `textTask` — tipo, subtipo, `intent` (ex. `text.email.create`), tom, público, origem (`user_message` | `attachment` | `canvas`)
- `textAssistant` — espelho resumido para telemetria/UI (mesmos campos principais)
- `textTaskFollowUpSuggestions`, `textTaskQuality`, `textTaskMetrics`, `textCanvasVersions`

## Testes

`tests/fixtures/text_specialist_regression_cases.py` (T1–T32), `test_chat_text_task_preference_service.py`, `scripts/run_text_specialist_validation.sh`, `scripts/smoke_text_editor_e2e.py`, `scripts/smoke_text_editor_http.py`
