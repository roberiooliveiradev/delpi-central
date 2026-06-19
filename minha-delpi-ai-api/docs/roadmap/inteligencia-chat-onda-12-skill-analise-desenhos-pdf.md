# Inteligência do chat — Onda 12: Skill de análise de desenhos DELPI (PDF)

**Status:** parcial (Fases 1–5 + E2E live + intent `drawing_analysis` no pipeline — maio/2026); extração carimbo/código → [Onda 14](./inteligencia-chat-onda-14-ocr-hierarquico-desenhos.md)  
**Criado:** 2026-05-29  
**Playbook de produto:** [playbook_skill_analise_desenhos_delpi.md](./melhorias/playbook_skill_analise_desenhos_delpi.md) (`drawing-analysis-delpi`) · extração hierárquica: [playbook OCR hierárquico](./melhorias/playbook_ocr_hierarquico_desenhos_delpi.md)  
**Pré-requisitos:** [Onda 11](./inteligencia-chat-onda-11-paridade-assistentes.md), [arquitetura chat base](../architecture/chat-intelligence-base.md), sync GPT_instructions ([coverage map](../knowledge/gpt-instructions-coverage-map.md))

---

## Objetivo

Replicar no **Minha DELPI Chat** a capacidade que o **ChatGPT DELPI legado** já oferece: **analisar desenhos técnicos em PDF**, extrair cotas e metadados do carimbo (OCR/visão), confrontar com dados reais do Protheus via **API DELPI** e emitir **relatório de conformidade** conforme normas e checklist DELPI.

A funcionalidade deve ser uma **skill de plataforma** (`drawing-analyser`), registrada no catálogo global e **herdável por qualquer agente** — o agente adiciona restrições (escopo, actions, RAG), mas a inteligência transversal (intent, pipeline, tools, policies) vive na **camada base do chat**.

---

## Situação atual vs alvo

| Aspecto | Hoje (maio/2026) | Alvo (Onda 12) |
|---------|------------------|----------------|
| Conhecimento normativo | Docs ingeridos no RAG do agente (`drawing_analyser`, `drawing_rules`, `drawing_requirements`, `validation_rules`, códigos 50xx) | Mesmo RAG + policy da skill |
| API operacional | `GET /products/{code}/analyser` em **api-delpi** e **api-externa** (mesma action `get_product_analyser`) | Fast path / roteamento automático quando houver código + PDF |
| PDF anexado na sessão | Anexo vira `session_source` no RAG (texto extraído se houver) | Pipeline dedicado: visão/OCR estruturado + checklist |
| PDF **sem anexo** | Não suportado | `ChatDrawingLibraryService` → `GET /products/{code}/drawing/pdf` (api-delpi) + OCR |
| Relatório técnico | LLM responde genericamente com contexto RAG | Formato padronizado (✅ / ⚠️ / ❌) alinhado ao GPT legado |
| Herança por agente | Não existe skill `drawing-analyser` | Agente habilita skill; engenharia/qualidade podem ser default |

**Paridade de referência:** fluxo descrito em `api-delpi-py/GPT_instructions/drawing_analyser_instructions.md` (adaptado em `docs/knowledge/domains/gpt-instructions/gpt-drawing-analyser-instructions.md`):

```text
PDF (OCR e cotas) ⇄ API DELPI (SB1010, SG1010, SG2010, QP6–QP8) ⇄ Checklist técnico automatizado
```

---

## Princípio de arquitetura (chat base)

Seguir a regra de inteligência herdada — **não** implementar só no `system_prompt` de um agente:

```text
Anexo PDF + mensagem
  → ChatDrawingIntentService (intent)
  → ChatIntelligencePipelineService (desliga fast path genérico; liga modo drawing)
  → ChatToolContextService
        · execute_external_action → GET /products/{code}/analyser (api-delpi ou api-externa)
        · (futuro) analyze_drawing_pdf → extração estruturada do PDF
  → RAG (drawing_* docs + Normas_Tecnicas quando global)
  → PromptPolicyService → drawing-analyser-skill.md
  → LLM → relatório + apresentação rica (tabela/cards)
```

O agente **só** filtra: skill ativa, actions permitidas, tags RAG de especialização.

---

## Skill `drawing-analyser` (proposta)

| Campo | Valor proposto |
|-------|----------------|
| `skillKey` | `drawing-analyser` |
| `label` | Análise de desenhos DELPI |
| `description` | Analisa PDFs de desenho técnico, valida cotas e carimbo contra Protheus e normas DELPI. |
| `policyFile` | `drawing-analyser-skill.md` |
| `metadataFlag` | `engineering` |
| `executionHint` | `GET /products/{code}/analyser` + anexo PDF |

**Herança:** agentes de engenharia/qualidade incluem `drawing-analyser` em `metadata.skills`. Agentes operacionais (estoque, vendas) não herdam por default.

