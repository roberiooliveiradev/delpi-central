# Playbook 03 — Especialista em Textos

**Status (03/06/2026):** **Concluído** (Fases 1–7) — especificação consolidada em [`playbook-especialista-editor-textos.md`](../playbook-especialista-editor-textos.md).  
**Código:** `ChatTextTaskService`, `ChatTextContextResolverService`, `ChatTextTaskPreferenceService`, `ChatTextQualityValidator`, `text-specialist.md`  
**Validação:** `scripts/run_text_specialist_validation.sh` · regressão T1–T32 · admin `GET /admin/metrics/text-tasks/summary`

## Núcleo

| Componente | Função |
|------------|--------|
| `ChatTextTaskIntentService` | Detecção `text_task` pura vs mista |
| `ChatTextTaskService` | Subtipos Playbook 03, supplement de prompt, `textTask` metadata |
| `ChatTextQualityValidator` | Validação pós-resposta |
| `ChatTextTaskFollowUpService` | Chips `textTaskFollowUpSuggestions` |
| `ChatTextTaskPreferenceService` | Preferências de sessão («só versão final», tom formal, …) |
| `ChatTextTaskMixedTurnService` | Metadata `textTaskMixed` (consulta + e-mail) |
| `ChatTextTaskCanvasService` | Lousa + `textCanvasVersions` |
| `ChatTextTaskAdminMetricsService` | Agregado admin (`GET /admin/metrics/text-tasks/summary`) |

## Policies

`administrative-writing.md`, `text-specialist.md`, `text-correction.md`, `email-writing.md`

## Regra central

Tarefa textual explícita → **sem** API/SQL/RAG/web no mesmo turno (roteamento Playbook 02 + estágio `text_task`).

## Metadata (exemplo)

```json
{
  "textTask": { "type": "correction", "subtype": "text_correct" },
  "textTaskFollowUpSuggestions": [{ "label": "Deixar mais formal", "query": "..." }],
  "textTaskMetrics": { "subtype": "text_correct" },
  "textTaskMixed": { "operational": true, "draftAttached": true },
  "textCanvasVersions": [{ "version": 1, "role": "previous" }, { "version": 2, "role": "current" }]
}
```

## Regressão T1–T16

`tests/fixtures/text_specialist_regression_cases.py`

## Admin

Painel Métricas (MFE): `AdminTextTaskMetrics` — `GET /admin/metrics/text-tasks/summary?hours=168`

Arquitetura: [`docs/architecture/text-specialist.md`](../../architecture/text-specialist.md)
