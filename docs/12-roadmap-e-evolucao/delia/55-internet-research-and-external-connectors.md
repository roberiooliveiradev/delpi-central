# DÉLIA — Internet Research e External Connectors

**Status:** `TARGET` — thematic architecture/security/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)

## 1. Decisão de produto

A DÉLIA deve poder buscar informação além da DELPI por dois caminhos complementares:

```text
PUBLIC INTERNET
→ pesquisa/fetch de fontes públicas

CONNECTED SOURCES
→ contas, caixas, canais e serviços explicitamente conectados
```

Famílias candidatas incluem Microsoft 365, Google Workspace, WhatsApp Business, Slack, GitHub, CRMs/service desks e outros providers futuros, **somente** quando contrato oficial, owner, autorização e policy forem comprovados.

O desenho é provider-neutral. O planner trabalha com capabilities semânticas, nunca com branches de provider.

## 2. Quatro operações diferentes

```text
SEARCH → localizar informação pública
READ   → ler recurso autorizado de uma conexão
ACT    → criar/alterar/enviar recurso externo
LEARN  → promover conhecimento externo por ciclo governado
```

Cada operação tem authority, risco e lifecycle próprios.

## 3. Internet Research

Target:

```text
user/Work goal
→ research need detection
→ provider-neutral search capability
→ safe fetch boundary
→ extraction/normalization
→ SourceRef/EvidenceRef
→ freshness/relevance assessment
→ grounded synthesis
→ citations/sources
```

Pesquisa na web é retrieval, não authority. Conteúdo externo é untrusted data e nunca altera system instructions, Policy, RBAC ou Decision Gates.

## 4. Pesquisa automática versus explícita

A DÉLIA pode decidir pesquisar fontes públicas quando atualidade ou cobertura externa forem necessárias e policy permitir egress.

Não pesquisar quando:

- fonte corporativa canônica já resolve a necessidade;
- policy proíbe egress;
- seria necessário enviar segredo ou contexto sensível desnecessário.

## 5. Safe Web Fetch / Egress Boundary

Nenhuma URL sugerida por modelo deve ser buscada por client irrestrito. O boundary deve aplicar scheme allowlist, DNS/IP/private-network protections, redirect revalidation, size/time/content limits, TLS, rate/concurrency, download/malware policy quando aplicável e minimização/redaction do contexto enviado.

## 6. Browser automation

Preferência:

```text
official API
→ native integration
→ deterministic function/script
→ governed RPA
→ governed computer-use
→ Human Task
```

Browser/computer-use é fallback governado, não integração padrão. Credenciais nunca entram em prompt/plaintext e actions materiais continuam sob AuthZ/Policy/Decision.

## 7. External Connector Architecture

Target:

```text
connection intent
→ official authorization flow
→ callback/verification
→ connection lifecycle
→ protected credential reference
→ provider adapter
→ normalized semantic capabilities
→ DÉLIA planning/orchestration
```

Tokens/secrets nunca entram no contexto do LLM.

## 8. Connection ownership

Classes candidatas:

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

C0 deve provar quais existem, seus owners e lifecycle. Conexão pessoal nunca vira organizacional por conveniência.

## 9. OAuth e least privilege

Usar fluxo oficial do provider e menor scope necessário. `read != write`; `draft != send`.

Provider scope é requisito de acesso externo, não autoridade final da DELPI. Core/domain permissions e Policy/Decision continuam independentes.

## 10. Secrets e tokens

Secrets/tokens:

- ficam em vault/secret owner apropriado;
- podem ser referenciados por secretRef quando aplicável;
- nunca vão para LLM/RAG/Personal Memory/MFE/log comum;
- suportam rotation/revocation/reconnect conforme contrato real.

## 11. Connector capability model

O planner usa capabilities semânticas, por exemplo:

```text
communication.email.search
communication.email.read
communication.email.draft
communication.email.send
calendar.events.read
calendar.events.create
files.search
files.read
messaging.conversations.read
messaging.message.send
collaboration.teams.channel.messages.read
collaboration.teams.chat.messages.read
collaboration.teams.message.send
```

Esses nomes são candidates; C0/C3 congelam catálogo real, owner e consumers.

## 12. External Reads

Reads autorizados podem produzir `SourceRef/EvidenceRef` com provider/resource scope/freshness/provenance, sem transformar cache/conexão em authority.

## 13. External Writes / comunicação

```text
draft/preview
→ review when required
→ live AuthZ + Policy/Decision
→ provider adapter
→ provider action
→ authoritative/contractual outcome verification when possible
```

`draft` e `send` são capabilities distintas. Technical success não equivale automaticamente a business/provider outcome final.

## 14. Microsoft 365 / Teams

Microsoft/Teams é uma provider family candidata. Contratos, permissions, resource scopes, webhook models e capabilities devem ser revalidados em fonte oficial no momento da implementação.

Teams segue `56` e não cria planner/backend separado.

## 15. Google Workspace

Google/Gmail/Drive/Calendar são provider candidates sujeitos a APIs oficiais, scopes mínimos, owner e C0 inventory. Push/event capabilities só entram quando suportadas e comprovadas no contrato oficial vigente.

## 16. WhatsApp

Não assumir suporte a conta pessoal. Qualquer integração deve usar interface oficial aprovada para o caso empresarial vigente.

