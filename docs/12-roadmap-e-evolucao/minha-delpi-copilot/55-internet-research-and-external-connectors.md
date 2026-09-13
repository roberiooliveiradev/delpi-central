# Minha DELPI Copilot — Internet Research e External Connectors

**Status:** thematic architecture/security/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Security:** [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)

## 1. Decisão de produto

O Minha DELPI Copilot deve conseguir buscar informação além da Minha DELPI por dois caminhos complementares:

```text
PUBLIC INTERNET
→ pesquisa/fetch de fontes públicas

CONNECTED SOURCES
→ contas, caixas, canais e serviços explicitamente conectados
```

Exemplos de fontes conectáveis, conforme APIs oficiais, autorização e policy:

```text
Microsoft 365 / Outlook / Calendar / OneDrive / SharePoint / Teams
Google Workspace / Gmail / Calendar / Drive
WhatsApp Business Platform
Slack
GitHub
service desks / CRMs / ERPs externos
outros provedores futuros
```

O desenho deve ser provider-neutral. O planner não contém branches como `if gmail`, `if outlook` ou `if whatsapp`.

## 2. Quatro operações diferentes

Não misturar:

```text
1. SEARCH   → localizar informação pública
2. READ     → ler recurso autorizado de uma conta conectada
3. ACT      → criar/alterar/enviar algo em sistema externo
4. LEARN    → promover conhecimento externo para estado durável governado
```

Cada operação tem authority, risco e lifecycle próprios.

## 3. Internet Research

Fluxo alvo:

```text
user goal
→ research need detection
→ SearchProviderPort
→ search candidates
→ SafeWebFetchPort
→ extraction/normalization
→ SourceRef + EvidenceRef
→ freshness/relevance assessment
→ grounded synthesis
→ citations/sources
```

Pesquisa na web é retrieval, não authority.

Conteúdo externo pode estar errado, desatualizado, malicioso ou conter prompt injection.

## 4. Pesquisa automática versus explícita

O Copilot pode decidir pesquisar a internet quando isso for necessário para responder corretamente, por exemplo:

- fatos atuais;
- notícias;
- normas/documentação pública;
- mercado/benchmark;
- fornecedores/produtos;
- documentação técnica;
- dados externos que não existem nas APIs DELPI.

A UI deve mostrar atividade como `Pesquisando fontes externas` e apresentar provenance quando material.

A pesquisa não deve ocorrer quando:

- a resposta já está coberta por source corporativo canônico e não há necessidade externa;
- policy classifica a consulta/contexto como não elegível para egress;
- a busca exigiria enviar segredo ou conteúdo sensível desnecessário.

## 5. Safe Web Fetch / Egress Boundary

Nenhuma URL produzida por LLM deve ser buscada por um HTTP client irrestrito.

O fetcher deve aplicar, quando pertinente:

```text
allowed schemes http/https
DNS/IP validation
private/link-local/loopback/metadata blocking
redirect revalidation
content-type/size/time limits
download/malware policy
TLS validation
rate/concurrency limits
robots/terms/policy considerations where applicable
redaction of sensitive query/context
```

Objetivo: impedir SSRF, acesso acidental à rede interna, metadata endpoints, downloads ilimitados e exfiltração.

## 6. Browser automation

Browser/interactive web automation não é o mecanismo padrão de integração.

Preferência:

```text
official API / connector
→ structured web search/fetch
→ browser automation only when justified
```

Se browser automation for introduzida futuramente:

- ambiente sandboxed;
- bounded domain/session;
- sem acesso livre à rede interna;
- credenciais por mecanismo protegido, nunca prompt/plaintext;
- actions materiais continuam Policy/Decision Gate;
- não substituir API oficial por scraping frágil quando API existe.

## 7. External Connector Architecture

Fluxo conceitual:

```text
user/admin chooses provider
→ authorization/enrollment flow
→ OAuth/API authorization
→ callback/verification
→ ExternalConnection lifecycle
→ encrypted credential/secret reference
→ provider adapter
→ normalized connector capabilities
→ Copilot retrieval/planner
```

