# Limites de leitura de arquivos — workspace e anexos

**Status:** vigente (jun/2026)  
**Público:** desenvolvimento e operação  
**Pipeline:** `ChatWorkspaceFileTextExtractionService` → `ChatAttachmentTextExtractor` (fachada)  
**Relacionado:** [playbook-17](../roadmap/playbook-17-importacao-arquivos-e-fontes-unificada.md) · [chat-pdf-document-extraction.md](./chat-pdf-document-extraction.md) · [chat-attachment-storage.md](../operations/chat-attachment-storage.md)

---

## O que este documento cobre

Limites aplicados na **extração de texto para indexação** (anexo de sessão, fonte de projeto/agente, conhecimento admin). Não substitui:

| Fluxo | Onde ver limites |
|-------|------------------|
| Visão de documento no turno (VLM, Docling, OCR completo) | `CHAT_DOCUMENT_VISION_*`, `document_vision.json`, [playbook visão/OCR](../roadmap/melhorias/playbook_skill_visao_documentos_ocr_delpi.md) |
| Análise de desenho DELPI | `CHAT_DRAWING_PDF_MAX_PAGES` (padrão **10**), perfil `drawing_delpi` |
| Chunking RAG pós-extração | `IngestKnowledgeDocumentUseCase` / pipeline de embeddings (sem truncar o texto extraído antes do chunk) |

---

## 1. Upload (antes da leitura)

Política canônica: `WorkspaceFileIngestPolicyService` · `GET /chat/ingest/policy`.

| Limite | Valor | Onde alterar |
|--------|-------|--------------|
| Tamanho máximo | **25 MB** por arquivo | Código: `_MAX_SIZE_BYTES` em `workspace_file_ingest_policy_service.py` |
| Arquivo vazio | Rejeitado | `attachments.json` → `ingestUi.workspace.fileEmpty` |

### Extensões permitidas por família

| Família | Extensões |
|---------|-----------|
| `session_attachment` | `.pdf` `.txt` `.md` `.doc` `.docx` `.xls` `.xlsx` `.csv` `.json` `.png` `.jpg` `.jpeg` `.webp` |
| `agent_source` / `project_source` / `global_knowledge` | `.pdf` `.txt` `.md` `.doc` `.docx` `.xls` `.xlsx` `.csv` `.json` |
| `context_paste` | `.txt` `.md` `.csv` `.tsv` `.json` |

Imagens **não** entram em fontes de projeto/agente/admin — só em anexo de sessão.

---

## 2. Resumo por formato (extração na indexação)

| Formato | Extrator | Truncamento na leitura | Falha típica |
|---------|----------|------------------------|--------------|
| `.txt` `.md` | UTF-8 (`errors=ignore`) | **Nenhum** — arquivo inteiro | — |
| `.json` | parse + pretty-print | **Nenhum** — fallback texto bruto se JSON inválido | — |
| `.csv` | `csv.reader` | **300 linhas** (`fileExtraction.csvMaxRows`) | — |
| `.xlsx` | openpyxl (`read_only`) | **10 planilhas** × **300 linhas/planilha** | planilha vazia → `unsupported` |
| `.xls` | xlrd | Mesmos limites de planilha/linha que `.xlsx` | parse falhou → hint `legacy_xls_format` |
| `.docx` | python-docx | **Nenhum** explícito — parágrafos + tabelas | vazio → `unsupported` |
| `.doc` | antiword | **Nenhum** explícito — saída texto | sem `antiword` ou timeout → `legacy_doc_format` |
| `.pdf` | `ChatPdfDocumentExtractionService` | **Até N páginas** (ver §3) | texto vazio após OCR → `index_failed` |
| `.png` `.jpg` … | metadados ± OCR | OCR: **4000 caracteres** (`CHAT_ATTACHMENT_IMAGE_OCR_MAX_CHARS`) | sem OCR: só metadados + prompt ao usuário |

