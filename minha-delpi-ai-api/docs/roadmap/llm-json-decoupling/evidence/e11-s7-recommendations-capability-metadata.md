# E11.S7 — Recommendations contextuais + capability metadata

**Status:** COMPLETE_GATE  
**Cobre:** RQ11-06, RQ11-07

## CUTOVER — capability

- `ChatCapabilityDiscoveryService.capabilities_from_actions` deriva:
  - `readWrite` / `risk` / `parallelSafe` / `requiresConfirmation`
  - de `method` + `sensitivity` via `ChatWriteConfirmationService` (mesma authority de execução).
- `contractSource=method+sensitivity` nos candidatos sintetizados.
- Defaults uniformes `read`/`low`/`parallelSafe=true` **removidos**.

## CUTOVER — recommendations

- Producer já era candidate-first; static = `LEGACY_FALLBACK`.
- Dual-run metadata agora inclui `staticFallbackRole` + `staticFallbackExitCriteria` explícitos.
- Smoke/eval **não** devem usar `recommendationQueries` como oracle principal (critério de remoção documentado).

## GENERALIZAÇÃO (unit)

| Caso | Resultado |
|---|---|
| GET read | low / parallel / no confirm |
| POST write | medium / not parallel / confirm |
| DELETE destructive | high |
| unknown PATCH sem sensitivity | write via method |
| e4_s2 baseline + e6_s3/s4 | PASS |

## Residual

- Profiles `recommendationQueries` ainda no JSON até exit criteria (coverage canary).
- LLM `llm_candidates` wiring permanece opt-in (sem delta obrigatório nesta subetapa).
- Registry capabilities não-action mantêm campos próprios.
