# Skill `drawing-analysis-delpi` — limitações e roadmap de fechamento

**Status:** jun/2026  
**Escopo:** análise e validação de desenhos técnicos DELPI (PDF × api-delpi × checklist)  
**Princípio:** toda semântica de desenho vive na skill (`ChatDrawing*` + `drawing_*.json`); chat comum e `document-vision-delpi` **não** participam.

---

## Arquitetura de responsabilidade

| Camada | Papel | Conversão de unidades |
|--------|--------|------------------------|
| `document-vision-delpi` | OCR/layout genérico | Não |
| **`drawing-analysis-delpi`** | BOM, SG1010, cotas, checklist | Pipeline `ChatDrawingBomQuantitySemanticsService` + `ChatDrawingProductUnitConversionService` |
| LLM (policies) | Narrativa e explicação | `drawing-analysis-unit-conversion.md` + RAG `produto-conversao-unidades-protheus.txt` |
| api-delpi `/analyser` | Dados Protheus | `pa_reference`, `conversion_factor` do PA; `B1_CONV` / `B1_CONV3` nos itens da estrutura |

**Ordem de autoridade:** checklist (`drawingAnalysis.items[]`) → pipeline → API → policies/RAG.

---

## Limitações conhecidas

### Conversão de unidades (Protheus)

| ID | Limitação | Impacto | Mitigação / status |
|----|-----------|---------|-------------------|
| U1 | Quantidades da SG1010 são **por 1 PA / 1 MI** | Usuário pode achar que 650 MT é «por chicote» sem conversão | Policy + pipeline dividem por milheiro; `pa_reference` no `/analyser` |
| U2 | `B1_CONV` do PA zerado no cadastro | Fallback `piecesPerMilheiro: 1000` em `drawing_validation.json` | Aceito para padrão DELPI; cadastro deve preencher `B1_CONV` quando ≠ 1000 |
| U3 | `B1_UM3` / `B1_CONV3` | Terceira UM em cadeia rara (CX→UN→MM) | **Implementado** — SQL estrutura + `ChatDrawingProductUnitConversionService` |
| U4 | Conversão **fiscal** (`SB5010`) | NF-e / DIPI | Fora do escopo de desenho (correto) |
| U5 | `SAH010` | Só descrição de UM | Pipeline não usa para fator (correto) |
| U6 | RAG do tutorial depende de **ingest** no agente | Narrativa sem chunks se não indexado | **Catálogo** `agentKnowledgeSources` + `scripts/sync_drawing_agent_knowledge.py --ingest` |
| U7 | Materiais em MT que **não** são cabo (`104…`) | QTD BOM sem cota no PDF | **Implementado** para tubo/termo (`101`/`105` + marcadores); sem cota → pendente |

### Extração PDF / OCR

| ID | Limitação | Impacto | Status |
|----|-----------|---------|--------|
| O1 | BOM **colunar** (âncora `90263149`) | Falsos extras por ruído de QTD | **Homologado** — regressão `test_chat_drawing_validation_90263149.py` + refinamento colunar |
| O2 | PDF **multipágina** com cobertura baixa | BOM parcial | **Implementado** — `multipage_coverage` + demotion de ausências |
| O3 | **Sem PDF** anexo e sem biblioteca | Só cadastro/roteiro/inspeção | Intencional — `pdf_missing` / `bom_pending` |
| O4 | PDF não indexado (`GET /drawing/pdf` 404) | Requer anexo na sessão | Intencional — por sessão |

### Validação × API

| ID | Limitação | Impacto | Status |
|----|-----------|---------|--------|
| V1 | Roteiro com PI **legado** (fingerprint de cabo) | Heurística, não prova formal | Parcial — por desenho |
| V2 | Família **7026** desliga `balloon_presence` | Regra não universal | Config JSON |
| V3 | Tolerâncias fixas (±10% QTD, mm) | JSON `drawing_validation.json` | Declarativo |
| V4 | Vigência BOM (`G1_FIM`) | Desenho antigo × estrutura vigente | **Implementado** — `structure.bom_validity` + checklist `structure_bom_validity` |
| V5 | LLM **não** reclassifica checklist | Render-only | Intencional |
| V6 | Código cabo **CA\*** (`00653`) confundido com comprimento do chicote | Falso crítico `653 MT` × PDF | **Implementado** — âncora `660MM` na descrição do PA + referência em mm (`90260027`) |
| V7 | `total_length` crítico com OCR de cotas ruim | Reprovação indevida | **Implementado** — `total_length` em `pdfDependentTemplateKeys` (gate ≥ 95%) |

