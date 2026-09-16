# DÉLIA — Matriz Canônica de Testes e Aceitação

**Status:** gate transversal canônico  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Specs temáticas:** `53–66`

> DÉLIA é o nome do produto. Prefixos técnicos históricos como `COPILOT_*` podem permanecer apenas como `LEGACY_TOKEN` de gate; não constituem identidade de produto nem prova de runtime. Paths ativos alvo: `delia-api` / `plugins/delia` / `/apps/delia*` (`FROZEN_CANDIDATE` C0.S1).

## 1. Regra de evidence

Todo PASS material registra, conforme aplicável:

```text
gitSha
DÉLIA API/MFE version
manifest/config/schema hashes
OpenAPI/Action Catalog hashes
model/provider/deployment/eval versions
expertise/playbook versions
media/biometric policy versions
external connector/connection/OAuth/egress policy versions
automation/executor/RPA package/worker versions
recurring-work definition/version + recurrence/timezone policy version
autonomy/decision policy version
process-log/model/metric definition versions
MCP/A2A server/agent/protocol version
memory policy/version
sandbox runtime/image/library versions
artifact version/hash
prediction/scenario/twin model versions
Edge device/package/model versions
AI asset/marketplace package versions
retention/consent policy version
environment
test/eval version
timestamp
```

Evidence incompatível, stale ou não reproduzível invalida o PASS afetado.

Estados factuais de inventário seguem `PROVEN | TO_INVENTORY`; planejamento usa `PLANNED | TARGET`. Gate de execução pode usar `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE` conforme esta matriz.

## 2. Gate C0 — Foundation Freeze

### Inventário factual obrigatório

Provar com paths/contracts reais:

- Portal/Core/Gateway/Compose/federation/plugin-ui;
- APIs/OpenAPIs/auth/idempotency/events;
- rooms/jobs/notifications/workflows;
- media/storage/device/privacy/biometric owners;
- Internet/egress/OAuth/vault/external/Teams/webhooks;
- RPA/automation/event/queue/worker/service-account infrastructure;
- schedulers/timers/cron/polling, recurring job/work definitions e owners;
- timezone/DST/calendar, misfire/missed-run/reconciliation e overlap/concurrency semantics existentes;
- background identity/AuthZ/revoke patterns para execução temporal;
- business outcome/postcondition sources;
- event logs/process owners/case keys/BPMN/task-mining sources;
- AI/model/automation asset inventories, eval/cost/incident/kill-switch tooling;
- MCP/A2A/tool registries/agents/delegation identities;
- user preference/memory-like stores and privacy controls;
- BI semantic models/KPI formulas/glossaries/metric owners;
- sandbox/code-execution/query/file/artifact infrastructure;
- predictive/anomaly/optimization/simulation/twin models and datasets;
- factory Edge/devices/MDM/local inference/offline requirements;
- model registry/MLOps/package/catalog/signing/supply-chain controls;
- OT/industrial boundaries;
- Minha DELPI Chat apenas como referência de inventário.

Unknown = `TO_INVENTORY`, nunca `PASS` por suposição.

Para scheduling, C0 deve provar separadamente:

```text
Recurring Governed Work product/definition ownership
!=
physical scheduler/timer owner
```

A ausência de scheduler físico comprovado não remove a capability `TARGET`; exige decisão de reuse/adapter/new only após Abstraction Gate.

### Standalone negatives

```text
DÉLIA importa runtime/source do Chat
DÉLIA depende de Chat API/container/database authority
DÉLIA usa Chat media/external/automation/model runtime como dependency obrigatória
```

### Foundation boundaries REQUIRED

