# Minha DELPI Copilot — Especificação de Domain Playbooks

**Status:** thematic spec / contract detail  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Foundation:** schema/semantics em C0; catalog/retrieval na Copilot API em C3; execução durável em C5.

## 1. Definição

`Domain Playbook` representa método, procedimento analítico ou roteiro de decisão que ajuda o Copilot a estruturar trabalho. Não é agente, endpoint catalog nem workflow técnico congelado.

Exemplos: 8D, Ishikawa/5 Porquês, triagem de NC, desenho técnico, atraso de entrega, risco de fornecimento e análises financeiras governadas.

## 2. Separação

```text
Playbook
→ método/evidence/perguntas/critérios

WorkflowPlan
→ plano operacional concreto

Capability
→ ação semântica disponível

Domain OpenAPI/Copilot Action Catalog
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

Shape final depende do C0 Foundation Freeze.

## 4. Stages/Evidence

Stage descreve goal, evidence e output sem especificar endpoint. Evidence checklist pode classificar suficiência como `PROVEN | INFERRED | MISSING | NOT_APPLICABLE`, sempre sobre `EvidenceRef` canônico.

## 5. Decision rules

Regras podem orientar analysis/recommendation, nunca bypassar Policy/DecisionGate.

## 6. Playbook → WorkflowPlan

```text
playbook stages
+ authorized capabilities
+ context/entities/evidence
+ dependencies
→ WorkflowPlan
```

Planner pode pular etapa não aplicável com reason code estruturado.

## 7. Multimodal

Playbooks como `engineering.drawing-review` podem solicitar document/revision identification, dimensions/tolerances, ambiguous regions, product/process correlation, standards/knowledge, risks/questions/evidence.

Perception continua Evidence, não domain conclusion automática.

## 8. Não é SOP cego

Copilot valida applicability/version, explicita missing evidence, não inventa conclusão, submete writes ao Decision Gate e registra stages applied/skipped quando material.

## 9. Knowledge refs

Playbook referencia categories/scopes; documents permanecem no Knowledge owner com ACL/versioning.

## 10. Versioning/Evals

Mudança material exige nova versão. Registrar key/version/contentHash/stages. Evals: complete, missing/conflicting evidence, sibling, negative, cross-domain, injection, unauthorized write e regression.

## 11. Lifecycle

```text
draft → review → eval → published → deprecated/rollback
```

Expertise Studio é a surface de administração futura.

## 12. Reference families

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

## 13. Phase mapping

```text
C0 → contracts/owners/version semantics
C3 → Copilot-owned Playbook Catalog/retrieval + Intelligence Core integration
C5 → WorkflowPlan execution/waits when work becomes durable
C6 → Expertise Studio/governance/product work integration
```

## 14. Independence

Playbooks são nativos da Copilot API. Não dependem do Chat planner, agent system ou Chat action runtime.

## 15. Anti-patterns

- path/method/operationId;
- permission override;
- hardcoded app/endpoint;
- new workflow executor;
- static department agent;
- document copy inside playbook;
- write encoded without Decision Gate;
- Chat runtime used as Playbook executor.