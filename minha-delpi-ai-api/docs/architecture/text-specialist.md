# Especialista em textos (editor textual DELPI)

**Playbook:** [`../roadmap/playbook-especialista-editor-textos.md`](../roadmap/playbook-especialista-editor-textos.md) (evolução do Playbook 03).

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
| `ChatTextTaskPreferenceService` | Preferências de sessão (memória de trabalho) |
| `ChatTextTaskMixedTurnService` | Turno misto: dados consultados + rascunho de e-mail |
| `ChatTextTaskCanvasService` | Atualização da lousa + histórico `textCanvasVersions` |
| `ChatTextTaskAdminMetricsService` | Snapshot em auditoria e agregado admin |
| `ChatTextTaskComposerService` | Rascunho operacional após tools (turno misto) |
| `ChatTextEditorSupplementService` | Templates por subtipo (carta, ata, ELI5, documentação, …) |

## Policies

- `administrative-writing.md` — regras gerais
- `text-specialist.md` — templates (e-mail, ata, checklist, comunicado)
- `text-correction.md` / `email-writing.md` — quando aplicável

## Admin

- `GET /admin/metrics/text-tasks/summary?hours=168` — agregado de `audit_metadata.textTaskMetrics`
- MFE: `AdminTextTaskMetrics` na aba Métricas

## Metadata

- `textTask` — tipo, subtipo, `intent` (ex. `text.email.create`), tom, público, origem (`user_message` | `attachment` | `canvas`)
- `textAssistant` — espelho resumido para telemetria/UI (mesmos campos principais)
- `textTaskFollowUpSuggestions`, `textTaskQuality`, `textTaskMetrics`, `textCanvasVersions`

## Testes

`tests/fixtures/text_specialist_regression_cases.py` (T1–T24), `scripts/run_text_specialist_validation.sh`, `scripts/smoke_text_editor_e2e.py`
