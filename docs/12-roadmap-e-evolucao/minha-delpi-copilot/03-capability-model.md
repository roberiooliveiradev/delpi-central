# 03 — Modelo de Capabilities

## 1. Conceito

Uma **Capability** representa algo que a plataforma consegue fazer para auxiliar ou em nome do usuário. É unidade semântica de discovery/planning; **não é sinônimo de endpoint, permission ou executor**.

## 2. Categorias

```text
business.read
business.write
business.destructive
platform.navigation
platform.view
knowledge
analysis
artifact
multimodal
workflow
```

Exemplos:

- consultar estoque → `business.read`;
- criar solicitação → `business.write`;
- cancelar processo → `business.destructive`;
- abrir app → `platform.navigation`;
- aplicar filtro local → `platform.view`;
- buscar procedimento → `knowledge`;
- comparar períodos → `analysis`;
- gerar relatório → `artifact`;
- analisar desenho → `multimodal`;
- conduzir investigação composta → `workflow`.

## 3. Capability Projection

O Copilot usa uma **projeção/visão semântica autorizada**, não um novo catálogo técnico.

Exemplo conceitual:

```json
{
  "capabilityId": "business-action-ref-or-stable-projection-id",
  "kind": "business.write",
  "label": "Criar solicitação de compra",
  "description": "Cria uma solicitação de compra autorizada.",
  "source": {
    "type": "action_catalog",
    "refId": "canonical-action-id"
  },
  "availability": "allowed",
  "risk": "write",
  "provenance": {}
}
```

O executor resolve o `source.refId` de volta à authority canônica para method/path/schema/policy.

Não copiar o OpenAPI inteiro para a projection.

## 4. Fontes de capabilities

```text
OpenAPI/Action Catalog
        +
Core/Portal authorized routes
        +
Knowledge/Internal Tools
        +
Analysis/Artifact/Multimodal capabilities
        ↓
Authorized Capability View
```

Cada fonte mantém sua authority.

## 5. Autorização

```text
identity
→ Core/domain RBAC + action policy
→ allowed source set
→ Capability Projection
→ semantic retrieval
```

Filtrar por:

- usuário/subject;
- permission/policy;
- feature availability;
- context requirement;
- environment;
- capability health.

**Não filtrar por agent ativo como authority final.** Expertise pode influenciar ranking, não availability.

## 6. Discovery

```text
goal + entities + context
→ authorized capability pool
→ semantic/schema retrieval
→ top-K
→ structured planner restrito aos candidates
```

Planner não inventa capability/action fora dos candidates autorizados.

## 7. Business capability

Para Business Actions:

```text
technical contract = OpenAPI + Action Catalog
availability = RBAC/policy
semantic projection = Capability Projection
execution = generic canonical executor
```

A projection pode conter semântica/risk para retrieval/UX, mas path/method/parameters/schema técnicos continuam na authority.

## 8. Platform capability

Derivada de:

```text
Core /me/apps/routes
+ generic Portal action definitions
```

Target usa app/route/entity IDs; Portal resolve/revalida.

Não manter lista `app → URL` no AI core.

## 9. Knowledge/Multimodal/Internal capabilities

Capabilities internas precisam owner/contract/policy claro.

Exemplo:

```text
document.inspect
drawing.inspect
knowledge.search
artifact.generate
```

Multimodal perception produz Evidence; não conclusão de negócio automaticamente.

## 10. Workflow capability

Uma capability composta representa objetivo/método de alto nível sem congelar endpoints.

Exemplo:

```text
investigate_nonconformity
```

Pode usar Playbook + allowed capabilities para construir `WorkflowPlan`.

Workflow capability não cria executor próprio.

## 11. Risk e Decision Gate

Evitar `requiresConfirmation` como booleano permanente dentro da projection.

O modelo alvo é:

```text
capability/action metadata
+ context/impact/arguments/evidence
+ deterministic policy
→ Decision Gate level
```

Níveis canônicos são definidos no foundation C0.

## 12. Idempotency/parallel safety

Metadata pode indicar expectations/hints, mas a garantia final pertence ao contrato/use case/domain owner.

Não assumir:

```text
GET = sempre safe em qualquer contexto
POST = sempre non-idempotent
```

Usar contratos/policy reais.

## 13. Availability state

Estados conceituais úteis:

```text
AVAILABLE
UNAUTHORIZED
UNAVAILABLE_PROVIDER
REQUIRES_CONTEXT
POLICY_BLOCKED
DEGRADED
```

Decision Gate pendente é estado de execução/decisão, não necessariamente availability da capability.

## 14. Relação com Expertise

```text
Expertise
→ melhora ranking/contexto
→ sugere capabilities/playbooks

Capability availability
→ continua RBAC/policy/source authority
```

Nenhum pack concede permission.

## 15. Relação com Entity/Evidence

Capabilities podem consumir/produzir refs compartilhadas:

```text
EntityRef
SourceRef
EvidenceRef
OutcomeRef
```

Evitar DTOs semânticos incompatíveis por capability.

## 16. Observabilidade

Registrar quando material:

- candidate set/count;
- selected capability/sourceRef;
- retrieval score/reasonCode estruturado;
- policy outcome;
- Decision Gate;
- executor/outcome;
- duration/error;
- no CoT.

## 17. Anti-padrões

Não criar:

- capability por path hardcoded;
- manual operationId catalog;
- capability granting access;
- `isAdmin=true` como universal policy;
- write classificado como read para facilitar planner;
- agent-specific action catalog como authority;
- copied request/response schema em JSON paralelo;
- workflow capability com endpoints congelados;
- `requiresConfirmation` boolean como substituto do Decision Gate completo.

## 18. Foundation rule

`CapabilityProjection` é um primitive definido/reutilizado em C0. Features posteriores devem estendê-lo por versionamento explícito, não criar projection própria por app/domain.