Config declarativa office/CSV: `attachments.json` → `fileExtraction`.  
PDF e OCR de indexação: `document_vision.json` → `pdfExtraction`.

---

## 3. PDF na indexação

Orquestrador: `ChatPdfDocumentExtractionService.extract_for_attachment_index`.

### Páginas lidas (texto embutido + pypdf + anotações)

| Parâmetro | Padrão | Variável / JSON |
|-----------|--------|-----------------|
| Limite de páginas na indexação | **20** | `CHAT_ATTACHMENT_INDEX_PDF_PAGE_LIMIT` (env) |
| Fallback quando `page_limit` não é passado no serviço | **20** | Mesma env (usada em `extract_from_storage_path`) |

Anexo de sessão passa explicitamente `pdf_page_limit=Settings.CHAT_ATTACHMENT_INDEX_PDF_PAGE_LIMIT`. Fontes de projeto/agente/admin **não** passam `pdf_page_limit`, mas o orquestrador PDF ainda usa o mesmo default de env (**20**).

Páginas além do limite **não entram** no texto indexado. O preview pode expor `pageLimit` para o aviso de arquivo extenso (§5).

### PDF escaneado (OCR Tesseract na indexação)

Acionado quando o texto embutido/fusionado fica **abaixo de 120 caracteres** (`pdfExtraction.regionOcr.minChars`).

| Parâmetro | Padrão | Variável / JSON |
|-----------|--------|-----------------|
| Habilitado | `true` | `pdfExtraction.attachmentIndex.pageOcrWhenEmbeddedBelowMinChars` |
| Páginas rasterizadas no OCR | **10** se `page_limit` omitido; senão **mesmo `page_limit` do turno** | `pdfExtraction.attachmentIndex.maxPages` |
| DPI de rasterização | **200** | `CHAT_DOCUMENT_VISION_DPI` |
| Idioma Tesseract | `por+eng` | `CHAT_DOCUMENT_VISION_TESSERACT_LANG` |

Estágio gravado em metadata: `attachment_index_tesseract`. **Não** usa regiões DELPI nem EasyOCR — só Tesseract página inteira.

### O que o PDF genérico não faz na indexação

- OCR regional de desenho (`drawing_delpi`) — reservado à skill de desenho.
- Visão completa (`ChatDocumentVisionService`) — por padrão **adiada** (`CHAT_ATTACHMENT_DEFER_VISION_ON_INDEX=true`).

---

## 4. Office legado e subprocessos

| Formato | Dependência | Timeout |
|---------|-------------|---------|
| `.doc` | binário `antiword` no container (`Dockerfile.prod` / `Dockerfile.dev`) | **30 s** — `fileExtraction.subprocessTimeoutSeconds` |
| `.xls` | pacote Python `xlrd` | — |

Hints ao usuário quando a leitura falha: `attachments.json` → `fileExtraction.legacyFormats` e `preview.indexReason`.

---

## 5. Imagens (anexo de sessão)

| Condição | Comportamento |
|----------|---------------|
| `attachmentImageOcrEnabled` = false (runtime admin) | Indexa **metadados** (nome, dimensões); conteúdo pede descrição ao usuário |
| OCR habilitado | Tesseract; texto truncado em **4000** chars (`CHAT_ATTACHMENT_IMAGE_OCR_MAX_CHARS`) |
| Idioma | `CHAT_ATTACHMENT_IMAGE_OCR_LANG` (padrão `por+eng`) |

---

## 6. Arquivo extenso (aviso UX — não é corte na extração)

Após indexação, `ChatAttachmentLargeFileService` marca anexo «extenso» quando o preview atinge:

| Limiar | Valor | JSON |
|--------|-------|------|
| Caracteres extraídos | **120 000** | `attachments.json` → `largeFile.charThreshold` |
| Páginas (PDF) | **40** | `attachments.json` → `largeFile.pageThreshold` |

Isso **não trunca** a extração — apenas exibe aviso e chips de trabalho por seção (`largeFile.body` / `largeFile.chips`).

---