```text
PLATFORM_INVENTORY=PASS
STANDALONE_BOUNDARY=PASS
AUTHORITIES=PASS
SHARED_PRIMITIVES=PASS
ARCHITECTURE_PATTERNS=PASS
PERSISTENCE_BOUNDARIES=PASS
MEDIA_PRIVACY_BOUNDARIES=PASS
BIOMETRIC_IDENTITY_BOUNDARY=PASS
HUMAN_OBSERVATION_BOUNDARY=PASS
EXTERNAL_EGRESS_BOUNDARY=PASS
OAUTH_CONNECTION_BOUNDARY=PASS
PROVIDER_SECRET_BOUNDARY=PASS
EXTERNAL_EVENT_BOUNDARY=PASS
AUTOMATION_EXECUTION_BOUNDARY=PASS
EVENT_SIGNAL_BOUNDARY=PASS
RECURRING_WORK_BOUNDARY=PASS
OUTCOME_VERIFICATION_BOUNDARY=PASS
AUTONOMY_SCOPE_BOUNDARY=PASS
PROCESS_INTELLIGENCE_BOUNDARY=PASS
AI_ASSET_GOVERNANCE_BOUNDARY=PASS
MCP_A2A_TRUST_BOUNDARY=PASS
PERSONAL_MEMORY_BOUNDARY=PASS
SEMANTIC_LAYER_BOUNDARY=PASS
SANDBOX_ARTIFACT_BOUNDARY=PASS
PREDICTIVE_TWIN_BOUNDARY=PASS
EDGE_OFFLINE_BOUNDARY=PASS
MODEL_MARKETPLACE_BOUNDARY=PASS
OT_SAFETY_BOUNDARY=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
FOUNDATION_DUPLICATION=0 material
```

### C0 negative tests adicionais

Devem falhar por design:

```text
Schedule/timer tick treated as permission
Stored schedule intent bypasses live AuthZ/Policy
Duplicate timer tick creates duplicate material side effect
Paused/cancelled recurring Work still fires
Misfire/restart silently replays material ACT without explicit policy
Process Mining without source provenance
Task Mining used as secret employee scoring
Control Tower admin grants business permission
MCP/A2A discovery auto-enables tool/agent
Tool description changes system policy
Personal Memory of user A visible to user B
Memory item overrides current Domain fact
LLM invents KPI formula when governed definition exists
Sandbox reaches host/private network/secret store directly
Read-only sandbox connector performs DDL/DML
Prediction persisted as FACT without semantics
Scenario modifies production state
Edge offline mode widens permissions
Marketplace package grants RBAC/provider scope
Revoked model/server/package remains selectable
```

## 3. Gate C1 — Standalone Bootstrap

Required:

```text
COPILOT_API_OWN_RUNTIME=PASS
COPILOT_MFE_OWN_RUNTIME=PASS
NO_CHAT_IMPORT=PASS
NO_CHAT_API_DEP=PASS
NO_CHAT_DB_AUTHORITY=PASS
INDEPENDENT_DEPLOY_ROLLBACK=PASS
```

Os identificadores `COPILOT_*` acima são `LEGACY_TOKEN` (semântica = DÉLIA API/MFE own runtime). Rename cosmético dos IDs de gate não é obrigatório em C0.S1.

Também provar:

- health/config/logging/JWT/Core;
- federation/plugin-ui/mount/unmount;
- manifest/Gateway/Compose dev-prod;
- full-page/global host/F5/logout;
- nenhuma capability `53–66` ativa capture/connect/execution/mining/sandbox/Edge implicitamente;
- nenhum Recurring Governed Work material é executado antes dos gates C5;
- secrets/credentials ausentes no browser.

## 4. Gate C2 — Portal Context + Commands

- WorkspaceContext bounded/sanitized;
- EntityRef/SourceRef sem credential/permission truth;
- shared-device logout/user-switch cleanup;
- authorized app/route/entity commands;
- arbitrary URL/navigation target rejected;
- iframe bridge safe;
- execution/model/memory/device refs no context não concedem authority;
- platform visual action não vira Business Action.

## 5. Gate C3 — Intelligence + Capability Foundations

### Planner/OpenAPI/Expertise

- own conversation state;
- OpenAPI ingestion/versioning;
- known/sibling/unknown/metamorphic provider;
- provider/executor/model-neutral planner;
- expertise/playbook cannot grant permission;
- no CoT persistence.

