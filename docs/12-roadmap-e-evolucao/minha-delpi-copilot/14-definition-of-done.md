# 14 — Definition of Done

**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Objetivo

Uma fase só fecha com comportamento, integração, segurança, privacidade, generalização, arquitetura e independência do Minha DELPI Chat provados no candidate vigente.

## 2. DoD global

```text
[ ] Copilot API/MFE/deploy/persistence próprios
[ ] zero runtime dependency no Chat
[ ] Core continua authority de apps/routes/RBAC
[ ] Domain APIs continuam authority de business rules/data
[ ] provider externo continua authority de seus recursos
[ ] permissions/scopes nunca são ampliados por prompt/context/media/external content
[ ] OpenAPI/capability contracts governam Business Actions
[ ] Internet Research preserva provenance/freshness
[ ] External Connectors usam provider-neutral adapters
[ ] provider credentials ficam fora de LLM/MFE/logs
[ ] personal external source não vira organizational source implicitamente
[ ] read != write e draft != send
[ ] external write possui governance/outcome verification
[ ] external events usam EventEnvelope/dedupe/reconciliation
[ ] external learning publica somente via governance
[ ] arquitetura segue 49
[ ] durable resume não duplica write/send
[ ] chain-of-thought não é persistida/exposta
[ ] media/biometric privacy boundaries respeitados
[ ] Copilot não vira industrial safety controller
```

## 3. DoD C0 — Foundation Freeze

```text
[ ] Portal/Core/Gateway/Infra/MFE/API inventory com evidence
[ ] Chat reference-only inventory
[ ] media/device/biometric/OT inventory
[ ] outbound egress/search/fetch inventory
[ ] OAuth/callback/secret-store inventory
[ ] Microsoft/Google/WhatsApp Business/other connector inventory
[ ] webhook/subscription/scheduler/reconciliation inventory
[ ] personal vs org source/privacy owner inventory
[ ] provider terms/compliance owner inventory
[ ] standalone boundary/names/storage ownership congelados
[ ] shared primitives/refs definidos sem duplicação
[ ] architecture/patterns/Abstraction Gate congelados
[ ] safe external egress boundary congelado
[ ] OAuth connection lifecycle/ownership/scopes congelados
[ ] provider secret boundary congelado
[ ] external read/write semantics congeladas
[ ] external event lifecycle congelado
[ ] external learning/promotion boundary congelado
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
[ ] Portal full-page/global host contract
[ ] responsive/accessibility baseline
[ ] media/biometric/external capabilities não ativam implicitamente
[ ] provider credentials não aparecem no browser
[ ] Chat offline não quebra bootstrap
[ ] independent rollback/shutdown
```

## 5. DoD C2 — Context + Platform Commands

```text
[ ] WorkspaceContext bounded/sanitized
[ ] EntityRef/SourceRef usados sem credential/permission truth
[ ] device/biometric/external context não concede authorization
[ ] authorized navigation + arbitrary target rejection
[ ] user-switch/logout limpa state local
[ ] iframe bridge seguro
[ ] full-page/panel policy parity
```

## 6. DoD C3 — Intelligence + Multimodal/Biometric/External Foundations

```text
[ ] conversation/runtime próprios
[ ] OpenAPI Action Catalog próprio
[ ] planner structured/provider-neutral
[ ] Expertise/Knowledge ACL/provenance
[ ] multimodal/biometric gates aplicáveis passam
[ ] Internet Research usa search + safe fetch + Evidence
[ ] external web content tratado como untrusted
[ ] external destination validation/limits aplicados
[ ] OAuth connection lifecycle implementado por contracts quando em escopo
[ ] least privilege scopes
[ ] provider token/secret isolado
[ ] unknown connector não exige planner patch
[ ] source freshness/conflict semantics
[ ] no Chat runtime dependency
```

## 7. DoD C4 — Business + External Reads + Graph

