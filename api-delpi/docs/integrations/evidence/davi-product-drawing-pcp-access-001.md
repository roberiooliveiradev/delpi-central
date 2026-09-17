# DAVI-PRODUCT-DRAWING-PCP-ACCESS-001 — Evidence

**Artifact class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`  
**Outcome:** `A_INFRA_ONLY`  
**Verdict (source):** `PASS_WITH_RESIDUAL` (deploy/live PDF = TEST_NOT_RUN)

## Root cause (PROVEN)

Production `infra/docker-compose.yml` mounted the FILESERVER drawing share only on `production-control-api` (`PC_DRAWING_PDF_HOST_PATH` → `/drawing-pdfs`).

`api-delpi` had:

- no `DRAWING_PDF_LIBRARY_DIR` override in prod compose (default `/app/data/drawing-pdfs`)
- no bind mount of the FILESERVER share

Therefore DAVI live saw `library_available=false` while PCP cockpit could serve PDFs from the same host share.

## PCP proven flow

```
CockpitPage / OperationDetailPage (public-hub)
→ fetchPublicDrawingPdf / buildPublicDrawingPdfUrl
→ GET /apps/production-control-api/public/machine-load/{token}/drawings/{pa}/pdf
→ PublicMachineLoadDrawingService.open_pdf
→ DrawingLibraryPort.resolve_pdf
→ DrawingPdfLibraryStorage (PC_DRAWING_PDF_LIBRARY_DIR)
→ host share (CIFS/SMB via PC_DRAWING_PDF_HOST_PATH)
→ FileResponse application/pdf inline
→ browser blob objectURL / iframe
```

AuthN: public machine-load token (+ branch). AuthZ: PA must be in published queue.

## Decision

Reuse existing api-delpi routes:

- `GET /products/{code}/drawing`
- `GET /products/{code}/drawing/pdf`
- `GET /products/drawings`

No new route. No PCP internal imports. Same host path as PCP.

## Implementation

1. Prod compose: mount `${PC_DRAWING_PDF_HOST_PATH:-/mnt/fileserver/desenhos}:/drawing-pdfs:ro` on api-delpi
2. Prod compose: `DRAWING_PDF_LIBRARY_DIR=/drawing-pdfs`
3. Distinguish `DrawingPdfLibraryUnavailableError` → HTTP **503** vs product not found → **404**

## DAVI state (unchanged)

allowlist v9 / eligible 17 / MCP tools 3  
`get_product_drawing_pdf` remains not promoted to JSON broker

## Deploy note

Requires recreate of `api-delpi` on host where `PC_DRAWING_PDF_HOST_PATH` is already mounted for PCP. Live verification is outside this source task.
