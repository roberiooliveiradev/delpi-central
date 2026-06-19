# Inteligência do chat — Onda 13: Skill de visão e OCR de documentos (chat base)

**Status:** MVP fechado (13.1–13.6 + intent `attachment_document`); **extração PDF no chat base** (`ChatPdf*`, jun/2026); refinamentos: profile `vision` em homologação, **OCR hierárquico desenhos** → [Onda 14](./inteligencia-chat-onda-14-ocr-hierarquico-desenhos.md) (jun/2026)  
**Criado:** 2026-05-31  
**Playbook:** [playbook_skill_visao_documentos_ocr_delpi.md](./melhorias/playbook_skill_visao_documentos_ocr_delpi.md) (`document-vision-delpi`) · regiões carimbo/BOM: [playbook OCR hierárquico](./melhorias/playbook_ocr_hierarquico_desenhos_delpi.md)  
**Pré-requisitos:** [Onda 12](./inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) MVP, [arquitetura chat base](../architecture/chat-intelligence-base.md)

---

## Objetivo

Implementar no **chat base** a skill **`document-vision-delpi`**: extração estruturada de PDFs e imagens (OCR + layout + VLM local opcional), reutilizável pela skill **`drawing-analysis-delpi`** e por anexos de sessão.

---

## Situação atual vs alvo

| Aspecto | Antes (pré-jun/2026) | Hoje |
|---------|----------------------|------|
| PDF anexo | Texto via pypdf + regex em `ChatDrawingPdfExtractionService` | **`ChatPdfDocumentExtractionService`** (embedded + anotações ODA + fusão + pypdf); parse DELPI só na skill desenho |
| Imagem | Tesseract via `ChatDocumentVisionService` (PNG/JPG/WebP) | OCR no contexto de anexo e no fluxo de desenho |
| Desenho técnico | Código/REV + BOM heurístico + `titleBlock` | + anotações CAD; BOM multi-fonte; OCR regional condicional |
| Skill plataforma | `document-vision-delpi` no catálogo | Policy + registry + métricas admin |
| Operação | Métricas + intent `attachment_document` | adminDebug + painel admin + audit por engine |

Doc canônica extração PDF: [`../architecture/chat-pdf-document-extraction.md`](../architecture/chat-pdf-document-extraction.md).

---

## Backlog por fase

### 13.1 — Contrato e skill

| ID | Entrega | Status |
|----|---------|--------|
| 13.1.1 | `DocumentVisionResult` (schema §5 do playbook) | ✅ |
| 13.1.2 | `ChatDocumentVisionService` + interface de backends | ✅ (`native`, `tesseract`, `auto`) |
| 13.1.3 | Skill `document-vision-delpi` em `catalog.json` + `document-vision-delpi-skill.md` | ✅ |
| 13.1.4 | `ChatSkillRegistry` + flags `documentVision` | ✅ |

### 13.2 — OCR clássico (CPU)

| ID | Entrega | Status |
|----|---------|--------|
| 13.2.1 | Rasterização PDF (PyMuPDF/pdf2image) | ✅ (PyMuPDF/fitz) |
| 13.2.2 | Backend `tesseract` multipágina + crop carimbo | ✅ (faixa superior + canto sup. direito na pág. 1) |
| 13.2.3 | Testes V1–V5 + fixtures | ✅ (`test_chat_document_vision_service.py`) |

### 13.3 — Layout neural (profile vision)

| ID | Entrega | Status |
|----|---------|--------|
| 13.3.1 | Backend `docling` (MIT) ou `paddleocr` (Apache 2.0) | ✅ (wired; requer `requirements-vision.txt` / profile `vision`) |
| 13.3.2 | Extração de tabelas BOM | ✅ (heurística `bomRows` + `bom_heuristic` em texto OCR) |

### 13.4 — Integração drawing (Onda 12 Fase 3)

| ID | Entrega | Status |
|----|---------|--------|
| 13.4.1 | `ChatDrawingPdfExtractionService` consome `DocumentVisionResult` | ✅ (`enrich_drawing_extract` no tool context) |
| 13.4.2 | Validação dimensional usa cotas/decapes do vision | ✅ (merge dimensions no parse) |

### 13.5 — VLM local (opcional)

| ID | Entrega | Status |
|----|---------|--------|
| 13.5.1 | Backend `ollama_vlm` (Qwen2.5-VL) com JSON schema | ✅ (`/api/chat` + imagens; fallback `auto` se indisponível) |

### 13.6 — UX, testes e ops

| ID | Entrega | Status |
|----|---------|--------|
| 13.6.1 | Stream + adminDebug `documentVision` | ✅ (stream `document_vision`; adminDebug fase `document_vision`) |
| 13.6.2 | `scripts/smoke_document_vision.py` | ✅ |
| 13.6.3 | Compose profile `vision` + `requirements-vision.txt` | ✅ (profile `vision`; `Dockerfile.vision.dev`; extras Docling backlog) |
| 13.6.4 | Métricas admin (opcional) | ✅ (`documentVisionMetrics`, audit, `GET /admin/metrics/document-vision/summary`) |

---

## Validação prevista

```bash
# Rebuild padrão (Tesseract + native)
docker compose -f infra/docker-compose.dev.yml build minha-delpi-ai-api minha-delpi-chat
docker compose -f infra/docker-compose.dev.yml --profile chat up -d --force-recreate minha-delpi-ai-api minha-delpi-chat

# Opcional — imagem vision (descomente pacotes em requirements-vision.txt antes)
docker compose -f infra/docker-compose.dev.yml -f infra/docker-compose.vision.yml \
  --profile chat build minha-delpi-ai-api

docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  bash scripts/run_onda13_validation.sh
```

Variáveis: ver tabela `CHAT_DOCUMENT_VISION_*` no [README da API](../../README.md).

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-05-31 | Criação da Onda 13 a partir do playbook de visão/OCR. |
| 2026-05-31 | MVP: `ChatDocumentVisionService`, skill `document-vision-delpi`, OCR PDF Tesseract + integração drawing. |
| 2026-05-31 | OCR de imagens (PNG/JPG/WebP) no anexo e no fluxo de desenho; enrich sem depender só de `attachment_context`. |
| 2026-05-31 | Stream `document_vision` no chat; README com env vars; validação container + smokes. |
| 2026-05-31 | Métricas `documentVisionMetrics` + endpoint admin summary; profile compose `vision`. |
| 2026-05-31 | `documentVision`/`documentVisionTrace` em turnos só com anexo (PDF indexado → snapshot native leve). |
| 2026-05-31 | Intent `attachment_document` (leitura de anexo sem planejar OpenAPI); painel admin Métricas visão/OCR. |
| 2026-05-31 | Crop carimbo Tesseract, fallback OCR em indexado curto, `run_onda13_validation.sh`, adminDebug MFE visão. |
| 2026-05-31 | BOM heurístico (`ChatDocumentVisionBomService`); fast path desligado em `attachment_document`. |
| 2026-05-31 | Backends `docling`, `paddleocr` e `ollama_vlm` wired com fallback; testes de contrato neural/VLM. |
| 2026-05-31 | `titleBlock`, `bomRows` no resultado; métricas `byStage`; compose `docker-compose.vision.yml`. |
| 2026-05-31 | Persistência `metadata.documentVision` no anexo (index + turno); `bomHints` no merge desenho. |
| 2026-05-31 | `tables[]` heurístico; `documentVisionSummary` na API de anexos; Docling em `requirements-vision.txt`. |
