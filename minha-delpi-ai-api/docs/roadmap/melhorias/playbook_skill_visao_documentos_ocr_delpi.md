# Playbook — Skill de Visão e OCR de Documentos DELPI (chat base)

> **Status (31/05/2026):** Backlog — playbook aprovado para implementação; código ainda não iniciado.  
> **Projeto:** Minha DELPI Chat IA  
> **Arquitetura:** serviço transversal no [chat base](../../architecture/chat-intelligence-base.md); **não** duplicar OCR no `system_prompt` de agentes.  
> **Consumidor principal:** [skill `drawing-analysis-delpi`](./playbook_skill_analise_desenhos_delpi.md) (Onda 12, Fase 3 — cotas e carimbo).  
> **Roadmap sugerido:** [Onda 13](../inteligencia-chat-onda-13-skill-visao-documentos-ocr.md) (criar após aprovação deste playbook).

| Campo | Valor proposto |
|-------|----------------|
| `skillKey` (canônico) | `document-vision-delpi` |
| `skillKey` (aliases) | `pdf-ocr-delpi`, `ocr-delpi`, `visao-documentos` |
| Nome amigável | Visão e OCR de documentos DELPI |
| `policyFile` (proposto) | `document-vision-delpi-skill.md` |
| `metadataFlag` | `documentVision` |
| Serviço central (proposto) | `ChatDocumentVisionService` |
| Extração legada (hoje) | `ChatDrawingPdfExtractionService` + `ChatAttachmentTextExtractor` (pypdf) + `ChatAttachmentImageOcrService` (Tesseract opcional em imagens) |

---

## 1. Objetivo

Oferecer no **chat base** uma capacidade **reutilizável** de ler documentos (PDF, imagens de desenho, scans) e devolver um **JSON estruturado e auditável** — texto, layout, tabelas, carimbo, cotas quando detectáveis — para skills e fluxos downstream (análise de desenho, anexos de sessão, indexação, RAG).

Princípios:

1. **Uma implementação, vários consumidores** — `drawing-analysis-delpi` chama o serviço; anexos genéricos e admin knowledge podem reutilizar o mesmo motor.
2. **Local-first** — processamento no cluster DELPI (WSL/Docker); sem enviar PDF confidencial a APIs cloud por padrão.
3. **Pipeline em camadas** — texto nativo do PDF → OCR clássico → layout/OCR neural → VLM local (opcional), com fallback e telemetria por estágio.
4. **Licença compatível com produto** — priorizar **Apache 2.0** e **MIT**; GPL (Surya/Marker) só com aval jurídica explícita.

---

## 2. Pesquisa — ferramentas open source (2025–2026)

Síntese de benchmarks e documentação pública (CodeSOTA, Unstract, Modal, IBM Docling, repositórios oficiais). Valores de acurácia variam por tipo de documento; desenhos técnicos CAD/PDF vetorial exigem **rasterização + OCR/VLM**, não só extração programática.

### 2.1 Matriz comparativa (resumo)

