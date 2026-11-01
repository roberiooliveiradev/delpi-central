# 97 — EVA Drawing Intelligence R8.2.1: Graphic Boundary Detection, Region Ownership & BOM Semantic Correction

**Status:** CORRIGIDO + DEPLOYED (runtime verificado) — defeitos semânticos da avaliação autenticada resolvidos nos dois desenhos de regressão; E2E MCP autenticado `TEST_NOT_RUN` (sem sessão OAuth). **SHA:** `76a0f0dcee`. **Data:** 2026-11-01. Refs: docs 93–96.

## 1. Defeitos → correções

| Defeito observado | Correção |
|---|---|
| `x_min=-43,845 / x_max=3004,95` fora da página | `_clip_box` — todo bbox dentro `0..w/0..h` (render_size_px real, fallback max OCR) |
| Tabela contém texto administrativo | tokens `COD/DES/REV/CLIENTE/LMP/OV` excluídos das células por vocabulário de rótulo |
| `90264302`/`90264161` como componente | `product_code` excluído de células `component_code` e do compare |
| `10020033`/`10080106` falsos `missing` | `extracted_but_unclassified` — código visível no OCR mas fora de célula tipada nunca vira `missing_in_drawing_table` |
| Ownership só declarado | exclusividade efetiva: `tb_ids` removidos de `tbl_ids`/`revh_ids` antes do membership |

## 2. Evidência real — regressão

**`90264302` (92 tokens):**
- `title_block [1167.7,184.9,2006.2,318.2]` — dentro da página ✓ (era -43..3004)
- `component_table [0.0,73.0,2339.0,249.5]` — clipped válido
- BOM `COMPARED_PARTIAL` matched `[50226113,50226114]` + `unclassified[10080106,10020033]` — **sem falsa ausência** (miss=[])
- `rev:`→`00` + `643±2`/`663±2` preservados

**`90264161` (126 tokens):**
- `title_block` + `component_table` válidos, admin cells=0
- `90264161` **removido** de componentes (nib=[])
- BOM `NOT_COMPARABLE` fail-closed; dims `15550±50`,`10000±50` etc preservadas

## 3. Residuais honestos

- Primitivas gráficas via OpenCV (linhas/bordas como evidência de região) — ainda não implementadas; os bounds agora são token-derived+clipped (válidos, mas não line-derived). Próxima etapa bounded.
- 1 admin cell residual no 90264302 (valor não-vocabulário).
- `revh.candidate=false` — histórico não forma cluster ≥2 próprio.
- E2E MCP autenticado `TEST_NOT_RUN`.
- Multipage coverage por página — PENDING.
