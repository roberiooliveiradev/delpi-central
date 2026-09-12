# 14 — Definition of Done

**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Uma fase só fecha quando prova comportamento, integração, segurança, privacidade, generalização, arquitetura e **independência do Minha DELPI Chat** no candidate vigente.

Quando mídia/Meeting/Frontline estiverem no escopo, também precisa provar consentimento/capture visibility, retention, shared-device isolation e industrial safety boundary.

## 2. DoD global

```text
[ ] Copilot API pertence a serviço próprio
[ ] Copilot MFE pertence a plugin próprio
[ ] não existe runtime import do Chat
[ ] não existe Chat API como proxy obrigatório
[ ] não existe tabela/session/agent do Chat como authority Copilot
[ ] deploy/rollback do Copilot é independente
[ ] authorities possuem owner claro
[ ] implementation segue 49 e boundaries 50/51/52/53
[ ] shared primitives não possuem duplicação material
[ ] abstrações novas passaram pelo Abstraction Gate
[ ] Domain/Application não dependem de framework/provider concreto
[ ] concrete wiring ocorre no Composition Root
[ ] Core continua authority de apps/routes/RBAC
[ ] Domain APIs continuam authority de business rules/data
[ ] permissions Copilot ⊆ permissions efetivas do usuário
[ ] Portal hospeda/navega, mas não contém AI runtime
[ ] OpenAPI + Copilot Action Catalog sustentam Business Actions
[ ] Workspace Context não concede autorização
[ ] Expertise/Playbook não concedem autorização
[ ] modality não concede autorização
[ ] Business Graph não replica dados operacionais
[ ] writes usam Decision Gate/idempotency/audit quando aplicável
[ ] durable resume não duplica write
[ ] observabilidade não persiste chain-of-thought
[ ] raw media não é persistida sem purpose/policy
[ ] device identity não substitui user identity
[ ] Copilot não vira safety controller
```

## 3. DoD C0 — Foundation Freeze

```text
[ ] Portal/Core/Gateway/Infra/MFE/API inventory com evidence
[ ] Chat inventariado apenas como reference-only
[ ] existing rooms/events/notifications/jobs inventariados
[ ] API/OpenAPI/auth/idempotency/entity/deep-link inventory
[ ] media/browser/streaming/storage inventory
[ ] devices/tablets/kiosks/room/frontline patterns inventariados
[ ] production/maintenance/quality context sources inventariados
[ ] OT/industrial owners/interfaces/safety boundaries inventariados
[ ] privacy/consent/retention owners inventariados
[ ] backend/MFE/serviceName/basePaths/manifestId congelados
[ ] standalone product boundary congelado
[ ] DB/schema/migration ownership congelado
[ ] authorities/bounded contexts congelados
[ ] shared primitives definidos/reutilizados
[ ] decisão MediaRef/equivalent registrada
[ ] Portal↔MFE, MFE↔API, API↔Core, API↔Domain contracts congelados
[ ] media/device integration boundaries congelados
[ ] architecture style/layers/dependency rules congelados
[ ] Pattern Decision Matrix + Abstraction Gate validados
[ ] error/event/state/resilience/frontend-state rules congeladas
[ ] media retention/capture/shared-device rules congeladas
[ ] OT safety non-authority congelada
[ ] persistence boundaries/ports definidos
[ ] contract + architecture conformance harness reproduzível
[ ] CHAT_RUNTIME_DEPENDENCY = 0 planejado/contractual
[ ] FOUNDATION_DUPLICATION = 0 material
[ ] FOUNDATION_FREEZE = PASS
```

C1 não inicia sem C0 completo.

## 4. DoD C1 — Standalone Application Bootstrap

```text
[ ] minha-delpi-copilot-api criado em root próprio
[ ] Copilot API segue layers/patterns C0
[ ] health endpoint funcional
[ ] JWT validation funcional
[ ] Core current-user/apps/routes integration funcional
[ ] plugins/minha-delpi-copilot criado
[ ] Module Federation funcional
[ ] plugin-ui reutilizado
[ ] mount/unmount conforme host contract
[ ] manifesto próprio válido
[ ] Gateway dev/prod próprio
[ ] Compose dev/prod próprio
[ ] env/config próprios
[ ] Portal full-page mount autorizado
[ ] global panel host contract funcional ou gateado conforme step
[ ] responsive/accessibility baseline
[ ] media permissions nunca iniciam captura automaticamente
[ ] F5/deep route/logout funcionais
[ ] Chat desligado não quebra Copilot bootstrap
[ ] nenhuma import/source/API/table dependency do Chat
[ ] rollback/shutdown independente
```

