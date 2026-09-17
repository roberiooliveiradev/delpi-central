# DAVI-PRODUCT-DRAWING-CANONICAL-ACCESS-001

## Decision

api-delpi remains the canonical owner of product drawing access.
PCP / Cockpit becomes an HTTP consumer of `GET /products/{code}/drawing/pdf`.
FILESERVER remains authoritative storage, mounted only on api-delpi.
DAVI / MCP / allowlist are unchanged in this task (v9 / 17 eligible READ / 3 MCP tools).

## Before

| Surface | Source |
|---------|--------|
| PCP / Cockpit | `DrawingPdfLibraryStorage` + host mount `PC_DRAWING_PDF_HOST_PATH` → `/drawing-pdfs` |
| api-delpi | `DrawingPdfLibraryStorage` + `DRAWING_PDF_LIBRARY_DIR` (prod mount added in PCP-ACCESS-001) |

Why api-delpi was previously `library_available=false`: missing prod mount (fixed earlier). This task removes the duplicate PCP filesystem owner.

## After

```text
public-hub / Portal PCP
→ production-control-api BFF (queue/snapshot AuthZ)
→ ApiDelpiDrawingLibraryClient
→ api-delpi GET /products/{code}/drawing/pdf (API_DELPI_ACCESS)
→ DrawingPdfLibraryStorage
→ FILESERVER mount
```

## Files (task scope)

- `production-control-api/.../api_delpi_drawing_library_client.py` (new)
- `production-control-api/.../drawing_response.py` (new)
- composer + drawing routes + services + errors
- removed PCP `DrawingPdfLibraryStorage` + `PC_DRAWING_*` compose mounts
- docs: production-control-api README, public-hub README, infra README, 14-desenhos-pdf.md

## Future DAVI

Once live PDF access is proven, DAVI document transport can consume the same api-delpi route.
Not implemented here.
