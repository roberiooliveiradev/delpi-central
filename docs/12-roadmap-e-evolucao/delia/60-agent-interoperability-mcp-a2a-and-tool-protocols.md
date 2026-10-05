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

Implementado (§6.94, `IMPLEMENTATION_HEAD=a5512c0b5d18f728f15cf0c652ffb0e8417e8e9d`): `KeycloakDelegatedCredentialProvider` + `InMemoryDelegatedTokenCache` em Infrastructure; subject bearer request-scoped via `flask.g`; perfis carregam `exchange_audience` (`mcp-*` client) + `resource_audience` (URL canônica); validação fail-closed de `sub`/aud/scope/exp/service-principal; `GLOBAL_USER_TOKEN_PATH=REMOVED`. Dev realm: bootstrap materializa `mcp:tools`, `mcp-audience-*`, `mcp-*` clients, requester `delia-api`, audience mapper `delia-api` no `delpi-central` e permissões `token-exchange` por alvo — idempotente. Evidence live: 3/3 exchanges com subject preservado e isolamento de resource aud. `tools/list` autenticado executado em R1B (§6.96, `IMPLEMENTATION_HEAD=cc65cc6388371224d955f266257d6aa3ca4967ce`): initialize+tools/list PASS para DAVI/TÉO/VISTA com bearer delegado same-subject resource-bound (`azp=delia-api` validado, invalidação em falha de auth em qualquer wire op). Notas de runtime: token de sujeito deve ser OIDC (scope=openid); exchange e MCP podem exigir Host público quando endereçamento interno (DELIA_EXCHANGE_HOST_HEADER / DELIA_MCP_*_HOST_HEADER); transporte negocia a revisão clássica 2024-11-05 (o caminho 2026-07-28 usa envelope `_meta` por request, sem método `initialize`). R1C (§6.98, `EVALUATED_SHA=78c87e12b079817de623adc7d4108ad3329a5364`): aceitação de segurança PASS — token Portal OIDC real elegível (aud `delia-api`, zero aud de recurso MCP); troca least-privilege com negativos vivos (alvo desconhecido 400, cliente não-MCP 403, cliente não-relacionado 403, secret errada 401); permissões convergidas para a policy canônica `delia-exchange-requester` (protótipo R1A removido idempotentemente); Host override apenas por configuração; piso de protocolo do servidor SUPPORTED ×3 (mcp 2.2.0 ≥ 2026-07-28) com cliente negociando 2024-11-05 legitimamente; matrizes adversariais de identidade/cache/discovery + gates de fase fail-closed; redaction verificado; determinismo de testes resolvido (conftest neutraliza env ambiente); eval live final 3/3 PASS. `C3-MCP-INTEROP-01R1C=ACCEPT_WITH_RESIDUAL` (§6.99); `C3_MCP_FEDERATION=APPROVED_CURRENT_SCOPE`; `C4_AUTHORIZED=NO`. Gate de prontidão §6.100: `C4-MCP-GOVERNED-READS-01` autorizado como slice delimitado — um READ, um especialista, dev-only; seleção DAVI/TÉO/VISTA no brief do slice. C4-MCP-GOVERNED-READS-01 executado (§6.101, `IMPLEMENTATION_HEAD=58a2d018d1ef28081e82e18148caa192d9d0b735`): seleção travada em DAVI `execute_delpi_information` → `search_products` (Product Master/API DELPI) com discovery `discover_delpi_information`; gate READ task-scoped em `rules.py` (`GOVERNED_READ_ACTIONS`) exigido nos dois enforcement boundaries (application `SpecialistInterop.invoke` + infrastructure `McpSpecialistAdapter._require_invocable`), habilitado apenas por `DELIA_C4_DAVI_PRODUCT_READ_ENABLED` (default off); `governed_action_id` atravessa o port sem virar autoridade. Live dev read PASS: Portal subject → Core `/me` → exchange → DAVI discover → exatamente um candidato `search_products` → execute → 10 produtos reais, `GROUNDED`, provenance product-master/api-delpi + specialist davi + protocol MCP + action_id + observed_at + correlation_id, `result_truncated` preservado. Negativos: outros action_ids DAVI, TÉO READ, VISTA READ, PREPARE/ACT, token fornecido pelo chamador, argumento desconhecido/`customer_reference`, annotation forjada — todos bloqueados; DAVI indisponível → `NON_GROUNDED` + `delpi_source_unverified`; vazio autoritativo → GROUNDED vazio. `LIVE_NEGATIVE_DOMAIN_AUTHZ=TEST_NOT_RUN`. Estado: `C4_MCP_GOVERNED_READS_01=REWORK` (§6.102: SPECIALIST_NOT_CONFIGURED/DISABLED degradavam para fallback não divulgado) → R1 fechado (§6.103, `IMPLEMENTATION_HEAD=8ea1e4b53835478138452e9004654d99b511b65c`): falhas na via de discovery viram SOURCE_UNAVAILABLE com disclosure canônico `delpi_source_unverified`; NOT_APPLICABLE só pós-consulta; live read re-provado PASS; `ARCHITECTURE_REVIEW_C4_MCP_GOVERNED_READS_01R1=ACCEPT_WITH_RESIDUAL` (§6.104) — `C4_MCP_GOVERNED_READS_01=APPROVED_CURRENT_BOUNDED_VERTICAL_SLICE` (só DAVI/search_products); `NEXT=C4-MCP-GOVERNED-READS-02` autorizado (segundo READ governado `teo.analyze` bounded a {view,limit}; EXTEND via binding por capability, Abstraction Gate re-executado na tarefa). `C4-MCP-GOVERNED-READS-02` executado (§6.105; `IMPLEMENTATION_HEAD=0161c77d260907ca573735c5dbc066776c2c2234`): segundo READ governado — `teo.analyze` → `gpt_analyze` bounded a `view=summary`, superfície de argumentos `{view}` (demais args/views TÉO rejeitados pré-wire), gate por tupla exata nos dois enforcement boundaries sob `DELIA_C4_TEO_DASHBOARD_ANALYZE_ENABLED` (default off); camada semântica capability-neutral `governed_read.py` compartilhada por DAVI e TÉO (BoundDirectRead para invocação direta; fluxo discovery/candidate DAVI preservado) — sem clone GovernedTeoRead, sem engine/router/registry/proxy; live dev PASS: resumo de KPIs real do Transformômetro GROUNDED+OBSERVATION com provenance transformometro-api; regressão DAVI PASS; `ARCHITECTURE_REVIEW_C4_MCP_GOVERNED_READS_02=ACCEPT_WITH_RESIDUAL` (§6.106) — `APPROVED_CURRENT_BOUNDED_VERTICAL_SLICE`; prova de READ governado fechada com dois consumidores; terceiro READ NÃO autorizado. Inventário de writes MCP (§6.106): TÉO `prepare_*`→`commit_proposal` com proposal_handle HMAC+expiração+actor binding+fingerprint TOCTOU+revalidação AuthZ+verify pós-commit (PROVEN); VISTA `prepare_change`/`commit_proposal` parcialmente inventariado; DAVI sem superfície de escrita MCP. `C5_ENTRY_VERDICT=C5_FOUNDATION_SLICE_REQUIRED` — falta fundação DÉLIA (semântica de write, confirmation gate determinístico, audit); next `C5-GOVERNED-WRITE-FOUNDATION-01` sem ACT de negócio; `C5-GOVERNED-WRITE-FOUNDATION-01` executado (§6.108; `IMPLEMENTATION_HEAD=c258a839bac117316e1105e9aa15acf8c29892ce`): `domain/governed_write` entrega os contratos de write (binding gate vazio, preview de proposta, confirmação determinística, decision gate, outcome verificado pelo owner, audit record) — superfície MCP de write permanece bloqueada (PREPARE/ACT = WRITE_CAPABILITY_BLOCKED); `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`; `C5_AUTHORIZED=NO`; `PRODUCTION_READINESS=NOT_PROVEN`.; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO` em nível de fase; `PRODUCTION_READINESS=NOT_PROVEN`. Dev-env: `DELIA_MCP_*_HOST_HEADER=localhost:8000` exigido pelo FastMCP DNS-rebinding (deriva de `PUBLIC_BASE_URL=http://localhost`); header público anterior respondia 421 antes de auth — config local apenas.

