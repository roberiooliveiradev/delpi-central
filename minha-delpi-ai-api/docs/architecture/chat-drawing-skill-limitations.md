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
| api-delpi `/analyser` | Dados Protheus | `pa_reference`, `conversion_factor` do PA; `B1_CONV` nos itens da estrutura |

**Ordem de autoridade:** checklist (`drawingAnalysis.items[]`) → pipeline → API → policies/RAG.

---

## Limitações conhecidas

### Conversão de unidades (Protheus)

| ID | Limitação | Impacto | Mitigação / status |
|----|-----------|---------|-------------------|
| U1 | Quantidades da SG1010 são **por 1 PA / 1 MI** | Usuário pode achar que 650 MT é «por chicote» sem conversão | Policy + pipeline dividem por milheiro; `pa_reference` no `/analyser` |
| U2 | `B1_CONV` do PA zerado no cadastro | Fallback `piecesPerMilheiro: 1000` em `drawing_validation.json` | Aceito para padrão DELPI; cadastro deve preencher `B1_CONV` quando ≠ 1000 |
| U3 | `B1_UM3` / `B1_CONV3` | Terceira UM não tratada | Fora do escopo chicote atual |
| U4 | Conversão **fiscal** (`SB5010`) | NF-e / DIPI | Fora do escopo de desenho (correto) |
| U5 | `SAH010` | Só descrição de UM | Pipeline não usa para fator (correto) |
| U6 | RAG do tutorial depende de **ingest** no agente | Narrativa sem chunks se não indexado | `build_rag_query` enriquece busca; policy fixa no turno; rodar ingest do bundle |
| U7 | Materiais em MT que **não** são cabo (`104…`) | QTD BOM pendente sem dimensão no PDF | Tubo via segmentos + `B1_CONV` componente; termoencolhível etc. pendente sem cota |

### Extração PDF / OCR

| ID | Limitação | Impacto |
|----|-----------|---------|
| O1 | BOM **colunar** difícil (âncora `90263149`) | Falsos extras/críticos residuais |
| O2 | PDF **multipágina** com cobertura baixa | `multipage_coverage` pendente |
| O3 | **Sem PDF** anexo e sem biblioteca | Só cadastro/roteiro/inspeção; `pdf_missing` / `bom_pending` |
| O4 | PDF não indexado (`GET /drawing/pdf` 404) | Requer anexo na sessão |

### Validação × API

| ID | Limitação | Impacto |
|----|-----------|---------|
| V1 | Roteiro com PI **legado** (fingerprint de cabo) | Heurística, não prova formal |
| V2 | Família **7026** desliga `balloon_presence` | Regra não universal |
| V3 | Tolerâncias fixas (±10% QTD, mm) | JSON `drawing_validation.json` |
| V4 | Vigência BOM (`G1_FIM`) | Desenho antigo × estrutura vigente pode divergir sem aviso explícito no checklist |
| V5 | LLM **não** reclassifica checklist | Por desenho (render-only); usuário pode discordar da narrativa sem mudar status |

---

## O que já está resolvido (jun/2026)

- MI → peça (`batch_scale` via `B1_CONV` do PA ou 1000 + `pa_reference`)
- **`B1_CONV` por componente** na estrutura (`ChatDrawingProductUnitConversionService` + campos api-delpi)
- Query RAG enriquecida em turnos de desenho (`ChatDrawingIntentService.build_rag_query`)
- Cota 650 mm × 650 MT tubo (90262008 **Aprovado**, 0 pendentes)
- Policies: render-only + conversão de unidades em todo turno de desenho
- api-delpi: `pa_reference` no `/analyser`; campos de conversão nos itens da estrutura
- 15/15 regras com regressão por categoria (`drawing_validation_rules.json`)

---

## Roadmap de fechamento (prioridade)

1. **Homologação BOM colunar** (`90263149`) — playbook 15.8
2. **Ingest RAG** `produto-conversao-unidades-protheus.txt` no agente de engenharia
3. **OCR hierárquico** fases 14.5–14.6 (cotas/BOM)
4. Cadastro Protheus: preencher `B1_CONV` onde o fator real ≠ default 1000

---

## Referências

- Tutorial RAG: [`../knowledge/domains/agents/minha-delpi-chat/produto-conversao-unidades-protheus.txt`](../knowledge/domains/agents/minha-delpi-chat/produto-conversao-unidades-protheus.txt)
- Playbook api-delpi: [`../../../api-delpi/docs/roadmaps/playbook-conversao-unidades-protheus.md`](../../../api-delpi/docs/roadmaps/playbook-conversao-unidades-protheus.md)
- Desacoplamento skill: [`../roadmap/melhorias/playbook_skill_desenho_desacoplamento.md`](../roadmap/melhorias/playbook_skill_desenho_desacoplamento.md)
- Inteligência chat base (desenho): [`chat-intelligence-base.md`](./chat-intelligence-base.md)
