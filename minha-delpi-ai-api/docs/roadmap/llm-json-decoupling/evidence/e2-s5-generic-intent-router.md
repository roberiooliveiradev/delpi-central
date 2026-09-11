# E2.S5 — Generic intent/router + analysis multi-consumer

**Status:** `CUTOVER_FULL_SLICE` (2026-09-10)  
**Onda:** C (plano 02)

## Chokes

1. `ChatIntentRouterService.classify` → overlay TU (`no_tool` / `presentation` / `compare_explain`)
2. `ChatAnalysisIntentService.is_*` → cutover multi-consumer:
   - `is_comparison_or_insight_request` — dial `compare_explain` (legacy ∪ TU reasoning + needles)
   - `is_data_interpretation_request` — dial `data_interpretation` (legacy ∪ TU reasoning **com** tool-data)
   - `is_email_from_operational_data_request` — **KEEP** heurístico (terms + tool-data)

## Aceite

```text
NO_TOOL_SMALLTALK_AGREE = PASS
PRESENTATION_TABLE_CHART_MAPPER = PASS
COMPARE_MULTI_CONSUMER = PASS
DATA_INTERPRETATION_MULTI_CONSUMER = PASS
NEGATIVE_OPERATIONAL_NOT_COMPARE = PASS
DIALS_OFF_EQUALS_LEGACY = PASS
HEURISTIC_JSON_UNTOUCHED = PASS
```

## Ainda KEEP (não é débito de E2.S5)

Cascade SQL/RAG/web/drawing e `intent_router.json` / `analysis_intent_vocabulary.json` como fallback — TARGET permite fast paths justificados (E2.S7).

## Rollback

`families.compare_explain|data_interpretation|presentation|no_tool=false` ou `cutoverEnabled=false`.
