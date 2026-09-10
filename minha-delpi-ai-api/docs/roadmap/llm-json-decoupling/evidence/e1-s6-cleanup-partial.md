# E1.S6 — Cutover/cleanup (fatia parameter binding)

**Status:** `PARTIAL` (2026-09-10) — fatia A ATENDIDA; cutover de seleção e DELETE de JSON **não** READY  
**Onda:** B (plano 01)

## EXECUTION_DRIFT (escopo vs aceite pleno)

```text
PLAN_SAID: E1.S6 = retirar autoridade runtime do registry técnico + unknown API + metamorphic
CURRENT_EVIDENCE:
  - E1.S4 ainda SHADOW_ON (CUTOVER_DEFAULT_CANDIDATE = NOT_STARTED)
  - ledger proíbe DELETE de registry sem candidate≥baseline + unknown API + metamorphic
  - markers/pathMarkers ainda authority residual em select_registry_route_id / product intent
INVALIDATED_DECISION: não declarar E1.S6 ATENDIDO nem apagar fields do registry nesta fatia
AFFECTED_STEPS: aceite pleno E1.S6; DELETE pathMarkers/parameterStrategy JSON
SAFE_ACTION: fatia A = cleanup do switch morto pós-E1.S5; binder permanente no resolver
```

## Fatia A (READY — feita)

**Objetivo:** remover braços tipados mortos de `OperationalRouteActionResolverService.build_parameters` e tornar o binder canônico o único path de dispatch.

| Antes | Depois |
|-------|--------|
| early-return se `uses_openapi_authority` (exige `cutoverEnabled`) + ~223 LOC switch | strategies ∈ `cutover_strategies()` → sempre `bind_via_openapi`; desconhecida → `None` |
| `cutoverEnabled=false` reativava switch legado | flag só afeta labels do shadow (`compare`); dispatch permanente |

**Não removido (correto):**
- `ParameterStrategyShadowService.legacy_strategy_parameters` (observer + domain binders)
- fields JSON do registry / `api_route_domains`
- autoridade de seleção por markers (E1.S4)

## Aceite desta fatia

```text
RESOLVER_TYPED_SWITCH_REMOVED = PASS
BINDER_DISPATCH_PERMANENT = PASS
CUTOVER_FLAG_OFF_STILL_BINDS = PASS
UNKNOWN_STRATEGY_RETURNS_NONE = PASS
SQL_NOT_IN_RESOLVER_CUTOVER = PASS
REGISTRY_JSON_UNTOUCHED = PASS
SELECTION_AUTHORITY_UNCHANGED = PASS
```

## Bloqueado até evidência

```text
SELECTION_CUTOVER = BLOQUEADO (E1.S4 agree live)
DELETE_REGISTRY_TECHNICAL_FIELDS = PROIBIDO (ledger)
UNKNOWN_OPENAPI_PROVIDER = PENDING
METAMORPHIC_RENAME_LIVE = PENDING (harness E1.S3 retrieval ≠ cutover seleção)
ACTION_SELECTION_WITHOUT_ENDPOINT_REGISTRY = PENDING
```

## Próximo

1. Agregar taxa `agree` E1.S4 (live/admin).  
2. Cutover de seleção default candidate.  
3. Só então DELETE/cleanup de fields técnicos do registry + R1–R11/gates.