### Media/Biometric/External

Manter todos os gates positivos/negativos de `53–56`: provenance, explicit capture, biometric unknown/correction/revoke, no permission elevation, safe fetch/SSRF, OAuth lifecycle, connection isolation, token absence, external content injection resistance.

### Event/Decision Intelligence

- trusted event accepted; forged event rejected;
- duplicate/out-of-order event cannot duplicate candidate;
- event payload cannot modify policy/permission;
- FAST handles deterministic rule without LLM;
- OPERATIONAL uses bounded reads/rules and optional classifier only when justified;
- REASONING uses Graph/Knowledge/Expertise/LLM when needed;
- path choice observable;
- no material ACT in C3.

### Process Intelligence foundation

- EventLog/ProcessTrace schema validation;
- missing event is missing, not invented;
- process case/activity/time/source mapping reproducible;
- actor identity minimized;
- task-mining raw capture disabled by default;
- process model never grants automation permission.

### AI Control Tower foundation

- AIAssetRef/registry metadata owner/version/risk/data scope/eval/dependencies/status;
- duplicate asset authority avoided;
- asset without owner/risk cannot become high-risk enabled asset;
- secret not exposed in registry.

### MCP/A2A foundation

- unknown server/agent starts untrusted/unapproved;
- tool/agent descriptions treated as untrusted;
- server/agent capability allowlist enforced;
- unrelated sensitive conversation/context not delegated;
- delegation credentials scoped/time-bounded when applicable;
- external agent result provenance preserved.

### Personal Memory foundation

- memory classes/version/provenance/retention;
- explicit/user-enabled material memory write policy;
- cross-user isolation;
- sensitive/personality inference blocked;
- user correction supersedes active wrong memory;
- memory cannot grant permission.

### Semantic Layer foundation

- MetricDefinition validation;
- owner/formula/grain/dimensions/unit/freshness/version present for material metric;
- conflict between same labels surfaced;
- metadata cannot grant source data access.

### Sandbox foundation

- container/session isolation;
- CPU/memory/time/storage quotas;
- no unrestricted host/network access;
- safe file ingest;
- no refresh/provider token exposure;
- runtime/version metadata captured;
- cleanup/expiry tested.

### Predictive/Twin foundation

- Prediction contract carries model/version/horizon/confidence/limitations;
- prediction remains `PREDICTION`, not FACT;
- model unavailable/stale/OOD semantics truthful;
- Scenario state separate from production state.

### Edge foundation

- device identity != user identity;
- package/model/cache versioning;
- offline mode state explicit;
- no broad long-lived secret by default;
- no unrestricted local OT command path.

### Model lifecycle foundation

- model registry covers model types in scope;
- revoked/unapproved model not selectable;
- eval lineage/version captured;
- deployment/rollback refs typed;
- package manifest cannot smuggle permission.

## 6. Gate C4 — Governed Reads + Analysis

### Business/external reads

- auth/schema/timeout/error/freshness;
- permission-aware Graph traversal;
- normalized Evidence;
- external/source isolation;
- no master-data duplication.

### Process Mining

- known process reconstructed from real log;
- variants correctly separated;
- conformance distinguishes deviation vs incomplete evidence;
- bottleneck metrics reproducible;
- no employee intent/fraud/personality inference;
- automation opportunity references Evidence.

### Semantic Query

- same governed metric + same source snapshot → same result;
- metric version traceable;
- unauthorized row/dimension blocked;
- stale source explicit;
- LLM paraphrase cannot change formula.

### Analysis Sandbox read-only

- authorized dataset only;
- read connector cannot mutate source;
- code/runtime/input refs allow reproduction when required;
- failed calculation not fabricated;
- output size/file policies enforced.

### Predictive reads

- ground-truth/eval metrics exist before production claim;
- horizon/freshness/calibration visible where relevant;
- drift/OOD changes status/degrades capability truthfully;
- protected/sensitive-person features excluded unless separately governed.

