# Inteligência do chat — Onda 14: OCR hierárquico de desenhos DELPI

**Status:** parcial — Fases 14.1–14.7 ✅; **14.5–14.6** (BOM/cotas por região) ✅ em código; **14.8** homologação `desenhos/` + CI ⬜ parcial (CI unit ✅)  
**Criado:** 2026-06-08 · **Última revisão doc:** jun/2026  
**Playbook:** [playbook_ocr_hierarquico_desenhos_delpi.md](./melhorias/playbook_ocr_hierarquico_desenhos_delpi.md)  
**Extração PDF (chat base):** [chat-pdf-document-extraction.md](../architecture/chat-pdf-document-extraction.md)  
**Pré-requisitos:** [Onda 12](./inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) MVP, [Onda 13](./inteligencia-chat-onda-13-skill-visao-documentos-ocr.md) MVP

---

## Objetivo

Fechar o gap entre o **pipeline atual de visão/OCR** e o fluxo normativo DELPI (**OCR hierárquico** §2.4 de `drawing_analyser_instructions_full`): extrair código do produto, revisão e metadados do **carimbo** (não da BOM), com suporte a **intermediários `50xx`** e demais cadastros SB1010, sem heurística por prefixo numérico.

---

## Situação atual vs alvo

| Aspecto | Hoje (pós-Onda 13 MVP) | Alvo (Onda 14) |
|---------|------------------------|----------------|
| Código do desenho | Primeiro número no texto OCR (~31% em `desenhos/`) | Carimbo/título rotulado + resolução de candidatos |
| Crop carimbo | Faixa superior da página | **Base direita** (norma gráfica DELPI) |
| BOM vs produto | Mesmo pool de regex | Regiões e papéis separados |
| `50xx` | Misturado com `productCode` | `intermediateCodes[]`; produto só com evidência no carimbo |
| Cotas/decape | Regex no texto global (0/13) | Região cotas + padrões OCR-tolerantes |
| Texto nativo `auto` | `charCount` alto aceita lixo | Gate semântico → força OCR |
| Conflito de códigos | Não detectado | `conflicts[]` + clarificação |

**Baseline homologação (08/06/2026):** 13 PDFs em `minha-delpi-ai-api/desenhos/` → 4/13 `productCode` correto. Detalhes no playbook §2.

---

## Backlog por fase

### 14.1 — Contrato e governança

| ID | Entrega | Status |
|----|---------|--------|
| 14.1.1 | Schema `DrawingHierarchicalExtract` (playbook §5) | ✅ doc |
| 14.1.2 | Bundle `drawing_stamp.json` | ✅ |
| 14.1.3 | `run_onda14_desenhos_validation.sh` | ✅ |
| 14.1.4 | `drawing_hierarchical_regression_cases.py` | ✅ |

### 14.2 — OCR por região

| ID | Entrega | Status |
|----|---------|--------|
| 14.2.1 | Bboxes stamp/title/bom/dimensions | ✅ |
| 14.2.2 | Crop carimbo base direita | ✅ |
| 14.2.3 | `regions` no `DocumentVisionResult` | ✅ (stamp) |
| 14.2.4 | Estágios stream/adminDebug | ✅ |

### 14.3 — Parse carimbo e título

| ID | Entrega | Status |
|----|---------|--------|
| 14.3.1 | `ChatDrawingStampExtractionService` | ✅ |
| 14.3.2 | Padrão «CHICOTE DE LIGAÇÃO» | ✅ |
| 14.3.3 | Exclusão `COD:`/`DES:` cliente | ✅ |
| 14.3.4 | Delegação `titleBlock` | ✅ |

### 14.4 — Resolução do código

| ID | Entrega | Status |
|----|---------|--------|
| 14.4.1 | `ChatDrawingProductCodeResolutionService` | ✅ |
| 14.4.2 | `productCodeCandidates` + confidence | ✅ |
| 14.4.3 | Conflitos e clarificação | ✅ |
| 14.4.4 | Intermediários `50xx` | ✅ |

### 14.5 — BOM por região

| ID | Entrega | Status |
|----|---------|--------|
| 14.5.1 | BOM só região `bom` | ✅ |
| 14.5.2 | Componentes excluídos de `productCode` | ✅ |
| 14.5.3 | Paridade smoke drawing | ✅ (unit) |

### 14.6 — Cotas e decapes

| ID | Entrega | Status |
|----|---------|--------|
| 14.6.1 | OCR região dimensions | ✅ |
| 14.6.2 | Regex OCR-tolerante | ✅ |
| 14.6.3 | Tolerâncias inalteradas | ✅ |

### 14.7 — Gate qualidade `auto`

| ID | Entrega | Status |
|----|---------|--------|
| 14.7.1 | Plausibilidade texto nativo | ✅ |
| 14.7.2 | Fallback OCR (ex. 90263622) | ✅ |
| 14.7.3 | Env documentado | ⬜ |

### 14.8 — Integração e homologação

| ID | Entrega | Status |
|----|---------|--------|
| 14.8.1 | Refatorar `ChatDrawingPdfExtractionService` — delega extração a `ChatPdfDocumentExtractionService` | ✅ |
| 14.8.2 | Merge vision → drawing | ✅ |
| 14.8.3 | Meta **≥ 10/13** em `desenhos/` | ✅ (13/13 jun/2026) |
| 14.8.4 | CI regressão | ✅ (unit `run_onda14`) |
| 14.8.5 | Critérios aceite Onda 12 | ⬜ |

---

## Critérios de aceite (Onda 14)

- [x] Código DELPI extraído do carimbo ou título — não do primeiro item da BOM — em ≥ 10/13 PDFs de homologação local.
- [ ] Desenho de intermediário (`50xx` no carimbo) resolve `productCode` sem regra de prefixo `902`.
- [ ] `90263622.pdf` correto com `CHAT_DOCUMENT_VISION_BACKEND=auto` (sem troca manual de backend).
- [ ] Conflito mensagem × carimbo registrado em `conflicts` e refletido no relatório drawing.
- [ ] Zero string PT nova fora de `drawing_stamp.json` / bundles existentes.
- [ ] Estoque, SQL e busca catálogo **não** regressam (`smoke_gpt_instructions_improvements.py` + intent router).

---

## Validação prevista

```bash
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  bash scripts/run_onda14_desenhos_validation.sh
```

Ver também playbook §9.

---

## Dependências e sequência

```text
Onda 12 (drawing MVP) ──┐
Onda 13 (vision MVP)  ──┼──► Onda 14 (OCR hierárquico)
Playbook §7 fases     ──┘         │
                                  ▼
                    Onda 12 critérios aceite (código carimbo)
                    Onda 13 refinamentos VLM (opcional, cotas confidence)
```

**Próxima ação recomendada:** homologação batch em `desenhos/` (BOM/cotas) + meta **≥ 6/13** com `dimensions` parciais.

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-06-08 | Onda 14 criada; playbook OCR hierárquico; baseline 4/13 `desenhos/`. |
| 2026-06-09 | Fase 14.1: `drawing_stamp.json`, casos H1–H13, baseline JSON, `run_onda14_desenhos_validation.sh`. |
| 2026-06-09 | Fase 14.4: resolução candidatos/conflitos; 14.7 gate nativo; homologação **13/13** em `desenhos/`. |
