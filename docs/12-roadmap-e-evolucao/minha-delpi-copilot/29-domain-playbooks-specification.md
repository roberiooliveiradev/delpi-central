# Minha DELPI Copilot — Especificação de Domain Playbooks

**Status:** thematic spec / contract detail  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** schema/semantics em C0; catalog/retrieval em C2; execução durável em C5.

## 1. Definição

`Domain Playbook` representa método, procedimento analítico ou roteiro de decisão que ajuda o Copilot a estruturar trabalho.

Não é agente, endpoint catalog nem workflow técnico congelado.

Exemplos:

- 8D;
- Ishikawa/5 Porquês;
- triagem de NC;
- análise de desenho;
- atraso de entrega;
- risco de fornecimento;
- análise financeira quando governada.

## 2. Separação

```text
Playbook
→ método/evidence/perguntas/critérios

WorkflowPlan
→ plano operacional concreto

Capability
→ ação semântica disponível

OpenAPI/Action Catalog
→ contrato técnico da Business Action

DecisionGate
→ governança de decisão/write
```

## 3. Estrutura conceitual

```json
{
  "schemaVersion":1,
  "key":"quality.8d",
  "version":"1.0.0",
  "label":"Análise 8D",
  "purpose":"Estruturar investigação e plano de ação.",
  "applicability":{"domains":["quality"],"signals":["nonconformity","complaint"]},
  "stages":[],
  "evidenceChecklist":[],
  "decisionRules":[],
  "recommendedCapabilities":[],
  "artifactTemplates":[],
  "completionCriteria":[],
  "safetyNotes":[],
  "owner":"quality-owner",
  "status":"active"
}
```

Shape final depende do C0 foundation freeze.

## 4. Stages

Stage descreve problema a resolver, evidência esperada e output sem especificar endpoint.

```json
{
  "stageId":"containment",
  "goal":"Definir contenção imediata",
  "requiredEvidence":["affectedScope","riskAssessment"],
  "optionalCapabilityKinds":["business.read","knowledge"],
  "produces":["containmentProposal"]
}
```

## 5. Evidence checklist

Playbook deve orientar suficiência de evidence e estados como:

```text
PROVEN
INFERRED
MISSING
NOT_APPLICABLE
```

Esses estados não substituem `EvidenceRef`; são avaliação metodológica sobre evidence disponível.

## 6. Decision rules

Podem orientar análise/recommendation, mas nunca bypassar Policy/DecisionGate.

Exemplo:

```text
stock=0 + critical purchase late
→ classify supply risk
→ recommend buyer review
```

A recommendation não executa write automaticamente.

## 7. Playbook → WorkflowPlan

```text
playbook stages
+ authorized capabilities
+ current context/entities/evidence
+ dependencies
→ WorkflowPlan
```

Planner pode pular stage não aplicável com reason code estruturado.

## 8. Multimodal playbook

`engineering.drawing-review`, por exemplo, pode pedir:

1. document/revision identification;
2. relevant notes/dimensions/tolerances;
3. ambiguous regions;
4. product/process correlation;
5. authorized standards/knowledge;
6. risks/questions/evidence;
7. output checklist/report.

Perception output continua Evidence, não conclusão automática.

## 9. Não é SOP cego

Copilot deve:

- validar applicability;
- usar versão vigente;
- explicitar missing evidence;
- não inventar conclusão;
- submeter writes ao Decision Gate;
- registrar stages aplicados/pulados quando material.

## 10. Knowledge refs

Playbook referencia categories/scopes, mas documentos permanecem no Knowledge owner com ACL/versioning.

## 11. Versioning

Mudança material de método/critério/output exige nova versão.

Registrar:

```text
playbookKey
version
contentHash
stagesApplied/skipped
```

## 12. Evals

- complete scenario;
- missing evidence;
- conflicting evidence;
- sibling;
- not applicable;
- cross-domain;
- malicious document/evidence;
- unauthorized proposed write;
- version regression.

## 13. Lifecycle

```text
draft
→ review
→ eval
→ published
→ deprecated/rollback
```

Expertise Studio é a surface de administração futura; não muda o contrato.

## 14. Reference families

Qualidade:
- `quality.8d`;
- `quality.root-cause`;
- `quality.nonconformity-triage`.

Engenharia:
- `engineering.drawing-review`;
- `engineering.change-impact-analysis`.

Suprimentos:
- `supplies.shortage-risk`;
- `supplies.purchase-delay-analysis`.

Cross-domain:
- `operations.delivery-delay-analysis`.

Implantação real começa por poucos playbooks com evidence disponível, não por um catálogo completo.

## 15. Anti-patterns

- path/method/operationId;
- permission override;
- hardcoded app/endpoint;
- new workflow executor;
- static department agent;
- document copy inside playbook;
- write execution encoded as methodology step without Decision Gate.
