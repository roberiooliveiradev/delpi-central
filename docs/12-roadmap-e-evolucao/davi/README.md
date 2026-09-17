# DAVI — Product / Architecture Baseline

> **Status:** baseline arquitetural/documental aprovado por Architecture / Coordination  
> **Escopo:** produto, princípios, modelo de capability/source, CURRENT PROVEN vs TARGET, boundaries de autoridade  
> **Não prova runtime.** Evidência de execução permanece nos docs de integração API DELPI + OpenAI/MCP e no provider/runtime.

```text
Documentation ≠ runtime proof
CURRENT PROVEN ≠ TARGET
```

---

## 1. Mission

Nome user-facing:

```text
DAVI — Especialista em Dados e Informações DELPI
```

Missão congelada:

```text
DAVI = DELPI Data & Information Intelligence
```

Responsabilidade:

```text
semantic discovery
+ authorized retrieval
+ composition
+ explanation
of DELPI information
```

Em linguagem de produto: localizar, consultar, compor e explicar informações autorizadas da DELPI por capabilities semânticas governadas, preservando identidade do usuário, autoridade das fontes e proveniência.

A amplitude informacional do DAVI pode crescer. Sua responsabilidade permanece especializada em inteligência de dados e informações. DAVI **não** se torna source of truth, RBAC, permission engine, owner de domínio ou executor genérico.

Persona (masculina, profissional, cordial, objetiva) é UX e **não** altera AuthN, AuthZ, data access, capability availability ou authority.

---

## 2. DAVI × DÉLIA

```text
DAVI architecture principles ≈ DÉLIA architecture principles
DAVI responsibility/context << DÉLIA responsibility/context
```

Significa:

```text
reuse architectural principle
!= copy DÉLIA product scope
!= inherit DÉLIA runtime
!= inherit DÉLIA authority
!= create DÉLIA subsystems inside DAVI
```

DÉLIA pode ser referência metodológica/arquitetural quando explicitamente útil (capability model, Clean/Hexagonal, Abstraction Gate, evidence taxonomy, MCP-as-adapter). Não herdar escopo de produto, runtime, authorities ou subsystems DÉLIA.

Não editar documentação DÉLIA para acomodar DAVI. Conflito factual real → Architecture / Coordination.

Referências de princípio (read-only):

- [`../delia/03-capability-model.md`](../delia/03-capability-model.md)
- [`../delia/16-execution-master-plan.md`](../delia/16-execution-master-plan.md)
- [`../delia/27-single-copilot-specialization-architecture.md`](../delia/27-single-copilot-specialization-architecture.md)
- [`../delia/49-architecture-and-design-patterns-standard.md`](../delia/49-architecture-and-design-patterns-standard.md)
- [`../delia/50-standalone-copilot-application-architecture.md`](../delia/50-standalone-copilot-application-architecture.md)
- [`../delia/51-platform-integration-baseline.md`](../delia/51-platform-integration-baseline.md)
- [`../delia/60-agent-interoperability-mcp-a2a-and-tool-protocols.md`](../delia/60-agent-interoperability-mcp-a2a-and-tool-protocols.md)

---

## 3. Architecture baseline

```text
Clean Architecture
+ Ports & Adapters / Hexagonal
+ Pragmatic DDD
+ semantic capabilities
+ owner/source-of-truth first
+ contract-first
+ backend-first AuthZ
+ provider/executor independence
+ evidence/provenance
+ minimum sufficient context
+ smallest correct pattern
+ Abstraction Gate
```

