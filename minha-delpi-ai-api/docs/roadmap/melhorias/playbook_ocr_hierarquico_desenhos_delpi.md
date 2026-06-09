# Playbook — OCR hierárquico de desenhos DELPI (chat base)

> **Status (08/06/2026):** Backlog aprovado — roadmap abaixo; implementação na [Onda 14](../inteligencia-chat-onda-14-ocr-hierarquico-desenhos.md).  
> **Projeto:** Minha DELPI Chat IA  
> **Arquitetura:** serviço transversal no [chat base](../../architecture/chat-intelligence-base.md); **não** duplicar heurísticas no `system_prompt` de agentes nem no use case de stream/send.

| Campo | Valor |
|-------|-------|
| Escopo | Extração estruturada do PDF de desenho (carimbo, título, BOM, cotas) |
| Consumidores | `drawing-analysis-delpi`, `document-vision-delpi`, `ChatDrawingValidationOrchestrationService` |
| Pré-requisitos | [Onda 12](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) MVP, [Onda 13](../inteligencia-chat-onda-13-skill-visao-documentos-ocr.md) MVP |
| Playbooks relacionados | [Análise de desenhos](./playbook_skill_analise_desenhos_delpi.md) · [Visão/OCR](./playbook_skill_visao_documentos_ocr_delpi.md) |

---

## 1. Objetivo

Corrigir a **identificação do produto e metadados do desenho** no pipeline de visão/OCR, alinhando-se ao fluxo oficial DELPI:

```text
PDF do desenho
  → OCR hierárquico por região (carimbo, título, BOM, cotas)
  → Resolução do código DELPI (sem heurística por prefixo numérico)
  → GET /products/{code}/analyser
  → Validação PDF × API × Normas
```

**Não é objetivo** deste playbook reescrever o relatório de conformidade (já coberto pela Onda 12) nem substituir backends neurais/VLM (Onda 13 backlog fino).

---

## 2. Problema (baseline jun/2026)

Homologação manual em `minha-delpi-ai-api/desenhos/` (13 PDFs reais, gitignored):

| Métrica | Resultado atual (`CHAT_DOCUMENT_VISION_BACKEND=auto`) |
|---------|--------------------------------------------------------|
| `productCode` = código do desenho | **4/13 (31%)** |
| `dimensions` (comprimento/decape) | **0/13** |
| `bomRows` estruturadas | **0/13** |
| OCR Tesseract acionado | 12/13 |

**Causas raiz (não sintomas):**

| # | Gap | Evidência |
|---|-----|-----------|
| G1 | Texto linear — primeiro número vira `productCode` | BOM `10070809` vence carimho `90264234` |
| G2 | Crop do “carimbo” na **faixa superior** | Norma DELPI: carimbo na **base direita** (`drawing_rules_delpi`) |
| G3 | `50xx` / `10xx` sem papel distinto | Doc: intermediário ≠ produto do desenho ≠ componente BOM |
| G4 | `COD:` / `DES:` do **cliente** misturados com código DELPI | Carimho WEG: `COD: 19402706`, `DES: 10014608724` |
| G5 | Modo `auto` aceita lixo nativo longo | `90263622.pdf`: pypdf → lixo; Tesseract isolado → **90263622** correto |
| G6 | Cotas no OCR, regex de dimensão vazio | `DECAPE 8MM` legível; `dimensions` sempre `null` |

**Estratégias proibidas** (frágeis ou fora da norma):

- Priorizar prefixo `902…` (intermediários `50xx` e outros cadastros são válidos no carimbo).
- Usar nome do arquivo como única fonte de código.
- Patch em `SendChatMessageUseCase` / `StreamChatMessageUseCase` / prompt de agente.

---

## 3. Fontes normativas (ordem de autoridade)