## 5. Capability allowlist

**Catalog ownership (decisão §6.109 — ARCH-DRIFT-MCP-FEDERATION-CATALOG-OWNER-01):** cada specialist é owner do próprio catálogo/capabilities. `tools/list` é a fonte primária da superfície MCP observada em runtime; a classe semântica da operação é projetada a partir do contrato tipado do owner (`_meta["delpi/toolClass"]`: `DISCOVERY|READ|ANALYSIS|PREPARE|ACT` — `ANALYSIS` projeta como `READ` na DÉLIA). O mirror local completo de nomes de tools (`SPECIALIST_CAPABILITY_CLASSES`) é **SUPERSEDED**: a DÉLIA não precisa mais conhecer nomes remotos para descobrir/projetar a superfície.

O registry DÉLIA representa apenas approvals governados e refs dos owners:

```text
provider/agent/server ref (approved specialist id + owner ref)
governed invocation bindings (DISCOVERY bindings; READ tuples
    task-scoped com governed_action_id)
risk tier / phase limit
connection profile ref
status
```

Classe ausente/inválida/desconhecida no owner ⇒ `UNKNOWN` ⇒ *discoverable, never invocable*. Invocation re-lê a classe do owner via `tools/list` fresco — reclassificação/remoção do owner é honrada sem mirror stale.

