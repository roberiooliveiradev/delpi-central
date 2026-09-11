# E11.S3 — Argument binding schema authority

**Status:** COMPLETE_GATE  
**Cobre:** RQ11-02 (path/oid→parameterStrategy removido do core de binding)

## CUTOVER

- `build_parameters` → `ParameterStrategyShadowService.bind_schema_first` (schema + grounding; sem gate path→strategy).
- Affinity / vocabulary: match flags + schema param names; sem `ParameterStrategyInferenceService`.
- Execute metadata: `parameterStrategy="schema"`.
- `ParameterStrategyInferenceService` virou stub (sempre `"schema"`); branches path/oid removidos.
- Gate `SEMANTIC_ENDPOINT_PARAMETER_STRATEGY` full-tree: **0**.

## GENERALIZAÇÃO (unit)

| Caso | Resultado |
|---|---|
| Positive required `code` + identifier | bind ok |
| Negative required code missing | `None` |
| Metamorphic path rename, mesmo schema | code estável |
| Registry strategy `sql` ignorada | ainda schema-bind |

## CLEANUP parcial

- Path→strategy heuristics DELETED.
- Shadow/legacy binders ainda existem para compat de strategies tipadas no content (`OperationalApiParameterBuilderService`) — residual tipado por **schema/helper**, não por path inference; E11.S5/S7 podem limpar catálogo `parameterStrategies` quando sem consumer.

## Residual explícito (não bloqueia S3 gate de path-inference)

- `legacy_strategy_parameters` / `parameterStrategies` JSON recipes ainda usados por helpers de data/branch quando schema declara esses campos.
- R3 live candidate final: E11.S9.