### Edge read-only

- cached procedure/drawing revision verified;
- stale critical revision blocked or clearly degraded;
- offline read does not imply offline write;
- local events buffered with dedupe metadata.

### MCP/A2A read-only

- timeout/cancel/unavailable behavior truthful;
- returned content untrusted;
- result normalized to Source/Evidence;
- sibling implementation does not require planner patch.

### Personalization reads

- memory affects relevance/presentation only;
- live Domain fact overrides stale memory;
- shared-device cache cleared on user switch.

## 7. Gate C5 — Governed ACT + Durable Work + Artifacts

C5 é o primeiro gate que pode liberar **ACT governado** para capabilities materiais específicas. Isso não significa autonomia L5, Watch autônomo ou autoridade ampliada.

Invariante:

```text
PREPARE != ACT
ACT_C5 = explicit authorized governed execution
ACT_C5 != autonomous L5
ACT_C5 != Watch autonomous trigger
SCHEDULE != PERMISSION
```

### Business/external/Teams writes

Decision Gate/revalidation/AuthZ/idempotency/audit/no blind retry/verified Outcome e `draft != send` são obrigatórios.

Teste positivo de ACT C5 deve provar:

- capability write explicitamente habilitada;
- actor/user/service identity explícita;
- Core/domain authorization válida no momento da ação;
- arguments/impact revalidados após Decision quando aplicável;
- idempotency/correlation preservadas;
- executor não amplia permission;
- postcondition material verificada em source autoritativa;
- technical success não substitui business Outcome.

### Automation/Executors

- semantic capability→versioned executor mapping;
- API preferred over RPA when authoritative supported contract exists;
- planner never sees raw click/selector;
- unknown sibling executor can be swapped by adapter;
- AutomationExecution lifecycle/lease/retry/timeout/cancel/AMBIGUOUS;
- resume/replay no duplicate side effect;
- background user/service identity explicit;
- RPA worker/session/credential/package isolation;
- technical success != business Outcome;
- outcome verifier queries authoritative source when required.

### Recurring Governed Work

Para `CP-312–CP-315`, provar no mínimo:

**Lifecycle/independência de sessão**

- create persiste a definição e sobrevive ao fechamento da conversa/session;
- inspect/list retorna definição/version/status sem expor credential;
- pause impede ocorrências futuras enquanto pausado;
- resume não reproduz silenciosamente ocorrências passadas;
- cancel impede definitivamente novas ocorrências daquela versão;
- update/reschedule, se suportado, preserva versionamento/audit ou usa cancel+create conforme contrato.

**Recurrence/timezone**

- timezone é IANA explícito, nunca timezone implícito do servidor/browser;
- mesma definição+timezone produz os mesmos instantes esperados;
- DST/calendar behavior possui caso positivo/edge quando aplicável ao timezone;
- start/end bounds são respeitados;
- `EXPIRED` ou equivalente não dispara nova ocorrência.

**Occurrence/idempotency**

- cada occurrence possui identity/correlation/idempotency próprias;
- duplicate timer signal produz uma única ocorrência material/effect;
- worker/process restart não duplica a mesma occurrence;
- retry após falha segura não duplica side effect;
- ambiguous write não recebe blind retry;
- overlap/concurrency policy é reproduzível;
- missed-run/misfire policy é explícita e testada (`SKIP`, bounded catch-up ou equivalente aprovado), nunca inferida.

**Authorization/revocation por ocorrência**

- creator autorizado na criação não implica autorização eterna;
- cada ACT material revalida current actor/service identity + Core AuthZ + Domain authority + Policy/Decision;
- usuário desativado/sem permissão bloqueia/degrada a occurrence;
- connection/provider revoke/expiry/scope loss bloqueia send/write;
- mudança material de policy/capability/recipient/source scope invalida autorização stale conforme contrato;
- timer/scheduler metadata nunca concede permission.

