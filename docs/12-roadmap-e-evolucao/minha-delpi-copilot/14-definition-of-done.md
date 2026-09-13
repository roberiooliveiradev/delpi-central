# 14 — Definition of Done

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Objetivo

Uma fase só fecha com comportamento, integração, segurança, privacidade, outcome truth, generalização, arquitetura e independência do Minha DELPI Chat provados no candidate vigente.

## 2. DoD global

```text
[ ] Copilot API/MFE/deploy/persistence próprios
[ ] zero runtime dependency no Chat
[ ] Core continua authority de apps/routes/RBAC
[ ] Domain APIs continuam authority de business rules/data/actions
[ ] external provider continua authority de seus recursos
[ ] RPA/executor nunca vira business-rule authority
[ ] event/provider/worker/device/biometric identity nunca concede permission
[ ] OpenAPI/capability contracts governam Business Actions
[ ] planner trabalha com semantic capabilities, não clicks/selectors
[ ] API oficial é preferida antes de RPA quando atende o contract
[ ] not every event invokes LLM
[ ] deterministic readiness usa Policy/Specification quando critérios existem
[ ] technical executor success != verified business outcome
[ ] outcome/postcondition é verificado quando material
[ ] background action possui user/service identity explícita
[ ] Watch PREPARE != ACT
[ ] autonomy é capability/context/risk scoped
[ ] L5 OFF por default
[ ] kill switches independem de prompt/LLM
[ ] Durable Workflow continua único work runtime
[ ] provider/RPA credentials ficam fora de LLM/MFE/logs
[ ] personal/restricted source não vira organizational source implicitamente
[ ] read != write e draft != send
[ ] external/RPA writes não usam blind retry em outcome ambíguo
[ ] external/event learning publica somente via governance
[ ] media/biometric privacy boundaries respeitados
[ ] Copilot/Automation Hub não vira industrial safety controller
```

## 3. DoD C0 — Foundation Freeze

```text
[ ] Portal/Core/Gateway/Infra/MFE/API inventory com evidence
[ ] media/device/biometric/OT inventory
[ ] Internet/OAuth/connector/Teams inventory
[ ] event source/broker/webhook/scheduler inventory
[ ] RPA tool/orchestrator/licence/bot/package inventory
[ ] scripts/functions/jobs inventory
[ ] queues/workers/desktop-session infrastructure inventory
[ ] service account/background identity inventory
[ ] credential/secret owner inventory
[ ] business postcondition/outcome source inventory
[ ] notification/escalation inventory
[ ] automation governance/SLA/kill-switch inventory
[ ] standalone boundary/names/storage ownership congelados
[ ] event trust/dedupe/order/correlation boundary congelado
[ ] executor preference/semantic contract congelado
[ ] Automation & Execution Hub ownership direction congelada
[ ] background identity boundary congelado
[ ] execution lifecycle/idempotency/ambiguous outcome semantics congelados
[ ] outcome verification boundary congelado
[ ] PREPARE/ACT semantics congeladas
[ ] capability-scoped autonomy/kill-switch model congelado
[ ] OT safety non-authority congelada
[ ] contract/conformance harness reproduzível
[ ] CHAT_RUNTIME_DEPENDENCY=0
[ ] FOUNDATION_DUPLICATION=0 material
[ ] FOUNDATION_FREEZE=PASS
```

## 4. DoD C1 — Standalone Bootstrap

```text
[ ] API/MFE/manifest/Gateway/Compose próprios
[ ] JWT/Core integration
[ ] Module Federation/plugin-ui
[ ] full-page/global host contract
[ ] Chat offline não quebra bootstrap
[ ] no RPA/Event engine/Automation Hub ACT runtime criado prematuramente
[ ] independent rollback/shutdown
```

## 5. DoD C2 — Context + Platform Commands

```text
[ ] WorkspaceContext bounded/sanitized
[ ] EntityRef/SourceRef sem credential/permission truth
[ ] execution/watch refs não concedem action authority
[ ] device/biometric/external context não concede authorization
[ ] user-switch/logout limpa state local
[ ] authorized navigation + arbitrary target rejection
```

## 6. DoD C3 — Intelligence/Event/Decision Foundations

```text
[ ] conversation/runtime próprios
[ ] Action Catalog/Capability Projection próprios
[ ] planner provider/executor-neutral
[ ] FAST path sem LLM quando condição determinística é suficiente
[ ] OPERATIONAL/REASONING path selection observável
[ ] deterministic readiness reproduzível
[ ] event source authenticity/trust validation
[ ] duplicate/out-of-order event handling
[ ] event payload não altera policy/permission
[ ] Internet/connector/media/biometric gates aplicáveis passam
[ ] no material autonomous ACT
```

## 7. DoD C4 — Reads + Graph + Operational Intelligence

```text
[ ] business/external reads authorized
[ ] no cross-user/source leak
[ ] Graph não replica masters
[ ] invoice/report/stock/supplier/machine readiness/anomaly scenarios são read-only
[ ] facts/calculations/hypotheses claramente diferenciados
[ ] anomaly não vira inferência de fraude/intenção de pessoa
[ ] no side effect implícito
```

