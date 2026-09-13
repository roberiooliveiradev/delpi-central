# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Produto:** aplicação standalone nova  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Definição

O Minha DELPI Copilot é a **interface inteligente entre pessoas, operação DELPI e fontes externas autorizadas**.

Possui API/MFE/persistência/manifest/deploy próprios e não depende do Minha DELPI Chat.

North Star:

> Entender contexto interno e externo, conectar dados, pessoas, processos e aplicações, pesquisar, investigar, comunicar, executar trabalho, acompanhar resultados e transformar conhecimento validado em ação governada.

## 2. Espaços de informação

O Copilot trabalha sobre três espaços claramente distintos:

```text
1. MINHA DELPI
   Core + Domain APIs + apps + Knowledge interno

2. INTERNET PÚBLICA
   pesquisa/fetch de fontes públicas atuais

3. FONTES EXTERNAS CONECTADAS
   contas/serviços explicitamente autorizados
```

Nenhum espaço herda automaticamente a authority do outro.

## 3. Surfaces

```text
GLOBAL      → painel contextual no Portal
WORKSPACE   → página completa
MEETING     → reunião assistida
FRONTLINE   → operador/posto/máquina
```

Todas usam mesma Copilot API/MFE/RBAC/Policy/Evidence/Durable Work e podem acessar Internet/Connectors conforme autorização.

## 4. Copilot único

Um único Copilot, especializado dinamicamente por Expertise Packs, Domain Playbooks, Knowledge, context e authorized capabilities. Sem agents departamentais.

## 5. Conversation / Context

- PT-BR natural;
- multi-intent;
- follow-up;
- WorkspaceContext + EntityRef + bounded SourceRef;
- no CoT persistence;
- texto/voz/mídia;
- provider credential nunca entra em context.

## 6. Platform / Business capabilities

Platform capabilities derivam de Core/Portal. Business capabilities derivam de Domain OpenAPI.

```text
OpenAPI
→ Action Catalog
→ authorized Capability Projection
→ retrieval/planner
→ validation
→ Policy/Decision
→ executor
→ Outcome/Evidence
```

## 7. Internet Research

O Copilot pode pesquisar a web quando a pergunta exige informação externa/atual.

```text
research need
→ Search Provider
→ Safe Web Fetch
→ extraction
→ SourceRef/EvidenceRef
→ freshness/authority assessment
→ grounded synthesis
```

Casos:

- normas/documentação pública;
- mercado/benchmark;
- notícias e fatos atuais;
- fornecedores/produtos;
- documentação técnica;
- referências externas para análise.

External web content é untrusted e não pode alterar policy/RBAC.

## 8. External Connectors

Conectores alvo, conforme API oficial e aprovação:

- Microsoft 365 / Outlook / Calendar / OneDrive / SharePoint / Teams;
- Google Workspace / Gmail / Calendar / Drive;
- WhatsApp Business Platform;
- Slack;
- GitHub;
- service desks/CRMs/outros providers futuros.

Architecture provider-neutral: novo provider entra por adapter/capability contract, não por branch no planner.

## 9. Connection ownership

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Uma conexão pessoal do usuário não vira fonte organizacional automaticamente.

## 10. OAuth / Credentials

- official provider authorization;
- least privilege scopes;
- consent/scope disclosure;
- callback integrity;
- refresh/revoke/reconnect;
- protected secret/vault storage;
- no access/refresh token in LLM/MFE/log;
- provider scope != Core permission.

## 11. External Reads

Quando conectado/autorizado, o Copilot pode:

- pesquisar/ler e-mails;
- resumir threads;
- localizar attachments;
- consultar agenda;
- procurar/ler arquivos;
- consultar mensagens/canais suportados;
- correlacionar recurso externo com EntityRefs/Case/Task DELPI.

Resultado externo recebe SourceRef/Evidence/freshness.

## 12. External Writes / Communication

Capacidades distintas:

```text
email draft
email send
calendar create/update
message send
file create/update
```

Invariantes:

```text
read != write
draft != send
```

External write passa por connection/scope validation, Policy/Decision Gate quando material e verified provider outcome.

## 13. Provider Events

Provider push/webhook/subscription pode alimentar EventEnvelope/Watch/Inbox/Workflow.

Obrigatório tratar authenticity, duplicates, ordering, expiry/renewal, missed events, reconciliation e revoked connection.

## 14. WhatsApp

Target suportado é integração por contratos oficiais disponíveis, especialmente WhatsApp Business Platform para canais empresariais quando aplicável.

Não usar scraping/automação de sessão pessoal do WhatsApp Web como integração default.

## 15. External learning

Níveis:

```text
TRANSIENT_RESEARCH
SESSION_EVIDENCE
USER_KNOWLEDGE_CANDIDATE
ORGANIZATIONAL_KNOWLEDGE_CANDIDATE
```

Nunca:

```text
web page/email/message/file
→ automatic corporate truth
```

Knowledge durável segue provenance + privacy + freshness + owner/review/eval/version/publish.

