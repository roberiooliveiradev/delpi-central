# Arquitetura — Extração de PDF no chat base

**Status:** vigente (jun/2026)  
**Público:** desenvolvimento `minha-delpi-ai-api`  
**Relacionado:** [chat-intelligence-base.md](./chat-intelligence-base.md) · [playbook visão/OCR](../roadmap/melhorias/playbook_skill_visao_documentos_ocr_delpi.md) · [playbook OCR hierárquico desenhos](../roadmap/melhorias/playbook_ocr_hierarquico_desenhos_delpi.md)

---

## Princípio

**Leitura de PDF é transversal ao chat base.** Qualquer anexo PDF (boleto, contrato, desenho CAD, scan) passa pelo mesmo pipeline de extração multi-fonte. A skill **`drawing-analysis-delpi`** aplica **somente** regras DELPI (carimbo, BOM, cotas, validação API) sobre o texto já extraído — não reimplementa OCR nem leitura de anotações.

| Camada | Responsabilidade | Módulos |
|--------|------------------|---------|
| **Chat base** | Texto embutido, anotações ODA/CAD, fusão, tabelas por bbox, OCR regional condicional | `ChatPdf*` (domain) · `ChatDocumentVisionService` (application) |
| **Skill desenho** | Parse DELPI, resolução de código, BOM, 50xx, cotas, validação | `ChatDrawingPdfExtractionService` · `ChatDrawingPdfBomExtractionService` · `ChatDrawingIntermediateCodeService` · `ChatDrawingStampExtractionService` |
| **Config** | Perfis de layout, fusão, tolerância de linhas | `document_vision.json` (`pdfExtraction`) · `drawing_stamp.json` (regiões DELPI) |

---

## Pipeline

```text
PDF (storage_path)
  → ChatPdfEmbeddedTextService
        · page.get_text() (nativo)
        · page.annots() (conteúdo ODA/CAD + bbox)
        · metadados PDF (producer, title, …)
  → pypdf (fallback estágio 0)
  → [opcional] ChatDrawingRegionService.ocr_drawing_regions
        · perfil drawing_delpi + texto insuficiente (< pdfExtraction.regionOcr.minChars)
        · carimbo, BOM, cotas (config em drawing_stamp.json)
  → ChatPdfTextFusionService
        · prioriza fitz_embedded / anotações
        · complementa com pypdf e regiões não sobrepostas
  → ChatPdfAnnotationTableService
        · agrupa anotações por Y (tolerância em pdfExtraction.annotationTable)
        · linhas tabulares genéricas (qualquer PDF com anotações posicionadas)
  → ChatPdfDocumentExtractionService.extract_from_storage_path
        · retorna fullText, stages, parseMetadata, annotationTables

Consumidores:
  · ChatAttachmentTextExtractor — indexação de qualquer PDF (perfil generic)
  · ChatDocumentVisionService._stage_native — visão de documentos (perfil generic)
  · ChatDrawingPdfExtractionService.extract_from_storage_path — perfil drawing_delpi + parse DELPI
  · ChatDocumentVisionService (auto) — Tesseract/VLM quando legibilidade insuficiente
  · ChatDrawingLibraryService — PDF da biblioteca api-delpi quando não há anexo (jun/2026)
```

---

## Biblioteca corporativa (sem anexo PDF)

Quando o usuário pede análise de desenho **com código na mensagem** (ou chip de contexto) e **sem** `attachment_ids`, o pipeline não exige upload:

```text
Mensagem + código explícito (sem PDF anexado)
  → ChatDrawingAnalysisTurnService
        · resolve_explicit_codes_without_attachment (mensagem ou userContextItems)
        · não herda código do histórico
  → ChatToolContextPreTurnService
        · ChatDrawingLibraryService.fetch_pdf
              GET {DELPI_API_URL}/products/{code}/drawing
              GET {DELPI_API_URL}/products/{code}/drawing/pdf
        · cache em drawing-library-cache/{code}/
        · ChatDocumentVisionTurnService.run_drawing_vision_from_storage_path
  → get_product_analyser + ChatDrawingValidationOrchestrationService
```

| Regra | Comportamento |
|-------|----------------|
| Sem código e sem PDF | `build_missing_product_code_answer` (`drawing_query_intent.json`) |
| Código sem PDF na biblioteca | `build_drawing_library_not_found_answer` |
| Vários códigos na mensagem | Análise completa do **primeiro** neste turno; demais em `drawingProductCodes` no metadata |
| Com PDF anexado | Fluxo anterior (storage do anexo) — biblioteca não é consultada |

Rotas api-delpi: [14-desenhos-pdf.md](../../../api-delpi/docs/api/14-desenhos-pdf.md).

---

## Serviços (domain)

