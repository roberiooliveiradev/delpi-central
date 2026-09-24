# E13 — Hygiene / residual allowlist

**Status:** IMPLEMENTED (classified)

## Allowlist MFE (KEEP)

| Symbol / pattern | Class | Reason |
|---|---|---|
| `create*Block` / `DEFAULT_*` | TRANSIENT_EDITOR_UI | Stub até ack; paint publicado usa modelo canônico |
| `alignComunicadoBlocks` local | TRANSIENT_EDITOR_UI | Fallback offline / error path |
| `updateBlock` local | TRANSIENT_EDITOR_UI + NETWORK ack | Preview + `commitUpsertBlocks` |
| `display*` paint | PAINT | serverDisplayApplied |
| Viewport place/center | VIEWPORT_TRANSFORM | Editor only |

## Residual search notes

- `DEFAULT_COMUNICADO_*` permanece exportado para testes/admin — não authority de create persistido.
- Paint path: preferir campos materializados; não expandir `??` novos.