**Dependência de conhecimento global:** `Normas_Tecnicas_DELPI.md` está em [`domains/global/normas-tecnicas-delpi.md`](../knowledge/domains/global/normas-tecnicas-delpi.md) (`company-knowledge`, maio/2026). Intent de descrição técnica: `ChatTechnicalDescriptionIntentService`.

---

## Backlog por fase

### 12.1 — Intent e contrato da skill

| ID | Entrega | Status |
|----|---------|--------|
| 12.1.1 | `ChatDrawingIntentService` — detecta pedido de análise de desenho + PDF anexado ou código de produto | ✅ |
| 12.1.2 | Policy `drawing-analysis-delpi-skill.md` + registro em `PromptPolicyService` / catálogo admin | ✅ |
| 12.1.3 | Skill `drawing-analysis-delpi` no `catalog.json` e bootstrap admin | ✅ |
| 12.1.4 | Bloqueio de roteamento incorreto (ex.: não confundir «analise o desenho 90264130» com busca catálogo) | ✅ |

### 12.2 — Extração do PDF (visão / OCR)

| ID | Entrega | Status |
|----|---------|--------|
| 12.2.1 | Definir provedor: LLM multimodal (anexo) vs serviço OCR dedicado vs pipeline híbrido | ✅ (híbrido: pypdf + parse heurístico) |
| 12.2.2 | `ChatDrawingPdfExtractionService` — schema estruturado (código, REV., cotas, cabos, terminais, carimbo) | ✅ (código/REV/cliente; **cotas → Onda 13** [playbook visão](./melhorias/playbook_skill_visao_documentos_ocr_delpi.md)) |
| 12.2.3 | Limites de tamanho/páginas; timeout; fallback quando OCR falhar | ✅ (`CHAT_DRAWING_PDF_MAX_PAGES`, legibilidade mínima) |
| 12.2.4 | Testes com PDFs reais anonimizados (fixtures em `tests/fixtures/drawings/`) | ✅ (`sample_carimbo_minimal.pdf` via `scripts/build_drawing_fixture_pdf.py`) |

### 12.3 — Orquestração PDF × API × checklist

| ID | Entrega | Status |
|----|---------|--------|
| 12.3.1 | `ChatDrawingValidationOrchestrationService` — merge PDF extraído + payload `/analyser` | ✅ (MVP API; PDF OCR pendente) |
| 12.3.2 | Regras de tolerância (±5% comprimento, ±1 mm decape) conforme `validation_rules_delpi` | ✅ |
| 12.3.2b | Decape E/D por lado; nota de máquina; sem falso positivo global 6 mm × `04/06` (`90264206`) | ✅ jun/2026 |
| 12.3.3 | Classificação consolidada ✅ / ⚠️ / ❌ por seção do checklist | ✅ |
| 12.3.4 | Integração em `ChatToolContextService` / action `get_product_analyser` com parâmetros de profundidade | ✅ (`page_size=50`, `max_depth=10`) |
| 12.3.5 | Biblioteca PDF api-delpi sem anexo (`ChatDrawingLibraryService` + rotas `/drawing`, `/drawing/pdf`) | ✅ jun/2026 |

### 12.4 — UX e apresentação

| ID | Entrega | Status |
|----|---------|--------|
| 12.4.1 | Template de relatório (markdown + tabela rica Onda 9) | ✅ (markdown + export `.md` em metadata) |
| 12.4.2 | UI: indicador de «analisando desenho» no stream (`ChatStreamActivityService`) | ✅ |
| 12.4.3 | Export PDF/XLSX do relatório de não conformidades (opcional) | ✅ (PDF/CSV/XLSX/MD no MFE via `drawingAnalysis` + `spreadsheetRows`) |

### 12.5 — Agentes, testes e operação

| ID | Entrega | Status |
|----|---------|--------|
| 12.5.1 | Agente `minha-delpi-chat` (ou engenharia) com skill default | ✅ (auto quando action `get_product_analyser` / path `/analyser`) |
| 12.5.2 | Smoke `scripts/smoke_drawing_analyser.py` + `smoke_drawing_analyser_live.py` (HTTP + PDF + chat E2E) | ✅ |
| 12.5.3 | Casos em `chat_intelligence_regression_cases.py` | ✅ |
| 12.5.4 | Documentar env vars (timeout OCR, max pages, model vision) | ✅ (`CHAT_DRAWING_PDF_MAX_PAGES`, `CHAT_DRAWING_PDF_MIN_LEGIBLE_CHARS`) |

### 12.6 — Qualidade (Fase 6)

