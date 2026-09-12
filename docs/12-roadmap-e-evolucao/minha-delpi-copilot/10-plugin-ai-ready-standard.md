# 10 — Padrão AI-ready para apps e plugins

## 1. Objetivo

Todo app da Minha DELPI deve poder evoluir para uso pela UI e pelo Copilot **sem hardcode central e sem criar contratos paralelos**.

## 2. Princípio

```text
App
├─ manifesto/routes/permissions
├─ APIs/use cases
├─ OpenAPI
├─ EntityRef/deep-link metadata
├─ Workspace Context adapter
├─ Evidence/provenance-friendly responses quando relevante
├─ sensitivity/Decision Gate metadata/policy
├─ optional UI capabilities
└─ optional event integration
        ↓
Minha DELPI Copilot
```

## 3. Requisitos estruturais

### App/route identity

- `appId` estável;
- rotas identificáveis;
- permission alinhada;
- labels/descrições semânticas;
- não ensinar URL livre ao LLM.

### Business use cases

Regra de negócio fica em API/use case, nunca apenas em componente React.

### OpenAPI

Para actions consumíveis:

- summary/description úteis;
- operationId estável como metadata técnica, não semântica de routing;
- required/type/enum/format corretos;
- request/response schemas;
- erros/security schemes;
- exemplos úteis.

### RBAC

Visibilidade de botão não é autorização. Backend revalida.

## 4. Shared foundations que o app deve reutilizar

Quando aplicável:

- `EntityRef` compartilhado;
- `SourceRef/EvidenceRef/OutcomeRef` semantics;
- `WorkspaceContext`;
- Platform Command/deep-link conventions;
- Decision Gate policy model;
- `EventEnvelope` para eventos integráveis;
- iframe protocol se render mode exigir.

Não criar `MyAppEntityRef`, `MyAppConfirmation`, `MyAppCopilotEvent` incompatíveis se o shared contract atende.

## 5. Workspace Context Adapter

Publicar somente contexto útil:

- entidade atual;
- filtros;
- período;
- seleção;
- view/aba;
- refs de dados visíveis.

Não publicar React state, DOM, token ou dataset inteiro.

## 6. Entity refs e deep links

Apps com entidades relevantes devem mapear entidade lógica → route metadata.

Exemplo conceitual:

```json
{
  "entityType": "customer",
  "routeId": "customer-detail",
  "routeParams": ["customerId"]
}
```

Portal resolve/revalida a navegação.

## 7. UI capabilities

Permitido quando verdadeiramente visual:

```text
open entity
select tab/view
focus section
apply local filter
refresh view
```

Não usar UI capability para:

```text
create/update/approve/cancel
```

se houver API/use case de negócio.

## 8. Business Action risk/decision readiness

Writes precisam permitir ao policy owner derivar/definir:

```text
read/write
action risk/sensitivity
Decision Gate requirement
idempotency expectations
parallel/retry safety
audit requirement
```

Não hardcodar “todos POST confirmam” no planner.

## 9. Evidence/provenance readiness

APIs importantes para análise devem oferecer dados suficientes para:

- source identification;
- timestamp/freshness;
- entity relation;
- status/outcome;
- limitation/error classification.

Não é obrigatório embrulhar toda API em `EvidenceRef`; o adapter do Copilot pode normalizar usando metadata real.

## 10. Event-ready opcional

Quando o app possui eventos relevantes para Watch/workflow:

- owner claro;
- schema versionado;
- eventId/dedupe semantics;
- entity refs;
- occurredAt;
- payload bounded/ref;
- permission/security model.

Não criar polling no Copilot core se evento confiável já existe.

## 11. Iframe readiness

Classificação ortogonal:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

AI_READY exige Business Actions por API/OpenAPI; `postMessage` sozinho não basta.

## 12. Help/knowledge

O app deve fornecer linguagem suficiente para explicar:

- função;
- entidades;
- campos/indicadores;
- operações;
- procedimentos associados.

Knowledge visibility continua sujeita a ACL.

## 13. Readiness levels

```text
L1 DISCOVERABLE
L2 CONTEXT_READY
L3 READ_READY
L4 WRITE_READY
L5 WORKFLOW_READY
```

### L1
rotas/permission/descrição discoverable.

### L2
Workspace Context + EntityRef/deep link quando material.

### L3
OpenAPI read + RBAC + outcome/evidence normalization.

### L4
write + policy/Decision Gate + idempotency/audit.

### L5
capabilities estáveis para Durable Workflow + events quando o fluxo precisar.

## 14. Matriz mínima de readiness

| Item | Status |
|---|---|
| app/routes autorizados deriváveis | |
| EntityRef/deep link | |
| Workspace Context | |
| Business APIs | |
| OpenAPI quality | |
| permissions/RBAC | |
| read outcome/evidence | |
| write sensitivity/Decision Gate | |
| idempotency/retry semantics | |
| UI capabilities necessárias | |
| events quando necessários | |
| help/knowledge | |
| evals | |

## 15. Testes mínimos

Conforme nível:

- authorized/unauthorized app/route;
- Workspace Context;
- entity deep link;
- read action;
- write Decision Gate;
- idempotency negative;
- unknown/sibling onboarding sem core patch;
- event duplicate/security quando aplicável;
- iframe security quando aplicável.

## 16. Definition of Ready AI

```text
[ ] UI/Copilot convergem para mesmos use cases
[ ] shared foundations foram reutilizadas
[ ] OpenAPI é suficiente para discovery/binding
[ ] nenhuma regra endpoint-specific foi adicionada ao core
[ ] permissions vêm dos owners canônicos
[ ] Entity/Context/navigation são tipados
[ ] writes possuem policy/Decision Gate semantics
[ ] evidence/outcome é rastreável quando material
[ ] smoke/evals do nível passam
```

AI-readiness é propriedade do ecossistema, não integração artesanal por app.