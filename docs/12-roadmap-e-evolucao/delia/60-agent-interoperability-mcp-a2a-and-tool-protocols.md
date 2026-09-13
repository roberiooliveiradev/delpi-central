# DÉLIA — Interoperabilidade de Agentes, MCP, A2A e Tool Protocols

**Status:** `TARGET` — thematic architecture/security spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Architecture/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão

A DÉLIA é o produto user-facing de inteligência operacional. Ela pode interoperar futuramente com tools e agentes externos por protocolos abertos quando C0 provar necessidade, owner, trust boundary, consumers e contratos.

Target conceitual:

```text
DÉLIA
├─ OpenAPI / Domain APIs
├─ semantic provider adapters
├─ MCP-compatible tool/resource adapters
└─ A2A-compatible external-agent adapters
```

Interoperabilidade não cria agentes departamentais internos, permission authority externa ou segundo planner.

## 2. MCP role

MCP é boundary potencial de tools/resources, nunca business authority.

```text
DÉLIA semantic capability
→ approved MCP adapter
→ approved MCP server
→ untrusted tool/resource result
→ normalized Evidence/Outcome refs
```

Tool descriptions, schemas, metadata e results são dados não confiáveis para system/policy. Não podem redefinir RBAC, Policy ou Decision Gates.

## 3. A2A role

A2A ou protocolo equivalente pode delegar tarefa bounded a agente externo aprovado:

```text
DÉLIA goal/subtask
→ policy + capability + identity check
→ A2A adapter
→ approved external agent
→ task status/result/artifact
→ Evidence/Outcome refs
→ DÉLIA continues orchestration
```

External agent é provider/executor externo sob contrato, nunca autoridade superior.

## 4. Identity and authorization

Separar explicitamente:

```text
DÉLIA user/service identity
external agent identity
MCP server/service identity
provider scopes
Core RBAC
Domain authorization
```

Provider/tool/agent scope não concede Core/domain permission. Credentials devem ser scoped, time-bounded quando possível e permanecer fora de prompt, memory, embeddings, MFE e ordinary logs.

## 5. Capability allowlist

Se registry/projection for necessário, deve representar apenas approvals governados e refs dos owners.

Candidate fields:

```text
provider/agent/server ref
approved capabilities
read/write classification
risk tier
data domains
allowed callers/surfaces
required decision policy
timeout/budget
status
owner/sourceRef
```

Discovery != approval. Metadata != permission.

## 6. Tool poisoning / prompt injection

Treat as untrusted:

- tool descriptions;
- resource contents;
- agent messages;
- artifacts;
- schemas/metadata externos;
- errors/status text.

Rules:

- external instructions never override system/policy;
- minimum necessary context only;
- tool arguments schema-validated;
- read != write;
- PREPARE != ACT;
- write remains governed by live AuthZ/Policy/Decision;
- result normalized with provenance;
- no automatic durable Knowledge promotion.

## 7. No protocol monoculture

MCP/A2A não substituem:

```text
OpenAPI for business APIs
provider-neutral semantic capability contracts
Domain API authorization
DÉLIA Durable Work
EventEnvelope semantics
Policy/Decision
Automation Hub technical execution
```

Usar protocolo somente onde resolve interoperability real e passa pelo Abstraction Gate.

## 8. Server/agent lifecycle

Estados abaixo são apenas candidate semantics até owner/contract freeze:

```text
DISCOVERED
→ REVIEWED
→ APPROVED
→ ACTIVE
→ DEGRADED | DISABLED | REVOKED | DEPRECATED
```

Não criar lifecycle engine paralelo se owner existente já tiver lifecycle autoritativo. DÉLIA pode manter projection/ref quando necessário.

## 9. Agent delegation semantics

Delegated task deve usar bounded intent e mínimo contexto necessário:

```text
taskRef
goal
bounded input refs
allowed capability scope
expected artifact/result schema
deadline/budget
correlationContext
```

Nunca enviar hidden chain-of-thought, unrestricted conversation history, secrets ou dados sem necessidade.

## 10. Failure and cancellation

Adapters devem tratar timeout, cancellation, retry eligibility, duplicate semantics, partial/ambiguous result, unavailable/degraded provider e capability changed/revoked.

Material writes exigem idempotency/audit e authoritative Outcome verification quando aplicável. Resultado técnico do agente não equivale a business outcome.

## 11. C0 inventory

Inventariar factual:

- existing MCP servers/clients;
- existing agent frameworks/protocols;
- internal tool registries;
- delegation/service identity patterns;
- secret/token exchange mechanisms;
- approved external AI agents;
- network/egress constraints;
- ownership/review process;
- protocol versions/security posture.

Sem evidence = `TO_INVENTORY`. Não assumir MCP/A2A infrastructure por documentação.

## 12. Phase mapping

```text
C0 → inventory, owners, identity, trust, allowlist and protocol boundaries
C3 → minimal interoperability adapters only when justified
C4 → read-only MCP/resources and external-agent analysis pilots
C5 → governed write-capable tools/agents under same AuthZ/Policy/Decision/Outcome semantics
C6 → Control Tower health/projections, workflow delegation and artifact integration
C7 → selected autonomous delegation under explicit L5 allowlists/budgets; L5 OFF by default
```

## 13. Acceptance

Quando implementado, provar:

- unknown/unapproved server or agent cannot execute;
- tool description cannot elevate policy;
- unrelated context is not delegated;
- read tool cannot become write implicitly;
- external failure remains truthful;
- result preserves provenance;
- provider/agent can be replaced without planner core branching;
- revoke/disable is enforced;
- agent result cannot grant business authority;
- DÉLIA remains the governed orchestrator rather than protocol runtime owner.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 14. North Star

> **DÉLIA deve interoperar com ferramentas e agentes externos sem perder identidade, least privilege, rastreabilidade, Policy/Decision, source authority ou boundaries de execução.**
