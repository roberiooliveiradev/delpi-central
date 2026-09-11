# E11.S9 — Candidate final R1–R11 fresco

**Status:** COMPLETE_GATE  
**Cobre:** RQ11-11, RQ11-12, RQ11-13 (parcial — flags/TODOs finais em S10)  
**FINAL_CANDIDATE_GIT_SHA:** `782a49721319571f0fe4733d59b8a5cc65ac4c04`

## Pré-condição

E11.S0–S8 concluídos; `SEMANTIC_*` full-tree = 0; corpus freeze `r1_r11_corpus_v1` hash `371f0cfa…` intacto.

## Offline

Runner: `scripts/run_e11_s9_final_candidate_offline.py`  
Evidência: [`e11-s9-final-candidate-offline-v1/manifest.json`](./e11-s9-final-candidate-offline-v1/manifest.json)  
Run: `docs/testing/evidence/runs/*_e11-s9-final-candidate-offline-v1/`

| Item | Resultado |
|---|---|
| Corpus 20 classes + sidecars E11/E9.S10 | **PASS_OFFLINE** |
| Unknown OpenAPI (logistics sidecar) | PASS |
| Metamorphic / registry cutover | PASS |
| Capability contract + smoke creds | PASS |
| R1–R11 offline | PASS_OFFLINE (todas) |

## Live (mesmo HEAD)

Credenciais apenas via env (`SMOKE_USER`/`SMOKE_PASSWORD`) — sem defaults versionados.

| Gate | Script | Resultado |
|---|---|---|
| Unknown + metamorphic + safety + args | `smoke_e9_s14_remaining_gates_live.py` | **PASS** (6/6) |
| Recs + SEND/STREAM/SIMULATE parity | `smoke_e9_s15_release_blockers_live.py` | **PASS** |
| Persist/reload/F5 | `smoke_e9_s16_f5_session_reload_live.py` | **PASS** |
| Latency/efficiency P50/P95 | `run_e9_s11_efficiency_live.py` | **PASS** (5/5; p50≈41.5s p95≈50.7s; `openai_compatible`) |
| Zero lateral path maps | `smoke_e10_zero_lateral_path_maps_live.py` | **PASS** |

Espelho: [`e11-s9-final-candidate-live-v1/`](./e11-s9-final-candidate-live-v1/)

## requiredDimensions (candidate final)

| Dim | Status | Evidência |
|---|---|---|
| R1 | PASS | offline corpus + live routing |
| R2 | PASS | offline + S14/S15 tools |
| R3 | PASS | offline no-tool + S14 required_args |
| R4 | PASS | offline + recommendations S15 |
| R5 | PASS | offline schema presentation |
| R6 | PASS | offline multi-turn + S16 F5 |
| R7 | PASS | S15 send/stream/simulate |
| R8 | PASS | S11 p50/p95 |
| R9 | PASS | S14 unknown/task success + E10 |
| R10 | PASS | S14 safety + write confirm |
| R11 | PASS | S11 efficiency + offline budget |

```text
globalReleasePass = true  (para dimensões R1–R11 deste candidate)
VERIFY_FINAL = ainda ABERTO até E11.S10 residual scan + docs
```

## Residual explícito → E11.S10

- Residual scan conceitual completo;
- RQ11-08 FS domain→infra (se ainda material);
- `recommendationQueries` profiles até exit criteria;
- `operationIds` observer arrays DELETE se sem consumer;
- README/roadmap/changelog archive somente após residual.
