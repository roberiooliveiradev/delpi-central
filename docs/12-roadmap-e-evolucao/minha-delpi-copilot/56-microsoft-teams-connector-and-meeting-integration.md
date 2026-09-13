# Minha DELPI Copilot — Microsoft Teams Connector e Meeting Integration

**Status:** thematic architecture/security/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**External connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)

## 1. Decisão de produto

Microsoft Teams é uma **capability family de primeira classe do conector Microsoft 365**, não um segundo Copilot e não um backend separado.

```text
Microsoft 365 Connection
        │
        ├─ Outlook / Mail
        ├─ Calendar
        ├─ OneDrive / SharePoint
        └─ Teams
             ├─ teams/channels
             ├─ chats/messages
             ├─ meetings
             ├─ transcripts/recordings
             ├─ notifications/events
             └─ future in-Teams Copilot surface
```

O mesmo `Microsoft365Adapter` pode ser dividido internamente em adapters menores por responsabilidade, mas o planner trabalha com **capabilities semânticas**, nunca com endpoints Graph hardcoded.

## 2. Objetivos

O Copilot deve poder, conforme scopes/policy aprovados:

- pesquisar e ler chats/canais autorizados;
- ler mensagens e respostas;
- buscar contexto de equipes/canais;
- preparar e enviar mensagens governadas;
- criar/referenciar reuniões online quando necessário;
- consumir transcrições e gravações autorizadas;
- receber change notifications de mensagens, canais, reuniões, transcrições e gravações quando suportadas;
- transformar conteúdo do Teams em `SourceRef/EvidenceRef`;
- relacionar conteúdo do Teams a `EntityRef`, Task, Case, Room, Watch e Meeting;
- gerar ata viva e ações candidatas a partir de reuniões Teams;
- futuramente expor o mesmo Copilot dentro do Teams como app/tab/bot, sem duplicar runtime.

## 3. Cinco níveis de integração

A evolução alvo é progressiva:

```text
NÍVEL 1 — READ
chats / canais / mensagens / replies / contexto

NÍVEL 2 — WRITE GOVERNADO
rascunho / responder / enviar mensagem

NÍVEL 3 — MEETING ARTIFACTS + EVENTS
reuniões / transcrições / gravações / change notifications

NÍVEL 4 — COPILOT DENTRO DO TEAMS
app/tab/bot como nova surface do mesmo Copilot

NÍVEL 5 — LIVE MEETING INTELLIGENCE AVANÇADA
participação em tempo real com mídia/realtime somente se evidence justificar
```

Níveis 1–3 devem ser priorizados antes de qualquer arquitetura de live raw-media participation.

## 4. Capability model

Exemplos semânticos:

```text
collaboration.teams.list
collaboration.teams.channel.list
collaboration.teams.channel.messages.read
collaboration.teams.chat.messages.read
collaboration.teams.message.reply
collaboration.teams.message.send
collaboration.teams.meeting.read
collaboration.teams.meeting.transcript.read
collaboration.teams.meeting.recording.read
collaboration.teams.meeting.events.watch
```

Esses nomes são exemplos conceituais. C0/C3 congelam o catálogo real sem acoplar planner a Microsoft Graph paths.

## 5. Teams reads

Fluxo alvo:

```text
user goal
→ semantic Teams capability
→ authorized Microsoft 365 connection
→ Microsoft365/Teams adapter
→ Microsoft Graph
→ normalized ExternalResource/SourceRef
→ EvidenceRef + freshness + permission scope
→ synthesis
```

Casos de uso:

- resumir conversa de canal;
- buscar mensagens sobre cliente/projeto/OP;
- recuperar contexto de discussão anterior;
- localizar decisão registrada em chat;
- correlacionar conversa com dados DELPI;
- alimentar Case/Evidence Board sem copiar mailbox/channel inteiro para o Copilot.

## 6. Teams writes

Writes permanecem separados de reads.

```text
read
!=
draft
!=
reply
!=
send
```

Fluxo preferido:

```text
Copilot prepara conteúdo
→ preview/target/channel/chat
→ user review when material
→ Policy/Decision Gate
→ Teams adapter
→ Microsoft Graph
→ verified external outcome
```

Nunca enviar mensagem apenas porque o modelo gerou texto.

## 7. Teams change notifications e Watch

Quando Microsoft Graph suportar o recurso/scenario aprovado:

```text
Graph change notification
→ webhook authenticity/lifecycle validation
→ Teams adapter
→ EventEnvelope
→ dedupe/correlation
→ Watch / Inbox / Workflow / Case
```

Casos:

- nova mensagem em canal;
- mensagem criada/alterada/excluída;
- alteração de team/channel quando material;
- reunião iniciada/finalizada/roster atualizado quando contract suportar;
- transcrição/gravação ficou disponível.

