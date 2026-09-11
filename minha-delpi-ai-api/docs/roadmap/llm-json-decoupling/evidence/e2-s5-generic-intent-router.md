# E2.S5 — Generic intent/router cutover (slice mínima)

**Status:** `CUTOVER_GENERIC_SLICE` (2026-09-10)  
**Onda:** C (plano 02)

## Choke

`ChatIntentRouterService.classify` → legacy `ClassifyService` → overlay TU.

## Famílias (dials em `productFamilyAuthorityShadow.families`)

| Família | Dial | Modo |
|---------|------|------|
| `presentation` | `true` | mapper-first (alinha `text_task`/`presentation_task`; agree em `format_refinement`) |
| `no_tool` | `true` | agree-gated (flag `tu_no_tool_agree`; não inventa small_talk) |
| `compare_explain` | `true` | agree-gated (flag `tu_compare_agree`) |

## Aceite da slice

```text
NO_TOOL_SMALLTALK_AGREE = PASS
PRESENTATION_TABLE_CHART_MAPPER = PASS
NEGATIVE_OPERATIONAL_NOT_SMALLTALK = PASS
DIALS_OFF_EQUALS_LEGACY = PASS
HEURISTIC_JSON_UNTOUCHED = PASS
```

## BLOCKED (E2.S5 full / E2.S7)

- DELETE `intent_router.json` / `analysis_intent_vocabulary.json`
- Cutover total do cascade ClassifyService (RAG/web/SQL/…)
- Consumers de `ChatAnalysisIntentService.is_*` fora do router

## Rollback

`families.no_tool|presentation|compare_explain=false` ou `cutoverEnabled=false`.
