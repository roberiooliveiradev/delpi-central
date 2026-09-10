# E9.S2 — Baseline R1–R11 (offline subset no corpus v1)

**Status:** `ATENDIDO_PARCIAL` (2026-09-10)  
**Onda:** H (plano 09)  
**Dataset:** `intelligence_baseline/r1_r11_corpus_v1` (`datasetHash=371f0cfa…`)  
**Run:** `docs/testing/evidence/runs/*_e9-s2-baseline-offline-v1/` · espelho `evidence/e9-s2-baseline-offline-v1/`

## Veredito

```text
SAME_DATASET_AS_E9_S1 = PASS
OFFLINE_HARNESS_SUBSET = PASS (16 modules / 99 tests)
FIXTURE_ONLY_INDEXED = 2 (nebula + product_description_vs_stock)
LIVE_LLM / L1-L4 = DEFERRED
RUNTIME_CATALOG_HASHES = PENDING_RUNTIME
```

## Escopo deste baseline

Reexecutou todos os `harnessRef` **`.py`** do corpus v1 no mesmo `datasetHash`.  
Fixtures JSON sem runner dedicado neste passo ficam **indexadas** (classes 2 e 3/12 compartilham nebula; class 2 também usa product_description fixture).

## Não coberto ainda (próximas fatias E9.S2 / L*)

- Trials LLM / dims semânticas que exigem modelo
- `openApiSchemaHash` / `actionCatalogHash` de catálogo persistido
- send/stream live parity
- Matriz R1–R11 com score por dimensão (hoje = smoke de harnesses indexados)

## Próximo

**E9.S3** — candidate evidence por plano 01–08 — **ATENDIDO** (`e9-s3-candidate-plans-offline.md`).  
**E9.S4** — shadow divergence — **ATENDIDO** (`e9-s4-shadow-divergence.md`). Próximo: **E9.S5** canary/default cutover.