## 5. DoD C2 — Portal + Operational Context + Platform Commands

```text
[ ] WorkspaceContext bounded/sanitized
[ ] Portal→Copilot context bridge tipado
[ ] authorized Platform Capability Projection deriva do Core
[ ] open app/route/entity funcional
[ ] URL arbitrária rejeitada
[ ] permission revocation/TOCTOU tratado
[ ] MFE context/deep-link helper sem business logic
[ ] OP/machine/product/operation/lote/posto usam EntityRef quando material
[ ] device/session metadata é bounded e não-authoritative
[ ] shared-device user change limpa local context/state
[ ] iframe PORTAL_ONLY funcional quando aplicável
[ ] bridge iframe avançado usa Adapter/ACL, não DOM automation
[ ] unknown app/iframe não exige planner patch
[ ] F5/logout/stale context corretos
[ ] full-page/panel possuem policy parity
```

## 6. DoD C3 — Intelligence Core + Multimodal Foundations

```text
[ ] conversation/turn model é Copilot-owned
[ ] não existe agent_id/chat_mode legado como requisito
[ ] provider/model abstraction por ports/adapters
[ ] OpenAPI ingestion Copilot-owned
[ ] Copilot Action Catalog/index Copilot-owned
[ ] capability retrieval positive/sibling/negative
[ ] structured planner usa contracts tipados
[ ] Expertise Catalog/retrieval/composition
[ ] Domain Playbook applicability/versioning
[ ] Knowledge/RAG respeita ACL/provenance
[ ] document/image multimodal evidence possui page/region/confidence/limitations
[ ] voice baseline, se em escopo, preserva mesma RBAC/policy do texto
[ ] camera/video, se em escopo, possui frame/time-range provenance
[ ] raw media retention segue policy class
[ ] stop/reload não reativa capture silenciosamente
[ ] visual/audio finding não vira FACT sem authority/evidence adequados
[ ] Evidence/epistemic classes consistentes
[ ] prompt/tool/context/document/media injection negatives passam
[ ] unknown provider/pack e metamorphic cases passam
[ ] no Chat runtime dependency
[ ] operational activity sem CoT
```

## 7. DoD C4 — Business Reads + Graph

```text
[ ] Domain OpenAPIs importadas por contrato
[ ] Business Capability Projection não duplica authority técnica
[ ] generic reads known/sibling/unknown/metamorphic passam
[ ] args/schema/RBAC corretos
[ ] normalized Outcome/Evidence consistente
[ ] Graph usa EntityRef/RelationshipRef compartilhados
[ ] traversal permission-aware
[ ] authoritative vs inferred relationship rastreável
[ ] source data buscado no owner
[ ] Graph não replica domain datasets como master
[ ] cycle/depth budget existe
[ ] OP/machine/product/operation context correlation preserva source owners
[ ] mídia/evidence referencia entities sem virar master data
[ ] nova relação/provider não exige hardcode central
```

## 8. DoD C5 — Governed Writes + Durable Foundation

```text
[ ] Decision Gate usa Policy + State Machine
[ ] impact preview corresponde ao payload efetivo
[ ] backend/domain API revalida authorization
[ ] idempotency/concurrency tratadas
[ ] retry cego de write inexistente
[ ] ambiguous outcome não vira sucesso narrativo
[ ] write outcome verificado/auditado
[ ] voice/meeting/frontline candidate action usa o mesmo Decision/action pipeline
[ ] repeated utterance/event não duplica write
[ ] WorkflowPlan/Step runtime usa executors canônicos
[ ] checkpoint persistente
[ ] wait_user/wait_approval/wait_event
[ ] timeout/cancel
[ ] crash/restart sem duplicate write
[ ] Saga somente se houver writes distribuídos + compensações reais
```

## 9. DoD C6 — Product Work + Proactivity + Meeting/Frontline + Ecosystem

```text
[ ] Task usa durable runtime; não possui engine paralela
[ ] Case usa refs/evidence compartilhados
[ ] Evidence Board não duplica EvidenceRef
[ ] Interaction Room reutiliza/estende/adapta owner existente quando C0 provar viável
[ ] Room membership não amplia source permissions
[ ] Inbox é projection de work/decision/watch/meeting state
[ ] Watch OBSERVE/ADVISE usa EventEnvelope/dedupe/revalidation
[ ] AI-ready SDK/templates não hardcodam apps
[ ] Organizational Knowledge possui owner/version/provenance
[ ] feedback não muda production behavior automaticamente
[ ] Expertise Studio usa lifecycle/admin RBAC
[ ] unknown app/pack onboarding sem core hardcode
```