---

## Apresentação do relatório (chat)

| Item | Onde | Notas |
|------|------|--------|
| Outline SG1010 | Markdown seção 3 (`format_analyser_detail_sections`) | Árvore interativa do `/analyser` suprimida no MFE — `assistantProseRendering.ts` |
| Cotas × estrutura | Markdown seção 4 (`format_dimensions_comparison_section`) | Tabela PDF × SG1010 + linhas por intermediário |
| Export completo | `drawingAnalysisExport` | PDF/CSV/XLSX com tabelas operacionais |

Changelog: [`../changelog/2026-06-drawing-cotas-estrutura-relatorio.md`](../changelog/2026-06-drawing-cotas-estrutura-relatorio.md).

---

## O que já está resolvido (jun/2026)

- MI → peça (`batch_scale` via `B1_CONV` do PA ou 1000 + `pa_reference`)
- **`B1_CONV` e `B1_CONV3`** por componente na estrutura (api-delpi + `ChatDrawingProductUnitConversionService`)
- Materiais consumíveis por comprimento (`101`/`105`, tubo/termoencolhível) com cotas PDF
- Query RAG enriquecida em turnos de desenho (`ChatDrawingIntentService.build_rag_query`)
- Cota 650 mm × 650 MT tubo (90262008 **Aprovado**, 0 pendentes)
- Policies: render-only + conversão de unidades em todo turno de desenho
- api-delpi: `pa_reference` no `/analyser`; `bom_validity` em `/structure`
- BOM colunar 90263149 e multipágina com regressão dedicada
- Aviso explícito de vigência BOM no checklist (`ChatDrawingStructureValidityNoticeService`)
- Ingest RAG: `ChatDrawingAgentKnowledgeCoverageService` + `sync_drawing_agent_knowledge.py`
- **16/16** regras com regressão por categoria (`drawing_validation_rules.json`)
- **Cotas × estrutura** no relatório markdown + referência de comprimento em mm (jun/2026 — `90260027`)
- PI aninhado sob PA na coleta de intermediários; gate `total_length` com confiança OCR

---

## Roadmap residual (prioridade)

1. **Rodar ingest** em ambiente com DB: `sync_drawing_agent_knowledge.py --ingest` (atualizar `manifest.json`)
2. **OCR hierárquico** fases 14.5–14.6 (cotas/BOM) — qualidade de extração da região `dimensions`
3. Cadastro Protheus: preencher `B1_CONV` onde o fator real ≠ default 1000
4. Estrutura **histórica** por data de revisão do PDF (hoje só vigente + aviso)

---

## Referências

- Tutorial RAG: [`../knowledge/domains/agents/minha-delpi-chat/produto-conversao-unidades-protheus.txt`](../knowledge/domains/agents/minha-delpi-chat/produto-conversao-unidades-protheus.txt)
- Sync ingest: [`../../scripts/sync_drawing_agent_knowledge.py`](../../scripts/sync_drawing_agent_knowledge.py)
- Playbook api-delpi: [`../../../api-delpi/docs/roadmaps/playbook-conversao-unidades-protheus.md`](../../../api-delpi/docs/roadmaps/playbook-conversao-unidades-protheus.md)
- Desacoplamento skill: [`../roadmap/melhorias/playbook_skill_desenho_desacoplamento.md`](../roadmap/melhorias/playbook_skill_desenho_desacoplamento.md)
- Inteligência chat base (desenho): [`chat-intelligence-base.md`](./chat-intelligence-base.md)
- Cotas e estrutura no relatório: [`../changelog/2026-06-drawing-cotas-estrutura-relatorio.md`](../changelog/2026-06-drawing-cotas-estrutura-relatorio.md)
- Infra prod (latência LLM): [`../../../infra/README-ambiente.md`](../../../infra/README-ambiente.md) § LLM chat
