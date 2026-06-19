# Changelog — BOM de desenhos: escopo regional, famílias PA e amostras

**Data:** 19/06/2026  
**Commit:** `7fb01471`  
**Escopo:** falsos positivos/negativos na extração e validação de BOM em PDFs DELPI (Onda 14.5).  
**Arquitetura:** [`chat-pdf-document-extraction.md`](../architecture/chat-pdf-document-extraction.md) · [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)

Princípio: regras **canônicas no chat base** (`ChatDrawingRegionalScopeService`, `ChatPdfBomSourceService`, `ChatDocumentVisionBomService`, `ChatDrawingPatternsService`); vocabulário em `drawing_stamp.json` — sem patch no agente ou no MFE.

---

## Problema

Validação em lote (`desenhos/*.pdf`) expunha três classes de erro:

| Sintoma | Causa raiz |
|---------|------------|
| `componentCodes=[]` → «componente ausente no PDF» | Região `bom_region` capturava **carimbo/revisão** (`MEDIDAS EM MILÍMETRO`, `CLIENTE:`, tabela de revisão) em vez da lista de materiais |
| Códigos extras (`10084053` em `90262019`) | Ruído OCR em descrições de termistor/PTC (`°C` colado a MP `10xxxx`) |
| Chicotes `9026` tratados como fantasma em PA `7026` | Família de produto acabado limitada a prefixo `90`; montagens com chicote filho eram sanitizadas como código de título |

---

## 1 — Escopo regional de BOM

**Módulo canônico:** `ChatDrawingRegionalScopeService`

| Regra | Comportamento |
|-------|---------------|
| Rejeição de carimbo como BOM | `score_bom_text` penaliza layout de carimbo (`is_stamp_layout_without_bom`) quando há marcadores `bomStampLayoutWithoutTable` |
| Códigos significativos | Escopo aceito só se `meaningful_bom_component_codes` retorna ≥ 1 código (MP, 50xx ou PA aninhado válido) |
| `product_code` no escopo | `validationScopes` resolvido **depois** de `productCode` — exclusão correta do PA raiz na pontuação |
| Ordem na fachada | `ChatDrawingPdfExtractionService` resolve carimbo → `productCode` → `validationScopes` → BOM |

**Vocabulário (`drawing_stamp.json`):**

- `patternLists.bomStampLayoutWithoutTable` — `MEDIDAS EM MILÍMETRO`, `CLIENTE:`, `CHICOTE DE LIGA`, etc.
- `patternLists.bomRevisionNoise` — revisão, executado/liberado, resumo de modificação

---

## 2 — Fontes suplementares de BOM

**Módulo canônico:** `ChatPdfBomSourceService`

Quando a fonte primária (`bom_region`, anotações) traz **menos de 2** códigos significativos, o pipeline complementa:

| Fonte | Chave | Quando entra |
|-------|-------|--------------|
| Recorte de tabela no carimbo | `stamp_bom_table` | `extract_bom_table_slice(stampText)` |
| Texto completo | `full_text_section` | Marcadores `QTD. \| CÓDIGO` ou score ≥ 20 |
| Referência CAD | `cad_reference_bom` | `cadReferenceText` com mais códigos que a primária |

Fusão final: `ChatDocumentVisionBomService.resolve_from_sources` escolhe a fonte com maior score.

---

## 3 — Parsing de linhas BOM

**Módulo canônico:** `ChatDocumentVisionBomService`

| Melhoria | Exemplo |
|----------|---------|
| Coluna QTD antes do código | `A \| 01 \| 90263188 \| CHICOTE DE LIGACAO` |
| Ruído PTC/°C em descrição | Ignora MP capturada após `°C`, `PTC`, `TERMISTOR` (`bomDescriptionCodeNoise`) |
| Modo regional | `region_scoped=True` em fontes recortadas; `full_text_section` pode usar parse amplo |

---

## 4 — Famílias de produto acabado (PA)

**Módulo canônico:** `ChatDrawingPatternsService` + `drawing_stamp.json` → `codeFamilies`

| Família | Prefixos | Semântica na BOM |
|---------|----------|------------------|
| Chicote | `9026` | PA folha; MPs `10xxxx` e 50xx na BOM |
| Montagem | `7026` | PA folha de montagem; **chicotes `9026` aninhados** são componentes válidos |
| Amostra | `8000`, `8001` | Tratadas como chicote folha (não montagem); `9026` na BOM **não** é «chicote aninhado» |

Helpers expostos:

- `is_finished_product`, `is_assembly_pa`, `is_sample_pa`, `is_chicote_leaf_pa`
- `meaningful_bom_component_codes` — inclui `9026` quando PA raiz é `7026`; exclui promoção indevida em amostras

**Sanitização:** `ChatDrawingBomRowSanitizationService` respeita montagem vs. amostra ao remover fantasmas de título.

**Resolução de código:** `70260048.pdf` com carimbo `90263188` → prevalece **filename** (`70260048`).

Regex atualizados em `patterns.componentCode`, `finishedProductCode`, `filenameCode`, etc.

---

## 5 — Casos de referência

| PDF / cenário | Antes | Depois |
|---------------|-------|--------|
| `90262019` | Extra `10084053` (PTC/°C) | Ruído filtrado |
| `90263396` | BOM vazio → crítico falso | `bomAvailable=false` (pendente legítimo) |
| `70260048` + chicote `90263188` na BOM | `90263188` removido como fantasma | Mantido como componente |
| `80016332` (amostra) | `9026` tratado como aninhado | Comportamento de chicote folha |

---

## Testes de regressão

| Arquivo | Cobertura |
|---------|-----------|
| `test_chat_drawing_assembly_pa_7026.py` | PA 7026, 8000/8001, chicote aninhado, filename vs. carimbo |
| `test_chat_drawing_regional_scope_service.py` | Rejeição carimbo, escopo com `product_code` |
| `test_chat_pdf_bom_source_service.py` | Fontes suplementares |
| `test_chat_document_vision_bom_service.py` | Score, layout carimbo, linhas QTD |
| `test_chat_drawing_bom_row_sanitization_service.py` | Montagem 7026 |
| `test_chat_drawing_patterns_service.py` | Famílias PA |

---

## Commits relacionados (jun/2026)

| Commit | Entrega |
|--------|---------|
| `7fb01471` | Escopo BOM, famílias PA, fontes suplementares, ruído PTC |
| `055908dc` | Falso BOM extra em `90261656` |
| `3c1221f8` | Catálogo `GET /products/drawings` (api-delpi) |
| `ba43c118` | Dev Docker: FILESERVER para biblioteca PDF |

---

## Homologação local

| Item | Nota |
|------|------|
| Biblioteca PDF | `DRAWING_PDF_FILESERVER_HOST_PATH` em `infra/.env` — ver [14-desenhos-pdf.md](../../../api-delpi/docs/api/14-desenhos-pdf.md) |
| WSL sem `/mnt/x` | Apontar path para `minha-delpi-ai-api/desenhos/` |
| Batch | `api-delpi/scripts/validate_drawing_library.py` — relatórios locais não versionados |
