# 14 — Definition of Done

## 1. Objetivo

Evitar fechamento prematuro por demo funcional. Cada fase precisa provar foundation, wiring, segurança, generalização e evidence no candidate vigente.

## 2. DoD global

```text
[ ] authorities possuem owner claro
[ ] shared primitives não possuem duplicação material
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
[ ] authorities/bounded contexts congelados
[ ] Correlation/Entity/Relationship/Source/Evidence/Outcome contracts definidos/reutilizados
[ ] Platform/Workspace/Iframe contracts definidos/reutilizados
[ ] Expertise/Playbook contracts definidos/reutilizados
[ ] Decision Gate contract definido/reutilizado
[ ] Workflow/Task/Case lifecycle contracts definidos/reutilizados
[ ] EventEnvelope definido/reutilizado
[ ] persistence boundaries/ports definidos
[ ] versioning/error/retry/idempotency/freshness semantics definidos
[ ] contract harness RED/GREEN reproduzível
[ ] nenhuma second authority material
[ ] FOUNDATION_FREEZE=PASS
```

C1 não inicia sem C0 completo.

## 4. DoD C1 — Platform/Context

```text
[ ] authorized route projection deriva do Core
[ ] CopilotBridge valida/revalida commands
[ ] open app/route funcional
[ ] open entity quando contrato existir
[ ] URL arbitrária rejeitada
[ ] Workspace Context bounded/seguro
[ ] MFE adapter reutilizável
[ ] iframe PORTAL_ONLY funcional
[ ] bridge avançado possui security negatives quando usado
[ ] unknown app/iframe não exige patch central
[ ] F5/logout/stale context corretos
[ ] send/stream parity
```

## 5. DoD C2 — Intelligence Core

```text
[ ] nova sessão não depende de agent_id
[ ] Expertise Catalog/Repository canônico
[ ] retrieval positive/sibling/negative
[ ] unknown pack sem core patch
[ ] cross-domain expertise composition
[ ] Playbook applicability/versioning
[ ] Knowledge ACL não é ampliada por expertise/project
[ ] multimodal evidence possui provenance/confidence/limitations
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
[ ] traversal é permission-aware
[ ] authoritative vs inferred relationship rastreável
[ ] source data é buscado no owner
[ ] cycle/depth budget existe
[ ] sibling relation/entity não exige planner hardcode
```

## 7. DoD C4 — Governed Writes

```text
[ ] Decision Gate Engine implementa níveis canônicos
[ ] impact preview corresponde ao payload efetivo
[ ] arguments/evidence change invalida decisão quando material
[ ] backend revalida RBAC/policy
[ ] idempotency/concurrency tratadas
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
[ ] wait_user
[ ] wait_approval
[ ] wait_event
[ ] timeout/cancel
[ ] DAG dependencies
[ ] parallel safe reads
[ ] retry/idempotency
[ ] crash/restart sem duplicate write
[ ] Task usa workflow runtime, sem engine própria
[ ] Case usa refs/evidence compartilhados
[ ] Evidence Board não duplica evidence model
[ ] Room respeita source permissions
[ ] Inbox materializa work state sem disparar write por leitura
[ ] reload/resume consistente
```

## 9. DoD C6 — Proactivity/Ecosystem/Learning

```text
[ ] Watch OBSERVE/ADVISE event-driven quando possível
[ ] dedupe/cooldown/expiry/revalidation
[ ] AI-ready SDK/templates
[ ] readiness scanner baseado em facts
[ ] unknown app/pack onboarding sem hardcode
[ ] project preferences não concedem permission
[ ] Reference/Decision/Experience knowledge possuem provenance/version/owner
[ ] feedback não muda production behavior automaticamente
[ ] Expertise Studio draft/review/eval/publish/rollback
[ ] admin RBAC/coverage
```

## 10. DoD C7 — Optimization/Autonomy/Rollout

```text
[ ] L5 OFF por default e allowlisted
[ ] Watch ACT sujeito a autonomy/Decision Gate
[ ] Simulation reproduzível e separada de Apply
[ ] Model Router baseado em baseline e data policy
[ ] provider incompatível é bloqueado
[ ] legacy agent-routing residual material = 0
[ ] canary/cohort/rollback
[ ] final R1–R11
[ ] accessibility/security/generalization
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
```

## 13. Evidence de release

```text
GIT_SHA
config/model/provider hashes
dataset/eval hashes
OpenAPI/Action Catalog hashes
expertise/playbook versions quando materiais
schema/migration versions
unit/integration/live results
security tests
residual scan
known limitations
rollout decision
```

## 14. Outcome final

O DoD não é “a IA respondeu”.

> O usuário autorizado atingiu o objetivo corretamente, com evidência, governança, continuidade e auditabilidade, usando os mesmos contratos da plataforma sem criar foundations paralelas.