| Ferramenta | Licença | Melhor para | CPU/GPU | Desenhos técnicos / carimbo | Tabelas / layout | PT-BR | Nota DELPI |
|------------|---------|-------------|---------|----------------------------|------------------|-------|------------|
| **pypdf / pdfplumber** | BSD/MIT | PDF com texto embutido | CPU | Fraco (só texto se existir no PDF) | Fraco | N/A | Já usado; manter como **estágio 0** |
| **Tesseract 5.x** | Apache 2.0 | Texto impresso limpo, edge | CPU (~10 MB) | Médio em scan; fraco em cotas finas | Fraco | Bom (`por+eng`) | Já parcial via `ChatAttachmentImageOcrService` |
| **RapidOCR** | Apache 2.0 | Leve, wrapper ONNX | CPU/GPU | Médio | Médio | Bom | Boa opção **leve** se Paddle pesar |
| **PaddleOCR v4/v5** | Apache 2.0 | Produção, 80+ idiomas, PP-Structure | GPU recomendado | Bom em scan rasterizado | **Forte** | **Forte** | **Recomendado estágio 2** self-hosted |
| **docTR** | Apache 2.0 | PyTorch/TF, documentos | GPU | Médio | Bom | Bom | Alternativa ao Paddle |
| **EasyOCR** | Apache 2.0 | Protótipo rápido | GPU | Médio | Médio | Bom | Menor prioridade (acurácia inferior em benchmarks 2026) |
| **Docling** | MIT | PDF→Markdown/JSON, layout Heron + TableFormer | CPU/GPU | Bom em multipágina; preserva ordem de leitura | **Muito forte** | OCR embutido | **Recomendado estágio 3** “document AI” |
| **Granite-Docling-258M** | Apache 2.0 | VLM compacto IBM, DocTags | GPU leve | Bom em elementos complexos | Forte | Sim | Candidato **VLM local** integrado ao Docling |
| **Surya** | **GPL 3.0** | Layout, 90+ idiomas | GPU | Forte | Forte | Sim | Evitar em produto fechado sem parecer jurídico |
| **Marker** (Datalab) | OpenRAIL + depende Surya | PDF→MD | GPU | Forte | Forte | Sim | Mesma ressalva GPL/indireta |
| **GOT-OCR 2.0** | Apache 2.0 | Layout denso, fórmulas | GPU | Forte | Muito forte | Multi | Candidato estágio 4 se Docling insuficiente |
| **Qwen2.5-VL / Qwen3-VL** | Apache 2.0 (modelo) | OCR + raciocínio visual | GPU | **Forte** em carimbo/cotas com prompt | Forte | **Forte** | Via **Ollama** já no compose — estágio **VLM opcional** |
| **Unstructured** | Apache 2.0 | Ingest 65+ formatos | Variável | Médio | Bom | Sim | Mais pesado operacionalmente; avaliar vs Docling |

### 2.2 Referências úteis

| Recurso | URL |
|---------|-----|
| Comparação Python OCR 2026 | https://www.codesota.com/ocr/best-for-python |
| Open-source OCR tools (Unstract) | https://unstract.com/blog/best-opensource-ocr-tools/ |
| 8 modelos OCR (Modal) | https://modal.com/blog/8-top-open-source-ocr-models-compared |
| Docling (IBM) | https://github.com/docling-project/docling |
| PaddleOCR | https://github.com/PaddlePaddle/PaddleOCR |
| Qwen2-VL / document parsing | https://github.com/QwenLM/Qwen2-VL |
| Ollama Qwen2.5-VL | https://ollama.com/search?q=qwen2.5vl |

---

## 3. Recomendação arquitetural DELPI

### 3.1 Estratégia em estágios (motor plugável)

```text
Entrada: storage_path | bytes | página(s) PDF
  → Estágio 0: texto programático (pypdf/pdfplumber) — rápido, zero GPU
  → Estágio 1: rasterizar páginas (PyMuPDF ou pdf2image + Poppler)
  → Estágio 2: OCR clássico (Tesseract por página ou região de carimbo)
  → Estágio 3: OCR neural + layout (PaddleOCR PP-OCR + PP-Structure OU Docling)
  → Estágio 4 (opcional): VLM local Ollama (qwen2.5vl:7b) com schema JSON fixo
  → Saída: DocumentVisionResult (schema §5)
```

**Política de seleção (`CHAT_DOCUMENT_VISION_BACKEND`):**

| Valor | Comportamento |
|-------|----------------|
| `auto` (default) | 0 → se legibilidade &lt; limiar, 1+2; se PDF scan/heavy layout, 3; se `engineering` flag e cotas, tentar 4 |
| `native` | Só estágio 0 |
| `tesseract` | 0+1+2 |
| `paddleocr` | 0+1+3 (motor Paddle) |
| `docling` | 0+3 (Docling unificado) |
| `ollama_vlm` | 0+1+4 (mais lento; só com GPU/RAM) |

### 3.2 Por que não um único motor?

| Cenário | Motor ideal |
|---------|-------------|
| PDF “digital” com texto selecionável | Estágio 0 (ms) |
| Foto/scan de folha de desenho | PaddleOCR ou Docling |
| Carimbo + tabela de materiais | Layout (Docling/Paddle Structure) ou crop heurístico + OCR |
| Cotas e símbolos gráficos | VLM (Qwen2.5-VL) com prompt de extração + validação cruzada API |
| Homologação local sem GPU | Tesseract + estágio 0 |
| Produção com GPU no compose | Docling ou Paddle + VLM sob demanda |