| ID | Entrega | Status |
|----|---------|--------|
| 12.6.1 | Testes D1–D12 (`test_drawing_analysis_skill.py`) | ✅ |
| 12.6.2 | Regressão intent desenho em `chat_intelligence_regression_cases.py` | ✅ |
| 12.6.3 | Métricas em metadata, adminDebug e auditoria (`drawingAnalysisMetrics`) | ✅ |
| 12.6.4 | Resumo admin agregado (`GET /admin/metrics/drawing-analysis/summary`) + painel em Métricas (MFE) | ✅ |

---

## Critérios de aceite (Onda 12)

- [ ] Usuário anexa PDF + informa código (ou código inferido do carimbo) → relatório com checklist completo.
- [ ] Divergências dimensionais e de estrutura aparecem como ❌ com mensagem padronizada (paridade com GPT legado).
- [ ] Agente sem skill `drawing-analyser` **não** entra no pipeline de desenho (ou recebe resposta orientando habilitar skill).
- [ ] Agente com skill herda comportamento sem duplicar lógica no `system_prompt`.
- [ ] Regressão: estoque, busca de produto e SQL produção **não** quebram (`smoke_gpt_instructions_improvements.py` + novos casos drawing).
- [x] `adminDebug` expõe fases: intent drawing, extração PDF, action analyser, validações (`drawingAnalysisTrace`).

---

## Riscos e decisões em aberto

| Tema | Opções | Nota |
|------|--------|------|
| OCR / visão | GPT-4o vision via anexo vs Tesseract vs serviço interno | Custo e latência vs precisão em cotas |
| Código do produto | Obrigatório na mensagem vs OCR do carimbo | Fallback: pedir código se ambíguo |
| PDF multipágina | Todas as páginas vs só folha principal | Limitar páginas no MVP |
| Normas técnicas | Global vs agente | Recomendado **global** (admin knowledge) |
| Provider API | api-delpi vs api-externa (`CHAT_PREFER_API_EXTERNA_PROVIDER`) | Mesma rota `/analyser`; local costuma só api-externa |
| api-delpi | Só `/analyser` vs endpoints futuros de drawing | Hoje `/analyser` cobre SB1/SG1/SG2/QP |

---

## O que já está pronto (não repetir na implementação)

- Docs GPT de desenho adaptados e ingeridos no agente ([sync script](../../scripts/sync_gpt_instructions_knowledge.py)).
- Mapa documento a documento ([gpt-instructions-coverage-map.md](../knowledge/gpt-instructions-coverage-map.md)).
- Action OpenAPI `get_product_analyser` nos catálogos api-delpi e api-externa.
- Pipeline base de anexos (`session_source`) e RAG por agente.

---

## Validação prevista

```bash
# Unit + D1–D12
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_drawing_analysis_skill.py \
  tests/unit/domain/services/test_chat_drawing_intent_service.py \
  tests/unit/domain/services/test_chat_drawing_validation_orchestration_service.py -q

# Smoke offline
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  python scripts/smoke_drawing_analyser.py

# Smoke E2E live (api-delpi direto + gateway + chat)
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app \\
  -e SMOKE_BASE_URL=http://delpi-gateway \\
  -e SMOKE_API_DELPI_URL=http://api-delpi:8000 minha-delpi-ai-api \\
  python scripts/smoke_drawing_analyser_live.py
```

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-05-29 | Criação: backlog Onda 12 a partir de paridade com ChatGPT DELPI (análise PDF); skill herdável na camada base. |
| 2026-05-31 | Estágio `drawing_analysis` no pipeline; smoke E2E HTTP; `drawingAnalysisExport` em `intelligence`. |
| 2026-05-31 | Testes regressão D1–D12 (`test_drawing_analysis_skill.py`) + intent drawing na regressão chat. |
| 2026-05-31 | `ChatDrawingMetricsService` — snapshot em metadata, adminDebug e audit log. |
| 2026-05-31 | Endpoint admin `GET /admin/metrics/drawing-analysis/summary` (histórico via audit). |
| 2026-05-31 | Painel **Análise de Desenhos DELPI** na aba Métricas do admin (MFE `minha-delpi-chat`). |
| 2026-05-31 | Roteamento explícito api-externa para `/analyser` (testes + smoke + policy/catálogo). |
| 2026-05-31 | Playbook OCR/visão chat base → [Onda 13](./inteligencia-chat-onda-13-skill-visao-documentos-ocr.md). |
| 2026-06-08 | Relatório DELPI (`drawingAnalysisExport`) sempre na resposta quando `/analyser` OK; card de anexo alinhado com `documentVision.legible` — ver [changelog](../../changelog/2026-06-chat-anexos-desenho-ux.md). |

---

## Relação com outras ondas

- **Onda 11** (paridade roteamento/velocidade) deve estar estável antes de adicionar intent drawing ao fast path.
- **Onda 12 alternativa** mencionada na Onda 11: `web_search` + citações — priorizar conforme produto; análise de desenhos é track **independente** (engenharia/qualidade).