| Serviço | Função |
|---------|--------|
| `ChatPdfEmbeddedTextService` | PyMuPDF: texto nativo + anotações com `{page, content, bbox, type}` |
| `ChatPdfTextFusionService` | Fusão multi-fonte com score (embedded > anotações > regiões > pypdf) |
| `ChatPdfAnnotationTableService` | Tabelas a partir de bbox de anotações (cluster por linha Y) |
| `ChatPdfDocumentExtractionService` | Orquestrador; perfis `generic` e `drawing_delpi` |
| `ChatPdfRegionOcrEngineService` | OCR regional plugável (`tesseract`, `easyocr`, `paddleocr`) |
| `ChatPdfRegionOcrFusionService` | Fusão de linhas entre motores por região |
| `ChatDrawingBomRowSanitizationService` | Fantasmas de produto na BOM + códigos aninhados em descrição |
| `ChatDrawingPdfEmbeddedTextService` | Alias de compatibilidade → delega para `ChatPdfEmbeddedTextService` |

### Perfis de layout (`layoutProfile`)

| Perfil | Uso | OCR regional |
|--------|-----|--------------|
| `generic` | Indexação, intent «ler PDF», boletos, contratos | Desligado por padrão |
| `drawing_delpi` | `ChatDrawingPdfExtractionService`, análise de desenho | Ligado quando texto embutido &lt; limiar (`document_vision.json` → `pdfExtraction.layoutProfiles.drawing_delpi`) |

---

## Skill de desenho (camada DELPI)

| Serviço | Função |
|---------|--------|
| `ChatDrawingPdfExtractionService` | Fachada: carimbo, revisão, cotas, legibilidade |
| `ChatDrawingPdfBomExtractionService` | BOM + componentes + `bomSource` + sanitização de linhas |
| `ChatDrawingBomRowSanitizationService` | Remove fantasmas (título como código), promove códigos aninhados em 50xx, dedup OCR |
| `ChatDrawingIntermediateCodeService` | Códigos `50xx` e deduplicação OCR |
| `ChatPdfRegionOcrEngineService` | OCR por região: `tesseract`, `easyocr`, `paddleocr` |
| `ChatPdfRegionOcrFusionService` | Fusão de linhas multi-motor (prevalece linha com mais códigos) |
| `ChatDrawingPdfProductContextService` | `productCode` (carimbo / filename / BOM) |
| `ChatDrawingStampExtractionService` | Parse de carimbo e candidatos |
| `ChatDocumentVisionBomService` | Linhas BOM, score de fonte, ruído de revisão/carimbo, ruído PTC/°C |
| `ChatDrawingRegionalScopeService` | Escopo por domínio (`bom`, `dimensions`, `stamp`); rejeita carimbo OCR como BOM |
| `ChatDrawingValidationOrchestrationService` | Validação normativa e comparação API |
| `ChatDrawingDimensionsExtractionService` | Cotas, decapes E/D, cotas `6±140±1`, notas de processo |
| `ChatDrawingIntermediateSemanticsService` | Parse `comprimento/decapeE/decapeD` na descrição 50xx |
| `ChatDrawingStructureValidationService` | Checklist PDF × estrutura (BOM, 50xx, decapes por lado) |

`ChatDrawingPdfExtractionService` **não** abre o PDF com pypdf isolado — delega a `ChatPdfDocumentExtractionService` e aplica parse DELPI sobre `fullText` + `parseMetadata`.

Na análise de desenho no chat, `ChatDocumentVisionService.enrich_drawing_extract` **deve** chamar `_extract_drawing_pdf` → `ChatDrawingPdfExtractionService` (perfil `drawing_delpi` + OCR regional). O pipeline genérico `extract_from_storage_path` (`LAYOUT_GENERIC`, sem `region_ocr`) é só para anexos/documentos comuns.

**Container:** EasyOCR + Tesseract habilitados por padrão no dev — ver [vision-container-setup.md](../operations/vision-container-setup.md).

---

## Configuração (`document_vision.json`)

Seção **`pdfExtraction`**:

| Chave | Descrição |
|-------|-----------|
| `fusion.minEmbeddedChars` | Mínimo de caracteres embedded para confiar sem OCR regional |
| `annotationTable.rowClusterTolerancePt` | Tolerância vertical (pt) para agrupar células na mesma linha |
| `regionOcr.minChars` | Abaixo disso, perfil `drawing_delpi` pode acionar OCR por região |
| `regionOcr.engines` | Motores por região: `tesseract`, `easyocr`, `paddleocr` (ver [vision-container-setup.md](../operations/vision-container-setup.md)) |
| `regionOcr.bomFusion` | BOM: só `tesseract`+`easyocr`, pesos por motor e voto por dígito com confiança OCR (sem catálogo API) |
| `layoutProfiles.generic.enableRegionOcr` | `false` — chat base genérico não corta regiões DELPI |
| `layoutProfiles.drawing_delpi.enableRegionOcr` | `true` — permite fallback regional na skill desenho |