### 3.3 Alinhamento com stack atual

| Componente existente | Papel após a skill |
|---------------------|-------------------|
| `delpi-ollama` + `qwen2.5:3b` | LLM texto; **não** substitui OCR — considerar imagem `qwen2.5vl` separado |
| `ChatAttachmentImageOcrService` | Absorvido/evoluído para `ChatDocumentVisionService.extract_image` |
| `ChatDrawingPdfExtractionService` | Passa a **consumir** `DocumentVisionResult` em vez de só regex em texto pypdf |
| `CHAT_DRAWING_PDF_MAX_PAGES` | Reutilizar como limite global de páginas vision |

---

## 4. Skill de plataforma `document-vision-delpi`

### 4.1 Escopo da skill

| Inclui | Não inclui |
|--------|------------|
| Extrair texto e estrutura de PDF/imagem anexados | Consultar Protheus (`get_product_analyser`) — skill `drawing-analysis-delpi` |
| Detectar legibilidade e motivo de falha | Decidir aprovação/reprovação de desenho |
| Devolver schema JSON para outros serviços | Substituir RAG de normas |
| Rodar offline no worker/API | Chamar OpenAI/Google Vision em produção (opt-in futuro separado) |

### 4.2 Quando acionar

**Automático (sem pedido explícito):**

- Anexo PDF/imagem em sessão **e** outra skill ou intent exige visão (`drawingAnalysisMode`, futuro “extrair dados do anexo”).
- Pipeline de indexação de anexo (`session_source`) com flag `useDocumentVision=true`.

**Explícito (mensagem):**

- “extrair texto do pdf”, “ocr deste anexo”, “ler carimbo do desenho”, “digitalizar este documento”.

**Não acionar:**

- PDF já com texto legível suficiente no estágio 0 **e** consumidor só precisa de código/revisão (fast path native).

### 4.3 Herança por agente

| Agente | Default skill |
|--------|----------------|
| Engenharia / qualidade | `documentVision: true` quando `drawing-analysis-delpi` ativa |
| Operacional genérico | `false` — só estágio 0 em anexos |
| Admin / knowledge | `true` para ingestão curatorial (futuro) |

Registro: `catalog.json`, `ChatSkillRegistry`, policy `document-vision-delpi-skill.md`, `metadata.skills.document-vision-delpi`.

---

## 5. Contrato de saída (`DocumentVisionResult`)

Schema versionado (`schemaVersion: "1.0"`) para metadata, audit e merge com desenho.

```json
{
  "schemaVersion": "1.0",
  "engine": "docling",
  "engineVersion": "2.96.0",
  "stages": ["native", "rasterize", "docling"],
  "durationMs": 4200,
  "pageCount": 2,
  "pagesProcessed": 2,
  "legible": true,
  "legibilityScore": 0.82,
  "warnings": [],
  "productCode": "90260140",
  "revision": "01",
  "customer": "CLIENTE X",
  "titleBlock": {
    "rawText": "...",
    "bbox": [0.72, 0.85, 0.98, 0.98],
    "fields": { "code": "90260140", "rev": "01" }
  },
  "bomHints": [
    { "componentCode": "50123456", "qty": "2", "evidence": "page 1 table" }
  ],
  "dimensions": [
    { "label": "comprimento total", "valueMm": 1250.0, "tolerance": "±5%", "confidence": 0.71 }
  ],
  "decapes": [
    { "side": "left", "valueMm": 12.5 },
    { "side": "right", "valueMm": 12.5 }
  ],
  "intermediateCodes": ["50123456"],
  "fullText": "...",
  "markdown": "...",
  "tables": [],
  "perPage": [
    { "page": 1, "charCount": 1200, "ocrUsed": true, "thumbnailRef": null }
  ]
}
```

Campos obrigatórios mínimos MVP: `engine`, `stages`, `legible`, `legibilityScore`, `productCode?`, `revision?`, `fullText`, `durationMs`.

Persistência sugerida: `metadata.documentVision` na mensagem ou no attachment; audit `metadata.documentVision` em `ai_audit_logs` (espelho drawing metrics).

---

## 6. Integração no pipeline do chat

