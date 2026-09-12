# 14 — Definition of Done

## 1. Objetivo

Uma fase só fecha quando prova comportamento, integração, segurança, generalização, arquitetura e **independência do Minha DELPI Chat** no candidate vigente.

## 2. DoD global

```text
[ ] Copilot API pertence a serviço próprio
[ ] Copilot MFE pertence a plugin próprio
[ ] não existe runtime import do Chat
[ ] não existe Chat API como proxy obrigatório
[ ] não existe tabela/session/agent do Chat como authority Copilot
[ ] deploy/rollback do Copilot é independente
[ ] authorities possuem owner claro
[ ] implementation segue 49 e boundaries 50/51/52
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
[ ] Business Graph não replica dados operacionais
[ ] writes usam Decision Gate/idempotency/audit quando aplicável
[ ] durable resume não duplica write
[ ] observabilidade não persiste chain-of-thought
```

## 3. DoD C0 — Foundation Freeze

```text
[ ] Portal/Core/Gateway/Infra/MFE/API inventory com evidence
[ ] Chat inventariado apenas como reference-only
[ ] existing rooms/events/notifications/jobs inventariados
[ ] API/OpenAPI/auth/idempotency/entity/deep-link inventory
[ ] backend/MFE/serviceName/basePaths/manifestId congelados
[ ] standalone product boundary congelado
[ ] DB/schema/migration ownership congelado
[ ] authorities/bounded contexts congelados
[ ] shared primitives definidos/reutilizados
[ ] Portal↔MFE, MFE↔API, API↔Core, API↔Domain contracts congelados
[ ] architecture style/layers/dependency rules congelados
[ ] Pattern Decision Matrix + Abstraction Gate validados
[ ] error/event/state/resilience/frontend-state rules congeladas
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
[ ] F5/deep route/logout funcionais
[ ] Chat desligado não quebra Copilot bootstrap
[ ] nenhuma import/source/API/table dependency do Chat
[ ] rollback/shutdown independente
```

## 5. DoD C2 — Portal Context + Platform Commands

```text
[ ] WorkspaceContext bounded/sanitized
[ ] Portal→Copilot context bridge tipado
[ ] authorized Platform Capability Projection deriva do Core
[ ] open app/route/entity funcional
[ ] URL arbitrária rejeitada
[ ] permission revocation/TOCTOU tratado
[ ] MFE context/deep-link helper sem business logic
[ ] iframe PORTAL_ONLY funcional quando aplicável
[ ] bridge iframe avançado usa Adapter/ACL, não DOM automation
[ ] unknown app/iframe não exige planner patch
[ ] F5/logout/stale context corretos
[ ] full-page/panel possuem policy parity
```

## 6. DoD C3 — Intelligence Core

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
[ ] multimodal evidence possui page/region/confidence/limitations
[ ] Evidence/epistemic classes consistentes
[ ] prompt/tool/context/document injection negatives passam
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
[ ] WorkflowPlan/Step runtime usa executors canônicos
[ ] checkpoint persistente
[ ] wait_user/wait_approval/wait_event
[ ] timeout/cancel
[ ] crash/restart sem duplicate write
[ ] Saga somente se houver writes distribuídos + compensações reais
```

## 9. DoD C6 — Product Work + Proactivity + Ecosystem

```text
[ ] Task usa durable runtime; não possui engine paralela
[ ] Case usa refs/evidence compartilhados
[ ] Evidence Board não duplica EvidenceRef
[ ] Interaction Room reutiliza/estende/adapta owner existente quando C0 provar viável
[ ] Room membership não amplia source permissions
[ ] Inbox é projection de work/decision/watch state
[ ] Watch OBSERVE/ADVISE usa EventEnvelope/dedupe/revalidation
[ ] AI-ready SDK/templates não hardcodam apps
[ ] Organizational Knowledge possui owner/version/provenance
[ ] feedback não muda production behavior automaticamente
[ ] Expertise Studio usa lifecycle/admin RBAC
[ ] unknown app/pack onboarding sem core hardcode
```

## 10. DoD C7 — Autonomy/Optimization/Rollout

```text
[ ] L5 OFF por default
[ ] Watch ACT allowlisted/policy-governed
[ ] Simulation reproduzível e separada de Apply
[ ] Model Router só existe após baseline/variações reais
[ ] provider incompatível com data policy é bloqueado
[ ] performance/cost/latency observáveis
[ ] progressive rollout/canary/rollback
[ ] accessibility/security/generalization finais
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
prompt/tool/context/document/event injection
Decision Gate
idempotency/replay
partial failure
persist/reload/restart
full-page/panel parity
layer/dependency conformance
port/adapter contracts
state transitions
error translation/resilience
CHAT_OFFLINE_INDEPENDENCE
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
architecture conformance
unit/integration/live/security results
CHAT_OFFLINE_INDEPENDENCE result
rollback evidence
known limitations
```

## 14. Resultado final

> O Copilot só está Done quando funciona como aplicação independente, integrada às authorities da Minha DELPI, sem herdar o runtime/dívida do Chat e sem criar authorities paralelas.