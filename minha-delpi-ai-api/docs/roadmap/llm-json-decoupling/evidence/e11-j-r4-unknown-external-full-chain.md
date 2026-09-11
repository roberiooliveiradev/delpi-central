# J-R4 — unknown external OpenAPI full chain

**Status:** COMPLETE_GATE = PASS (`UNKNOWN_EXTERNAL_FULL_CHAIN`)  
**HEAD_BEFORE:** `d90d35d8aa7bada1780db81be6bc515220c6517d`  
**Bloqueio:** A11-04

## Problema

E9.S10 / smoke S14 paravam em import→retrieve→plan/bind e aceitavam HTTP falho em `example.invalid`. Isso **não** prova executor → payload → presentation → outcome R9.

## Correção

Harness offline controlado:

`tests/unit/application/services/test_j_r4_unknown_external_openapi_full_chain_offline.py`

```text
OpenAPI never-seen (providerKey=acme-harbor-jr4-never-seen)
→ Action Catalog in-memory
→ retrieve + plan + args
→ ValidateActionArguments / ExternalActionExecutionPolicy
→ HttpExternalActionGateway → ThreadingHTTPServer local
→ payload controlado
→ presentation metadata schema-driven
→ outcome assert
```

Sem edição de core/registry/content por endpoint.

## Testes

| Caso | Esperado |
|---|---|
| tracking full chain | PASS (HTTP 200 + payload + presentation) |
| sibling warehouse stock | PASS |
| actionId desconhecido | ValueError; zero hits HTTP |

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/unit/application/services/test_j_r4_unknown_external_openapi_full_chain_offline.py
```

## Gate

```text
UNKNOWN_EXTERNAL_FULL_CHAIN = PASS
COMPLETE_GATE (J-R4) = PASS
NEXT = J-R5
```
