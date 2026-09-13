# DÉLIA — Especificação de Domain Playbooks

**Status:** `TARGET` — thematic spec / contract detail  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Evidence rule:** schema, catalog, storage e retrieval só são implementados quando owner/contract/lifecycle forem provados e o Abstraction Gate justificar.

## 1. Definição

`Domain Playbook` representa método, procedimento analítico ou roteiro de decisão que ajuda a DÉLIA a estruturar trabalho. Não é agente, endpoint catalog, permission authority nem workflow técnico congelado.

Exemplos conceituais: 8D, Ishikawa/5 Porquês, triagem de NC, revisão de desenho, atraso de entrega, risco de fornecimento e análises financeiras governadas.

## 2. Separação

```text
Playbook
→ método/evidence/perguntas/critérios

WorkflowPlan
→ plano operacional concreto da DÉLIA Work

Capability
→ ação semântica disponível

Domain API/OpenAPI
→ contrato técnico e business authority

Policy/Decision
→ governança de PREPARE/ACT

Automation Hub
→ execução técnica quando aplicável
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

O shape é candidate. C0 deve decidir owner, fonte canônica, consumers, versioning, storage e lifecycle.

## 4. Stages/Evidence

Stage descreve goal, evidence e output sem especificar endpoint. Evidence checklist pode classificar suficiência de forma estruturada, sempre sobre Evidence/Source refs governados.

Não usar classificação epistemic local que conflite com `38-evidence-provenance-and-epistemic-ux.md`.

## 5. Decision rules

Regras podem orientar análise/recommendation, nunca bypassar Policy/Decision ou Domain authorization.

## 6. Playbook → WorkflowPlan

```text
playbook stages
+ authorized capabilities
+ context/entities/evidence
+ dependencies
→ WorkflowPlan candidate
```

Planner pode pular etapa não aplicável com reason code estruturado. Playbook não executa side effect diretamente.

## 7. Multimodal

Playbooks como `engineering.drawing-review` podem solicitar document/revision identification, dimensions/tolerances, ambiguous regions, product/process correlation, standards/knowledge, risks/questions/evidence.

Perception continua Evidence, não domain conclusion automática.

## 8. Não é SOP cego

DÉLIA valida applicability/version, explicita missing evidence, não inventa conclusão, submete material ACT a Policy/Decision/AuthZ e registra stages applied/skipped quando material.

## 9. Knowledge refs

Playbook referencia categories/scopes; documentos permanecem no Knowledge/source owner com ACL/versioning.

## 10. Versioning/Evals

Mudança material exige versionamento. Quando implementado, registrar key/version/contentHash/stages. Evals incluem complete, missing/conflicting evidence, sibling, negative, cross-domain, injection, unauthorized write e regression.

## 11. Lifecycle

Target:

```text
draft → review → eval → published → deprecated/rollback
```

Nenhuma candidate vira procedure/policy/conhecimento corporativo automaticamente.

## 12. Reference families

Famílias abaixo são exemplos, não catálogo implementado:

```text
quality.8d
quality.root-cause
quality.nonconformity-triage
engineering.drawing-review
engineering.change-impact-analysis
supplies.shortage-risk
supplies.purchase-delay-analysis
operations.delivery-delay-analysis
```

## 13. Phase mapping

```text
C0 → owner/contracts/version/lifecycle decisions
C3 → retrieval/catalog somente se requirements + Abstraction Gate justificarem
C5 → Durable Work pode materializar etapas que requerem waits/Decision/execution
C6 → governance/product integration quando priorizada
```

## 14. Independence

Playbooks são capability target da DÉLIA e não dependem do Chat planner, agent system ou Chat action runtime.

## 15. Anti-patterns

- path/method/operationId como método;
- permission override;
- hardcoded app/endpoint;
- novo workflow executor;
- static department agent;
- document copy inside playbook;
- write encoded sem Policy/Decision/AuthZ;
- technical execution implementada pelo playbook;
- Chat runtime usado como executor.