O Copilot não recebe tokens como contexto de LLM.

## 8. Connection ownership

Distinguir pelo menos:

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Exemplos:

```text
Gmail pessoal conectado pelo próprio usuário       → USER_DELEGATED
Outlook corporativo com delegated scopes           → USER_DELEGATED
shared mailbox                                      → SHARED_RESOURCE
WhatsApp Business number da empresa                 → ORG_MANAGED / SERVICE_CONNECTION
```

Uma conexão de usuário não vira conexão organizacional por conveniência.

## 9. OAuth e least privilege

Conexões OAuth devem usar o fluxo oficial do provider e solicitar o menor scope necessário.

Exemplo conceitual:

```text
mail.read
!=
mail.send
!=
mail.modify
```

O produto deve suportar:

- scope disclosure;
- user/admin consent quando aplicável;
- state/nonce/callback validation;
- token refresh por adapter;
- revocation;
- reconnect;
- expiry/failure state;
- scope change detection;
- audit.

Scopes concedidos ao provider nunca substituem Core RBAC/policy do Copilot.

## 10. Secrets e tokens

Access/refresh tokens, client secrets e provider credentials são infraestrutura sensível.

Regras:

- encrypted secret/vault storage ou owner corporativo equivalente;
- Copilot DB armazena apenas `secretRef` quando possível;
- nunca logar token;
- nunca enviar token para LLM/RAG;
- nunca retornar refresh token ao MFE;
- rotation/revocation suportadas;
- provider credentials separados por environment;
- emergency disconnect.

## 11. Connector capability model

O planner deve trabalhar com capabilities semânticas, não provider endpoints hardcoded.

Exemplo:

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
```

Provider adapter resolve isso contra o contrato real permitido.

Se a integração possuir OpenAPI/schema oficial utilizável, preferir ingestão/normalização contract-driven conforme a filosofia OpenAPI-first do Copilot.

## 12. External Reads

Exemplos permitidos quando conectados/autorizados:

- buscar e-mails relacionados a cliente/projeto;
- resumir thread;
- localizar anexos;
- consultar agenda;
- localizar arquivos no Drive/OneDrive/SharePoint;
- consultar mensagens/canais suportados;
- correlacionar informação externa com EntityRefs DELPI;
- comparar dados internos com informação pública.

Resultados externos entram como `SourceRef/EvidenceRef` com provider/resource/user scope/freshness.

## 13. External Writes / comunicação

Ações externas materiais são separadas de reads.

Exemplos:

```text
criar rascunho
responder e-mail
enviar e-mail
criar evento
alterar evento
enviar mensagem
upload/alteração de arquivo
```

Preferência de governance:

```text
draft/preview
→ user review when material
→ Decision Gate
→ provider adapter
→ verified external outcome
```

`draft` e `send` são capabilities diferentes.

Nenhum modelo pode transformar uma resposta sugerida em mensagem enviada implicitamente.

## 14. Outlook / Microsoft 365

O adapter Microsoft deve tratar Microsoft Graph como contract owner para capabilities suportadas.

A arquitetura deve suportar, conforme scopes aprovados:

- mail;
- calendar;
- contacts quando necessário;
- files/OneDrive/SharePoint;
- Teams/resources suportados.

Change notifications/subscriptions podem alimentar EventEnvelope/Watch quando o provider suportar.

Provider-specific lifecycle permanece no adapter.

## 15. Google Workspace / Gmail

O adapter Google deve usar APIs oficiais e OAuth scopes mínimos.

A arquitetura pode suportar, conforme scopes aprovados:

- Gmail read/search;
- Gmail draft/send;
- Calendar;
- Drive;
- demais APIs Workspace aprovadas.

Gmail push notifications/Pub/Sub podem alimentar EventEnvelope/Watch, com renewal/reconciliation encapsulados no adapter.

## 16. WhatsApp

Não assumir que uma conta pessoal de WhatsApp pode ser integrada como se fosse Gmail/Outlook.

O target suportado deve usar **interfaces oficiais disponíveis**, especialmente WhatsApp Business Platform/Cloud API para números/canais empresariais quando essa for a necessidade.

Proibido como default:

- scraping de WhatsApp Web;
- automação de sessão pessoal não suportada;
- armazenamento de cookies/session secrets em prompt/state comum;
- bypass de políticas/templates/janelas/regras do provider.

Se no futuro existir contrato oficial adicional para outro tipo de conta, ele entra como novo adapter, sem patch no planner.

## 17. Eventos, webhooks e sincronização

Quando provider permitir:

```text
provider webhook/subscription/push
→ adapter validates authenticity
→ normalize
→ EventEnvelope
→ dedupe/correlation
→ Watch/Inbox/Workflow
```

Obrigatório tratar:

- webhook authenticity/signature/validation;
- duplicate delivery;
- out-of-order events;
- subscription expiry/renewal;
- missed events;
- reconciliation/full sync fallback;
- permission revoked;
- connection disabled.

## 18. Personal versus organizational privacy

O Copilot deve distinguir dados pessoais/conectados do usuário de dados corporativos compartilhados.

Exemplos:

```text
user personal Gmail connection
-X→ searchable by other employees

