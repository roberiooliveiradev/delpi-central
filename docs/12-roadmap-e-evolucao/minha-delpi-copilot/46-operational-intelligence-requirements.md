# Minha DELPI Copilot — Requisitos da Inteligência Operacional

**Status:** extensão da rastreabilidade `25-requirements-traceability.md`.

## 1. Requisitos CP-071+

| ID | Funcionalidade | Owner principal | Implantação sugerida | Gate | Status |
|---|---|---|---|---|---|
| CP-071 | DELPI Business Graph mínimo | AI/Platform + domain owners | O2 / C5 | permission-aware traversal | PLANNED |
| CP-072 | EntityRef cross-domain canônico | shared/domain owners | O0–O2 | contract/generalization | PLANNED |
| CP-073 | RelationshipRef com provenance | Business Graph | O2 | source/confidence | PLANNED |
| CP-074 | EvidenceRef transversal | AI/Presentation | O1 / C3 | provenance/freshness | PLANNED |
| CP-075 | FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION | AI synthesis | O1 | epistemic eval | PLANNED |
| CP-076 | Evidence multimodal por página/região | Multimodal | O1 | multimodal provenance | PLANNED |
| CP-077 | Copilot Task persistente | workflow/product | O3 / C4 | reload/no duplicate write | PLANNED |
| CP-078 | Copilot Case | product/workflow | O5 / C5 | lifecycle/evidence | PLANNED |
| CP-079 | Evidence Board do Case | Case/AI | O5 | accepted/contested/superseded | PLANNED |
| CP-080 | Interaction Room ligada a Case | Portal/domain room | O6 | RBAC/context | TO_INVENTORY |
| CP-081 | Copilot Inbox | Portal/AI | O7 | pending/result lifecycle | PLANNED |
| CP-082 | Watch por condição/evento | workflow/events | O8 | event/dedupe/RBAC | PLANNED |
| CP-083 | Watch modo OBSERVE | workflow | O8 | audit only | PLANNED |
| CP-084 | Watch modo ADVISE | workflow/AI | O8 | grounded alert | PLANNED |
| CP-085 | Watch modo ACT | policy/workflow | O8/C6 | L5/decision gate | LOCKED |
| CP-086 | Durable Workflow persistence/checkpoint | workflow runtime | O4/C4 | restart/resume | PLANNED |
| CP-087 | wait_user | workflow runtime | O4 | resume semantics | PLANNED |
| CP-088 | wait_approval | workflow runtime | O4/O9 | approval semantics | PLANNED |
| CP-089 | wait_event | workflow runtime | O4/O8 | event correlation | PLANNED |
| CP-090 | no duplicate write after resume | workflow/executor | O4 | idempotency | PLANNED |
| CP-091 | Decision Gate proporcional a risco | policy | O9/C6 | risk/policy | PLANNED |
| CP-092 | Approval workflow humano | policy/workflow | O9 | approver/RBAC/revalidate | PLANNED |
| CP-093 | What-if Simulation | domain analytics | O12 | reproducible model | LOCKED |
| CP-094 | Simulate → Apply separado | domain API/policy | O12 | new gate before write | LOCKED |
| CP-095 | Reference Knowledge lifecycle | Knowledge | O10 | owner/version/scope | REVALIDATE |
| CP-096 | Decision Knowledge | Case/Knowledge | O10 | no CoT + provenance | PLANNED |
| CP-097 | Experience Knowledge | Case/Knowledge | O10 | governed promotion | PLANNED |
| CP-098 | Solution Pattern lifecycle | Knowledge/Expertise | O10 | review/eval/version | PLANNED |
| CP-099 | Governed Learning Loop | AI admin | O10/O11 | no auto-publish | PLANNED |
| CP-100 | Expertise Studio lifecycle | AI admin | O11 | draft→published gates | PLANNED |
| CP-101 | Expertise/Playbook version rollback | AI admin | O11 | version/eval | PLANNED |
| CP-102 | Model Router | AI infrastructure | O13 | quality/cost/latency | LOCKED |
| CP-103 | Compute Policy | AI/policy | O13 | model/provider constraints | LOCKED |
| CP-104 | Provider data-policy filtering | AI/security | O13 | privacy/security | LOCKED |
| CP-105 | Task Completion por Task/Case | observability | O3/O5 | metric validity | PLANNED |
| CP-106 | Case resolution learning candidate | Case/Knowledge | O10 | governed candidate only | PLANNED |
| CP-107 | Inbox approval → workflow resume | Portal/workflow | O7/O9 | correlation/revalidation | PLANNED |
| CP-108 | Room summary grounded em Case | AI/Room | O6 | evidence/RBAC | TO_INVENTORY |
| CP-109 | Business Graph sibling onboarding | Business Graph | O2 | no planner hardcode | PLANNED |
| CP-110 | Anchor workflow reclamação→8D→watch→ação | cross-domain | O1–O9 | integration gate | LOCKED |

## 2. Regras

- estes requisitos seguem os mesmos status e COMPLETE_GATE de `25-requirements-traceability.md`;
- `TO_INVENTORY` não deve ser convertido por suposição;
- `LOCKED` só é liberado após dependências técnicas/policy correspondentes;
- nenhuma feature estratégica altera a ordem obrigatória de iniciar em C0.S0.

## 3. Coverage final adicional

```text
BUSINESS_GRAPH_REQUIREMENTS
EVIDENCE_REQUIREMENTS
TASK_CASE_REQUIREMENTS
PROACTIVE_REQUIREMENTS
DURABLE_WORKFLOW_REQUIREMENTS
DECISION_REQUIREMENTS
KNOWLEDGE_REQUIREMENTS
MODEL_ROUTER_REQUIREMENTS
UNMAPPED_OPERATIONAL_REQUIREMENTS
```

`UNMAPPED_OPERATIONAL_REQUIREMENTS` deve ser zero no release que declare o escopo correspondente completo.