**Outcome/audit**

- occurrence referencia Work/Decision/Execution/Outcome/Evidence;
- audit liga scheduledFor, triggeredAt, definitionVersion e actor/service identity;
- technical scheduler fire não é business Outcome;
- executor `SUCCEEDED` não basta quando há fonte autoritativa melhor.

**Anchor relatório diário → email**

Provar end-to-end, sem chat aberto:

```text
persist recurring definition
→ deterministic trigger at configured timezone
→ one correlated occurrence
→ live AuthZ/Policy
→ authorized previous-period reads
→ grounded/versioned report artifact
→ communication.email.send as separate ACT
→ provider/executor result
→ authoritative/contractual outcome verification when available
→ Evidence/Audit/Outcome
```

Negativos obrigatórios:

```text
report generated but send not authorized → no email
email connection revoked → no send
recipient outside allowed scope → no send
duplicate tick → one send
retry/restart → no duplicate send
paused/cancelled definition → no send
creator loses permission before next run → no send
provider accepted request but outcome unverifiable → PENDING/INCONCLUSIVE, not false success
```

### Process opportunity governance

Process Mining opportunity → candidate/Task/PREPARE; never automatic bot deployment or policy change.

### MCP/A2A writes

External tool/agent write passes same Policy/Decision/idempotency/Outcome gates as any other action.

### Semantic TOCTOU

Metric/semantic definition version change material invalidates old decision/preview when it affects action.

### Artifact lifecycle

- draft/version/owner/ACL/provenance;
- human edits preserved;
- regeneration cannot silently overwrite human content;
- attach/export/share controlled;
- external send is separate action.

### Prescriptive output

- alternatives/objectives/constraints/assumptions/trade-offs visible;
- recommendation != authorization;
- simulate != apply;
- Apply starts new live revalidation/Decision context.

## 8. Gate C6 — Product Work + Governance + Experience

### Watch/Product Work

Watch permanece, por default, em `OBSERVE|ADVISE|PREPARE`; PREPARE não produz side effect. **Watch não dispara ACT autonomamente em C6.** Isso não revoga as capabilities de ACT governado já liberadas em C5: uma ação C5 pode ser iniciada por fluxo explicitamente autorizado/confirmado e deve passar novamente pelos mesmos gates de Policy/Decision/AuthZ/idempotency/audit/Outcome.

Task/Case/Room/Inbox/source ACL e Workflow correlation permanecem obrigatórios.

Recurring Governed Work é trigger temporal bounded distinto de Watch. Sua UX/admin deve provar:

- lista apenas definições visíveis ao usuário/admin autorizado;
- mostra status + recurrence/timezone + next occurrence quando derivável + last occurrence/outcome;
- pause/resume/cancel respeitam owner/RBAC e são auditados;
- history não expõe segredo/token e mantém correlation/Evidence refs;
- admin de schedules não concede domain/provider write permission;
- C6 Watch continua sem autonomous ACT mesmo existindo schedules C5 governados.

### Process Intelligence UX

- process map/variants/bottlenecks/conformance;
- automation opportunity backlog;
- before/after metrics;
- source/evidence drill-down;
- no hidden person leaderboard by default.

### AI Control Tower

- inventory/owner/risk/status/eval/data scope/dependencies;
- health/cost/value separate;
- incident records/containment;
- kill switch works independently of LLM;
- disabling one asset does not unnecessarily disable unrelated assets;
- Control Tower admin role does not imply domain action permission.

### MCP/A2A lifecycle

`DISCOVERED→REVIEWED→APPROVED→ACTIVE→DEGRADED|DISABLED|REVOKED|DEPRECATED`; revoked becomes unavailable to planner/workflow.

### Personal Memory UX

- view/search/correct/delete/disable controls;
- personalized briefing grounded in live authorized Tasks/Cases/Watches/sources;
- private memory not auto-shared;
- deletion propagates to indexes according to policy.

### Semantic catalog

