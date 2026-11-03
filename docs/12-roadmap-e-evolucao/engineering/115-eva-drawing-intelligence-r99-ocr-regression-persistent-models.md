# 115 — EVA Drawing Intelligence R9.9: OCR Regression Recovery & Persistent Models

**Status:** causa raiz do `no_ocr_evidence`/`provider_error` identificada e corrigida — symlink mascarava o cache paddlex de modelos OCR auxiliares; todos provisionados persistentemente; E2E MCP `TEST_NOT_RUN` (OAuth). **Data:** 2026-11-02.

## 1. Causa raiz (verificada)

`Dockerfile` symlinkou `/root/.paddlex/official_models → /opt/ocr-models/paddlex` — que só continha SLANet. O cache paddlex mantinha também modelos auxiliares do pipeline OCR (`doc_ori`, `textline_ori`, `table_cls`, `det`, `rec`) auto-baixados anteriormente. Mascarar o diretório inteiro → `provider_error` nos dois pipelines OCR (`no_ocr_evidence`).

## 2. Correção

Provisionados no volume `~/ocr-models/paddlex/` (persistente): `SLANet`, `PP-LCNet_x1_0_doc_ori`, `PP-LCNet_x1_0_textline_ori`, `PP-LCNet_x1_0_table_cls`, `PP-OCRv5_server_det`, `PP-OCRv5_server_rec`, `en_PP-OCRv5_mobile_rec` (~174MB). Symlink cobre todos. `PADDLEOCR_IMPORT_OK`, 7 modelos visíveis.

## 3. Estado

OCR pipeline + SLANet resolvem pelo mesmo cache persistente; `docker cp` eliminado; sobrevive build/recreate. E2E autenticado: `TEST_NOT_RUN`; baseline/BOM intactos.