Subscription expiry, renewal, lifecycle notification, duplicate delivery, out-of-order e reconciliation seguem `55`.

## 8. Meeting integration

A integração de reuniões Teams deve priorizar **artifacts oficiais da reunião** antes de capturar raw media por conta própria.

Fluxo alvo:

```text
Teams online meeting
→ transcript/recording/event refs autorizados
→ Teams adapter
→ MeetingSession / SourceRef / EvidenceRef
→ participantes/assuntos/fatos
→ DELPI APIs / Business Graph / Knowledge
→ decisões/pending topics
→ candidate actions
→ ata viva
→ Task / Case / Room / Watch
```

Semântica obrigatória:

```text
Teams transcript
!=
Copilot summary
!=
confirmed human decision
!=
candidate action
!=
executed action
```

## 9. Transcrições e gravações

Transcrição e gravação têm lifecycles/permissões diferentes.

O Copilot deve preservar:

- meeting resource ref;
- source provider;
- timestamps/time ranges quando disponíveis;
- participant/speaker refs quando autorizados;
- transcript freshness/version;
- recording/transcript permission scope;
- retention/policy refs;
- Evidence provenance.

Não duplicar gravação inteira para storage Copilot sem necessidade/policy explícita.

## 10. Identidade de participantes

Teams participant identity, invitation/roster e biometric identity são fontes distintas.

Preferência:

```text
Teams/Graph participant identity
→ primary meeting participant ref when authoritative

biometric face/speaker candidate
→ supplemental identity evidence only when enabled
```

Nunca usar biometria para sobrescrever silenciosamente uma identidade corporativa resolvida pelo tenant/provider.

## 11. Copilot dentro do Teams

É permitido evoluir para uma surface Teams do mesmo produto.

Target:

```text
Microsoft Teams
→ Minha DELPI Copilot app/tab/bot
→ authenticated/approved host context
→ same Copilot API
→ same Core/RBAC/Policy/Evidence/Workflow
```

Possíveis experiências:

- app pessoal do Copilot;
- tab em contexto suportado;
- bot/conversational entry;
- acesso a Inbox/Tasks/Cases;
- deep link de volta para Minha DELPI.

Proibido criar `teams-copilot-api` ou um planner independente apenas para Teams.

## 12. Live meeting participation

Participação ao vivo com áudio/vídeo/raw media é **advanced capability**, separada do conector Teams básico.

Antes de implementar, exigir evidence de valor e ADR cobrindo:

- modelo oficial suportado pela Microsoft no momento da implementação;
- hosting/media requirements;
- latency/concurrency/cost;
- consent/recording indicators;
- transcript versus raw-media necessity;
- tenant/admin permissions;
- data residency/privacy;
- failure/degraded mode;
- whether transcript/change-notification approach already solves the use case.

Default:

```text
Graph/API artifacts + change notifications
BEFORE
raw realtime meeting media bot
```

## 13. OAuth/scopes

Teams usa a mesma fundação Microsoft 365 definida em `55`.

C0/C3 devem mapear scopes mínimos por capability, distinguindo:

```text
read messages
send messages
read meetings
read transcripts
read recordings
subscriptions/change notifications
application permissions
resource-specific consent when applicable
```

Não solicitar tenant-wide permission por conveniência quando delegated/resource-specific scope atender o caso.

## 14. Resource-specific and tenant governance

Alguns cenários do Teams podem depender de consentimento específico de recurso, permissões de aplicação ou configuração do tenant.

O Copilot deve modelar explicitamente:

```text
connection scope
resource scope
consent/admin state
capability availability
```

Uma capability indisponível por policy/tenant deve aparecer como indisponível, não como erro genérico ou tentativa de bypass.

## 15. Privacy e sharing

Mensagens privadas, canais restritos, transcrições e gravações mantêm as regras de acesso da fonte.

```text
private Teams chat
-X→ shared Knowledge automaticamente

restricted channel message
-X→ Case visível a usuários sem acesso à fonte

meeting transcript
-X→ organizational truth automática
```

Promotion/sharing segue `55` e `40`.

## 16. Prompt injection e conteúdo externo

Teams messages/files/transcripts são `UNTRUSTED_EXTERNAL_CONTENT` para system/policy.

Não podem:

- alterar policy;
- solicitar provider tokens;
- conceder Core permission;
- disparar write automaticamente;
- publicar Knowledge automaticamente;
- modificar retention;
- ampliar Teams scopes.

## 17. State model

Preferir referências:

```text
ExternalConnectionRef
SourceRef / ExternalResourceRef
meetingRef
teamRef/channelRef/chatRef/messageRef
subscriptionRef
EvidenceRef
```

