# 14 — Definition of Done

## 1. Objetivo

Evitar fechamento prematuro por demo funcional. Cada fase precisa provar foundation, wiring, segurança, generalização, conformidade arquitetural e evidence no candidate vigente.

## 2. DoD global

```text
[ ] authorities possuem owner claro
[ ] shared primitives não possuem duplicação material
[ ] implementação segue arquitetura/patterns canônicos do documento 49
[ ] layer/dependency rules são preservadas
[ ] abstrações novas passaram pelo Abstraction Gate
[ ] divergência arquitetural material possui decisão/ADR explícita
[ ] external dependencies estão atrás de boundary/adapter adequado quando aplicável
[ ] concrete wiring ocorre no Composition Root/DI
[ ] estado durável de negócio permanece no backend owner
[ ] permissions do Copilot ⊆ permissões efetivas do usuário
[ ] UI/Copilot convergem para os mesmos use cases
[ ] OpenAPI + Action Catalog são authority técnica de Business Actions
[ ] Workspace Context não concede autorização
[ ] Expertise/Playbook não concedem autorização
[ ] Entity/Evidence/Decision/Workflow/Event contracts são compartilhados
[ ] Business Graph não replica dados operacionais
[ ] writes usam Decision Gate/policy/idempotency/audit conforme risco
[ ] durable resume não duplica write
[ ] activity representa estado real
[ ] app/provider/pack/relation desconhecido funciona por contrato quando no escopo
[ ] eval evidence pertence ao candidate final
[ ] observabilidade não persiste chain-of-thought
```

## 3. DoD C0 — Foundation

```text
[ ] C0.S0 inventário total com evidence
[ ] patterns/camadas/DI/error/event/state/resilience atuais do repo inventariados
[ ] authorities/bounded contexts congelados
[ ] Correlation/Entity/Relationship/Source/Evidence/Outcome contracts definidos/reutilizados
[ ] Platform/Workspace/Iframe contracts definidos/reutilizados
[ ] Expertise/Playbook contracts definidos/reutilizados
[ ] Decision Gate contract definido/reutilizado
[ ] Workflow/Task/Case lifecycle contracts definidos/reutilizados
[ ] EventEnvelope definido/reutilizado
[ ] persistence boundaries/ports definidos
[ ] architecture style validado
[ ] layer responsibilities validadas
[ ] dependency rules validadas
[ ] Pattern Decision Matrix validada contra padrões reais do repo
[ ] error/event/state-machine/persistence/frontend-state rules congeladas
[ ] resilience/idempotency rules congeladas
[ ] testing/migration patterns congelados
[ ] Abstraction Gate definido e aplicável
[ ] architectural exception/ADR process definido
[ ] versioning/error/retry/idempotency/freshness semantics definidos
[ ] contract + architecture conformance harness RED/GREEN reproduzível
[ ] nenhuma second authority material
[ ] FOUNDATION_FREEZE=PASS
```

C1 não inicia sem C0 completo.

## 4. DoD C1 — Platform/Context

```text
[ ] authorized route projection deriva do Core
[ ] CopilotBridge valida/revalida commands
[ ] Command + Handler/Adapter seguem padrão canônico sem handler por app
[ ] open app/route funcional
[ ] open entity quando contrato existir
[ ] URL arbitrária rejeitada
[ ] Workspace Context bounded/seguro
[ ] MFE adapter reutilizável
[ ] iframe PORTAL_ONLY funcional
[ ] iframe integration usa Adapter/ACL tipado, não DOM automation
[ ] bridge avançado possui security negatives quando usado
[ ] unknown app/iframe não exige patch central
[ ] F5/logout/stale context corretos
[ ] send/stream parity
```

## 5. DoD C2 — Intelligence Core

```text
[ ] nova sessão não depende de agent_id
[ ] legacy agent migration usa adapter/ACL/strangler com exit criteria
[ ] Expertise Catalog/Repository canônico somente se authority persistida for comprovada
[ ] retrieval positive/sibling/negative
[ ] unknown pack sem core patch
[ ] cross-domain expertise composition
[ ] Playbook applicability/versioning
[ ] Knowledge ACL não é ampliada por expertise/project
[ ] multimodal evidence possui provenance/confidence/limitations
[ ] extraction Strategy só existe se variação real justificar
[ ] FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION semanticamente distinguidos
[ ] injection negatives passam
[ ] shadow agent migration possui exit criteria
[ ] operational activity sem CoT
```

## 6. DoD C3 — Business Reads + Graph

```text
[ ] gates OpenAPI-first aplicáveis PASS
[ ] Business Capability Projection não duplica contrato técnico
[ ] known/sibling/unknown/metamorphic reads passam
[ ] args/schema/RBAC corretos
[ ] normalized outcome/evidence consistente
[ ] Graph usa EntityRef/RelationshipRef compartilhados
[ ] Graph segue Ports & Adapters; materialização/repository só existe com gap comprovado
[ ] traversal é permission-aware
[ ] authoritative vs inferred relationship rastreável
[ ] source data é buscado no owner
[ ] cycle/depth budget existe
[ ] sibling relation/entity não exige planner hardcode
```

