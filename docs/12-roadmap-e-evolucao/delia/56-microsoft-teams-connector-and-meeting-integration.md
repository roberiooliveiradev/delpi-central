# DÉLIA — Microsoft Teams Connector e Meeting Integration

**Status:** `TARGET` — thematic architecture/security/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**External connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)

## 1. Decisão de produto

Microsoft Teams é uma **provider capability family candidata** dentro da integração Microsoft 365. Não é segundo produto, segundo planner nem backend separado.

Target:

```text
Microsoft 365 connection
→ provider adapter(s)
→ semantic capabilities
→ DÉLIA planning/orchestration
```

A decomposição concreta em adapters, scopes, resources e lifecycles depende de C0 inventory e do contrato oficial vigente do provider.

## 2. Objetivos

Quando contrato, scopes e policy permitirem, a DÉLIA poderá:

- pesquisar/ler chats/canais autorizados;
- ler mensagens/replies;
- preparar/enviar mensagens governadas;
- consumir meeting metadata/artifacts autorizados;
- receber provider events/change notifications suportados;
- transformar conteúdo autorizado em SourceRef/EvidenceRef;
- relacionar conteúdo a EntityRef/Task/Case/Room/Watch;
- produzir candidate actions/ata viva a partir de reunião;
- expor no futuro uma surface dentro do Teams sem duplicar inteligência/authority.

## 3. Níveis de integração alvo

```text
N1 READ
N2 WRITE GOVERNADO
N3 MEETING ARTIFACTS + EVENTS
N4 TEAMS SURFACE
N5 LIVE/REALTIME ADVANCED
```

Essa sequência é product target, não prova de suporte atual do Microsoft Graph ou da DELPI.

## 4. Capability model

Exemplos conceituais:

```text
collaboration.teams.channel.messages.read
collaboration.teams.chat.messages.read
collaboration.teams.message.reply
collaboration.teams.message.send
collaboration.teams.meeting.read
collaboration.teams.meeting.transcript.read
collaboration.teams.meeting.recording.read
collaboration.teams.meeting.events.watch
```

C0/C3 congelam o catálogo real. Planner nunca contém Graph paths/permissions hardcoded.

## 5. Teams reads

Target:

```text
user/Work goal
→ semantic capability
→ authorized connection/resource scope
→ provider adapter
→ provider API
→ normalized Source/Evidence
→ synthesis
```

Source permission deve ser revalidada; cache/reference não concede acesso.

## 6. Teams writes

```text
read != draft != reply != send
```

Target:

```text
PREPARE content
→ target/resource confirmation when required
→ live AuthZ + provider scope + Policy/Decision
→ provider adapter
→ provider action
→ verified Outcome when contract allows
```

Nunca enviar mensagem apenas porque o modelo gerou texto.

## 7. Provider events e Watch

Somente quando o contrato oficial vigente suportar o cenário:

```text
provider event
→ authenticity/lifecycle validation
→ adapter normalization
→ EventEnvelope
→ dedupe/correlation
→ Watch/Inbox/Workflow/Case
```

Event payload não concede ACT authority.

## 8. Meeting integration

Preferir artifacts oficiais autorizados antes de raw media customizado.

```text
meeting artifact/event refs
→ provider adapter
→ Source/Evidence
→ authorized DELPI context
→ facts/topics
→ confirmed decisions
→ candidate actions
→ ata/Task/Case/Room
```

```text
transcript
!= DÉLIA summary
!= confirmed human decision
!= candidate action
!= executed action
```

## 9. Transcrições e gravações

Preservar source/provider refs, timestamps quando disponíveis, participant refs quando autorizados, freshness/version, permission scope, retention/policy refs e Evidence provenance.

Não copiar gravações inteiras para storage DÉLIA sem owner/purpose/policy explícitos.

## 10. Identidade de participantes

Provider participant identity e biometric candidate são fontes distintas.

Provider-resolved corporate identity tem precedência como source de participant association quando autoritativa; biometria é apenas supplemental candidate evidence e nunca sobrescreve silenciosamente identidade corporativa.

## 11. DÉLIA dentro do Teams