| # | Documento | Uso neste playbook |
|---|-----------|-------------------|
| 1 | [`drawing_analyser_instructions_full.md`](../../knowledge/sources/gpt-instructions/drawing_analyser_instructions_full.md) §2.4–2.5 | OCR hierárquico; identificação do código |
| 2 | [`drawing_rules_delpi.md`](../../knowledge/sources/gpt-instructions/drawing_rules_delpi.md) | Posição carimbo (base direita), título «CHICOTE DE LIGAÇÃO / …» |
| 3 | [`drawing_requirements_delpi.md`](../../knowledge/sources/gpt-instructions/drawing_requirements_delpi.md) §2 | Campo **CÓDIGO DELPI** (`902…` **ou** `502…`) |
| 4 | [Playbook análise de desenhos](./playbook_skill_analise_desenhos_delpi.md) §7.2–7.4 | Schema de extração; conflito de códigos → erro/clarificação |
| 5 | [Intermediários 50xx](../../knowledge/domains/agents/minha-delpi-chat/engenharia-codigos-intermediarios-delpi.md) | Papel do código intermediário no desenho |
| 6 | [Playbook visão/OCR](./playbook_skill_visao_documentos_ocr_delpi.md) | Backends, estágios, `DocumentVisionResult` |

Domínio adaptado: [`gpt-drawing-analyser-instructions.md`](../../knowledge/domains/gpt-instructions/gpt-drawing-analyser-instructions.md).

---

## 4. Princípios de design

1. **Região antes de regex global** — cada campo vem da zona gráfica correta (carimbo, título, BOM, cotas).
2. **Papel do código** — `productCode`, `intermediateCodes[]`, `bomComponentCodes[]` são listas distintas; nunca promover componente BOM a produto.
3. **Rótulo antes de posição** — preferir campos rotulados (`CÓDIGO DELPI`, `REV.`, `CLIENTE`, `CHICOTE DE LIGAÇÃO`) a ordem de leitura OCR.
4. **Desambiguação honesta** — 0 ou >1 candidato plausível → clarificação (texto em JSON); não inventar código.
5. **API como validação** — candidato resolvido alimenta `/analyser`; divergência carimho × SB1010 é erro crítico na Onda 12.
6. **Conteúdo PT em JSON** — rótulos, mensagens de clarificação e `reason` em `app/content/pt-BR/assistant/drawing_stamp.json` (novo bundle).
7. **Um módulo canônico** — ver §6; testes de regressão obrigatórios antes de merge.

---

## 5. Contrato de dados (`DrawingHierarchicalExtract`)

Extensão do payload já consumido por `ChatDrawingPdfExtractionService` / `DocumentVisionResult`:

```json
{
  "schemaVersion": "2.0",
  "productCode": "90264234",
  "productCodeSource": "stamp_labeled",
  "productCodeCandidates": [
    { "code": "90264234", "source": "stamp_labeled", "confidence": 0.92 },
    { "code": "10070809", "source": "bom_row", "confidence": 0.15 }
  ],
  "revision": "01",
  "customer": "WEG INDUSTRIA S.A - LINHARES",
  "customerCode": "19402706",
  "customerDescription": "10014608724",
  "description": "CHICOTE DE LIGACAO",
  "lmp": "082/26",
  "executedBy": "GABRIELLA",
  "releasedBy": "WILLIAM",
  "date": "22/05/26",
  "intermediateCodes": ["50225940"],
  "bomRows": [
    { "position": "A1", "code": "10070809", "description": "CABO MANGA...", "qty": 1 }
  ],
  "dimensions": {
    "totalLengthMm": null,
    "leftDecapeMm": 8,
    "rightDecapeMm": null
  },
  "regions": {
    "stamp": { "bbox": [0.5, 0.62, 1.0, 1.0], "charCount": 420, "engine": "tesseract" },
    "title": { "bbox": [0.2, 0.0, 0.8, 0.12], "charCount": 80 },
    "bom": { "bbox": [0.0, 0.0, 0.55, 0.35], "charCount": 1200 },
    "dimensions": { "bbox": [0.0, 0.12, 1.0, 0.62], "charCount": 900 }
  },
  "conflicts": [],
  "legible": true,
  "warnings": []
}
```

### 5.1 `productCodeSource` (enum)

| Valor | Significado |
|-------|-------------|
| `user_message` | Código informado na mensagem do turno |
| `stamp_labeled` | Campo rotulado no carimbo (CÓDIGO DELPI, etc.) |
| `title_pattern` | Título «CHICOTE DE LIGAÇÃO / {code}» ou adjacente no carimho |
| `filename_crosscheck` | Só validação — não seleciona sozinho |
| `unresolved` | Candidatos conflitantes ou ausentes — pedir código |

