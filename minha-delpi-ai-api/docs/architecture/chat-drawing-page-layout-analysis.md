# Análise de layout de página — desenhos DELPI

> **Módulo canônico:** `ChatDrawingPageLayoutAnalysisService`  
> **Config:** `drawing_stamp.json` → `layoutAnalysis`  
> **Consumidor:** `ChatDrawingRegionService` (OCR regional antes da extração estruturada)

---

## Objetivo

Segmentar uma **página de desenho** em regiões semânticas (carimbo, título, BOM, cotas) antes do OCR, em vez de depender só de bounding boxes fixos. O pipeline segue o padrão de **Document Layout Analysis (DLA)** usado por engines documentais e VLMs (Azure prebuilt-layout + GPT-4o, MinerU 2.5, DocLayNet):

```text
Estágio 1 — Layout global (rápido, thumbnail)
  → XY-Cut recursivo (projeções horizontal/vertical)
  → blocos com bbox normalizado

Estágio 2 — Classificação semântica DELPI
  → stamp | title | bom | dimensions | drawing_body

Estágio 3 — OCR regional (existente)
  → ChatDrawingRegionService recorta cada região detectada
  → ChatPdfRegionOcrEngineService / fusão BOM
```

Referências externas: [CodeSOTA — Layout Analysis](https://www.codesota.com/ocr/layout-analysis), MinerU 2.5 (layout global → reconhecimento local em alta resolução), Azure Document Intelligence `prebuilt-layout`.

---

## Algoritmo (`xy_cut_semantic_v1`)

| Passo | Descrição |
|-------|-----------|
| 1 | Renderizar página (ou thumbnail ≤ `thumbnailMaxEdgePx`) |
| 2 | Binarizar (`binarizeThreshold`) — tinta escura = 1 |
| 3 | **XY-Cut:** cortes recursivos onde a projeção de tinta cai abaixo de 8% do pico (vales ≥ `xyCutMinGapRatio`) |
| 4 | Descartar blocos menores que `xyCutMinBlockAreaRatio` da área da página |
| 5 | Classificar cada bloco por posição, área, aspect ratio e densidade de tinta |
| 6 | Fundir blocos da mesma categoria → bbox semântico |
| 7 | Refinar com **priors estáticos** DELPI (`regionBboxes`) — blend ponderado pela confiança |
| 8 | Se confiança global < `minConfidenceForAdaptiveBboxes` → fallback 100% aos bboxes estáticos |

### Ordem de leitura

Coluna esquerda → direita; dentro da coluna, topo → base (mesma heurística de pipelines que não usam modelo neural de reading order).

---

## Regiões semânticas

| Região | Heurística principal | Uso downstream |
|--------|----------------------|----------------|
| `stamp` | Quadrante inferior direito; área moderada | Código DELPI, revisão, cliente |
| `title` | Faixa superior central; altura ≤ 16% | Descrição «CHICOTE DE LIGAÇÃO» |
| `bom` | Metade esquerda superior; densidade de texto/tabela | Lista de materiais |
| `dimensions` | Faixa central ampla | Cotas, decape, comprimentos |
| `drawing_body` | Área grande central (fallback de cotas) | Referência CAD / anotações |

---

## Contrato de metadata

Após OCR regional, `regions["_layoutAnalysis"]` em `parseMetadata` contém:

```json
{
  "algorithm": "xy_cut_semantic_v1",
  "confidence": 0.653,
  "usedStaticFallback": false,
  "semanticRegions": {
    "stamp": [0.5, 0.62, 1.0, 1.0],
    "bom": [0.0, 0.0, 0.55, 0.35]
  },
  "blocks": [{ "bbox": [], "category": "bom", "readingOrder": 0 }],
  "readingOrder": ["bom", "title", "dimensions", "stamp"]
}
```

Propagação:

```text
ChatPdfDocumentExtractionService._ocr_layout_regions
  → ChatDrawingRegionService.ocr_drawing_regions
  → parseMetadata.regions._layoutAnalysis
  → pdf_extract.pageLayoutAnalysis (ChatDrawingPdfExtractionService)
```

---

## Configuração (`drawing_stamp.json`)

| Chave | Default | Significado |
|-------|---------|-------------|
| `enabled` | `true` | Master switch |
| `thumbnailMaxEdgePx` | `1200` | Downscale para estágio 1 |
| `binarizeThreshold` | `210` | Limiar PIL (0–255) |
| `xyCutMinGapRatio` | `0.018` | Vale mínimo entre blocos |
| `xyCutMinBlockAreaRatio` | `0.003` | Área mínima do bloco |
| `xyCutMaxDepth` | `5` | Profundidade recursiva |
| `minConfidenceForAdaptiveBboxes` | `0.65` | Abaixo disso → bboxes estáticos |
| `staticFallbackConfidence` | `0.55` | Score reportado no fallback |

Bboxes estáticos permanecem em `regionBboxes` — usados como prior e fallback.

---

## Gate de confiança da validação (Onda 15.7)

Complementar ao layout: `ChatDrawingExtractionConfidenceService` + `ChatDrawingValidationAssertionService` aplicam limiar **≥ 95%** antes de reprovar por divergências PDF-dependentes.

| Camada | Módulo | Config |
|--------|--------|--------|
| Score composto | `ChatDrawingExtractionConfidenceService` | `drawing_validation.json` → `validationLayers.extractionConfidence` |
| Gate (demotion) | `resolve_gate_confidence` → `evaluate_for_extraction` / retry metadata | **Não** usar `evaluate()` com checklist (evita circularidade) |
| Demotion assertiva | `ChatDrawingValidationAssertionService` | `minConfidenceForPdfCritical: 0.95` |
| Orquestração | `ChatDrawingValidationOrchestrationService._apply_validation_layers` | metadata `validationLayers.extractionConfidence` |

Itens **autoritativos da API** (roteiro, inspeção) não são rebaixados.

### Retentativas de extração (qualidade ≥ 95%)

Antes da validação, `ChatDrawingExtractionQualityRetryService` repete a leitura do PDF com perfis escalonados até `targetConfidence` (default **95%**), esgotar `maxAttempts` ou detectar **estagnação**.

**Por que era lento e pesado:** cada região (carimbo, BOM, cotas) rasteriza a página e, no default global, rodava **Tesseract + EasyOCR**. EasyOCR carrega modelos PyTorch (~1–1.5 GB RAM) e executa por recorte; com 2–3 passagens e DPI alto, o WSL estourava memória (exit 137).

**Política atual:** o **loop de retry usa só Tesseract** (`extractionQualityRetry.regionOcrEngines: ["tesseract"]`). EasyOCR permanece disponível fora do loop (visão de documento / enriquecimento opcional), mas não entra nas retentativas de validação de desenho.

```text
ChatDrawingPdfExtractionService.extract_from_storage_path
  → ChatDrawingExtractionQualityRetryService.extract_until_confident
       motores: Tesseract only (override em ChatPdfRegionOcrEngineService)
       tentativa 1: standard (OCR regional automático)
       tentativa 2: high_dpi_tesseract (DPI × 1.5) — só se score < 95%
  → gc.collect() + libera cache EasyOCR entre tentativas (caso tenha sido usado antes)
  → ChatDrawingExtractionConfidenceService.evaluate_for_extraction
```

| `stoppedReason` | Significado |
|-----------------|-------------|
| `target_reached` | Score ≥ `targetConfidence` na tentativa corrente |
| `max_attempts` | Esgotou perfis sem atingir o alvo — retorna a **melhor** tentativa |
| `no_improvement` | Parada antecipada — score e códigos BOM não subiram vs. tentativa anterior |

Seleção da melhor tentativa: maior score → mais `componentCodes` → maior `charCount`.

Config (`drawing_stamp.json` → `extractionQualityRetry`):

| Chave | Default | Significado |
|-------|---------|-------------|
| `enabled` | `true` | Master switch |
| `targetConfidence` | `0.95` | Limiar para parar com sucesso |
| `maxAttempts` | `2` | Máximo de perfis (standard + DPI alto) |
| `regionOcrEngines` | `["tesseract"]` | **Só Tesseract** em todo o loop — sem EasyOCR |
| `releaseMemoryBetweenAttempts` | `true` | `gc` + libera readers EasyOCR entre passagens |
| `attempts[]` | ver JSON | `enableRegionOcr`, `regionOcrDpiMultiplier`, `layoutAnalysisEnabled` |

Metadata em `pdf_extract.extractionQualityRetry`: `attemptCount`, `selectedAttemptId`, `selectedScorePercent`, `meetsTarget`, histórico `attempts[]`.

**Operação:** retentativas com OCR regional + EasyOCR consomem RAM; default **2 passagens** com liberação de cache entre elas. Em WSL, parar serviços pesados (ex.: Ollama) antes de batch OCR; aumentar swap se necessário.

Doc relacionada: [playbook validação desenhos](../roadmap/melhorias/playbook_validacao_desenhos_delpi_roadmap.md) § Fase 15.7.

---

## Testes

| Arquivo | Escopo |
|---------|--------|
| `test_chat_drawing_page_layout_analysis_service.py` | XY-Cut sintético, integração region service |
| `test_chat_drawing_extraction_confidence_service.py` | Componentes de confiança + `evaluate_for_extraction` |
| `test_chat_drawing_extraction_quality_retry_service.py` | Retentativas até 95%, parada por estagnação |
| `test_chat_drawing_validation_assertion_service.py` | Demotion PDF vs API |
| `test_chat_drawing_validation_90264227.py` | Regressão FLEXTRONICS |

Smoke batch:

```bash
cd minha-delpi-ai-api
DRAWING_VALIDATE_CODES=90264227,90263622 python scripts/validate_drawing_samples.py
```

---

## Anti-padrões

1. **BBox fixo único** para todos os layouts de cliente — usar layout adaptativo + fallback estático.
2. **Classificar BOM só por regex global** — região primeiro (`ChatDrawingRegionalScopeService`).
3. **Reprovar BOM/cotas com OCR ruim** — gate 95% (`ChatDrawingValidationAssertionService`).
4. **Duplicar XY-Cut** no MFE ou no prompt do agente.

---

## Histórico

| Data | Entrega |
|------|---------|
| jun/2026 | `ChatDrawingPageLayoutAnalysisService` + integração OCR regional |
| jun/2026 | Gate confiança ≥95% na validação (`validationLayers`) |
| jun/2026 | Retentativas de extração até 95% (`ChatDrawingExtractionQualityRetryService`) |