## 8. DoD C5 — Governed Execution Foundation

```text
[ ] Decision Gate/revalidation/idempotency
[ ] semantic capability→versioned executor mapping
[ ] planner não contém RPA UI mechanics
[ ] API preferred over RPA when supported
[ ] executor adapters substituíveis
[ ] AutomationExecution lifecycle válido
[ ] background actor/service identity explícita
[ ] worker/queue/lease/session isolation quando RPA está em escopo
[ ] protected credential injection
[ ] timeout/ambiguous write não recebe blind retry
[ ] resume/replay não duplica efeito
[ ] technical result separado de business Outcome
[ ] postcondition verificada em source autoritativo quando material
[ ] Durable Workflow continua único runtime
```

## 9. DoD C6 — Product Work + Automation Hub

```text
[ ] Task/Case/Room/Inbox preservam source ACL
[ ] Watch OBSERVE/ADVISE/PREPARE funciona
[ ] PREPARE não produz side effect
[ ] Watch ACT permanece bloqueado
[ ] Automation Hub Admin não cria segundo planner/workflow engine
[ ] catalog/executions/workers/exceptions/outcomes são rastreáveis
[ ] success técnico e verified outcome aparecem separadamente
[ ] notification/escalation usa estado verdadeiro e dedupe/SLA
[ ] manual exception retoma mesmo Workflow
[ ] Meeting/Frontline/external learning governance permanece válida
```

## 10. DoD C7 — Autonomous Operations

```text
[ ] no global unrestricted L4/L5 switch
[ ] L5 OFF by default
[ ] capability/actor/context/risk/amount/environment allowlists/limits
[ ] authorization/policy revalidated immediately before ACT
[ ] kill switch blocks new ACT independently of LLM
[ ] duplicate event não duplica action
[ ] autonomous execution produces verified Outcome
[ ] failed/ambiguous Outcome is never announced as completed
[ ] computer-use, if any, is sandboxed/allowlisted/audited
[ ] autonomous invoice anchor passes when declared in scope
[ ] progressive rollout/canary/rollback
[ ] final Chat-offline independence
[ ] OT physical actuation remains separate safety initiative
```

## 11. Testes transversais obrigatórios

```text
positive/sibling/negative
unauthorized/TOCTOU
unknown/metamorphic
injection from prompt/tool/document/media/external/event/RPA screen
Decision Gate
idempotency/replay
partial/ambiguous outcome
persist/reload/restart
layer/dependency conformance
event source authenticity/dedupe
FAST_PATH_NO_LLM_WHEN_DETERMINISTIC
DETERMINISTIC_READINESS_REPRODUCIBLE
PLANNER_NO_RPA_UI_MECHANICS
API_PREFERRED_OVER_RPA_WHEN_SUPPORTED
EXECUTOR_SUBSTITUTION_NO_PLANNER_PATCH
BACKGROUND_IDENTITY_EXPLICIT
AUTOMATION_EXECUTION_IDEMPOTENT
RPA_WORKER_SESSION_CREDENTIAL_ISOLATION
AMBIGUOUS_WRITE_NO_BLIND_RETRY
VERIFIED_BUSINESS_OUTCOME
PREPARE_NOT_ACT
CAPABILITY_SCOPED_AUTONOMY
L5_OFF_DEFAULT
AUTONOMY_KILL_SWITCH
COMPUTER_USE_BOUNDED
CHAT_OFFLINE_INDEPENDENCE
OT_COMMAND_BLOCK
```

## 12. Blockers

```text
PARTIAL
INCONCLUSIVE
PENDING
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
ARCHITECTURE_PATTERN_DRIFT
UNJUSTIFIED_ABSTRACTION
CHAT_RUNTIME_IMPORT
CHAT_API_REQUIRED
CHAT_DATABASE_AUTHORITY
PORTAL_AI_LOGIC_LEAK
DOMAIN_RULE_DUPLICATION
EVENT_PERMISSION_ELEVATION
DUPLICATE_EVENT_DUPLICATE_EXECUTION
PLANNER_RPA_UI_MECHANICS_LEAK
RPA_SELECTED_OVER_AUTHORITATIVE_API_WITHOUT_JUSTIFICATION
BACKGROUND_EXECUTION_WITHOUT_EXPLICIT_IDENTITY
AUTOMATION_EXECUTION_DUPLICATE
RPA_CREDENTIAL_OR_SESSION_LEAK
AMBIGUOUS_WRITE_BLIND_RETRY
EXECUTOR_TECHNICAL_SUCCESS_AS_BUSINESS_SUCCESS
PREPARE_BECOMES_ACT_IMPLICITLY
GLOBAL_UNSCOPED_L5
AUTONOMY_KILL_SWITCH_BYPASS
COMPUTER_USE_UNBOUNDED_ACCESS
PROVIDER_TOKEN_LEAK
CROSS_USER_EXTERNAL_DATA_LEAK
BIOMETRIC_PERMISSION_ELEVATION
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

Nenhuma fase fecha com blocker material aberto.
