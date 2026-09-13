# Minha DELPI Copilot — Packs de Referência: Qualidade e Engenharia

**Status:** `REFERENCE_ONLY` — exemplos funcionais  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Mostrar como Expertise Packs, Playbooks, Knowledge, Multimodal Evidence e Business Capabilities se combinam no mesmo Copilot.

Não define schema/phase novo.

## 2. Referência `quality-industrial`

Finalidade:

- NC/reclamação;
- inspeção;
- reincidência;
- causa raiz;
- contenção;
- plano/efetividade.

Knowledge candidates, sujeitos a ACL:

- procedimentos/normas;
- planos de controle;
- instruções de inspeção;
- histórico curado;
- reclamações;
- critérios de liberação.

Preferred playbooks:

```text
quality.root-cause
quality.8d
quality.nonconformity-triage
quality.customer-complaint-analysis
```

Guidance:

- separar contenção, sintoma, causa e efeito;
- não declarar causa sem evidence;
- buscar recorrência;
- explicitar missing/conflicting evidence;
- recomendar ação proporcional ao risco;
- verificar efetividade.

## 3. Referência `product-engineering`

Finalidade:

- desenho/revisão;
- alteração de engenharia;
- tolerâncias/especificações;
- material/processo;
- technical comparison/change impact.

Preferred playbooks:

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
- correlacionar impacto somente com evidence.

## 4. Composição Engenharia + Qualidade

> “Analise este desenho e veja se ele pode explicar a não conformidade dimensional do lote.”

```text
attachment
→ Multimodal Evidence
→ product-engineering + quality-industrial
→ drawing-review playbook
→ authorized inspection/NC reads
→ specification x measurement comparison
→ FACT/CALCULATION/HYPOTHESIS/CONCLUSION
→ missing evidence
→ recommendation
```

Não afirmar causalidade sem evidence suficiente.

## 5. `quality.root-cause` — stages de referência

```text
RC1 definir problema
RC2 delimitar escopo
RC3 coletar evidence
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

Copilot pode preparar draft com campos faltantes explícitos; nunca inventar dados para completar formulário.

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

> “Analise o desenho 90264238, veja riscos de qualidade, procure problema semelhante e monte um 8D preliminar.”

```text
Entity/Attachment resolution
→ Multimodal Evidence
→ Engineering + Quality Expertise
→ drawing-review
→ Business/Knowledge reads
→ root-cause analysis
→ 8D artifact draft
→ gaps/limitations
```

Se houver write:

```text
Business Action
→ current RBAC/policy
→ Decision Gate
→ execute
→ verify Outcome/Evidence
```

## 9. Evals do piloto

- desenho legível;
- segunda revisão/item;
- desenho ilegível;
- unauthorized history;
- no evidence of cause;
- prompt injection in PDF;
- Engineering + Quality + Supplies composition;
- evidence provenance;
- no causality hallucination;
- session without agent.

## 10. Acceptance

```text
SINGLE_COPILOT_IDENTITY=PASS
EXPERTISE_COMPOSITION=PASS
MULTIMODAL_EVIDENCE=PASS
NO_CAUSALITY_HALLUCINATION=PASS
UNAUTHORIZED_DATA_BLOCKED=PASS
PLAYBOOK_GROUNDED=PASS
DECISION_GATE_ON_WRITES=PASS quando write no escopo
```