### Dependency rule

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure
```

Composition Root wires concretes. Domain/Application não conhecem framework HTTP, DB driver, MCP SDK, OpenAI SDK, Keycloak SDK, provider SDK ou internals de outro bounded context.

### Bounded-context rule

Integração por contrato estável apropriado. Proibido por default:

```text
DAVI context → importar domain/use case de outro context
DAVI context → acessar banco/TOTVS de outro owner diretamente
DAVI context → reconstruir AuthZ de negócio
DAVI context → duplicar source of truth
```

### Authority model

```text
Keycloak = identity / SSO
Core/plataforma = platform RBAC/governance where applicable
Domain/API owner = data + business rules + final business AuthZ
DAVI = intelligence / orchestration / presentation
MCP / OpenAI / provider = interface / protocol / transport — not authority
GitHub = persistent code / contracts / docs / SHAs
```

DAVI nunca amplia a autoridade do usuário.

Não autorizam por si só: JWT isolado, OAuth scope, tool securitySchemes, tool annotation, Agent instructions/persona/memory, uploaded file, workspace sharing, frontend state, provider metadata.

---

## 4. Capability model

```text
Capability
!= endpoint
!= operationId
!= HTTP route
!= MCP tool
!= provider
!= permission
!= database table
```

Objetivo:

```text
semantic capability
→ technical resolution
```

sem reescrever a semântica quando endpoint, provider ou mecanismo técnico mudar.

IDs ilustrativos (`product.search`, `inventory.read`, …) **não** são congelados neste baseline sem owner, grain e consumers comprovados. Este documento **não** inventa capability registry nem capability IDs.

Um contrato técnico pode apoiar mais de uma capability; uma capability pode compor mais de um contrato autoritativo.

Tool MCP / rota HTTP / adapter expõe uma **projection** pequena e model-constructible da capability aprovada; não define a capability.

Classificação antes de implementar:

```text
READ = consulta sem side effect
PREPARE = preview/draft/simulação sem persistir
ACT = cria/altera/remove/envia/aprova/finaliza
```

---

## 5. Information-source model

```text
business need
→ source owner
→ authoritative contract
→ classification + freshness + AuthZ
→ semantic capability
→ bounded adapter/integration
→ provenance/evidence
```

Cada fonte mantém owner, authority, AuthZ, contract, freshness e classificação. DAVI não se torna source of truth ao consultar ou compor.

### API DELPI — Wave 1 role

```text
API DELPI
= FIRST MAJOR INFORMATION SOURCE / DOMAIN CONTRACT FAMILY

API DELPI
!= DAVI architecture
```

A resolução futura **não** hardcoda `api-delpi` como única fonte possível após o MCP.

Existência futura de backend/runtime DAVI próprio permanece **`TO_INVENTORY`**. Não criar serviço novo sem boundary real, owner, consumers, contrato, benefício e Abstraction Gate.

---

## 6. CURRENT PROVEN V1

Para a superfície Workspace Agent / Plugin / MCP:

```text
search_products (specialized Product Master fast path)
discover_delpi_information + execute_delpi_information
  (governed dynamic READ over DAVI_ELIGIBLE_READ technical actions)