- metric glossary/owner/version/lineage/conflicts visible;
- new metric onboarding without planner patch;
- deprecated metric handled explicitly.

### Artifact Workspace

- edit/collaboration/version/history;
- templates;
- attach to Case/Task/Room/Meeting;
- export under ACL;
- AI-generated vs human-edited material distinction where needed.

### Operational Twin scenario

- simulated state isolated;
- source freshness present;
- scenario assumptions explicit;
- compare alternatives reproducibly;
- no production write from scenario state.

### Edge/Offline pilot

- ONLINE/DEGRADED/OFFLINE_READ_ONLY/SYNCING visible;
- event buffering/idempotent sync;
- user/session cleanup;
- package/model/cache health;
- no authority widening offline.

### Model/Marketplace product

- drift/health/latency/cost metrics appropriate to model type;
- Marketplace lifecycle draft/review/approved/published/deprecated/revoked;
- manifest declares dependencies/permissions/data scopes/evals;
- install/enable still requires local authorization/config.

## 9. Gate C7 — Advanced Autonomy / Scale

C7 não cria o conceito de ACT; amplia **autonomia operacional governada** sobre capabilities que já possuem contratos, enforcement e Outcome verification comprovados.

Recurring Governed Work C5 não precisa de L5 quando a recorrência é bounded e cada ocorrência passa por live gates. C7 não converte schedule em permission e não é necessário para o anchor de relatório diário governado.

### Capability-scoped autonomy

No global unrestricted L5. L5 OFF default; allowlist/actor/service identity/business limits/budget/rate/kill switch/live revalidation/verified Outcome.

### Watch autonomous ACT

Selected Watch ACT só pode ser habilitado por capability/context/risk scope explícito, após C5/C6 gates e com policy live, service/user identity, limits, idempotency, audit, kill switch e verified Outcome.

### Closed-loop Process Intelligence

- process optimization recommendation measured before/after;
- no permanent policy change from one successful run;
- ACT only if capability explicitly approved;
- regression/reversal possible.

### A2A autonomous delegation

- approved agent/capability only;
- bounded goal/context/deadline/budget;
- cancel/timeout;
- no hidden CoT/context dumping;
- external agent cannot recursively expand authority;
- verified result/outcome.

### Advanced personalization

- no hidden employee score/sensitive inference;
- user controls remain;
- personalization eval does not reward permission overreach.

### Semantic scale

Federation/materialization/cache preserve source permission/freshness/lineage; cache not authority.

### Sandbox scale

Pool isolation/quotas/cleanup/no corporate shell; workload cost/budget limits.

### Predictive/Prescriptive ACT

Model output alone never authorizes action. Policy/Decision/autonomy live checks + verified Outcome required.

### Operational Twin / Simulate→Apply

`SIMULATED_STATE != PRODUCTION_STATE`. Apply re-reads live state, permissions, model/semantic versions and creates new action context.

### Edge rollout/offline bounded actions

- device cohorts;
- signed/hash-verified packages where applicable;
- health/rollback/revoke;
- offline action allowlist + expiry + idempotency + sync/reconciliation;
- loss of cloud never increases authority;
- OT safety still independent.

### Model lifecycle / Marketplace

- approved deployment environment/cohort;
- rollback/revocation tested;
- revoked model/package/server no longer selectable;
- supply-chain review for executable assets;
- marketplace/model/package metadata cannot grant permission.

## 10. Injection/safety transversal

Treat as untrusted:

```text
user prompt
voice transcript
RAG/tool/API result
WorkspaceContext
biometric/Human Observation result
public webpage/search result
external email/message/file/calendar
provider webhook/event payload
scheduler/timer trigger metadata
RPA/computer-use screen/result
MCP tool description/resource/result
A2A agent message/artifact
personal memory candidate
sandbox-generated code/output
marketplace package metadata
model output
Edge buffered event
iframe/room/meeting/frontline content
```

Untrusted data nunca changes system policy, RBAC, provider scopes, autonomy allowlist, retention, package trust or safety boundary.

