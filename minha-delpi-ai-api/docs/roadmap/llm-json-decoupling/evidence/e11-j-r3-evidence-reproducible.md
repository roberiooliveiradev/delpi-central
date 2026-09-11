# J-R3 — evidence reproduzível

**Status:** COMPLETE_GATE = PASS (`EVIDENCE_REPRODUCIBLE`)  
**HEAD_BEFORE:** `277a89c6a49ec791ac7906dcc32c1dfabacdaddb`  
**Bloqueio:** A11-03

## Problema

O runner `run_e11_s9_final_candidate_offline.py` grava `globalReleasePass=false` (live deferred). O manifest versionado tinha `globalReleasePass=true` **e** `reasonGlobalReleasePassFalse` — não reproduzível.

## Correção

| Artefato | Papel |
|---|---|
| `ChatEvidenceReproducibilityService` | invariantes + provenance |
| `scripts/align_evidence_release_pass.py` | alinha manifests (nunca inventa PASS) |
| offline runner | emite `runnerSha256`/`configHash`/`timestamp`/… e valida antes de escrever |

Invariante:

```text
reasonGlobalReleasePassFalse OU liveDeferred OU role OFFLINE+liveLlm=false
→ globalReleasePass DEVE ser false
```

## Ação sobre evidence histórica

`e11-s9-final-candidate-offline-v1/manifest.json` alinhado por script:

```text
previous=true → now=false
```

Não foi edição manual de veredito para “passar”.

## Testes

| Caso | Esperado |
|---|---|
| true + reason | FAIL |
| false + reason | PASS |
| align() reescreve contradição | PASS |
| manifest offline em disco | PASS (após align) |

```bash
PYTHONPATH=. python3 -m unittest tests.unit.domain.services.test_j_r3_evidence_reproducibility -v
PYTHONPATH=. python3 scripts/align_evidence_release_pass.py --check
```

## Gate

```text
EVIDENCE_REPRODUCIBLE = PASS
COMPLETE_GATE (J-R3) = PASS
NEXT = J-R4
```