## 7. DoD C4 — Governed Writes

```text
[ ] Decision Gate Engine usa Policy + State Machine conforme padrão
[ ] impact preview corresponde ao payload efetivo
[ ] arguments/evidence change invalida decisão quando material
[ ] backend revalida RBAC/policy
[ ] idempotency/concurrency tratadas
[ ] retry cego de write inexistente
[ ] write outcome verificado
[ ] ambiguous outcome não vira sucesso narrativo
[ ] audit/deep-link/evidence presentes
[ ] operational tools não dependem de agent ativo após cutover
[ ] soft handoff removido do fluxo alvo
[ ] iframe DOM write rejeitado
```

## 8. DoD C5 — Durable Work

```text
[ ] workflow persistence/checkpoint
[ ] workflow runtime usa Application orchestration + State Machine + Idempotency
[ ] wait_user
[ ] wait_approval
[ ] wait_event
[ ] timeout/cancel
[ ] DAG dependencies
[ ] parallel safe reads
[ ] retry/idempotency
[ ] Saga somente existe se houver múltiplos writes distribuídos + compensações reais
[ ] crash/restart sem duplicate write
[ ] Task usa workflow runtime, sem engine própria
[ ] Case usa refs/evidence compartilhados
[ ] Evidence Board não duplica evidence model
[ ] Room respeita source permissions
[ ] Inbox materializa work state sem virar workflow engine
[ ] reload/resume consistente
```

## 9. DoD C6 — Proactivity/Ecosystem/Learning

```text
[ ] Watch OBSERVE/ADVISE event-driven quando possível
[ ] Watch usa EventEnvelope/State Machine/dedupe canônicos
[ ] dedupe/cooldown/expiry/revalidation
[ ] AI-ready SDK/templates
[ ] readiness scanner baseado em facts
[ ] unknown app/pack onboarding sem hardcode
[ ] project preferences não concedem permission
[ ] Reference/Decision/Experience knowledge possuem provenance/version/owner
[ ] feedback não muda production behavior automaticamente
[ ] Expertise Studio usa Use Cases + State Machine + admin RBAC
[ ] Expertise Studio draft/review/eval/publish/rollback
[ ] admin RBAC/coverage
```

## 10. DoD C7 — Optimization/Autonomy/Rollout

```text
[ ] L5 OFF por default e allowlisted
[ ] Watch ACT sujeito a autonomy/Decision Gate
[ ] Simulation reproduzível e separada de Apply
[ ] Model Router introduz Strategy/Policy somente após baseline/variações reais
[ ] provider/model names não vazam para domain/application
[ ] provider incompatível é bloqueado
[ ] legacy agent-routing residual material = 0
[ ] compatibility adapters temporários removidos conforme exit criteria
[ ] canary/cohort/rollback
[ ] final R1–R11
[ ] accessibility/security/generalization
[ ] architecture conformance final
[ ] CP coverage sem UNMAPPED
```

## 11. Evals obrigatórios conforme escopo

```text
positive
sibling
negative/no-tool
unauthorized
TOCTOU
required missing
workspace follow-up
unknown app/provider/pack/iframe/relation
metamorphic rename
prompt/tool/context/document/event injection
Decision Gate
idempotency/replay
partial failure
persist/reload/restart
send/stream parity
layer/dependency conformance
port/adapter contracts
state transition rules
error translation/resilience
latency/cost
```

## 12. Critério de não conclusão

Estados bloqueantes quando materiais:

```text
PARTIAL
LEGACY_FALLBACK
SHADOW_ONLY sem exit criteria
INCONCLUSIVE
PENDING
TODO/FIXME/HACK/TEMPORARY
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
ARCHITECTURE_PATTERN_DRIFT
DEPENDENCY_RULE_VIOLATION
UNJUSTIFIED_ABSTRACTION
UNDOCUMENTED_ARCHITECTURAL_EXCEPTION
```

## 13. Evidence de release

```text
GIT_SHA
config/model/provider hashes
dataset/eval hashes
OpenAPI/Action Catalog hashes
expertise/playbook versions quando materiais
schema/migration versions
architecture layer/pattern conformance
ADR/exception refs quando houver
unit/integration/live results
security tests
residual scan
known limitations
rollout decision
```

## 14. Outcome final

O DoD não é “a IA respondeu”.

> O usuário autorizado atingiu o objetivo corretamente, com evidência, governança, continuidade e auditabilidade, usando os mesmos contratos da plataforma e a arquitetura canônica, sem criar foundations ou abstrações paralelas.