**Decision supersession (§6.118 — ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02):** per-capability availability state lived in DÉLIA config/code (`DELIA_C4_*_ENABLED`, `GOVERNED_READ_ACTIONS`, `GOVERNED_DISCOVERY_BINDINGS`, `enabled_governed_read_tuples`) — a second local capability authority that made specialist-owned capabilities dependent on DÉLIA-local state. That model is **SUPERSEDED** (historical records preserved):

```text
SPECIALIST_CAPABILITY_CATALOG_OWNER = SPECIALIST
LIVE_CAPABILITY_SOURCE = authenticated tools/list (fresh, per call)
DELIA_LOCAL_FULL_TOOL_MIRROR = NONE
PER_CAPABILITY_ENV_ENABLE_FLAGS = SUPERSEDED
PER_TOOL_NAME_AVAILABILITY_ALLOWLIST = SUPERSEDED
CURRENT_INTERACTIVE_INVOCABLE_CLASSES = DISCOVERY | READ (ANALYSIS projects READ)
PREPARE = BLOCKED; ACT = BLOCKED; UNKNOWN = discoverable, never invocable
OWNER_REMOVAL / OWNER_RECLASSIFICATION = HONORED_LIVE
THIRD_MCP_GOVERNED_READ=NOT_AUTHORIZED -> SUPERSEDED_BY AUTHORITY-02
```

Capability existence/class is specialist-owned; DÉLIA retains orchestration policy only: approved+enabled specialist connections (`DELIA_MCP_*_ENABLED`), class/phase gates, human-subject delegated identity, and domain AuthZ downstream. `GOVERNED_READ_ACTIONS`, `GOVERNED_DISCOVERY_BINDINGS` and the `DELIA_C4_*_ENABLED` switches are superseded as active authority — they remain only as historical evidence of the bounded slices. Discovery != approval; class != permission; PREPARE/ACT stay policy-blocked regardless of advertisement.

Discovery != approval. Metadata != permission. Owner toolClass != permission.

**Current acceptance (§6.124):** `ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02=ACCEPT_CURRENT_READ_SCOPE` — the bounded MCP READ federation over DAVI|TÉO|VISTA (DISCOVERY/READ/ANALYSIS-as-READ) is accepted for the proven scope; production READ slice proven on DÉLIA SHA `ff27cfaf47`; grounded output passes deterministic redaction + business projection before OBSERVATION rendering.

**Binding extension (§6.126 — ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03, Product Master decision):** DÉLIA is the orchestrator of approved MCP specialists — it discovers, selects, governs, invokes, observes, verifies outcome evidence and presents; it never owns, mirrors, lists, pairs or flags MCP capabilities (`DELIA_LOCAL_MCP_CAPABILITY_CATALOG=FORBIDDEN`). For the approved MCP federation scope `MCP_PREPARE`/`MCP_ACT` are `GOVERNED_INVOKABLE` under generic write governance — capability existence is never permission: live Core AuthZ, specialist/domain authority, schema validation, confirmation when the owner contract requires it, idempotency and owner-authoritative postcondition all apply; `UNKNOWN` remains discoverable, never invocable. `PREPARE=BLOCKED`/`ACT=BLOCKED` still hold for every non-MCP write family. Static local write bindings (`GOVERNED_WRITE_BINDINGS`, `write_binding_for`, `GovernedWriteBinding` capability-name/enabled fields) are SUPERSEDED_AS_TARGET — reusable C5 concepts are preview/confirmation/gate/outcome/audit semantics, not a registry.

**Owner intelligence surface (§6.133 — ARCH-DRIFT-MCP-OWNER-FULL-CAPABILITY-INTELLIGENCE-SURFACE-01):** a superfície do owner não é só ferramentas de escrita — inclui inteligência de domínio e qualidade. VISTA (primeiro reference owner) expõe `preview_data_block` (`toolClass=ANALYSIS`, não-persistente: `semanticDigest`, `visualRecommendation`, `joinHints`, `formatHints`) e o `designAudit` em `get_playlist_context`/PREPARE `candidatePreview`; correções determinísticas seguras rodam dentro do candidato PREPARE (`apply_safe_layout_fixes` como op canônica para correção explícita de todos os issues `safeAutoFix`; correção automática apenas de issues introduzidas pelo plano; issue sem correção provavelmente segura permanece como evidência — nunca correção insegura nem segundo ACT oculto). DÉLIA não implementou mudança central: `ANALYSIS→READ` já projetado e class-gate já genérico — o mecanismo vale para qualquer owner aprovado futuro (prova: fake specialist `quarto` orquestrado pelo mesmo caminho).

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
