# E9.S1 — Dataset e manifesto imutável (corpus R1–R11 ampliado)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** H (plano 09)  
**Corpus:** `tests/fixtures/intelligence_baseline/r1_r11_corpus_v1.json`  
**Harness:** `tests/unit/domain/services/test_e9_s1_r1_r11_corpus_coverage.py`  
**Run:** `docs/testing/evidence/runs/*_e9-s1-corpus-v1/` · espelho `evidence/e9-s1-corpus-v1/`

## Veredito

```text
CORPUS_20_CLASSES = PASS
HARNESS_REFS_RESOLVE = PASS
ONDA_A_BASELINE_UNTOUCHED = PASS
DATASET_HASH_FROZEN = PASS
LIVE_LLM = NOT_REQUIRED (E9.S2)
```

## Freeze

| Campo | Valor |
|-------|-------|
| `datasetVersion` | `intelligence_baseline/r1_r11_corpus_v1` |
| `datasetHash` | `371f0cfa802188c805f986ff15452e152a5f98e636132fa81145fad7cfcf26b8` |
| `runId` | `e9-s1-corpus-v1` |
| classes | **20/20** (índice → harness existentes) |
| Onda A `runId` | `0249db78-…` **imutável** |

## Pendente (não bloqueia S1)

- `openApiSchemaHash` / `actionCatalogHash` = `PENDING_RUNTIME`
- Execução plena R1–R11 no mesmo dataset = **E9.S2**

## Não DELETE

Legado B–D (registry markers, intent heuristics, terms) permanece até gates E9.S6.

## Próximo

**E9.S2** — baseline R1–R11 no corpus v1 (offline subset + dims aplicáveis).