```text
Upload anexo
  → ChatAttachmentTextExtractor (estágio 0 — mantém)
  → [NOVO] ChatDocumentVisionService.enrich(attachment)
        · respeita skill document-vision-delpi + settings
        · grava DocumentVisionResult no metadata do attachment / session_source
  → RAG session_source (texto + markdown resumido)

Turno com desenho
  → ChatDrawingAnalysisTurnService
  → ChatDocumentVisionService.get_for_session_attachment(...)
  → ChatDrawingPdfExtractionService.merge(vision_result)  # deprecar regex-only
  → ChatToolContextService → analyser
  → ChatDrawingValidationOrchestrationService
```

**Stream:** `ChatStreamActivityService.emit_document_vision_progress` — fase `document_vision` (`start`, `ocr`, `complete`); integrado no fluxo de desenho antes da análise DELPI.

**adminDebug:** bloco `documentVision` com engine, stages, legibility, tempo, páginas.

---

## 7. Variáveis de ambiente (propostas)

| Variável | Default | Descrição |
|----------|---------|-----------|
| `CHAT_DOCUMENT_VISION_ENABLED` | `false` | Master switch |
| `CHAT_DOCUMENT_VISION_BACKEND` | `auto` | `native` \| `tesseract` \| `paddleocr` \| `docling` \| `ollama_vlm` \| `auto` |
| `CHAT_DOCUMENT_VISION_MAX_PAGES` | `10` | Herda conceito de `CHAT_DRAWING_PDF_MAX_PAGES` |
| `CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS` | `120` | Timeout por documento |
| `CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS` | `40` | Alinhado ao drawing |
| `CHAT_DOCUMENT_VISION_DPI` | `200` | Rasterização PDF→imagem |
| `CHAT_DOCUMENT_VISION_TESSERACT_LANG` | `por+eng` | Reuso OCR imagem |
| `CHAT_DOCUMENT_VISION_PADDLE_USE_GPU` | `false` | GPU no container |
| `CHAT_DOCUMENT_VISION_DOCLING_MODEL` | `heron` | Layout Docling |
| `CHAT_DOCUMENT_VISION_OLLAMA_MODEL` | `qwen2.5vl:7b` | VLM local |
| `CHAT_DOCUMENT_VISION_OLLAMA_BASE_URL` | `$OLLAMA_BASE_URL` | Endpoint Ollama |
| `CHAT_DOCUMENT_VISION_ALLOW_CLOUD` | `false` | Futuro: Azure/Google — fora do MVP |

Documentar em `README.md` da API e em `docs/architecture/chat-intelligence-base.md` (tabela de serviços).

---

## 8. Container e dependências

### 8.1 Imagem `minha-delpi-ai-api`

| Perfil | Pacotes / libs |
|--------|----------------|
| **Slim (default)** | Tesseract + `por`/`eng` traineddata; pypdf (já) |
| **Vision (profile compose)** | + `poppler-utils`, `libgl1`, PaddleOCR ou Docling via pip extras `vision` |
| **GPU (opcional)** | NVIDIA runtime + paddle-gpu |

Sugestão: `requirements-vision.txt` opcional; CI roda testes com mocks sem instalar Paddle.

### 8.2 Ollama

```bash
# Homologação — modelo VLM separado do qwen2.5:3b texto
ollama pull qwen2.5vl:7b
# ou menor: llava / granite3.2-vision conforme RAM
```

Validar RAM: 7B VLM quantizado ~5–8 GB + api + postgres.

---

## 9. Roadmap de implementação (Onda 13 proposta)

| Fase | Entrega | IDs |
|------|---------|-----|
| **13.1 — Contrato e skill** | `DocumentVisionResult`, `ChatDocumentVisionService` interface, skill no catálogo, policy, registry | 13.1.1–13.1.4 |
| **13.2 — Estágio 0+2** | Unificar Tesseract PDF multipágina + carimbo heurístico; testes fixtures | 13.2.1–13.2.3 |
| **13.3 — Docling ou Paddle** | Backend `docling` em profile vision; tabelas BOM | 13.3.1 ⬜; **13.3.2 ✅** (`ChatDocumentVisionBomService`, `bom_heuristic`) |
| **13.4 — Integração desenho** | `ChatDrawingPdfExtractionService` consome vision; fechar Onda 12 Fase 3 | 13.4.1 |
| **13.5 — VLM Ollama** | Backend `ollama_vlm` opt-in; cotas com confidence | 13.5.1 |
| **13.6 — UX e ops** | Stream, adminDebug, métricas `documentVision`, smoke, compose profile | 13.6.1–13.6.4 |

