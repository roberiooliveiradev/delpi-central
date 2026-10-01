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

### 4.1 DÉLIA user-delegated credential model (C3-MCP-INTEROP-01R1A)

Direção aprovada (ledger §6.93): DÉLIA autentica como **um** client confidencial (`delia-api`) e executa Keycloak token exchange sobre o bearer do usuário do Portal (request-scoped), recebendo access token curto com exatamente **um** resource audience MCP (`…/apps/<api>/mcp`), `mcp:tools` no `scope`, `aud` mantendo `delpi-central` (contrato `delpi_auth`), e `sub` preservado. O subject bearer nunca entra em `PlatformAccessContext`, model, MFE, logs ou persistência; cache process-local limitado (≤120s reuse, ≤300s hard cap, invalidação em falha de autenticação). Proibidos: token global estático por especialista, client DÉLIA por especialista, `aud` MCP no token do Portal, service account como substituto do usuário humano. Business READ continua `C4`-gated.

Implementado (§6.94, `IMPLEMENTATION_HEAD=a5512c0b5d18f728f15cf0c652ffb0e8417e8e9d`): `KeycloakDelegatedCredentialProvider` + `InMemoryDelegatedTokenCache` em Infrastructure; subject bearer request-scoped via `flask.g`; perfis carregam `exchange_audience` (`mcp-*` client) + `resource_audience` (URL canônica); validação fail-closed de `sub`/aud/scope/exp/service-principal; `GLOBAL_USER_TOKEN_PATH=REMOVED`. Dev realm: bootstrap materializa `mcp:tools`, `mcp-audience-*`, `mcp-*` clients, requester `delia-api`, audience mapper `delia-api` no `delpi-central` e permissões `token-exchange` por alvo — idempotente. Evidence live: 3/3 exchanges com subject preservado e isolamento de resource aud. `tools/list` autenticado executado em R1B (§6.96, `IMPLEMENTATION_HEAD=cc65cc6388371224d955f266257d6aa3ca4967ce`): initialize+tools/list PASS para DAVI/TÉO/VISTA com bearer delegado same-subject resource-bound (`azp=delia-api` validado, invalidação em falha de auth em qualquer wire op). Notas de runtime: token de sujeito deve ser OIDC (scope=openid); exchange e MCP podem exigir Host público quando endereçamento interno (DELIA_EXCHANGE_HOST_HEADER / DELIA_MCP_*_HOST_HEADER); transporte negocia a revisão clássica 2024-11-05 (o caminho 2026-07-28 usa envelope `_meta` por request, sem método `initialize`). R1C (§6.98, `EVALUATED_SHA=78c87e12b079817de623adc7d4108ad3329a5364`): aceitação de segurança PASS — token Portal OIDC real elegível (aud `delia-api`, zero aud de recurso MCP); troca least-privilege com negativos vivos (alvo desconhecido 400, cliente não-MCP 403, cliente não-relacionado 403, secret errada 401); permissões convergidas para a policy canônica `delia-exchange-requester` (protótipo R1A removido idempotentemente); Host override apenas por configuração; piso de protocolo do servidor SUPPORTED ×3 (mcp 2.2.0 ≥ 2026-07-28) com cliente negociando 2024-11-05 legitimamente; matrizes adversariais de identidade/cache/discovery + gates de fase fail-closed; redaction verificado; determinismo de testes resolvido (conftest neutraliza env ambiente); eval live final 3/3 PASS. `C3-MCP-INTEROP-01R1C=CANDIDATE_FOR_ARCHITECTURE_REVIEW`; `C4_AUTHORIZED=NO`.

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
