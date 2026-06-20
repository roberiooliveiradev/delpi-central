# Changelog — BOM colunar, refinamento de visão e assertividade 95% (Fase 15.8)

**Data:** 20/06/2026  
**Escopo:** documentação de implementação pendente — skill desenho orquestra visão do chat base; usuário não envia print/zoom.  
**Playbook:** [`playbook_bom_colunar_visao_skill_desenho.md`](../roadmap/melhorias/playbook_bom_colunar_visao_skill_desenho.md)

---

## Contexto

Regressão `90263149`: OCR lia QTD da **descrição** (`6,35`, `6 PINOS`, `00120` mm), gerando críticos BOM falsos. O fix jun/2026 (`ChatDrawingBomQuantityAssertivenessService`) evita crítico, mas **pending** não substitui leitura correta da coluna QTD.

## Diretriz

| Camada | Responsabilidade |
|--------|------------------|
| Chat base (`document-vision-delpi`) | OCR, regiões, `tables[]` genérico, `TableCellRefinementPort` — **sem** vocabulário BOM/QTD/SG1010 |
| Skill (`drawing-analysis-delpi`) | Interpreta tabela como BOM; compara × SG1010; orquestra refinamento; assertividade |
| Usuário | Anexa PDF uma vez — **não** participa do loop de leitura |

Fronteira detalhada: playbook § 0.

## Entregas planejadas (15.8.1–15.8.6)

Ver playbook § 5 — serviços novos, JSON, testes, gate `--assertiveness-gate`.

## Relacionado

- Assertividade QTD jun/2026: commit `fix(chat): assertividade na validação BOM…`
- Onda 15.7 retry confiança: `ChatDrawingExtractionQualityRetryService` (alvo 95% extração global)