## 7. Tabela de configuração (fonte de verdade)

### `attachments.json` → `fileExtraction`

| Chave | Valor atual | Efeito |
|-------|-------------|--------|
| `csvMaxRows` | 300 | Máximo de linhas CSV indexadas |
| `xlsxMaxSheetLimit` | 10 | Planilhas lidas (.xlsx e .xls) |
| `xlsxMaxRowsPerSheet` | 300 | Linhas por planilha |
| `subprocessTimeoutSeconds` | 30 | Timeout do `antiword` em `.doc` |

### `document_vision.json` → `pdfExtraction`

| Chave | Valor atual | Efeito |
|-------|-------------|--------|
| `regionOcr.minChars` | 120 | Gatilho OCR Tesseract na indexação de PDF |
| `attachmentIndex.pageOcrWhenEmbeddedBelowMinChars` | true | Liga/desliga OCR de indexação |
| `attachmentIndex.maxPages` | 10 | Teto de páginas OCR quando `page_limit` omitido |
| `fusion.minEmbeddedChars` | 80 | Confiança na fusão (não é gatilho de index OCR) |

### Variáveis de ambiente (extração / indexação)

| Variável | Padrão | Efeito |
|----------|--------|--------|
| `CHAT_ATTACHMENT_INDEX_PDF_PAGE_LIMIT` | 20 | Páginas PDF na extração de indexação |
| `CHAT_ATTACHMENT_IMAGE_OCR_MAX_CHARS` | 4000 | Teto OCR em imagens |
| `CHAT_ATTACHMENT_IMAGE_OCR_LANG` | por+eng | Idioma OCR imagem |
| `CHAT_DOCUMENT_VISION_DPI` | 200 | DPI rasterização PDF→imagem (index OCR) |
| `CHAT_ATTACHMENT_DEFER_VISION_ON_INDEX` | true | Não roda visão completa no index |

---

## 8. Limitações conhecidas (comportamento atual)

1. **PDF longo** — só as primeiras N páginas (§3) entram no RAG; o restante exige novo envio, recorte ou pergunta por seção.
2. **Planilha grande** — linhas/planilhas além do limite são **silenciosamente omitidas** na extração.
3. **DOCX** — não extrai texto de imagens embutidas nem caixas de texto complexas fora do modelo python-docx.
4. **DOC** — qualidade depende do `antiword`; documentos muito antigos ou protegidos podem falhar.
5. **CSV** — delimitador inferido nos primeiros **4096** bytes (`;` vs `,`); arquivo inteiro é lido para as linhas.
6. **Imagem sem OCR** — indexação não descreve o visual automaticamente.
7. **Contexto efêmero** — família `context_paste` não persiste arquivo nem indexa RAG; só texto no chip.

---

## 9. Código de referência

| Módulo | Responsabilidade |
|--------|------------------|
| `ChatWorkspaceFileTextExtractionService` | Leitura canônica por extensão |
| `ChatAttachmentTextExtractor` | Fachada para use cases |
| `WorkspaceFileIngestPolicyService` | Tamanho e extensões por família |
| `ChatPdfDocumentExtractionService.extract_for_attachment_index` | PDF + OCR de scan |
| `ChatPdfPageTesseractOcrService` | Tesseract página inteira (index) |
| `ChatAttachmentImageOcrService` | OCR opcional em imagens |
| `ChatAttachmentLargeFileService` | Aviso pós-index (extenso) |
| `IndexChatAttachmentUseCase` | Passa `pdf_page_limit` na indexação de sessão |

---

## 10. Testes de regressão

| Arquivo | Escopo |
|---------|--------|
| `test_chat_workspace_file_text_extraction_service.py` | docx, xlsx, doc, xls |
| `test_chat_attachment_content_file_extraction.py` | Limites JSON |
| `test_chat_pdf_attachment_index_ocr.py` | Gatilho OCR na indexação |
| `test_workspace_file_ingest_policy_service.py` | Extensões e tamanho |
