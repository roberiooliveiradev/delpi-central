# Especialista em textos (Playbook 03)

## Princípio

**Texto bom = sentido preservado + clareza + tom adequado + zero invenção.**

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

## Policies

- `administrative-writing.md` — regras gerais
- `text-specialist.md` — templates (e-mail, ata, checklist, comunicado)
- `text-correction.md` / `email-writing.md` — quando aplicável

## Admin

- `GET /admin/metrics/text-tasks/summary?hours=168` — agregado de `audit_metadata.textTaskMetrics`
- MFE: `AdminTextTaskMetrics` na aba Métricas

## Testes

`tests/fixtures/text_specialist_regression_cases.py` (T1–T16), `scripts/run_text_specialist_validation.sh`