```text
[ ] business reads known/sibling/unknown/metamorphic
[ ] external read exige active connection/scope
[ ] no cross-user connection/data leak
[ ] read não implica modify/send
[ ] provider unavailable vs no-data distinguishable
[ ] external attachments passam por safe ingest
[ ] SourceRef/EvidenceRef sem credential
[ ] revoked connection blocks future reads
[ ] Graph não replica domain/external master data
[ ] internal/external authority/freshness explícita
```

## 8. DoD C5 — Governed Business/External Writes + Durable Foundation

```text
[ ] Decision Gate/revalidation/idempotency/outcome verification
[ ] draft != send
[ ] generated content never sends implicitly
[ ] write scope revalidated immediately before external action
[ ] target/payload preview when policy requires
[ ] provider timeout does not cause blind duplicate send
[ ] verified external Outcome/Evidence/Audit
[ ] Workflow checkpoint/waits/restart without duplicate business/external write
```

## 9. DoD C6 — Product Work + External Events/Learning + Meeting/Frontline

```text
[ ] Task/Case/Room/Inbox preserve source ACL
[ ] external source sharing is explicit
[ ] provider webhook/event authenticity validated
[ ] duplicate/out-of-order events handled
[ ] subscription renewal/expiry/reconciliation works
[ ] revoked connection/source reflected in projections
[ ] Watch ACT remains blocked in C6
[ ] external Knowledge starts as candidate when durable
[ ] personal source not auto-promoted to organizational Knowledge
[ ] freshness/privacy/licensing checked for publication
[ ] Meeting/Frontline preserve same external-source governance
[ ] biometric/Human Observation rules still pass
```

## 10. DoD C7 — External Proactivity + Advanced Autonomy/Rollout

```text
[ ] L5 OFF by default
[ ] external ACT explicitly allowlisted/scoped/limited
[ ] provider scope/connection revalidated at execution
[ ] kill switches for research/provider/connection/write/event sync
[ ] background/proactive external work respects privacy/cost/rate limits
[ ] browser fallback, if any, is sandboxed and not alternate ungoverned write path
[ ] provider terms/scopes revalidated at rollout
[ ] progressive rollout/canary/rollback
[ ] final Chat-offline independence
[ ] OT physical actuation still separately governed
```

## 11. Testes transversais obrigatórios

```text
positive/sibling/negative
unauthorized/TOCTOU
unknown/metamorphic
prompt/tool/document/media/external injection
Decision Gate
idempotency/replay
partial/ambiguous outcome
persist/reload/restart
layer/dependency conformance
provider-neutral connector generalization
connection/user isolation
credential leakage negative
safe external egress
OAuth lifecycle
webhook renewal/reconciliation
external learning promotion
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
HIDDEN_MEDIA_CAPTURE
SHARED_DEVICE_STATE_LEAK
BIOMETRIC_PERMISSION_ELEVATION
SENSITIVE_PERSON_INFERENCE
UNSAFE_WEB_EGRESS
EXTERNAL_PROMPT_INJECTION_POLICY_CHANGE
OAUTH_SCOPE_ESCALATION
PROVIDER_TOKEN_LEAK
CROSS_USER_EXTERNAL_DATA_LEAK
EXTERNAL_WRITE_WITHOUT_GATE
DRAFT_SENT_IMPLICITLY
UNVERIFIED_EXTERNAL_SUCCESS
INVALID_PROVIDER_EVENT_ACCEPTED
MISSED_EVENT_WITHOUT_RECONCILIATION
PERSONAL_SOURCE_AUTO_PROMOTED_TO_ORG_KNOWLEDGE
UNSUPPORTED_WHATSAPP_SESSION_AUTOMATION
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 13. Evidence de release

Registrar candidate SHA, versions/hashes, migrations, contracts, model/provider/policy versions, connection/scope policy, egress policy, tests/evals, security/privacy results, rollback e limitações conhecidas.

## 14. Resultado final

> O Copilot só está Done quando funciona como aplicação standalone, multimodal e conectada de forma governada às fontes internas e externas, sem herdar runtime do Chat, sem duplicar authorities, sem vazar credentials/dados pessoais, sem enviar comunicação implicitamente e sem ultrapassar limites de segurança industrial.