### 5.2 Conflitos (`conflicts[]`)

| Tipo | Severidade | Ação |
|------|------------|------|
| `stamp_vs_title` | Erro | Registrar; priorizar carimbo rotulado se confidence maior |
| `stamp_vs_message` | Erro crítico | Mensagem do usuário vence; registrar divergência no relatório |
| `stamp_vs_filename` | Pendente | Alerta no checklist §7.4 playbook desenho |
| `multiple_stamp_codes` | Erro | Clarificação — não chutar |
| `bom_code_promoted` | — | **Proibido** — candidato BOM nunca vira `productCode` |

---

## 6. Mapa canônico de módulos

| Responsabilidade | Módulo (proposto / existente) | Não duplicar em |
|------------------|-------------------------------|-----------------|
| **Ativação da skill** (anexo, desenho, intent) | `ChatDocumentVisionSkillService` (domain) | `should_run_*` inline em use case |
| **Orquestração por turno** | `ChatDocumentVisionTurnService` (application) | `ChatToolContextPreTurnService`, result assembly |
| Vocabulário PT / padrões intent | `document_vision.json` + `ChatDocumentVisionContentService` | regex em `ChatAttachmentDocumentIntentService` |
| Raster + OCR por região | `ChatDocumentVisionService` (estender) | use case, tool context inline |
| Parse carimbo/título por rótulos | **`ChatDrawingStampExtractionService`** (domain, **novo**) | `ChatProductQueryIntentService.extract_product_code` no texto bruto |
| Resolução de candidatos | **`ChatDrawingProductCodeResolutionService`** (domain, **novo**) | presenter, prompt agente |
| Parse BOM tabular | `ChatDocumentVisionBomService` (estender) | regex no PDF inteiro |
| Parse cotas/decape | `ChatDrawingPdfExtractionService._extract_dimensions` (estender) + região cotas | componentes MFE |
| Vocabulário PT (rótulos, padrões) | **`drawing_stamp.json`** + loader via `ChatAssistantContentService` | strings em Python |
| Orquestração merge vision → drawing | `ChatDrawingPdfExtractionService` (refatorar) | `enrich_drawing_extract` ad hoc |
| Validação PDF × API | `ChatDrawingValidationOrchestrationService` (consumir) | — |

**Regra Cursor:** alterações neste escopo atualizam `.cursor/rules/centralized-rules-first.mdc` somente se surgir nova linha na tabela canônica.

---

## 7. Roadmap por fases (Onda 14)

### Visão geral

```text
Fase 14.1 — Contrato + bundle JSON + baseline testes     [backlog]
Fase 14.2 — Regiões gráficas + crop carimbo correto      [backlog]
Fase 14.3 — Parse carimbo/título (stamp service)         [backlog]
Fase 14.4 — Resolução de código + conflitos              [backlog]
Fase 14.5 — BOM por região + exclusão de componentes     [backlog]
Fase 14.6 — Cotas/decape (região + regex OCR-tolerante)  [backlog]
Fase 14.7 — Gate qualidade texto nativo (auto)           [backlog]
Fase 14.8 — Integração pipeline + regressão desenhos/    [backlog]
```

---

### Fase 14.1 — Contrato e governança

| ID | Entrega | DoD |
|----|---------|-----|
| 14.1.1 | Schema `DrawingHierarchicalExtract` documentado (este playbook §5) | Revisado em PR |
| 14.1.2 | Bundle `drawing_stamp.json` (rótulos carimbo, padrão título, exclusões `COD:`/`DES:`) | Gate: chaves referenciadas em teste |
| 14.1.3 | `scripts/test_desenhos_extraction.py` vira `scripts/run_onda14_desenhos_validation.sh` | Exit code ≠ 0 se taxa < meta fase 14.8 |
| 14.1.4 | Casos H1–H13 em `tests/fixtures/drawing_hierarchical_regression_cases.py` | Lista commitada (PDFs permanecem gitignored) |

**Meta de baseline:** registrar 4/13 atual como `baseline_2026-06.json` no primeiro PR da fase.

