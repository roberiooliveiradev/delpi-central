# E11.S2 — apiRouteDomain sem path authority

**Status:** COMPLETE_GATE  
**Cobre:** RQ11-01 (path→domain), parcial RQ11-11 (unknown/metamorphic unit)

## CUTOVER

- Removido `_DOMAIN_RULES` / matching por fragmento de path.
- Authority: `apiRouteDomain` explícito → `entity` (exact/bindings/prefix) → `categoryToDomain` → `generic`.
- Content: `api_route_domains.json#semanticBindings`.
- Importer stamp via `classify_action` (metadata), não `infer_from_path`.
- Consumers path-only (`classify_path`, follow-up fallback, route match domain-only, suggestions) alinhados a metadata/`generic`.

## GENERALIZAÇÃO (unit)

| Caso | Resultado |
|---|---|
| Positive entity `product_search` | `product_search` |
| Sibling entity `product_stock` | `product` |
| Category `commercial` (entity dashboard) | `department_kpi` |
| `production_schedule` entity vs category production | `production_schedule` |
| Negative path-only / unknown external | `generic` |
| Metamorphic path rename, entity preserved | domain estável |

## CLEANUP

- Path domain table removida do runtime.
- Gate `SEMANTIC_PATH_DOMAIN_MAP` no full-tree: **0**.
- Docs/tests de paridade path map reescritos.

## Residual

Outras dívidas E11 (strategy/routeSegment/registry/smoke) permanecem; S2 não as fecha.