Regiões gráficas (bbox carimbo/BOM/cotas) e **padrões regex de cotas/decape** continuam em **`drawing_stamp.json`** (seção `patterns` / `patternLists` / `codeFamilies`).

### Famílias de PA e escopo BOM (jun/2026)

| Família | Prefixos | Na BOM |
|---------|----------|--------|
| Chicote folha | `9026` | MPs + 50xx |
| Montagem | `7026` | MPs + chicotes `9026` aninhados |
| Amostra | `8000`, `8001` | Como chicote folha (sem semântica de montagem) |

`ChatDrawingPdfExtractionService` resolve `productCode` **antes** de `validationScopes` e BOM. Fontes suplementares (`stamp_bom_table`, `full_text_section`, `cad_reference_bom`) entram via `ChatPdfBomSourceService` quando a região primária tem &lt; 2 códigos significativos.

Changelog: [`2026-06-drawing-bom-pa-families.md`](../changelog/2026-06-drawing-bom-pa-families.md).

Tolerâncias numéricas do checklist dimensional ficam em **`drawing_validation.json`** → `validationRules` (`decapeToleranceMm`, `lengthToleranceRatio`).

---

## Validação dimensional (PDF × descrição 50xx)

Orquestração: `ChatDrawingValidationOrchestrationService` → `ChatDrawingStructureValidationService.build_check_items`.

Roadmap de novos validadores (estrutura recursiva, inspeção, multipágina): [playbook Onda 15](../roadmap/melhorias/playbook_validacao_desenhos_delpi_roadmap.md).

### Extração de cotas (`ChatDrawingDimensionsExtractionService`)

Objeto `dimensions` no `pdf_extract`:

| Campo | Origem típica |
|-------|----------------|
| `leftDecapeMm` | `DECAPE ESQUERDO`, nota `DECAPAR O LADO DE X MM`, ou primeira cota `X±comprimento±tol` |
| `rightDecapeMm` | `DECAPE DIREITO`, nota global `DECAPE DE X MM` (quando E não preenchido) |
| `totalLengthMm` | `COMPRIMENTO TOTAL`, ou maior cota de trecho |
| `segmentLengthsMm` | Valores centrais das cotas `decape±comprimento±tolerância` |
| `cotaDecapeValuesMm` | Decapes únicos lidos nas cotas (ex.: `6` em `6±140±1`) |

Padrões em `drawing_stamp.json`:

| Chave | Exemplo no desenho |
|-------|-------------------|
| `decapeNote` | `DECAPE DE 6MM` (enrolamento — preenche E/D se ausentes) |
| `decapeMachineSide` | `DECAPAR O LADO DE 4MM NA MÁQUINA` → **sobrescreve** `leftDecapeMm` |
| `cotaDecapeLength` | `6±140±1` |
| `intermediateSegment` | `CT26VERM-00036/04/06-…` (parse na API, não no PDF) |

**Ordem de precedência (esquerdo):** rótulo `DECAPE E` → nota global → nota de máquina (ganha sobre global) → cota.

### Parse da descrição 50xx (`ChatDrawingIntermediateSemanticsService`)

Regex `intermediateSegment` extrai da SG1010:

```text
CT26VERM-00036/04/06-0000-0000  →  comprimento 36 mm, decape E 4 mm, decape D 6 mm
```

### Confronto no checklist (`ChatDrawingStructureValidationService`)

| Item template | Regra |
|---------------|-------|
| `decape_mismatch` | Decape do 50xx × PDF **somente no lado indicado** no desenho (`decapeIndication`) — ±1 mm |
| `decapes_ed` | Apenas indica se E e D foram **lidos** do PDF — não substitui confronto por código |
| `segment_length_pending` | Cotas de trecho no PDF × comprimentos 50xx (semânticas distintas; pode ficar pendente) |

Fallback: se o lado não tiver valor explícito, aceita qualquer candidato em `{leftDecapeMm, rightDecapeMm, cotaDecapeValuesMm}` dentro da tolerância.

**Anti-padrão corrigido (jun/2026):** usar um único `leftDecapeMm` global para validar **ambos** os lados e **todos** os 50xx — gerava falsos positivos quando a nota global era 6 mm e a descrição tinha `04/06`.

### Caso de referência: `90264206.pdf`

| Leitura | Valor |
|---------|-------|
| Nota enrolamento | `DECAPE DE 6MM` |
| Nota máquina | `DECAPAR O LADO DE 4MM` → `leftDecapeMm = 4` |
| Cotas | `6±140±1`, `6±150±1`, … → `cotaDecapeValuesMm = [6]` |
| Resultado | `50215423` / `50215424` (`04/06`) ✅; `50215431` / `50215432` (`2,5/06`) ❌ se cadastro divergir do 4 mm do desenho |