Proibido por default:

- scraping de WhatsApp Web;
- sessão pessoal não suportada;
- cookie/session secret em prompt/state comum;
- bypass de regras/templates/janelas do provider.

## 17. Eventos, webhooks e sincronização

Quando houver contrato suportado:

```text
provider event/webhook
→ authenticity validation
→ adapter normalization
→ EventEnvelope
→ dedupe/correlation
→ Watch/Inbox/Workflow
```

Tratar duplicate/out-of-order, expiry/renewal, missed events, reconciliation e revoke/disable conforme contrato do provider.

## 18. Personal versus organizational privacy

Dados de conexão pessoal/privada não viram automaticamente Case compartilhado, Organizational Knowledge ou fonte acessível a outros usuários.

Promotion/sharing exige policy explícita e source permission revalidation.

## 19. External content is untrusted

Email, webpage, attachment, chat, transcript, tool output, schema e provider metadata são dados não confiáveis para system/policy.

Nunca podem solicitar/alterar secrets, Policy, RBAC, Decision Gates, retention ou autonomy.

## 20. External attachments

```text
provider resource
→ safe download
→ type/size/malware policy
→ source/media ref
→ extraction
→ Evidence
→ synthesis
```

Nunca executar conteúdo ativo recebido como anexo.

## 21. Learning from external sources

Separar:

```text
TRANSIENT_RESEARCH
SESSION_EVIDENCE
PERSONAL_KNOWLEDGE_CANDIDATE
ORGANIZATIONAL_KNOWLEDGE_CANDIDATE
```

Fluxo corporativo:

```text
Evidence
→ candidate
→ owner/review
→ eval
→ version
→ publish
```

Nada vira corporate truth automaticamente.

## 22. Source authority e conflito

Distinguir source authority, freshness e provenance. Informação pública não substitui fonte oficial interna quando existe owner canônico.

## 23. Search/fetch cache

Cache é derivado/invalidável, com TTL/freshness e isolamento user/connection/resource. Nunca vira authority.

## 24. Failure/degraded mode

Distinguir estados como not_connected, scope_missing, consent_required, expired, unavailable, rate_limited, permission_revoked, unsafe_url e stale sync. Não narrar indisponibilidade como inexistência factual.

## 25. Kill switches

Prever disable independente onde material para internet research, provider, connection, external writes, outbound messaging, webhook ingestion, background sync/watch e browser/computer-use.

## 26. Arquitetura alvo

```text
DÉLIA planner/work
  ├─ public research adapter(s)
  └─ provider-neutral connector capabilities
       ├─ provider adapter A
       ├─ provider adapter B
       └─ provider adapter N

ACT
→ live AuthZ + Policy/Decision
→ approved provider adapter
→ provider
→ Outcome/Evidence
```

Nenhum provider vira planner, Policy authority ou Core permission authority.

## 27. C0 foundation inventory

Inventariar com evidence:

- outbound HTTP/egress patterns;
- proxy/DNS/network restrictions;
- web/search providers;
- OAuth callback patterns;
- Keycloak/SSO relation with external authorization;
- vault/encryption patterns;
- existing provider integrations;
- webhook/signature patterns;
- scheduler/event infrastructure;
- file/malware scanning;
- privacy/LGPD owners;
- provider/compliance owners.

Unknown = `TO_INVENTORY`.

## 28. Phase mapping

### C0
Freeze egress, OAuth, credential, connector ownership, privacy, webhook/event e external-learning boundaries.

### C1
Bootstrap somente a infraestrutura aprovada pelo freeze; sem provider feature antecipada.

### C2
External-source refs podem integrar bounded context sem conceder permission.

### C3
Provider-neutral research/connection foundations somente quando justificadas.

### C4
Governed external reads/cross-source analysis.

### C5
Governed external writes/L4 ACT quando explicitamente autorizados, com live AuthZ, Policy/Decision, idempotency/audit quando aplicável e Outcome verification.

### C6
Provider events podem alimentar Watch/Inbox/Tasks/Cases; Watch continua `OBSERVE|ADVISE|PREPARE` por default.

### C7
Selected proactive/autonomous external ACT somente sob allowlists/limits, L5 OFF por default e kill switches.

## 29. Acceptance outcomes

Quando capabilities entrarem em runtime, provar no SHA/config avaliado:

```text
provenance/freshness
safe egress
untrusted-content isolation
least privilege
secret isolation
user/org scope isolation
read/write/draft/send separation
verified outcome for material sends/writes
EventEnvelope authenticity/dedupe/reconciliation
revoke/expiry lifecycle
no cross-user leak
knowledge candidate before publish
new provider without planner hardcode
```

Sem evidence obrigatória: `PENDING`/`INCONCLUSIVE`, nunca PASS.

## 30. Provider facts

Este documento **não congela fatos atuais de vendors**. Capabilities, scopes, limits, webhook models e terms mudam fora do repositório DELPI e devem ser verificados em fonte oficial recente na fase de implementação/inventory correspondente.

## 31. North Star externo

> **A DÉLIA deve combinar contexto interno autorizado com fontes públicas e conexões externas aprovadas sem perder provenance, least privilege, source authority, privacidade, Decision Gates, segurança de credenciais e governança de conhecimento.**
