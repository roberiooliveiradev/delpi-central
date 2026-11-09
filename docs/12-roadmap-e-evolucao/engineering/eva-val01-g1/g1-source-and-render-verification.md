# G1_SOURCE_AND_RENDER_VERIFICATION

**TASK:** `EVA-VAL01-G1-STRUCTURAL-GT-COMPLETION-AND-OWNER-HANDOFF`  
**Date:** 2026-11-09  
**Document:** `90264135.pdf`

## Source identity

| Campo | Valor |
|---|---|
| Path autorizado | `/mnt/fileserver/desenhos/90264135.pdf` (host `srv-api`) |
| SHA-256 medido | `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` |
| SHA histórico esperado | `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` |
| `SOURCE_HASH_STATUS` | `MATCH` |
| Páginas físicas conferidas | 10, 12, 13 |

## Render de referência

| Campo | Valor |
|---|---|
| Engine | PDFium (container `infra-engineering-api:latest`, offline) |
| DPI | 200 |
| Orientação | landscape (largura > altura) |
| Sistema de coordenadas | `pixels_top_left` (origem canto superior esquerdo do PNG) |

| Página | Arquivo PNG | size_px (W×H) | SHA-256 |
|---|---|---|---|
| 10 | `90264135_p10_dpi200.png` | 2339×1653 | `f0cef06a74061d318d3994aa469bb829e9109c0c8667c6a2669ecf74819a2f0f` |
| 12 | `90264135_p12_dpi200.png` | 2339×1653 | `cf9cb4f5a8671d3b99bd79747dbd1780d9f292c2bee6b862d05cfa471e0be310` |
| 13 | `90264135_p13_dpi200.png` | 2339×1653 | `7e2f80f03872e4311cfc78e203af76a3aeca586c29df6cf501d30bde86323a81` |

Armazenamento raster: `.local/eva-val01-g1-overlays/` (gitignored). Hashes versionados em `overlays/overlay-registry.json`.

## Overlay ↔ PDF

Overlays de grade/células (`p{10,12,13}_cells_overlay.png` + zooms) foram regenerados nesta rodada a partir dos mesmos PNG DPI 200 e das mesmas bounding boxes dos JSON DRAFT. Nenhuma revisão alternativa do PDF foi misturada (`SOURCE_HASH_STATUS=MATCH`).

## Nota de autoridade

Esta verificação **não** homologa ground truth. Confirma apenas identidade da fonte e coerência render/coordenadas para revisão do owner.