Uma futura surface Teams deve consumir os mesmos contratos canônicos da DÉLIA e não criar `teams-copilot-api`, planner, Policy ou Work runtime independentes.

Host context/provider metadata continua untrusted para autorização final.

## 12. Live meeting participation

Raw audio/video/realtime participation é advanced capability separada.

Antes de implementação, exigir evidence de valor e ADR cobrindo contrato oficial vigente, hosting/media requirements, latency/cost, consent, permissions, privacy/residency, failure mode e necessidade real versus transcript/artifact/event approach.

## 13. OAuth/scopes

Usar fundação definida em `55`. C0 deve mapear scopes mínimos e distinguir delegated/application/resource-specific patterns somente conforme provider contract vigente.

Não solicitar tenant-wide permission por conveniência.

## 14. Tenant/resource governance

Modelar explicitamente connection scope, resource scope, consent/admin state e capability availability. Provider scope != Core/domain permission.

Capability indisponível deve falhar closed, sem bypass.

## 15. Privacy e sharing

Private chat, restricted channel, transcript e recording preservam source ACL. Nada vira Case compartilhado/Organizational Knowledge automaticamente.

Promotion segue `Evidence → candidate → owner/review → eval → version → publish`.

## 16. Prompt injection e conteúdo externo

Messages/files/transcripts/provider metadata são untrusted external content. Não alteram Policy, RBAC, Decision Gates, retention, provider scopes ou system instructions.

## 17. State model

Preferir refs canônicas e provider-neutral. Não criar cópia persistente completa de teams/channels/messages sem lifecycle/owner comprovado.

Cache, se necessário, é connection/resource scoped, TTL/freshness-aware e não-authoritative.

## 18. Reliability

Distinguir connection_expired, scope_missing, resource_not_accessible, subscription_expired, notification_lost, throttled, provider_unavailable e artifact_not_available. Indisponibilidade não significa inexistência factual.

## 19. Observability

Quando runtime existir, medir reads/writes, latency/errors, verified outcomes, event auth/dedupe/reconciliation, throttling, scope failures e ausência de token/secret logging.

## 20. C0 inventory

Inventariar factual:

- existing Microsoft/Entra/Graph registrations/integrations;
- delegated/application/resource-specific patterns;
- tenant/admin ownership;
- callback/webhook ingress;
- secret/certificate storage;
- existing Teams apps/bots/tabs;
- meeting artifact access patterns;
- renewal infrastructure;
- app distribution/deep links;
- privacy/retention owners.

Unknown = `TO_INVENTORY`.

## 21. Phase mapping

### C0
Freeze Graph/tenant/scopes/resource-consent/webhook/privacy/app-distribution boundaries.

### C1
Somente bootstrap de callback/webhook/config quando C0 provar necessidade.

### C3
Provider-neutral Microsoft/Teams adapter foundation e capability projection quando justificados.

### C4
Governed reads/artifact refs autorizados.

### C5
Governed Teams writes/L4 ACT quando explicitamente autorizados e verificados.

### C6
Provider events e meeting artifacts podem alimentar Inbox/Task/Case/Watch; Watch não dispara ACT autonomamente.

### C7
Live/realtime participation e selected autonomous provider ACT somente com gates próprios; L5 OFF por default.

## 22. Acceptance outcomes

Quando implementado, provar:

```text
provider-neutral capability model
source/resource scope isolation
read/draft/send separation
write Outcome verification where possible
event authenticity/dedupe/reconciliation
artifact provenance
private-resource no leak
no provider token in LLM/MFE/log
no second planner/backend/authority
```

Sem mandatory evidence: `PENDING`/`INCONCLUSIVE`.

## 23. Provider facts

Este documento não congela capacidades, permissions ou limitations atuais do Microsoft Graph/Teams. Esses fatos devem ser verificados em documentação oficial recente durante C0/implementation e registrados como external evidence separada, não como authority arquitetural DELPI.

## 24. Regra final

```text
Teams/Graph = external source/action provider
DÉLIA = intelligence/context/Evidence/Policy/Decision/Work orchestration
Core = platform RBAC/governance authority
Domain APIs = DELPI business authority
provider tenant/scopes = external authorization boundary
```

Teams amplia alcance colaborativo; não cria nova authority.
