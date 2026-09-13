# DÉLIA — Packs de Referência: Qualidade e Engenharia

**Status:** `REFERENCE_ONLY` — exemplos funcionais, não prova de runtime/catalog  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Mostrar conceitualmente como Expertise Packs, Playbooks, Knowledge, Multimodal Evidence e Business Capabilities podem se combinar na mesma DÉLIA.

Não define schema, owner, phase, catalog ou implementation novos.

## 2. Referência `quality-industrial`

Finalidade conceitual:

- NC/reclamação;
- inspeção;
- reincidência;
- causa raiz;
- contenção;
- plano/efetividade.

Knowledge candidates, sempre sujeitos a owner/ACL/version:

- procedimentos/normas;
- planos de controle;
- instruções de inspeção;
- histórico curado;
- reclamações;
- critérios de liberação.

Preferred playbooks candidatos:

```text
quality.root-cause
quality.8d
quality.nonconformity-triage
quality.customer-complaint-analysis
```

Guidance:

- separar contenção, sintoma, causa e efeito;
- não declarar causa sem Evidence;
- buscar recorrência;
- explicitar missing/conflicting Evidence;
- recomendar ação proporcional ao risco;
- verificar efetividade.

## 3. Referência `product-engineering`

Finalidade conceitual:

- desenho/revisão;
- alteração de engenharia;
- tolerâncias/especificações;
- material/processo;
- technical comparison/change impact.

Preferred playbooks candidatos:

```text
engineering.drawing-review
engineering.change-impact-analysis
engineering.technical-comparison
```

Guidance:

- registrar documento/revisão;
- não inventar dimensão ilegível;
- separar especificação de inferência;
- apontar ambiguity/limitation;
- correlacionar impacto somente com Evidence.

## 4. Composição Engenharia + Qualidade

Cenário de referência:

```text
attachment/source
→ Multimodal Evidence
→ product-engineering + quality-industrial
→ drawing-review playbook
→ authorized inspection/NC reads
→ specification x measurement comparison
→ FACT/CALCULATION/HYPOTHESIS/CONCLUSION
→ missing Evidence
→ recommendation
```

Não afirmar causalidade sem Evidence suficiente.

## 5. `quality.root-cause` — stages de referência

```text
RC1 definir problema
RC2 delimitar escopo
RC3 coletar Evidence
RC4 separar sintomas de causas candidatas
RC5 estruturar hipóteses
RC6 testar hipóteses
RC7 selecionar causas suportadas
RC8 propor ação/verificação
```

## 6. `quality.8d` — stages de referência

```text
D1 equipe/responsáveis quando aplicável
D2 descrição
D3 contenção
D4 causa raiz
D5 ação corretiva
D6 implementação/verificação
D7 prevenção
D8 conclusão
```

DÉLIA pode preparar draft com campos faltantes explícitos; nunca inventar dados para completar formulário.

## 7. `engineering.drawing-review` — stages de referência

```text
E1 documento/revisão
E2 título/notas/material
E3 características críticas
E4 tolerâncias/símbolos
E5 ambiguity/unreadable
E6 item/process correlation
E7 related standards/knowledge
E8 risks/questions
```

## 8. Caso composto

```text
Entity/Attachment resolution
→ Multimodal Evidence
→ Engineering + Quality Expertise
→ drawing-review
→ authorized Business/Knowledge reads
→ root-cause analysis
→ 8D artifact draft
→ gaps/limitations
```

Se houver material ACT:

```text
Business Action intent
→ live AuthZ/Policy/Decision
→ Domain API or Automation Hub/approved executor path
→ authoritative Outcome verification
```

## 9. Evals do piloto

- desenho legível;
- segunda revisão/item;
- desenho ilegível;
- unauthorized history;
- no Evidence of cause;
- prompt injection in PDF;
- cross-domain composition;
- provenance;
- no causality hallucination;
- no agent dependency.

## 10. Acceptance

Este arquivo não pode declarar `PASS` por si só. Os cenários são acceptance targets; prova válida depende de runtime/tests/evidence do SHA/config avaliado.