Testes: `test_chat_drawing_validation_90264206.py`, `test_chat_drawing_dimensions_extraction_service.py`.

---

## Caso de referência: PDF ODA (`90262019.pdf`)

Desenhos exportados pelo **ODA** expõem códigos e quantidades como **anotações Square** com `content` textual — não como texto selecionável na página.

| Fonte | Resultado típico |
|-------|------------------|
| pypdf / `get_text()` | ~55 caracteres (insuficiente) |
| `ChatPdfEmbeddedTextService` | 100+ anotações; códigos `90262019`, `10080591`, `10090481`, `10250032` |
| Pipeline completo | `engine: fitz_embedded`, estágio `native` apenas (~850 ms), sem Tesseract |

Testes: `test_chat_pdf_document_extraction_service.py`, `test_chat_drawing_pdf_embedded_text_service.py`.

---

## Integração com `ChatDocumentVisionService`

Estágios após extração base (`native`):

1. Gate de legibilidade (`CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS`, `ChatDrawingNativeTextGateService` em desenhos)
2. `tesseract_pdf` — página inteira + regiões DELPI quando habilitado
3. `docling` / `paddleocr` / `ollama_vlm` — backends opcionais (`CHAT_DOCUMENT_VISION_BACKEND`)

`_build_from_text` ainda enriquece com campos de desenho quando o consumidor é visão/análise DELPI; o **texto** vem do pipeline base.

---

## Testes e smoke

| Artefato | Escopo |
|----------|--------|
| `tests/unit/domain/services/test_chat_pdf_*.py` | Fusão, tabelas por anotação, fixture `90262019` |
| `tests/unit/domain/services/test_chat_drawing_assembly_pa_7026.py` | PA 7026/8000/8001, chicote aninhado, escopo BOM |
| `tests/unit/domain/services/test_chat_drawing_regional_scope_service.py` | Rejeição carimbo como BOM |
| `tests/unit/domain/services/test_chat_pdf_bom_source_service.py` | Fontes suplementares de BOM |
| `tests/unit/domain/services/test_chat_drawing_validation_90264206.py` | Decape E/D por lado; nota de máquina; regressão FLEXTRONICS |
| `tests/unit/application/services/test_chat_attachment_text_extractor.py` | Indexação via pipeline base |
| `scripts/smoke_document_vision.py` | Offline + live opcional |
| `desenhos/*.pdf` | Fixtures manuais (não versionar PDFs grandes em CI se política mudar) |

---

## Anti-padrões

1. **OCR ou parse de anotações só na skill desenho** — usar `ChatPdfDocumentExtractionService`.
2. **pypdf como única fonte** — perde anotações ODA/CAD.
3. **OCR regional sempre ativo** — só `drawing_delpi` + texto insuficiente.
4. **Strings PT de status OCR** em Python — `document_vision.json` / `assistant-content-json.mdc`.
5. **Duplicar fusão** em `ChatAttachmentTextExtractor` e `ChatDocumentVisionService` — um orquestrador.
6. **Reconciliar dígitos OCR com cadastro API** (`40091640` → `10091640`) — erro de leitura deve ser corrigido na **extração** (OCR multi-motor, região, parse), não por chute contra SG1010.
7. **Usar texto de BOM na região de cotas** para inferir decape — região `dimensionsText` contaminada ignora notas genéricas; prevalece `fullText` embutido com notas/cotas.

---

## Leitura vs. reconciliação (jun/2026)

| Abordagem | Quando usar |
|-----------|-------------|
| **Leitura** | OCR regional multi-motor, anotações ODA, fusão de linhas, parse de BOM/cotas/notas |
| **Saneamento semântico** | Código do **título** na BOM (fantasma), ruído de **revisão**, cabo-filho já sob 50xx |
| **Proibido** | Ajustar dígito lido porque «existe na API» — gera falso OK e mascara falha de OCR |
| **BOM multi-motor** | `ChatPdfRegionOcrFusionService.fuse_bom` — peso `tesseract`/`easyocr` + voto por dígito com confiança OCR |

Melhoria contínua de acurácia: `ChatPdfRegionOcrEngineService`, perfis em `document_vision.json`, homologação em `desenhos/`.

---

## Histórico

| Data | Entrega |
|------|---------|
| jun/2026 | Escopo BOM regional; famílias PA (`9026`/`7026`/`8000`/`8001`); fontes suplementares; ruído PTC — [`2026-06-drawing-bom-pa-families.md`](../changelog/2026-06-drawing-bom-pa-families.md) |
| jun/2026 | Decape E/D por lado; `decapeMachineSide`; candidatos de cota; regressão `90264206` |
| jun/2026 | `ChatPdf*` no chat base; skill desenho consome fusão; anotações ODA; BOM fallback multi-fonte |