user Outlook mailbox
-X→ organizational Knowledge automatically

private message
-X→ Case/Room accessible by everyone
```

Sharing/promotion exige regra explícita.

## 19. External content is untrusted

Email, webpage, attachment, chat message e documento externo são dados não confiáveis para system/policy.

Prompt injection externo não pode:

- solicitar secrets/tokens;
- modificar policy;
- ampliar RBAC;
- autorizar novo connector;
- disparar write externo;
- mudar retention;
- criar persistent Knowledge automaticamente.

## 20. External attachments

Arquivos externos passam pelo mesmo boundary multimodal/documental:

```text
provider resource
→ safe download
→ type/size/malware policy
→ MediaRef/SourceRef
→ extraction
→ EvidenceRef
→ synthesis
```

Nunca executar conteúdo ativo recebido como anexo.

## 21. Learning from Internet / Connected Sources

"Aprender" possui níveis distintos:

```text
TRANSIENT_RESEARCH
→ usado somente para a resposta/task atual

SESSION_EVIDENCE
→ persistido somente quando Task/Case/audit exige

USER_KNOWLEDGE_CANDIDATE
→ memória/conhecimento privado candidato do usuário

ORGANIZATIONAL_KNOWLEDGE_CANDIDATE
→ candidato corporativo com owner/review/eval
```

Nunca:

```text
web page / email / WhatsApp message
→ automatic corporate truth
```

Fluxo organizacional:

```text
external SourceRef/Evidence
→ candidate
→ owner/reviewer
→ eval/freshness/licensing/privacy checks
→ versioned Knowledge/Playbook
→ publish
```

## 22. Source authority e conflito

O Copilot deve saber distinguir:

```text
DELPI authoritative source
external authoritative source
public reference
personal communication
unverified web content
```

Quando fontes conflitam, apresentar conflito/freshness/provenance em vez de escolher silenciosamente.

Informação pública não substitui dado oficial interno quando o negócio define um owner canônico.

## 23. Search/fetch cache

Cache de web/external reads, se criado, é derivado e invalidável.

Regras:

- TTL/freshness explícitos;
- user/connection scope preservado;
- no cross-user cache leak;
- sensitive content não vira shared cache por default;
- cache não vira authority.

## 24. Failure/degraded mode

Distinguir:

```text
not_connected
scope_missing
consent_required
connection_expired
provider_unavailable
rate_limited
resource_not_found
permission_revoked
web_fetch_blocked
unsafe_url
webhook_invalid
sync_stale
```

Não narrar ausência de dado como se fosse dado inexistente quando connector está indisponível.

## 25. Kill switches

Deve ser possível desabilitar:

- internet research globalmente;
- provider específico;
- connection específica;
- external writes;
- outbound messaging;
- webhook ingestion;
- background sync/watch;
- browser automation futura.

Kill switch não depende de prompt/LLM.

## 26. Arquitetura alvo

```text
                    ┌─────────────────────┐
                    │   Copilot Planner   │
                    └─────────┬───────────┘
                              │
             ┌────────────────┴─────────────────┐
             │                                  │
     Internet Research                   External Connectors
             │                                  │
       SearchProviderPort                 Capability/Connection
             │                                  │
       SafeWebFetchPort             ┌────────────┼────────────┐
             │                      │            │            │
       Source/Evidence         Microsoft      Google      WhatsApp/... 
             │                 Adapter        Adapter        Adapter
             └──────────────────────┬────────────┴────────────┘
                                    │
                              Policy/Decision
                                    │
                             verified Outcome
