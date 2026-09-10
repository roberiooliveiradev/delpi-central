# E9.S6 — Cleanup gates

**Status:** `ATENDIDO_PARCIAL` (2026-09-10) — gates instalados; **DELETE bloqueado**  
**Onda:** H (plano 09)  
**Fixture:** `tests/fixtures/intelligence_baseline/e9_s6_cleanup_gates.json`  
**Harness:** `tests/unit/domain/services/test_e9_s6_cleanup_gates.py`

## Veredito

```text
GATES_INVENTORIED = PASS (9 required)
DELETE_AUTHORIZED = false
CANDIDATES_BLOCKED = PASS (4)
PASS_OFFLINE_ALONE_INSUFFICIENT = PASS (negative)
SIBLING_ALL_PASS_AUTHORIZES = PASS
NO_PREMATURE_DELETE = PASS
```

## Gates (estado atual — pós E9.S10)

| Gate | Status |
|------|--------|
| candidate_task_success | PASS_OFFLINE |
| unknown_api | PASS_OFFLINE |
| metamorphic | PASS_OFFLINE |
| safety | PASS_OFFLINE |
| required_args | PASS_OFFLINE |
| multi_turn | PASS_OFFLINE |
| compound | PASS_OFFLINE |
| latency_cost | PASS (E9.S11 live) |
| legacy_fallback_hit_rate | PASS_OFFLINE |

`passStatusesForDelete` = `PASS` | `PASS_OFFLINE_AND_LIVE` | `APPROVED`.  
**PASS_OFFLINE sozinho não autoriza DELETE.**

## Candidates BLOCKED (não removidos)

- registry `pathMarkers` / `operationIdMarkers` / …
- registry `parameterStrategy` fields
- follow-up `messageSegmentTerms` / `playbookPathMarkers`
- turn-understanding heuristics (cutover família ainda shadow-only)

## Decisão

Não executar DELETE enquanto dims required estiverem INCONCLUSIVE — alinhado a R09-07 e à proibição de PASS global com INCONCLUSIVE (E9.S3).

## Próximo

**E9.S7** — architecture audit de residuals (justificar ou remover **somente** se gate permitir; senão documentar justificação).
