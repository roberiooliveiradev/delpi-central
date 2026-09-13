# 08 — Segurança, autonomia e auditoria

**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Invariante principal

```text
Copilot effective permissions ⊆ user effective permissions
```

External provider scope amplia somente o connector correspondente; não amplia Core RBAC/Domain API authorization.

## 2. Fluxo de autorização

```text
identity
→ Core effective permissions
→ authorized capabilities
→ optional external connection/scope
→ planner restrito
→ policy/risk/sensitivity
→ Decision Gate quando necessário
→ executor/adapter
→ final owner validation
→ outcome/audit
```

## 3. Trust boundaries

São dados não confiáveis para system/policy:

- user prompt;
- voice/transcript/image/video/screen;
- WorkspaceContext/device metadata;
- RAG/tool/API result;
- Expertise/Playbook content;
- iframe/Room/Event payload;
- public webpage/search result;
- email/message/file/calendar item externo;
- external attachment;
- provider webhook/event;
- biometric/Human Observation result.

Nenhuma dessas fontes altera permission, system instruction, Decision Gate, provider scope, retention ou safety boundary.

## 4. Autonomia

```text
L0 explain
L1 navigate
L2 read/analyze
L3 prepare change
L4 governed execute
L5 allowlisted automatic execute within explicit limits
```

L5 OFF por default. L5 não concede OT nem external write irrestrito.

## 5. Sensitivity/risk

Classes podem incluir:

```text
read
write
sensitive_write
admin
destructive
external_communication
financial
personal_data
biometric_sensitive
media_capture
external_personal_source
provider_credential
industrial_safety
```

## 6. Decision Gates

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

External send/update pode exigir target/payload preview, connection/scope state e expiry/revalidation.

## 7. TOCTOU

Antes de execute/resume/Watch ACT revalidar, conforme aplicável:

- Core permission;
- Domain entity state;
- policy;
- evidence freshness;
- media/biometric state;
- external connection active state;
- provider scope;
- recipient/target constraints;
- provider availability;
- industrial preconditions.

## 8. Capability minimization

Planner recebe somente candidates autorizados/relevantes. Expertise, context, web result ou provider message não concedem capability.

## 9. Internet egress security

Public research usa boundary de egress seguro.

Regras:

- somente destinos/protocolos permitidos;
- protected/internal destinations bloqueados;
- redirect revalidado;
- request/response size/time/concurrency limits;
- download/content policy;
- TLS e provider policy;
- minimizar/redigir contexto sensível enviado para fora;
- nenhuma URL de LLM vai direto a client irrestrito.

Browser automation não é default e, se futura, permanece sandboxed/bounded.

## 10. OAuth / External Connection security

Connection types:

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Obrigatório:

- official provider auth flow;
- least privilege scopes;
- callback/session integrity validation;
- consent/scope disclosure;
- refresh/revoke/reconnect;
- connection owner explicit;
- scope increase requer nova autorização adequada;
- kill switch.

Provider scope != Core permission.

## 11. Provider credentials

Access/refresh tokens, client secrets e provider credentials:

- ficam em approved secret/vault boundary;
- Copilot DB prefere `secretRef`;
- nunca chegam ao LLM;
- nunca retornam ao MFE;
- nunca entram em ordinary logs/telemetry;
- são rotacionáveis/revogáveis;
- separados por environment/connection.

## 12. Personal versus organizational data

```text
personal/user-delegated source
-X→ another user's search
-X→ organizational Knowledge automatically
-X→ Room/Case sharing automatically
```

Promotion/sharing exige ação/policy explícita.

## 13. External reads

Read capability valida connection/scope e preserva SourceRef/Evidence/freshness. Cache não vira authority e não pode vazar entre owners.

## 14. External writes / communication

```text
draft != send
read != write
```

External write exige, conforme risk:

- current connection/scope;
- policy/Decision Gate;
- target/payload preview;
- idempotency/duplicate protection;
- verified provider outcome;
- audit.

External content nunca dispara write diretamente.

## 15. Provider events/webhooks

Obrigatório:

- authenticity/contract validation;
- normalize to EventEnvelope;
- dedupe/correlation;
- renewal/expiry handling;
- missed-event reconciliation;
- permission/connection revocation handling;
- event payload treated as untrusted.

Webhook não é um alternate executor.

## 16. External prompt injection

Web/email/message/file/event content não pode:

- pedir/receber token/secret;
- mudar policy/system;
- ampliar permission/scope;
- conectar provider;
- enviar mensagem;
- alterar retention;
- publicar Knowledge automaticamente.

## 17. External attachment safety

```text
provider resource
→ approved download boundary
→ type/size/content policy
→ MediaRef/SourceRef
→ extraction
→ Evidence
```

Conteúdo ativo não é executado como parte da análise.

## 18. Knowledge security

Knowledge scopes respeitam source ACL. External/personal source só vira durable Knowledge por candidate/review/eval/publish conforme owner/privacy/freshness/licensing.

## 19. Business Graph / Case / Room security

Graph/Case/Room podem referenciar external SourceRefs, mas membership/relationship não concede acesso ao source original. Revogação deve ser respeitada.

## 20. Durable Workflow / Watch security

Resume/Watch revalida Core/domain/policy/external connection/scopes. External event duplicado não duplica send/write.

ACT externo em C7 exige allowlist/limits/kill switch e verified outcome.

## 21. Iframe security

Origin/source/session/schema validation, bounded payload, no JWT/refresh token, visual command não vira Business Action.

## 22. Biometric/Human Observation security

Biometric match é candidate identity, não auth/RBAC. Templates protegidos/revogáveis. Human Observation fica em evidência observável de processo, sem inferências psicológicas/sensíveis ou decisão trabalhista automática.

## 23. Industrial/OT boundary

Copilot não é safety controller. Free-form LLM → machine actuation permanece bloqueado sem programa/gate industrial separado.

## 24. Auditoria

Eventos conceituais adicionais:

```text
copilot.web.research_started|completed|blocked
copilot.external.connection_created|reauth_required|revoked
copilot.external.read_completed|failed
copilot.external.action_requested|completed|failed
copilot.external.subscription_created|renewed|stale
copilot.external.event_received|rejected|deduped
copilot.external.knowledge_candidate_created
```

Audit registra refs/decisions/outcomes, não credentials nem full sensitive content por default.

## 25. Dados proibidos em logs/state comum

- JWT/refresh tokens;
- provider access/refresh tokens;
- passwords/API keys/client secrets;
- biometric templates;
- chain-of-thought;
- raw sensitive payload sem necessidade;
- raw media fora do storage/policy apropriado.

## 26. Emergency stop

Deve ser possível desabilitar separadamente:

- Copilot writes;
- provider/action;
- Internet Research;
- web fetch/browser automation;
- external connection específica;
- external writes/outbound messaging;
- webhook ingestion;
- background sync/watch;
- voice/video/biometric capture;
- OT integration.

Kill switch é deterministic/admin-owned, não prompt-controlled.

## 27. Success criteria

Security está correta quando o Copilot continua útil com sources internas e externas, mas nenhum prompt, webpage, email, message, file, webhook, biometric result ou device context consegue elevar permissions/scopes, vazar credentials/dados entre usuários, enviar conteúdo sem governance, publicar conhecimento automaticamente ou ultrapassar safety boundaries.
