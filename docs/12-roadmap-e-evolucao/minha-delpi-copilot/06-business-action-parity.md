# 06 — Business Action Parity

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Automation fallback:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Objetivo

Garantir que operações materiais possuam **use case/contract reutilizável e verificável** para UI/Copilot, preservando as mesmas regras de negócio e autorização.

> Se uma operação pode ser exposta por Domain API/use case autoritativo, esse contrato é o caminho preferencial do Copilot.

## 2. Caminho preferencial

```text
UI ──────────────┐
                 ▼
           Use Case/API
                 ▲
Copilot ─────────┘
```

O formulário/tela não é business contract.

## 3. Legacy fallback — nuance importante

A ausência de API continua sendo um **AI-readiness gap do domínio**, mas `57` permite, quando C0/produto justificar, um executor legado governado:

```text
semantic capability
→ Policy/Decision
→ Automation & Execution Hub
→ RPA / computer-use adapter
→ legacy UI
→ Outcome verification
```

Esse fallback:

- não transforma DOM em contrato de negócio;
- não coloca click/selector no planner;
- não vira regra de negócio;
- não impede evolução futura RPA→API;
- exige idempotency/credentials/session isolation/outcome verification;
- computer-use é ainda mais restrito/sandboxed.

Portanto: **API-first, legacy executor only when justified**.

## 4. Runtime standalone

```text
Domain OpenAPI
→ Copilot importer/Action Catalog
→ Capability Projection
→ retrieval/planner
→ schema/argument validation
→ Policy/Decision Gate
→ executor selection
→ Domain API or governed legacy adapter
→ verified Outcome/Evidence
```

Never use Chat runtime as proxy.

## 5. Requirements for Copilot-ready operation

As applicable:

- business owner;
- use case/contract;
- schema/errors;
- RBAC/domain validation;
- risk/sensitivity;
- Decision/Autonomy policy;
- idempotency/concurrency semantics;
- correlation/audit;
- pre/postconditions;
- authoritative outcome verification source;
- tests/evals;
- entity/source metadata.

## 6. Reads — C4

Reads validate schema/authorization, normalize Evidence/Outcome/freshness, and never unexpectedly mutate state.

Analysis/metric/process reads do not create write authority.

## 7. Writes — C5+

```text
intent/event
→ allowed semantic capability
→ grounded arguments
→ schema validation
→ live authorization/policy
→ preview when material
→ Decision Gate
→ revalidation
→ executor
→ Outcome verification
→ Evidence/Audit/Notification
```

## 8. Decision Gate

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Decision binds arguments/evidence/impact/version and can expire/invalidate on material state/metric/model/policy change.

## 9. High-risk/destructive

Financial/material/admin/destructive/people/sensitive/external actions receive stronger policy/approval/audit and generally lower autonomy.

## 10. Binding / Validation

```text
Copilot binder/schema validator
→ early structured validation

Domain API/use case
→ definitive business validation/authority
```

RPA does not bypass domain/business validation; when legacy UI is the only formal boundary, C0 must document how business errors/postconditions are detected.

## 11. Outcome truth

Do not narrate success from transport/technical state alone.

```text
API 200
RPA Save clicked
provider accepted
```

may still require authoritative postcondition verification.

Ambiguous outcome is explicit and blocks blind retry.

## 12. Idempotency

Prefer domain guarantee. Otherwise use documented idempotency/reconciliation/lease semantics appropriate to executor. Resume/event duplicate cannot duplicate effect.

## 13. Coverage matrix

| Business function | Domain use case/API | OpenAPI | Permission | Risk | Decision/Autonomy | Idempotency | Outcome verifier | Legacy executor? | AI-ready |
|---|---|---|---|---|---|---|---|---|---|

Populate from real code/contracts during onboarding.

## 14. Iframe / UI

Iframe/view commands remain presentation-only. Business Action uses API when available. Legacy executor is an Automation Hub concern, never an IframeBridge/Portal shortcut.

## 15. Generalization

New OpenAPI/provider/executor implementation should satisfy same semantic capability without planner core patch. RPA→API migration changes adapter/mapping, not user intent/policy/workflow.

## 16. Benefit

Business Action parity improves UI, integrations, automation and Copilot by forcing reusable contracts and preserving a clean migration path away from fragile UI automation.
