# Changelog — Extração de PDF no chat base (jun/2026)

## Resumo

Leitura de PDF deixou de ser responsabilidade exclusiva da skill de desenho. O **chat base** extrai texto de qualquer PDF (nativo, anotações ODA/CAD, fusão com pypdf, tabelas por bbox). A skill **`drawing-analysis-delpi`** aplica apenas regras DELPI sobre o `fullText` já obtido.

## Entregas

| Área | Detalhe |
|------|---------|
| Domain | `ChatPdfEmbeddedTextService`, `ChatPdfTextFusionService`, `ChatPdfAnnotationTableService`, `ChatPdfDocumentExtractionService` |
| Integração | `ChatAttachmentTextExtractor`, `ChatDocumentVisionService._stage_native`, `ChatDrawingPdfExtractionService` |
| Config | `document_vision.json` → seção `pdfExtraction` |
| Caso ODA | `90262019.pdf` — códigos em anotações Square, sem OCR |
| Commit | `d0997361` — feat(chat): leitura genérica de PDF no chat base com fusão multi-fonte |

## Documentação

- [`architecture/chat-pdf-document-extraction.md`](../architecture/chat-pdf-document-extraction.md) — doc canônica
- Atualizados: `chat-intelligence-base.md`, `assistant-content-catalog.md`, playbooks Onda 13/14, visão/OCR, análise desenhos

## Testes

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_pdf_*.py \
  tests/unit/domain/services/test_chat_drawing_pdf_embedded_text_service.py \
  tests/unit/domain/services/test_chat_drawing_pdf_extraction_bom_fallback.py -q
```