---

### Fase 14.2 — OCR por região

| ID | Entrega | DoD |
|----|---------|-----|
| 14.2.1 | Bboxes normalizadas: `stamp` (base direita), `title` (topo central), `bom` (topo esquerdo), `dimensions` (corpo) | Constantes em domain ou JSON |
| 14.2.2 | `_ocr_stamp_regions` migra para **base direita**; remover dependência só de faixa superior | Comentário cita `drawing_rules_delpi` |
| 14.2.3 | `DocumentVisionResult.regions` preenchido por estágio | Teste unitário com mock fitz |
| 14.2.4 | Estágios SSE/adminDebug: `stamp_ocr`, `title_ocr`, `bom_ocr`, `dimensions_ocr` | Chaves em `stream.json` |

**Nota:** bboxes iniciais são heurísticas A4 DELPI; calibrar com amostras em `desenhos/` sem overfit de um único layout.

---

### Fase 14.3 — Parse carimbo e título

| ID | Entrega | DoD |
|----|---------|-----|
| 14.3.1 | `ChatDrawingStampExtractionService.extract_from_stamp_text()` | REV, CLIENTE, LMP, EXECUTADO/LIBERADO, DATA |
| 14.3.2 | Padrão título `CHICOTE DE LIGAÇÃO` + código adjacente | Termos em `drawing_stamp.json` |
| 14.3.3 | Exclusão explícita: tokens após `COD:`, `DES:`, `CÓD. CLIENTE` | Testes H4, H5 |
| 14.3.4 | `titleBlock.fields` alimentado só pelo stamp service | `ChatDocumentVisionTitleBlockService` delega |

---

### Fase 14.4 — Resolução do código DELPI

| ID | Entrega | DoD |
|----|---------|-----|
| 14.4.1 | `ChatDrawingProductCodeResolutionService.resolve(candidates, message_code?, filename?)` | Ordem: mensagem → stamp rotulado → título → unresolved |
| 14.4.2 | `productCodeCandidates` com `source` + `confidence` heurística | Sem filtro por prefixo `90` |
| 14.4.3 | Conflitos em `conflicts[]`; clarificação via `drawing_validation.json` | Texto PT só no JSON |
| 14.4.4 | Intermediários `50xx` em `intermediateCodes[]`; promoção a `productCode` só com evidência no carimbo | Teste com fixture intermediário |

---

### Fase 14.5 — BOM por região

| ID | Entrega | DoD |
|----|---------|-----|
| 14.5.1 | `ChatDocumentVisionBomService` parseia só texto da região `bom` | Colunas Pos/Código/Qtd |
| 14.5.2 | Códigos BOM **não** entram em `productCodeCandidates` com confidence > 0.5 | Regressão H2 (90261040) |
| 14.5.3 | `bomRows` populadas; merge com SG1010 na Onda 12 inalterado | Smoke drawing existente verde |

---

### Fase 14.6 — Cotas e decapes

| ID | Entrega | DoD |
|----|---------|-----|
| 14.6.1 | OCR da região `dimensions` (ou corpo menos stamp/BOM) | Estágio dedicado |
| 14.6.2 | Regex OCR-tolerante: `DECAPE` + número + `MM`, `COMPR` fragmentado, `±` cotas | Termos em JSON se necessário |
| 14.6.3 | Tolerâncias na validação permanecem em `ChatDrawingToleranceService` | ±5% / ±1mm inalterados |

---

### Fase 14.7 — Gate de qualidade (modo `auto`)

| ID | Entrega | DoD |
|----|---------|-----|
| 14.7.1 | `_native_text_is_drawing_plausible(text)` — marcadores carimbo ou código candidato na região stamp | Substitui critério “charCount >= N” |
| 14.7.2 | Texto nativo implausível → forçar Tesseract multipágina | 90263622 passa sem trocar backend manual |
| 14.7.3 | Env opcional `CHAT_DOCUMENT_VISION_NATIVE_MIN_STAMP_MARKERS` | Documentado no README API |

---

### Fase 14.8 — Integração e homologação