## 16. Multimodalidade

PDF, image, drawing, spreadsheet, voice, camera, video, screen share e external attachments convergem para Evidence. Provider/attachment content não altera policy.

## 17. Biometric Identity / Human Observation

Closed-set face/speaker recognition somente para enrolled users quando policy permitir. Match não autentica nem concede permission.

Human Observation descreve fatos observáveis do processo; não infere personality/trust/emotion/health/sensitive traits nem toma decisão trabalhista automática.

## 18. Meeting Mode

Meeting pode combinar:

```text
transcript
internal APIs/Graph
Internet Research
connected email/calendar/files/messages
participant association when enabled
Evidence
human decisions
candidate actions
ata viva
```

Uma ação citada na reunião não é executada automaticamente.

## 19. Frontline Mode

Frontline combina OP/machine/product/operation, voice/camera, drawings/procedures/history e external sources apenas como complemento governado. Source/revision interna oficial permanece authority operacional quando definida.

## 20. Business Graph

EntityRef/RelationshipRef conectam domínios sem replicar masters. External SourceRefs podem ser relacionados a Cases/Tasks/Entities sem transformar mailbox/file provider em Graph master.

## 21. Evidence / Epistemic UX

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Evidence material preserva source/freshness/location/confidence/limitations. Fonte externa não vira fato autoritativo por estar disponível.

## 22. Decision / Writes

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Business e External writes revalidam authority no execute.

## 23. Durable Work

WorkflowPlan único orquestra reads/writes internos e externos com checkpoints/waits/resume/idempotency. Não existe workflow engine por provider.

## 24. Task / Case / Room / Inbox / Watch

Podem relacionar SourceRefs internos/externos respeitando source ACL. Watch pode acompanhar eventos internos e provider events; ACT somente sob policy/autonomy adequada.

## 25. Privacy / Security

Obrigatório:

- data minimization;
- safe external egress;
- external content untrusted;
- least privilege OAuth;
- secret isolation;
- cross-user connection isolation;
- explicit personal→shared promotion;
- read/write separation;
- no implicit send;
- external event validation;
- kill switches;
- media/biometric privacy;
- OT safety boundary.

## 26. Administration / Connections

Admin/UX deve permitir, conforme role:

- listar providers/connections;
- connect/reconnect/revoke/disable;
- visualizar scopes/capabilities em linguagem humana;
- provider health;
- webhook/subscription status;
- research/provider/write kill switches;
- audit/evals/coverage.

Credentials nunca são exibidos.

## 27. AI-ready / Connector-ready

Apps continuam com readiness L1–L5. External connector readiness acrescenta:

```text
auth contract
connection ownership
semantic capabilities
read/write classification
resource/source mapping
provider event lifecycle
privacy/retention
error/degraded semantics
evals
```

## 28. Error semantics

Adicionar:

```text
ExternalNotConnected
ExternalConsentRequired
ExternalScopeMissing
ExternalConnectionExpired
ExternalPermissionRevoked
ExternalProviderUnavailable
ExternalRateLimited
ExternalResourceNotFound
ExternalAccessBlocked
ExternalEventInvalid
ExternalSyncStale
```

Nunca narrar “sem resultados” quando source está indisponível.

## 29. Non-functionals

- independent deployment/rollback;
- security/privacy by default;
- provider-neutral architecture;
- current-source freshness/provenance;
- secret isolation;
- idempotency/outcome verification;
- external rate/cost budgets;
- no duplicate authorities;
- generalization tests;
- no Chat dependency;
- industrial safety boundary.

## 30. Fora de escopo/default

- Chat→Copilot migration;
- unrestricted browser/desktop control;
- arbitrary internet fetch;
- provider token in LLM/browser state;
- personal account sharing by default;
- implicit send;
- scraping personal WhatsApp Web session;
- external content auto-published as corporate Knowledge;
- open-world biometric surveillance;
- global L5 autonomy;
- free-form machine actuation.

## 31. Reference scenarios

### Research
> “Pesquise a norma mais recente e compare com nosso procedimento.”

### Outlook/Gmail
> “Ache a última conversa com o fornecedor sobre este item e relacione com a OC.”

### Draft/send
> “Prepare uma resposta com os dados da DELPI, mas só envie depois que eu revisar.”

### Watch
> “Me avise quando o fornecedor responder e atualize este Case.”

### Meeting
> “Use os indicadores, a correspondência com o fornecedor e pesquisa externa; ao final gere a ata e as ações candidatas.”

### Frontline
> “Mostre o procedimento vigente e, se necessário, busque documentação externa aprovada sem substituir a revisão oficial.”

## 32. Product Complete

O release completo, conforme escopo declarado, exige standalone independence, Portal/Core integration, intelligence, business/external reads, governed writes, durable work, media/biometric/external privacy, provider events, external learning governance, security/evals/generalization, observability/rollback e CP coverage sem gaps materiais.

Estado real vive no execution ledger.
