# J-R5 — metamorphic rename verdadeiro

**Status:** COMPLETE_GATE = PASS (`METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME`)  
**HEAD_BEFORE:** `973594c5b525dbff4c4d1e91a279797c68ab53a4`  
**Bloqueio:** A11-05

## Problema

O gate live chamado “metamorphic” media sinônimo/paráfrase na mesma família `/stock`. Isso não é rename técnico de provider/path/operationId.

## Correção

Duas OpenAPIs semanticamente equivalentes:

| | V1 | V2 |
|---|---|---|
| provider | `metamorphic-tracking-a` | `metamorphic-tracking-z` |
| path | `/shipments/{id}/tracking` | `/cargo/{id}/position` |
| operationId | `get_shipment_tracking` | `locateCargo` |
| summary/description/tags/schema | **iguais** | **iguais** |

Harness: retrieve → plan → HTTP local → outcome idêntico. Sem matcher V2 no core.

## Testes

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/unit/application/services/test_j_r5_metamorphic_provider_path_operation_id_rename.py
```

## Gate

```text
METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME = PASS
COMPLETE_GATE (J-R5) = PASS
NEXT = J-R6
```
