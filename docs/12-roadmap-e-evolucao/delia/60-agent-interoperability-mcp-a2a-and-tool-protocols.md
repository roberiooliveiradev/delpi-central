# Minha DELPI Copilot — Interoperabilidade de Agentes, MCP, A2A e Tool Protocols

**Status:** thematic architecture/security spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Architecture/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)

## 1. Decisão

O Minha DELPI Copilot continua sendo o **único produto/entry point de inteligência da DELPI**, mas deve poder interoperar com tools e agentes externos por protocolos abertos quando isso reduzir acoplamento e ampliar capabilities.

Target conceitual:

```text
Minha DELPI Copilot
├─ OpenAPI / Domain APIs
├─ semantic connectors
├─ MCP-compatible tool/resource adapters
└─ A2A-compatible external agent adapters
```

Interoperabilidade não reintroduz agentes departamentais internos nem cria permission authority externa.

## 2. MCP role

MCP é tratado como boundary de tools/resources, não como business authority.

```text
Copilot semantic capability
→ MCP Tool Adapter
→ approved MCP server
→ tool/resource result
→ normalize SourceRef/EvidenceRef/OutcomeRef
```

MCP server metadata/tool description é untrusted integration data e não pode redefinir system policy, RBAC ou Decision Gate.

## 3. A2A role

A2A ou protocolo equivalente pode ser usado para delegar tarefa a agente externo aprovado:

```text
Copilot goal/subtask
→ policy + agent capability check
→ A2A adapter
→ external agent
→ task status/result/artifact
→ Evidence/Outcome
→ Copilot continues orchestration
```

External agent is a provider/executor, not a superior authority.

## 4. Identity and authorization

Separate:

```text
Copilot user/service identity
external agent identity
MCP server/service identity
provider scopes
Core RBAC
domain authorization
```

Nunca propagar credential mais ampla do que a capability exige. Delegation token/credential, quando necessário, deve ser scoped, time-bounded e protected.

## 5. Capability allowlist

Cada server/agent aprovado precisa de projection explícita:

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
owner
```

Discovery não equivale a aprovação automática.

## 6. Tool poisoning / prompt injection

Treat as untrusted:

- tool descriptions;
- resource contents;
- agent messages;
- artifacts;
- errors/status text.

Rules:

- external instructions do not override system/policy;
- never send unrelated sensitive context;
- tool arguments schema-validated;
- write tool remains governed;
- result normalized before use;
- provenance preserved.

## 7. No protocol monoculture

MCP/A2A não substituem:

```text
OpenAPI for business APIs
semantic connector contracts
Domain API authorization
Durable Workflow
EventEnvelope
Decision Gate
```

Use protocol only where it solves real interoperability.

## 8. Server/agent lifecycle

Target states:

```text
DISCOVERED
→ REVIEWED
→ APPROVED
→ ACTIVE
→ DEGRADED | DISABLED | REVOKED | DEPRECATED
```

Version/capability change may require re-review.

## 9. Agent delegation semantics

Delegated task must specify bounded intent:

```text
taskRef
goal
input refs bounded
allowed capability scope
expected artifact/result schema
deadline/budget
correlationContext
```

Do not send hidden chain-of-thought or unrestricted conversation history.

## 10. Failure and cancellation

A2A/MCP adapters define:

- timeout;
- cancellation;
- retry eligibility;
- duplicate request semantics;
- partial/ambiguous result;
- agent unavailable/degraded;
- capability changed/revoked.

Material writes require Outcome verification where applicable.

## 11. C0 inventory

Inventariar:

- existing MCP servers/clients;
- existing agent frameworks/protocols;
- internal tool registries;
- delegation/service identity patterns;
- secret/token exchange mechanisms;
- approved external AI agents;
- network/egress constraints;
- ownership/review process;
- protocol versions/security posture.

Do not assume MCP/A2A infrastructure exists.

## 12. Phase mapping

```text
C0 → inventory, identity, trust, allowlist and protocol boundaries
C3 → generic tool/agent interoperability ports/adapters and RED security tests
C4 → read-only MCP/resources and external-agent research/analysis pilots
C5 → governed write-capable tools/agents under Decision/Outcome semantics
C6 → Control Tower registry/health, workflow delegation and artifact integration
C7 → selected autonomous delegation under capability-scoped L5 and budgets
```

## 13. Acceptance

- unknown MCP server cannot execute automatically;
- tool description cannot elevate policy;
- agent cannot receive unrelated data;
- read tool cannot become write implicitly;
- external agent failure remains truthful;
- agent result preserves provenance;
- A2A agent can be replaced without planner core rewrite;
- disabled server/agent becomes unavailable immediately;
- same Copilot remains user-facing orchestrator.

## 14. North Star

> **O Minha DELPI Copilot deve conversar com o ecossistema de ferramentas e agentes sem perder identidade, governança, rastreabilidade ou autoridade corporativa.**
