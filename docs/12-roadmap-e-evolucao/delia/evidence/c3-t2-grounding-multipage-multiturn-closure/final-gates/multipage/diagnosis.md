# WS-2 — Integridade de coleção multipágina

## Owner da identidade da coleção

`_joint_collection_coverage` (mesmo `specialist_id`/`provider`/
`remote_capability`/`action_id` + `invocation_scope` +
`invocation_identity` + total único). O agregador de apresentação
`aggregate_paginated_pages` não é autoridade de owner/filtro/AuthZ.

## Reuse decision

```yaml
RESPONSIBILITY: multipage collection integrity
OWNER: _joint_collection_coverage
EXISTING_EQUIVALENT: YES
REUSE_DECISION: REUSE
```

## Contratos

- R5-N3: owners distintos → não SATISFIED
- R5-N4: filtros materiais distintos → não SATISFIED
- R5-N5: escopos AuthZ (`filial_id`) distintos → não SATISFIED

Live `INT2_R5_multipage_full_enumeration`: GROUNDED + SATISFIED
(3× MCP:read, enumeração completa).
