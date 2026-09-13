# DÉLIA — Model Router e Compute Policy

**Status:** `TARGET` — thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Princípio

O usuário fala com uma DÉLIA. Model/provider selection é detalhe interno governado, mas **Model Router não é model registry, lifecycle authority, provider credential owner nem policy authority**.

```text
task requirements
+ approved model/deployment candidates
+ data/provider policy
→ Compute Policy
→ selected approved config
→ inference adapter
```

Nenhum model/provider é considerado disponível apenas por estar documentado.

## 2. Authorities

```text
Model/AI lifecycle owner → approval/version/eval/deploy/revoke truth
Provider/secret owner    → account/credential/technical availability
Core/domain policy       → permissions/data/business constraints
DÉLIA Compute Policy     → selection entre candidates já permitidos
```

Router nunca amplia permission, scope, data residency ou model approval.

## 3. Dimensões

Podem incluir modality, reasoning complexity, context size, structured-output requirement, data sensitivity, latency/cost budget, reliability, tool compatibility e health.

## 4. Classes conceituais

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

São candidates de compute class, não enum obrigatório nem mapping 1:1 para provider/model.

## 5. Compute Policy

C0 identifica owner/data-policy/provider/model inventory. C3 pode usar abstraction mínima se um consumer real exigir. Roteamento inteligente só é justificado quando métricas/evals provarem benefício sobre configuração simples.

Evitar criar `ComputePolicyV1`, registry ou engine prematuramente.

## 6. Fallback

```text
preferred unavailable
→ approved candidate compatible with policy/data/output requirements
→ fallback
→ explicit degraded state when material
```

Fallback nunca usa model/provider revogado, não aprovado ou incompatível.

## 7. Multimodal

Selecionar multimodal apenas quando necessidade real justificar. Não encaminhar indiscriminadamente dados/sources a provider mais amplo.

## 8. Internal stage specialization

Understanding/planning/synthesis/perception podem usar configs diferentes apenas quando contracts isolam stages, evals provam vantagem e policy permanece central. Isso não cria agentes/produtos separados.

## 9. Data/provider policy

Filtrar candidates por data classification, provider allowlist, privacy/residency/tenancy, retention contract, supported capability, deployment approval e health.

Provider scope não equivale a Core/domain permission.

## 10. Observability

Quando implementado, registrar model/deployment ref, compute class, structured route reason, latency, usage/cost, fallback e output validity sem CoT/secrets.

## 11. Admin boundary

A DÉLIA pode expor projection/configuration de routing quando aplicável. Model lifecycle/governance permanece com owner canônico definido em `66`/C0; não duplicar registry ou deployment truth dentro do Router.

## 12. Tests

- simple route;
- multimodal compatibility;
- unavailable provider;
- revoked/unapproved model rejected;
- incompatible fallback rejected;
- sensitive data provider blocked;
- latency/cost constraints;
- structured output validity;
- baseline vs candidate quality;
- Chat independence.

## 13. Implementation mapping

```text
C0 → model/provider/lifecycle/data-policy inventory
C3 → minimal provider-neutral inference abstraction only if required
C3–C6 → collect real metrics/evals
C7 → intelligent routing/optimization only if evidence justifies
```

## 14. Independence

Chat provider routing/config is reference-only and never fallback/runtime authority da DÉLIA.

## 15. Gate

Sem baseline de qualidade/latência/custo e sem approved model/deployment candidates reais, Router permanece `TARGET/PLANNED`; configuração simples é preferida a engine especulativo.