Dependência: Onda 12 MVP (drawing) **concluído** antes de 13.4.

---

## 10. Testes e validação

| Artefato | Conteúdo |
|----------|----------|
| `tests/fixtures/drawings/` | PDFs anonimizados (já existe minimal) + scans |
| `tests/unit/.../test_chat_document_vision_service.py` | Engines mockados, fallback auto |
| `tests/fixtures/document_vision_regression_cases.py` | Páginas, legibilidade, códigos |
| `scripts/smoke_document_vision.py` | Offline + opcional live Docling |
| Regressão | Garantir que estoque/SQL não disparam vision |

Casos mínimos (V1–V8):

| Caso | Entrada | Esperado |
|------|---------|----------|
| V1 | PDF digital com texto | Estágio 0 only, legível, código certo |
| V2 | Scan sem texto embutido | OCR estágio 2+, legível |
| V3 | PDF ilegível / vazio | `legible: false`, motivo |
| V4 | > max páginas | Truncar + warning |
| V5 | PNG de desenho | OCR imagem |
| V6 | Backend `docling` mock | Tabela BOM parseada |
| V7 | Skill desligada | Só estágio 0 legado |
| V8 | Integração drawing | `productCode` alimenta analyser |

---

## 11. Métricas e observabilidade

| Métrica | Uso |
|---------|-----|
| `documentVisionRuns` | Contagem por engine |
| `documentVisionFailures` | Por `reason` (timeout, ocr_failed, …) |
| `documentVisionDurationMs` p50/p95 | SLA |
| `documentVisionLegibilityRate` | Qualidade anexos |
| `documentVisionStageUsage` | native / tesseract / docling / vlm |

Admin: estender painel Métricas ou subseção em drawing; endpoint opcional `GET /admin/metrics/document-vision/summary`.

---

## 12. Riscos e decisões

| Tema | Decisão recomendada |
|------|---------------------|
| Licença GPL (Surya/Marker) | **Não** embutir no produto sem aval jurídica |
| Custo GPU | Profile `vision` opcional; default CPU + Tesseract |
| Latência VLM | Só com confirmação implícita (desenho) ou setting agente |
| Alucinação VLM | Schema JSON + validação cruzada API Protheus (drawing skill) |
| Dados sensíveis | Local-only; audit sem armazenar imagem rasterizada (só hash + excerpt) |
| Duplicação com Playbook 07 | Vision skill **alimenta** anexos; 07 trata indexação/welcome |

---

## 13. Critérios de aceite (playbook)

- [ ] Skill `document-vision-delpi` no catálogo e registry.
- [ ] `ChatDocumentVisionService` com backends `native`, `tesseract`, `docling` (mínimo).
- [ ] `drawing-analysis-delpi` usa vision quando texto nativo &lt; limiar.
- [ ] Metadata `documentVision` no turno e adminDebug.
- [ ] Smokes V1–V8 passando no container vision profile.
- [ ] Documentação env vars + compose profile.
- [ ] Sem regressão em `smoke_drawing_analyser.py` e roteamento operacional.

---

## 14. Relação com outros documentos

| Documento | Relação |
|-----------|---------|
| [playbook_skill_analise_desenhos_delpi.md](./playbook_skill_analise_desenhos_delpi.md) | Consumidor; Fase 3 dimensional |
| [inteligencia-chat-onda-12-...](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) | 12.2.x passa a delegar para Onda 13 |
| [07_anexos_e_arquivos.md](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Anexos e indexação |
| [chat-intelligence-base.md](../../architecture/chat-intelligence-base.md) | Serviço transversal a registrar |
| [gpt-drawing-analyser-instructions.md](../../knowledge/domains/gpt-instructions/gpt-drawing-analyser-instructions.md) | Paridade funcional |

---

## 15. Histórico

| Data | Alteração |
|------|-----------|
| 2026-05-31 | Criação do playbook: pesquisa OSS (Tesseract, PaddleOCR, Docling, Qwen-VL, Ollama), arquitetura em estágios, skill `document-vision-delpi`, contrato JSON, Onda 13 proposta. |