| ID | Entrega | DoD |
|----|---------|-----|
| 14.8.1 | `ChatDrawingPdfExtractionService` consome hierarquia; remove `extract_product_code` no texto completo | Paridade testes unitários existentes |
| 14.8.2 | `ChatDocumentVisionService.merge_into_drawing_parse` usa novo contrato | `enrich_drawing_extract` inalterado na interface |
| 14.8.3 | Regressão `desenhos/`: **≥ 10/13** `productCode` correto; **≥ 6/13** com `dimensions` parciais | Script de validação |
| 14.8.4 | `chat_intelligence_regression_cases.py` + smokes drawing/vision verdes | CI |
| 14.8.5 | Atualizar Onda 12 critérios de aceite (checkbox código carimbo) | Doc |

---

## 8. Casos de teste (H1–H13)

PDFs em `minha-delpi-ai-api/desenhos/` (local, gitignored). IDs referenciam nomes de arquivo.

| Caso | PDF | Esperado `productCode` | Notas |
|------|-----|------------------------|-------|
| H1 | 90262373 | 90262373 | Já passa — regressão |
| H2 | 90261040 | 90261040 | BOM não pode vencer (10400006) |
| H3 | 90262511 | 90262511 | Decape no corpo |
| H4 | 90264234 | 90264234 | `COD:` cliente ≠ DELPI |
| H5 | 90264235–38 | respectivo 9026423x | Layout WEG repetido |
| H6 | 90263622 | 90263622 | Gate nativo → OCR |
| H7 | 90263149 | 90263149 | Código só no carimho parcial |
| H8 | — | 50232222 | Fixture sintético intermediário no carimbo |
| H9 | — | conflito | Stamp A + mensagem B → `conflicts` |
| H10 | — | `unresolved` | Carimbo ilegível → clarificação |
| H11 | 90263655 | 90263655 | Decape + código |
| H12 | 90264236 | 90264236 | PDF multipágina / corpo denso |
| H13 | 90264231/33 | respectivo | Regressão acertos atuais |

---

## 9. Validação

```bash
# Baseline / homologação local (PDFs em desenhos/)
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  bash scripts/run_onda14_desenhos_validation.sh

# Unit (mock de regiões)
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_drawing_stamp_extraction_service.py \
  tests/unit/domain/services/test_chat_drawing_product_code_resolution_service.py \
  tests/fixtures/drawing_hierarchical_regression_cases.py -q

# Regressão drawing + vision
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_drawing_analysis_skill.py \
  tests/unit/application/services/test_chat_document_vision_service.py -q
```

---

## 10. Métricas

Estender `documentVisionMetrics` / `drawingAnalysisMetrics`:

| Métrica | Uso |
|---------|-----|
| `drawingStampOcrChars` | Volume OCR carimbo |
| `drawingProductCodeSource` | Distribuição `stamp_labeled` / `title_pattern` / `unresolved` |
| `drawingCodeConflictRate` | Taxa de clarificação |
| `drawingDesenhosValidationRate` | Homologação batch (admin opcional) |

---

## 11. Riscos e decisões

| Tema | Decisão | Nota |
|------|---------|------|
| Layouts não padronizados | Bboxes heurísticas + fallback VLM (Onda 13) | Não bloquear MVP Tesseract |
| Desenho = intermediário `50xx` | Permitido no carimbo | Validar via `/analyser` |
| Filename vs carimbo | Só cross-check | Playbook desenho §7.4 |
| Performance | OCR 4 regiões × N páginas | Respeitar `CHAT_DOCUMENT_VISION_MAX_PAGES` |
| GPL/neural | Docling/Paddle fora do slim | Profile `vision` opcional |

---

## 12. O que não fazer

- Heurística «se começa com 902 é produto».
- `extract_product_code` no texto concatenado do PDF inteiro.
- Crop de carimbo só no topo da página (estado atual — **bug**).
- Strings PT novas em serviços domain/application sem `drawing_stamp.json`.
- Bypass do pipeline em use case quando o turno é `drawing_analysis`.

---

## 13. Histórico

| Data | Alteração |
|------|-----------|
| 2026-06-08 | Playbook criado após homologação 4/13 em `desenhos/`; define Onda 14 e contrato hierárquico. |
