# J-R6 — Architecture Enforcement independente

**Status:** COMPLETE_GATE = PASS (`ARCHITECTURE_GATE_INDEPENDENT`)  
**HEAD_BEFORE:** `15609d309fea89ba4fac7f2348ddf44ec820013a`  
**Bloqueio:** A11-06

## Problema

`scan_registry_operation_id_catalog` retornava `[]` quando o próprio registry declarava:

```text
cleanupMeta.operationIdsRuntimeAuthority = false
```

Self-attestation do artefato auditado silenciava o finding estrutural.

## Correção

Scanner sempre inspeciona `routes[].route.operationIds` não-vazios. Metadata só anota a mensagem (`authority`/`role`); **não** suprime.

```text
registry contém catálogo técnico
+ cleanupMeta diz "não authority"
→ scanner AINDA detecta
```

## Evidência

```bash
python3 -m unittest scripts.ci.test_audit_architecture_phase3 -v
python3 scripts/ci/audit_architecture_phase3.py --check-semantic-debt
# totals_by_rule={"SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG": 84}
```

Debt 84 = arrays observer ainda presentes → **J-R8** deve limpar. J-R6 não declara SEMANTIC_*=0.

## Testes

| Caso | Esperado |
|---|---|
| payload com authority=false + operationIds | finding |
| routes sem operationIds | [] |
| registry live | ≥1 finding |

## Gate

```text
ARCHITECTURE_GATE_INDEPENDENT = PASS
COMPLETE_GATE (J-R6) = PASS
NEXT = J-R7
```