### Meeting Mode

```text
[ ] start/stop explícitos
[ ] indicators de mic/transcript/camera/screen/raw recording visíveis
[ ] meeting query usa permissões efetivas do usuário
[ ] transcript != summary != confirmed decision != executed action
[ ] ata viva possui sources/evidence quando material
[ ] candidate actions exigem review/governance
[ ] raw media retention segue policy
[ ] revoked source access é respeitado
[ ] Meeting funciona sem Chat runtime
```

### Frontline Mode

```text
[ ] shared-device login/user-switch sem state leak
[ ] OP/machine/product/operation context usa EntityRef
[ ] voice hands-free tem fallback touch/text
[ ] noisy/ambiguous speech não causa ação insegura
[ ] camera finding mostra confidence/limitations
[ ] procedure/drawing/training usa source/revision vigente
[ ] register issue/escalate usa Business Action governada
[ ] process observation cria candidate knowledge apenas
[ ] sem hidden worker surveillance
[ ] sem direct free-form machine actuation
[ ] Frontline funciona sem Chat runtime
```

## 10. DoD C7 — Advanced Realtime/Autonomy/Optimization/Rollout

```text
[ ] L5 OFF por default
[ ] Watch ACT allowlisted/policy-governed
[ ] Simulation reproduzível e separada de Apply
[ ] Model Router só existe após baseline/variações reais
[ ] provider incompatível com data policy é bloqueado
[ ] realtime media, se em escopo, possui duration/concurrency/backpressure budgets
[ ] degraded/async fallback existe para falha de rede/provider quando necessário
[ ] performance/cost/latency observáveis
[ ] progressive rollout/canary/rollback
[ ] accessibility/security/privacy/generalization finais
[ ] OT arbitrary command continua BLOCK sem safety gate específico
[ ] architecture conformance final
[ ] Copilot continua independente do Chat
[ ] CP coverage sem UNMAPPED para release declarado
```

## 11. Testes transversais obrigatórios

```text
positive
sibling
negative/no-tool
unauthorized
TOCTOU
required missing
unknown app/provider/pack/iframe/relation
metamorphic rename
prompt/tool/context/document/media/event injection
Decision Gate
idempotency/replay
partial failure
persist/reload/restart
full-page/panel/meeting/frontline security parity
layer/dependency conformance
port/adapter contracts
state transitions
error translation/resilience
shared-device isolation
media retention/consent
CHAT_OFFLINE_INDEPENDENCE
OT_COMMAND_BLOCK
latency/cost quando aplicável
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
DEPENDENCY_RULE_VIOLATION
UNJUSTIFIED_ABSTRACTION
UNDOCUMENTED_ARCHITECTURAL_EXCEPTION
CHAT_RUNTIME_IMPORT
CHAT_API_REQUIRED
CHAT_DATABASE_AUTHORITY
CHAT_MIGRATION_DEPENDENCY
PORTAL_AI_LOGIC_LEAK
DOMAIN_RULE_DUPLICATION
HIDDEN_MEDIA_CAPTURE
UNDEFINED_MEDIA_RETENTION
SHARED_DEVICE_STATE_LEAK
VOICE_PERMISSION_BYPASS
VISUAL_FINDING_AS_UNVALIDATED_FACT
HIDDEN_WORKER_SURVEILLANCE
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 13. Evidence de release

```text
GIT_SHA
Copilot API image/version
Copilot MFE bundle/version
manifest version/hash
Gateway/Compose config evidence
schema/migration version
OpenAPI/Action Catalog hashes
config/model/provider hashes
expertise/playbook versions
media/provider policy version
retention/consent policy version
architecture conformance
unit/integration/live/security results
shared-device/media/OT safety gate results when applicable
CHAT_OFFLINE_INDEPENDENCE result
rollback evidence
known limitations
```

## 14. Resultado final

> O Copilot só está Done quando funciona como aplicação independente e multimodal governada, integrada às authorities da Minha DELPI, útil no escritório e preparada para Meeting/Frontline sem herdar o runtime/dívida do Chat, sem criar authorities paralelas, sem capturar mídia de forma opaca e sem ultrapassar o boundary de segurança industrial.