```

## 27. C0 foundation inventory

C0.S0 deve inventariar, com evidence:

- outbound HTTP/egress patterns atuais;
- proxy/DNS/network restrictions;
- existing web/search providers;
- existing OAuth callback patterns;
- Keycloak/SSO relation with external OAuth flows;
- secrets manager/vault/encryption patterns;
- existing Microsoft Graph/Google/WhatsApp integrations;
- provider app registrations/config/env conventions;
- existing webhook endpoints/signature verification;
- job/scheduler/event infrastructure;
- object/file/malware scanning patterns;
- privacy/LGPD/data-classification owners;
- approved domains/providers;
- personal versus organizational connection policy;
- provider terms/compliance owners.

Unknown = `NOT_PROVEN`.

## 28. Phase mapping

### C0

Freeze egress, OAuth, credential, connector ownership, external-data privacy, webhook/event and external-learning boundaries.

### C1

Bootstrap application/config prepared for protected callback/connection infrastructure, without implementing provider features prematurely.

### C2

External-source context may be represented in bounded Copilot context, without granting permissions.

### C3

Implement Internet Research foundation and generic connection/provider ports/adapters only when justified.

### C4

Enable governed External Reads and cross-source analysis.

### C5

Enable governed External Writes such as draft/send/create/update, with Decision Gates and verified outcomes.

### C6

Integrate provider events with Watch/Inbox/Tasks/Cases and governed learning candidates.

### C7

Selected proactive/automated external actions only under explicit allowlists, budgets, provider policy and kill switches.

## 29. Acceptance outcomes

A capability está arquiteturalmente correta quando:

```text
internet research has provenance/freshness
unsafe URLs/private network access are blocked
external content cannot change system policy
OAuth scopes are least privilege
secrets never reach LLM/logs/MFE
connections are user/org scoped correctly
read and write capabilities are separate
send has governance and verified outcome
provider events normalize to EventEnvelope
revoke/expiry/missed-event lifecycle works
external data does not leak across users
external knowledge is candidate before publication
new provider does not require planner hardcode
WhatsApp integration uses supported official contracts
```

## 30. Current provider facts verified for planning — 2026-09

These are **external platform facts**, not Copilot architecture authorities:

- Gmail API provides authorized mailbox access and sending via OAuth; Gmail supports push mailbox-change notifications using Cloud Pub/Sub and `watch` lifecycle.
- Microsoft Graph provides authorized Outlook mail access and supports change-notification subscriptions/webhooks for supported resources.
- WhatsApp Business Platform/Cloud API is the official Meta business messaging API; it uses business assets such as a WhatsApp Business Account/business phone number. Personal WhatsApp scraping is not treated as an approved connector contract.

Provider rules/scopes/limits must be revalidated during implementation because they evolve independently of the DELPI repository.

## 31. North Star externo

> **O Minha DELPI Copilot deve conseguir combinar o contexto interno autorizado da DELPI com fontes públicas atuais e contas externas explicitamente conectadas, pesquisar, ler, correlacionar, comunicar e acompanhar trabalho entre sistemas sem perder provenance, least privilege, privacidade, Decision Gates, segurança de credenciais e governança de conhecimento.**