```

Technical Action Catalog is **derived** from OpenAPI/baseline + `davi_external_read_allowlist.json`. It is **not** the semantic capability authority.

Inventory evidence (generated, not runtime authority):

```text
api-delpi/docs/integrations/evidence/davi-api-delpi-operation-inventory.json
api-delpi/docs/integrations/evidence/davi-api-delpi-operation-inventory.md
api-delpi/docs/integrations/evidence/davi-governed-read-coverage-005.json
```

`DAVI-DYNAMIC-READ-005` historically decided **`PROMOTE_ZERO_NEW_OPERATIONS`** under the old gate model. That coverage freeze is **superseded for eligibility logic** by **`DAVI-READ-AUTHZ-REBASELINE-001`**.

Canonical AuthZ policy:

```text
api-delpi/docs/integrations/evidence/davi-read-authz-policy-rebaseline-001.md
```

```text
DAVI capability <= authenticated user capability
DAVI_LOCAL_RBAC / DAVI_BRANCH_AUTHZ = FORBIDDEN
branch = query filter (unless backend policy says otherwise)
backend AuthZ = final authority
```

After Wave 2 (source): `DAVI_ELIGIBLE_READ` = 13 via allowlist v7 governed READ promotion (`product.commercial.pricing`, `product.purchase.price_history`, `product.purchase.last_valid` plus the previous ten). Nested Abstraction Gate remains PASS. MCP tools remain **exactly 3**. Agent Instructions unchanged. `product.cost.impact_simulation` remains PREPARE / `DEFER_FROM_READ_WAVE` and is not executable through the READ broker.

Wave 1 (historical source): `DAVI_ELIGIBLE_READ` = 10 via allowlist v6 (`product.factory.status`, `product.structure.exclusivity`, `product.shipping.status` plus the previous seven).

Historical governance packs (`DAVI-GOV-READ-001`) remain as provenance with `SUPERSEDED_IN_PART`.

Stock (`get_product_stock`) is **eligible** when allowlisted — `branch` is a query filter, not a DAVI AuthZ boundary.

Pendências de rollout amplo permanecem pendentes (second-user identity, negative business AuthZ, MCP rate policy, wider publication).

No runtime V1, MCP e `application/external_capabilities` estão fisicamente no bounded context `api-delpi`. Isso prova que **não** há um bounded context DAVI separado importando internals da API DELPI.

### Known EXECUTION_DRIFT (resolved)

```text
app.application.external_capabilities.product_search_service
→ imports app.composition.product_composer
```

```text
DAVI_V1_EXTERNAL_CAPABILITY_LAYERING = RESOLVED
```

Remediation (`DAVI-ARCH-RUNTIME-001`): `search_products` accepts injected `SearchProductsUseCase`; Interface/Composition call `build_search_products_use_case()` and pass it in. No new DAVI backend/context. See integration evidence in `api-delpi/docs/integrations/openai-plugin-mcp.md`.

---

## 7. TARGET architecture (product)

```text
semantic DAVI capability
→ approved technical resolution / integration boundary
→ authoritative owner contract
→ owner-side AuthZ and business rules
→ authoritative source
```

```text
CURRENT PROVEN V1 — API DELPI integration
!= universal DAVI TARGET architecture
```

---

## 8. MCP role

```text
MCP = interface / protocol / adapter
MCP != domain / business / AuthZ authority
```

MCP não é source of truth, segundo RBAC, catálogo de domínio semântico, nem bypass de use case / banco.

---

## 9. Context budget

```text
authorized candidates
→ semantic/schema retrieval
→ small bounded configurable top-K
→ planner/reasoning
```

Não enviar OpenAPI inteiro, catálogo técnico inteiro, todas as tools, histórico ilimitado ou payloads completos sem necessidade. Valores numéricos de budget exigem evidence/eval.

---

## 10. Capability / source gate

Nenhuma capability começa por “expor endpoint”, “adicionar tool” ou “mapear tabela”.

```text
PROBLEM / USER NEED
→ RESPONSIBILITY
→ BUSINESS / DOMAIN OWNER
→ AUTHORITATIVE SOURCE + CONTRACT
→ CONSUMERS
→ READ | PREPARE | ACT
→ SEMANTIC CAPABILITY
→ INPUT MINIMIZATION
→ OUTPUT ALLOWLIST
→ IDENTITY MODEL
→ BACKEND AUTHZ
→ PRIVACY / CLASSIFICATION
→ FRESHNESS / PROVENANCE
→ LIMITS
→ BOUNDARY / ADAPTER
→ SIMPLEST CANONICAL PATTERN
→ ABSTRACTION GATE
→ IMPLEMENTATION OWNER
→ OBSERVABILITY
→ TESTS
→ DEPLOY
→ PROVIDER DISCOVERY WHEN APPLICABLE
→ POSITIVE LIVE TEST
→ NEGATIVE AUTHZ TEST
→ AGENT UX / INSTRUCTIONS
→ DOCS / ACCEPTANCE
```

Nova information source exige gate explícito de owner / source / contract / AuthZ / classification / provenance.

---

## 11. Generic-access prohibition

Forbidden by default:

```text
generic SQL
generic HTTP
arbitrary endpoint/method
arbitrary field selector
generic CRUD
expose-all
mechanical one-tool-per-route mapping
query_delpi_generic / execute_sql / call_api
```

---

## 12. CURRENT PROVEN vs TARGET taxonomy

| Estado | Significado |
|---|---|
| `PROVEN` / `CURRENT PROVEN` | evidência direta no HEAD/runtime/provider, escopo explícito |
| `TO_INVENTORY` | owner/contrato/comportamento ainda não ratificado |
| `PLANNED` | decisão ordenada, runtime ainda não entregue |
| `TARGET` | arquitetura/capability desejada — não implica implementação |
| `EXECUTION_DRIFT` | premissa/alvo invalidado por evidência; não normalizar silenciosamente |
| `LEGACY_TRANSITIONAL` | bridge legada (ex.: GPT Actions); não expandir por default |

Nunca usar “provavelmente”, “deve funcionar”, “o Agent disse” ou “teste passou ⇒ produção” como evidência.

---

## 13. Abstraction Gate

Antes de nova abstração / camada / serviço:

```text
boundary real?
owner real?
consumer real?
equivalente existente?
variation/lifecycle real?
reduz coupling?
algo simples basta?
credentials continuam bounded?
read/write preservados?
PREPARE/ACT preservados?
rollback/revoke existe quando aplicável?
```

“Pode ser útil depois” não justifica abstração. Este baseline **não** decide nem inventa um DAVI backend target.

---

## 14. Anti-pattern ledger

| Anti-pattern | Classificação |
|---|---|
| endpoint / operationId / route = capability | forbidden |
| MCP tool = business capability authority | forbidden |
| MCP = business / AuthZ authority | forbidden |
| OAuth scope = business permission | forbidden |
| DAVI direct SQL / TOTVS bypass | forbidden |
| generic query / generic API tool | forbidden |
| expose-all / one tool per route | forbidden |
| DAVI imports sibling domain/application | forbidden by default |
| OpenAPI duplicado como catálogo semântico DAVI | forbidden |
| RBAC duplicado no Agent/MCP | forbidden |
| GPT Actions `operationId` catalog como autoridade semântica DAVI | `LEGACY_TRANSITIONAL` — não é authority |
| Application → Composition Root (V1 product_search_service) | `RESOLVED` (`DAVI-ARCH-RUNTIME-001`) — do not reintroduce |
| Contrariar princípios DÉLIA reutilizados sem ADR | escalate Architecture |

`api-delpi/app/application/external_capabilities/catalog_service.py` descreve capabilities por `operationId` GPT Actions com `status: LEGACY_TRANSITIONAL`. Isso **não** é o catálogo semântico DAVI.

---

## 15. Document authority map

| Documento | Ownership |
|---|---|
| Este arquivo (`docs/12-roadmap-e-evolucao/davi/README.md`) | baseline de produto/arquitetura DAVI no GitHub |
| `DAVI — Diretrizes Gerais, Chats e Handoffs` (Project ChatGPT) | coordenação GPT ↔ Cursor ↔ GitHub; pode viver fora do repo |
| [`../../../api-delpi/docs/integrations/openai-plugin-mcp.md`](../../../api-delpi/docs/integrations/openai-plugin-mcp.md) | CURRENT API DELPI + OpenAI/MCP contract/evidence |
| [`../../../api-delpi/docs/integrations/openai-workspace-agent-davi.md`](../../../api-delpi/docs/integrations/openai-workspace-agent-davi.md) | CURRENT Workspace Agent / Agent Studio; **Agent Instructions = stable behavior only**; capability inventory = governed dynamic discovery (not enumerated in the prompt) |
| [`../../../api-delpi/docs/integrations/keycloak-mcp-client-runbook.md`](../../../api-delpi/docs/integrations/keycloak-mcp-client-runbook.md) | Keycloak client / OAuth runbook |
| [`../../../api-delpi/docs/integrations/keycloak-mcp-oauth-evidence.md`](../../../api-delpi/docs/integrations/keycloak-mcp-oauth-evidence.md) | OAuth/MCP evidence ledger |
| `.cursor/rules/*` materiais | authorities transversais da plataforma (não duplicar aqui) |
| Docs DÉLIA listados acima | princípios arquiteturais de referência — não escopo DAVI |

Precedência:

```text
.cursor transversal > especialização DAVI em conflito de responsabilidade
owner/domain contract > DAVI summary para verdade de negócio
runtime/provider evidence > documentação para prova de execução
CURRENT PROVEN != TARGET
```

---

## 16. TO_INVENTORY residuals

```text
DAVI dedicated backend/runtime existence
DAVI semantic capability registry (if ever needed)
capability IDs beyond V1 search_products evidence
additional information sources beyond API DELPI Wave 1
DAVI stock / pricing / BOM / production capabilities (separate inventories)
DAVI_STOCK_BUSINESS_AUTHZ and related AuthZ contracts
formal data classification for candidate fields
MCP_RATE_POLICY owner decision
second-user identity + negative business AuthZ for wider publication
other Application → query_cache_composer imports (separate inventory; out of DAVI-ARCH-RUNTIME-001 scope)
```

---

## 17. References

- Platform: `.cursor/rules/openai-plugin-mcp-integration.mdc`, `.cursor/rules/openai-workspace-agent-integration.mdc`, architecture/security/API/quality rules
- V1 integration evidence: `api-delpi/docs/integrations/*`
- DÉLIA principle baseline (reuse principles only): `docs/12-roadmap-e-evolucao/delia/*` paths listed in §2

North Star:

```text
understand broadly
→ discover semantically
→ retrieve only what is authorized/needed
→ expose narrowly
→ authorize canonically
→ preserve provenance
→ verify externally
→ expand one governed capability/source at a time
```
