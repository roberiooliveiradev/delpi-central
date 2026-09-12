# 06 — Business Action Parity

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Objetivo

Garantir que toda operação material disponível na UI possua use case/API reutilizável pelo Copilot sob as mesmas regras de negócio e autorização.

> Se a UI consegue executar uma ação de negócio, o Copilot deve conseguir usar o mesmo contrato quando o usuário estiver autorizado — sem automatizar a tela.

## 2. Anti-padrão

```text
Copilot
→ abre tela
→ procura botão/input
→ preenche DOM
→ clica salvar
```

Se não existir API/use case, o gap pertence ao domínio. DOM/browser workaround não torna a operação AI-ready.

## 3. Padrão correto

```text
UI ──────────────┐
                 ▼
           Use Case/API
                 ▲
Copilot ─────────┘
```

## 4. Runtime standalone

A cadeia é implementada **na nova Copilot API**, diretamente sobre Domain OpenAPIs/APIs.

```text
Domain OpenAPI
→ Copilot importer/Action Catalog
→ authorized Capability Projection
→ retrieval/planner
→ schema/argument validation
→ policy/Decision Gate
→ generic executor
→ Domain API
→ Outcome/Evidence
```

Não usar `minha-delpi-ai-api` como proxy/runtime.

## 5. Requisitos Copilot-ready

Uma operação deve possuir, conforme aplicável:

- business owner;
- use case/contract claro;
- HTTP/API ou internal capability tipada;
- OpenAPI quando HTTP;
- input/output schema;
- errors;
- RBAC;
- risk/sensitivity;
- Decision Gate policy;
- idempotency/concurrency semantics;
- correlation/audit para writes;
- tests;
- outcome verificável;
- entity/source metadata suficiente para presentation/evidence.

## 6. Reads — C4

C4 libera generic reads após C3 estabilizar o Intelligence Core/OpenAPI Action foundation.

Reads devem:

- validar schema/args;
- revalidar authorization;
- normalizar outcome;
- registrar source/freshness/evidence quando material;
- não mutar estado inesperadamente.

## 7. Writes — C5

C5 libera writes após reads/evidence C4 e Decision Gate contracts C0.

```text
intent
→ allowed action
→ grounded arguments
→ schema validation
→ RBAC/policy
→ impact preview
→ Decision Gate
→ revalidation
→ execute
→ verify outcome
→ evidence/audit/deep link
```

## 8. Decision Gate

Não usar boolean `requiresConfirmation` como modelo final.

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Decision vincula arguments/evidence/impact e possui expiry/invalidation semantics.

## 9. High-risk/destructive

Cancelamento, exclusão, rejeição irreversível, aprovação de alto impacto e alteração financeira/sensível podem exigir gate/approver/audit mais forte.

## 10. Formulário não é contrato

Schema vem do Domain API/use case, não da tela.

```text
User request
→ grounded fields
→ required missing
→ clarify only missing
→ Decision Gate when required
→ Domain API
```

## 11. Validation

```text
Copilot binder/validator
→ early structured validation

Domain API/use case
→ definitive business validation/authority
```

## 12. Outcome/Evidence

Write só é narrado como executado após outcome real.

Errors/states podem incluir:

```text
validation_error
permission_denied
not_found
conflict
policy_blocked
decision_required
decision_expired
provider_unavailable
timeout
ambiguous_outcome
business_rule_violation
partial_failure
```

Ambiguous outcome requer reconciliation antes de retry.

## 13. Idempotency

Preferir garantia do domínio. Retry write somente com idempotency comprovada ou reconciliation segura.

Essas semantics nascem em C0 e são usadas por C5 Durable Work.

## 14. Coverage matrix por app

| UI function | Domain API/use case | OpenAPI | Permission | Risk | Decision Gate | Idempotency | Outcome/Evidence | AI-ready |
|---|---|---|---|---|---|---|---|---|

Matriz baseada em código/contratos reais durante onboarding.

## 15. Ordem canônica

```text
C3 intelligence/action foundation
→ C4 reads + Graph
→ C5 prepare/Decision Gate/non-destructive writes
→ C5 high-risk writes when gates pass
→ C5 durable foundation
→ C6 Tasks/Cases/Watch composition
```

Não criar write-demo antes das foundations.

## 16. Iframe

Mesmo com UI em iframe:

```text
Copilot → Domain API Business Action
```

Nunca `view.click_button` como substituto.

## 17. Generalization

Novo OpenAPI/provider semanticamente descrito e autorizado deve funcionar pelo pipeline genérico sem selector por path/provider/opId.

## 18. Benefício

Parity melhora simultaneamente UI, integrações, automação e Copilot porque força o negócio para contratos reutilizáveis, verificáveis e owner-driven.