Evitar cópia persistente completa de teams/channels/messages.

Quando cache for necessário:

- connection/resource scoped;
- TTL/freshness;
- invalidável;
- no cross-user leak;
- not authority.

## 18. Reliability

Tratar explicitamente:

```text
connection_expired
scope_missing
resource_not_accessible
subscription_expired
notification_lost
throttled
provider_unavailable
transcript_not_available
recording_not_available
meeting_not_started
meeting_ended
```

Nenhum desses estados deve ser narrado como “não existe” quando o problema é acesso/disponibilidade.

## 19. Observability

Métricas mínimas quando o connector entrar em runtime:

- Teams read success/error/latency;
- message send success/error/verified outcome;
- subscription renew success/error;
- webhook auth failures;
- duplicate/out-of-order rate;
- reconciliation lag;
- transcript availability latency;
- meeting artifact processing latency;
- throttling/rate-limit incidents;
- permission/scope failures;
- no secret/token logging.

## 20. C0 inventory

C0.S0 deve inventariar factual:

- Microsoft Entra/Azure app registrations existentes;
- Microsoft Graph integrations existentes no repo/infra;
- delegated/application/resource-specific consent patterns;
- tenant/admin ownership;
- Teams policies relevantes;
- Graph callback/webhook ingress patterns;
- secret/certificate storage;
- existing Teams bots/apps/tabs, se houver;
- meeting/transcript/recording access patterns;
- scheduler/subscription renewal infrastructure;
- deep-link/app-distribution patterns;
- privacy/retention owners para chats/transcripts/recordings.

Unknown = `NOT_PROVEN`.

## 21. Phase mapping

### C0

Inventário e freeze de Graph/tenant/scopes/resource consent/webhook/privacy/app-distribution boundaries.

### C1

Nenhuma feature Teams obrigatória; somente bootstrap/callback/webhook foundation se C0 contract exigir.

### C3

Microsoft 365/Teams adapter foundation e capability model provider-neutral.

### C4

Teams reads: teams/channels/chats/messages/meeting metadata/transcript refs quando autorizados.

### C5

Teams writes governados: reply/send e demais ações aprovadas, sempre com verified outcome.

### C6

Change notifications, Meeting artifacts → ata/Task/Case/Watch, e opcional Teams app/tab/bot como surface do mesmo Copilot após architecture gate.

### C7

Live/realtime meeting participation somente se evidence justificar e após ADR/gates próprios.

## 22. Acceptance outcomes

```text
TEAMS_PROVIDER_NEUTRAL_CAPABILITIES = PASS
TEAMS_READ_SCOPE_ISOLATION = PASS
TEAMS_DRAFT_SEND_SEPARATION = PASS
TEAMS_WRITE_VERIFIED_OUTCOME = PASS
TEAMS_EVENT_AUTH_DEDUPE_RECONCILIATION = PASS
TEAMS_TRANSCRIPT_PROVENANCE = PASS
TEAMS_PRIVATE_RESOURCE_NO_LEAK = PASS
TEAMS_MEETING_ARTIFACT_TO_EVIDENCE = PASS
TEAMS_APP_SAME_COPILOT_RUNTIME = PASS when surface exists
TEAMS_RAW_REALTIME_NOT_REQUIRED_FOR_BASE_CONNECTOR = PASS
NO_TEAMS_TOKEN_TO_LLM_MFE_LOG = PASS
```

## 23. Current verified planning facts — September 2026

A documentação oficial atual do Microsoft Graph confirma, entre outros pontos:

- APIs de Teams para listar mensagens em chat/canal, listar replies e enviar/responder mensagens;
- change notifications para mensagens em canais/chats;
- change notifications para teams/channels;
- notificações de eventos de online meeting como call started/call ended/roster updated em cenários suportados;
- change notifications para disponibilidade de transcrições e gravações de reuniões online em cenários suportados;
- permissões variam entre delegated, application e, em alguns cenários, resource-specific consent.

Esses fatos devem ser **revalidados contra Microsoft Learn/Graph no momento da implementação**, pois permissões, limitações e modelos recomendados podem mudar.

## 24. Regra final

Teams amplia o alcance colaborativo do Copilot, mas não cria nova authority:

```text
Teams/Graph = source/action provider
Copilot = orchestration/intelligence/work
Core = platform RBAC authority
Microsoft tenant/scopes = provider authorization boundary
Domain APIs = DELPI business authority
```

O objetivo é que conversas e reuniões do Teams deixem de ser informação isolada e possam, quando autorizado, participar do mesmo ciclo de Evidence → Decision → Task/Case/Watch → Governed Learning da Minha DELPI.