## 11. Cross-surface parity

Equivalent auth/policy/evidence semantics across Global, Workspace, Meeting, Frontline, Teams, Internet, connected sources, background Watch/Workflow, **Recurring Governed Work**, Automation Hub, Process Intelligence, Sandbox/Artifacts, Control Tower and Edge.

## 12. Release blockers

```text
CHAT_RUNTIME_IMPORT
CHAT_API_REQUIRED
CHAT_DATABASE_AUTHORITY
FOUNDATION_DUPLICATION
ARCHITECTURE_PATTERN_DRIFT
RBAC_LEAKAGE
WRITE_WITHOUT_REQUIRED_DECISION_GATE
RESUME_DUPLICATE_WRITE
HIDDEN_MEDIA_CAPTURE
SHARED_DEVICE_STATE_LEAK
BIOMETRIC_PERMISSION_ELEVATION
SENSITIVE_PERSON_INFERENCE
UNSAFE_WEB_EGRESS
PROVIDER_TOKEN_LEAK
CROSS_USER_EXTERNAL_DATA_LEAK
DRAFT_SENT_IMPLICITLY
UNVERIFIED_EXTERNAL_SUCCESS
INVALID_PROVIDER_EVENT_ACCEPTED
EVENT_PERMISSION_ELEVATION
DUPLICATE_EVENT_DUPLICATE_EXECUTION
SCHEDULE_PERMISSION_ELEVATION
SCHEDULE_WITHOUT_LIVE_AUTHZ
DUPLICATE_SCHEDULE_OCCURRENCE_SIDE_EFFECT
PAUSED_OR_CANCELLED_SCHEDULE_EXECUTES
SCHEDULE_MISFIRE_POLICY_UNDEFINED
SCHEDULE_TIMEZONE_IMPLICIT
SCHEDULE_RETRY_DUPLICATE_ACT
PLANNER_RPA_UI_MECHANICS_LEAK
BACKGROUND_EXECUTION_WITHOUT_EXPLICIT_IDENTITY
AMBIGUOUS_WRITE_BLIND_RETRY
EXECUTOR_TECHNICAL_SUCCESS_AS_BUSINESS_SUCCESS
PREPARE_BECOMES_ACT_IMPLICITLY
ACT_WITHOUT_LIVE_AUTHZ
ACT_WITHOUT_IDEMPOTENCY_OR_AUDIT
ACT_WITHOUT_REQUIRED_OUTCOME_VERIFICATION
WATCH_AUTONOMOUS_ACT_BEFORE_C7
GLOBAL_UNSCOPED_L5
PROCESS_MINING_WORKER_PROFILING
MCP_A2A_AUTO_TRUST
TOOL_AGENT_POLICY_INJECTION
CROSS_USER_PERSONAL_MEMORY_LEAK
MEMORY_OVERRIDES_LIVE_AUTHORITY
UNGOVERNED_METRIC_FORMULA
SANDBOX_ESCAPE_OR_UNGOVERNED_WRITE
ARTIFACT_PROVENANCE_LOSS
PREDICTION_PRESENTED_AS_FACT
SIMULATION_MUTATES_PRODUCTION
EDGE_OFFLINE_PERMISSION_EXPANSION
REVOKED_AI_ASSET_STILL_ACTIVE
MARKETPLACE_PERMISSION_ELEVATION
AI_PACKAGE_SUPPLY_CHAIN_BYPASS
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
REQUIRED_TEST_FAIL_OR_INCONCLUSIVE
STALE_NONREPRODUCIBLE_EVIDENCE
```

## 13. Regra final

Qualquer gate REQUIRED em `FAIL | INCONCLUSIVE | PENDING | TEST_NOT_RUN | STALE_EVIDENCE` bloqueia a fase. Nunca enfraquecer teste para fazer candidate passar.

Documentação, target, schema candidate ou commit documental não promovem gate a PASS. Evidence vale somente para o SHA/config realmente avaliados.
