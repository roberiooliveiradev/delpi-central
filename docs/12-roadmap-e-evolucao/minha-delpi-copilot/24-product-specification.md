# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Produto:** aplicação standalone nova  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Definição

O Minha DELPI Copilot é a **interface e inteligência operacional entre pessoas, operação DELPI, fontes externas e automações governadas**.

Possui API/MFE/persistência/manifest/deploy próprios e não depende do Minha DELPI Chat.

North Star:

> Observar eventos autorizados, entender contexto interno e externo, conectar dados/pessoas/processos/aplicações, combinar regras determinísticas e raciocínio de IA, decidir dentro de policies, coordenar APIs/RPAs/pessoas, verificar resultados, comunicar e transformar experiência validada em aprendizado governado.

## 2. Não é somente Chat + RAG

O produto suporta dois tipos de entrada:

```text
USER INTENT
→ pergunta, pedido, comando, conversa

EVENT / SIGNAL
→ mudança de negócio/produção/manutenção/external provider/Watch
```

Pipeline alvo:

```text
intent/event
→ context / Business Graph / Evidence
→ DecisionPathPolicy
   FAST | OPERATIONAL | REASONING
→ Policy / Decision / Autonomy
→ Durable Workflow
→ semantic capability
→ executor
→ verified Outcome
→ Evidence / Notification / Learning candidate
```

Nem todo evento deve chamar um LLM.

## 3. Espaços de informação

```text
1. MINHA DELPI
   Core + Domain APIs + apps + Knowledge interno

2. INTERNET PÚBLICA
   pesquisa/fetch de fontes públicas atuais

3. FONTES EXTERNAS CONECTADAS
   Microsoft 365/Teams, Google Workspace, WhatsApp Business e outros providers autorizados
```

Nenhum espaço herda automaticamente a authority do outro.

## 4. Surfaces

```text
GLOBAL      → painel contextual no Portal
WORKSPACE   → página completa
MEETING     → reunião assistida
FRONTLINE   → operador/posto/máquina
TEAMS       → futura app/tab/bot surface do mesmo Copilot
BACKGROUND  → Watches/Workflows governados reagindo a eventos
```

Todas usam mesma Copilot API/RBAC/Policy/Evidence/Durable Work.

## 5. Copilot único

Um único Copilot, especializado dinamicamente por Expertise Packs, Playbooks, Knowledge, context e authorized capabilities. Sem agents departamentais e sem planner separado por provider/executor.

## 6. Conversation / Context

- PT-BR natural;
- multi-intent/follow-up;
- WorkspaceContext + EntityRef + bounded SourceRef;
- no CoT persistence;
- texto/voz/mídia;
- provider/RPA credential nunca entra em context;
- event/execution refs podem aparecer apenas como bounded refs, não authority.

## 7. Platform / Business capabilities

Platform capabilities derivam de Core/Portal. Business capabilities derivam de Domain OpenAPI.

```text
OpenAPI
→ Action Catalog
→ authorized Capability Projection
→ planner
→ validation
→ Policy/Decision
→ executor
→ Outcome/Evidence
```

Capabilities são semânticas e independentes do executor concreto.

## 8. Internet Research

Pesquisa externa usa Search Provider + Safe Web Fetch + SourceRef/EvidenceRef/freshness. Web content é untrusted para policy/RBAC.

## 9. External Connectors / Teams

Connectors provider-neutral, com OAuth/least privilege/secret isolation, read/write separation, provider events e source ACL.

Teams é capability family do Microsoft 365 connector, não runtime separado. Chats/canais/mensagens/meetings/transcripts/recordings/eventos preservam scopes/ACL/provenance.

## 10. External Reads/Writes

```text
read != write
draft != send
```

Writes revalidam connection/scope/policy e produzem verified provider outcome.

## 11. Event / Signal Plane

O Copilot pode reagir a eventos de owners autorizados:

```text
Domain APIs / ERP / MES / manutenção / qualidade
External provider webhooks/change notifications
Watch timer/schedule
Approved telemetry/read paths
Automation outcomes
```

Fluxo:

```text
source
→ authenticity/trust validation
→ EventEnvelope
→ dedupe/order/correlation
→ Watch / Workflow / Decision
```

Event payload nunca concede permission ou autorização de ACT.

Polling/scheduler é fallback bounded quando não existe evento suportado.

## 12. Decision Intelligence

O Copilot seleciona o menor caminho suficiente:

```text
FAST
→ deterministic Policy/Specification/State Machine

OPERATIONAL
→ bounded reads + deterministic rules + optional classifier/small model

REASONING
→ Graph + Knowledge + Expertise + LLM
```

Material readiness com critérios conhecidos não deve depender somente de texto probabilístico do LLM.

## 13. Continuous Operational Intelligence

Exemplos de condições observáveis:

```text
pedido pronto para faturar
máquina parada
apontamento improvável
estoque crítico
fornecedor atrasado
OP aguardando material
qualidade desviando
approval/prazo expirando
resposta de fornecedor recebida
```

Essas condições são implementadas sobre Watch/EventEnvelope/Policy/Workflow, não em engine paralelo de “agentes”.

## 14. Automation & Execution Hub

Separação canônica:

```text
COPILOT
= intelligence + context + decision + policy + orchestration

AUTOMATION & EXECUTION HUB
= execution
```

Não construir somente “Hub de RPAs”. RPA é um tipo de executor.

Preferência de executor:

```text
1 API oficial
2 integração nativa suportada
3 função/script determinístico
4 RPA
5 computer-use/UI automation governada
6 Human Task
```

A existência do conceito `Hub` não implica microservice; ownership físico é decidido em C0 por evidence/ADR.

## 15. Semantic Automation Capabilities

Exemplos:

```text
billing.invoice.issue
maintenance.request.create
production.report.validate
communication.email.send
inventory.read
```

Planner conhece capability/schema/policy, nunca:

```text
click(x,y)
selector
screen coordinate
RPA package internals
```

Trocar RPA por API deve alterar mapping/adapter, não o planner/workflow.

## 16. AutomationExecution

Lifecycle conceitual:

```text
QUEUED
→ RUNNING
→ SUCCEEDED | FAILED | AMBIGUOUS | CANCELLED | TIMED_OUT
```

A execução registra correlation, actor/service identity, capability, executor/version, inputHash, attempt/idempotency, result/error e outcome verification refs.

## 17. RPA executor

Quando priorizado:

- worker pool/capabilities;
- queue/priority/concurrency;
- worker heartbeat;
- lease/lock;
- environment separation;
- package/version traceability;
- protected credential injection;
- timeout/cancel/retry eligibility;
- screenshot/artifact retention/classification;
- desktop/session isolation;
- full audit/correlation.

Bot/RPA nunca vira authority de business rule.

## 18. Computer Use

Fallback avançado quando API/RPA determinístico não atender e houver justificativa.

Requer sandbox/session isolation, app/domain/network allowlist, protected credentials, bounded actions, human takeover/stop e audit.

## 19. Outcome Verification

Invariante:

```text
technical executor success != verified business outcome
```

Exemplos:

```text
HTTP 200 != nota emitida corretamente
RPA clicou Salvar != transação confirmada
provider accepted != final delivery when async
```

Sempre que material, verificar postcondition em source autoritativo antes de declarar conclusão.

## 20. Exemplo — faturamento autônomo

```text
order/shipment event
→ load authoritative order/customer/shipment/fiscal facts
→ deterministic InvoiceReadinessPolicy
→ READY?
   ├─ NO → Evidence + exception/Inbox
   └─ YES → AutonomyPolicy
             ├─ PREPARE/CONFIRM → Decision Gate
             └─ ACT allowed → billing.invoice.issue
                                  → API/RPA executor
                                  → verify invoice outcome
                                  → Evidence/Audit
                                  → notify Minha DELPI/email/Teams/WhatsApp
```

A IA pode investigar/explicar exceções; readiness formal usa critérios verificáveis.

## 21. Exemplo — validação de apontamento

```text
production report event
→ OP/operation/machine/standard cycle/shift/stoppages/scrap
→ deterministic plausibility calculation
→ Evidence
→ ACCEPT | ASK_CONFIRMATION | BLOCK_AND_REVIEW
```

Anomalia não é inferência automática de fraude/intenção do operador.

## 22. Exemplo — máquina parada

```text
approved machine/MES event
→ alarm/history/last maintenance/affected OP
→ classify need/criticality
→ maintenance.request.create
→ eligible technician/team
→ notify
→ Watch acknowledgement/SLA
→ escalate when needed
```

Isso não autoriza comando físico de máquina.

## 23. Watch / Proactivity

```text
OBSERVE → detect/record
ADVISE  → analyze/notify
PREPARE → prepare candidate action/preview, no side effect
ACT     → execute only under C7 autonomy gate
```

`PREPARE != ACT`.

## 24. Autonomy Model

```text
L0 explain
L1 observe/analyze
L2 advise
L3 prepare
L4 execute after required governance
L5 autonomous within explicit allowlist/policy/budgets
```

Autonomy is resolved by:

```text
capability
+ actor/service identity
+ event trust
+ context
+ risk/sensitivity
+ financial/material limits
+ environment
+ reversibility
+ policy
```

No global unrestricted L4/L5. L5 OFF by default.

## 25. Human-in-the-loop

Quando ambiguidade/risco/policy exigir:

```text
Workflow
→ wait_user / wait_approval
→ Inbox/Decision
→ human resolution
→ resume same Workflow
```

Não criar processo manual paralelo sem correlation.

## 26. Notification / Escalation

Canais aprovados podem incluir Minha DELPI, email, Teams, WhatsApp Business e Interaction Rooms.

Recipients/severity/dedupe/SLA/escalation seguem policy. Notification success não prova business outcome.

## 27. Multimodal / Biometric / Meeting / Frontline

Mídia converge para Evidence. Biometrics são candidate identity only. Meeting/Frontline usam o mesmo Policy/Workflow/Automation model.

Human Observation permanece limitada a fatos/padrões observáveis do processo.

## 28. Business Graph / Evidence

EntityRef/RelationshipRef conectam domínios sem replicar masters.

Epistemic UX:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Event/RPA/computer-use output não vira FACT autoritativo por existir; source/postcondition authority importa.

## 29. Decision / Writes

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Business/external/automation writes revalidam authority imediatamente antes da execução quando material.

## 30. Durable Work

WorkflowPlan único orquestra internal/external/automation capabilities com checkpoints/waits/resume/idempotency. Automation Hub não cria segundo workflow engine.

## 31. Privacy / Security / Safety

Obrigatório:

- data minimization;
- safe egress;
- external/event/RPA screen content untrusted;
- secret isolation;
- source ACL;
- explicit background actor/service identity;
- event != permission;
- capability-scoped autonomy;
- kill switches;
- no blind retry after ambiguous write;
- RPA worker/session isolation;
- computer-use sandbox/allowlists;
- media/biometric privacy;
- OT safety boundary.

## 32. Administration

Admin/UX deve evoluir para cobrir:

```text
Connections
Capabilities
Automation Catalog
Executions
Workers when applicable
Exceptions
Decision/approval queues
Watch conditions/modes
Autonomy policies
Outcome/Evidence
Kill switches
Audit/Evals/Coverage
```

Credentials nunca são exibidos.

## 33. Error semantics

Além de external errors, suportar canonical errors como:

```text
EventSourceInvalid
EventDuplicate
EventStale
DecisionInconclusive
AutomationCapabilityUnavailable
AutomationExecutorUnavailable
AutomationWorkerUnavailable
AutomationExecutionTimedOut
AutomationExecutionAmbiguous
AutomationExecutionFailed
AutomationOutcomeNotVerified
AutomationPolicyBlocked
AutomationKillSwitchActive
ComputerUseBoundaryBlocked
```

Nunca narrar success quando state/outcome é pending/ambiguous/inconclusive.

## 34. Non-functionals

- independent deployment/rollback;
- security/privacy by default;
- provider/executor-neutral planner;
- event latency/throughput budgets;
- decision-path latency observability;
- executor queue/worker observability when applicable;
- idempotency/no duplicate effect;
- verified Outcome semantics;
- kill switches;
- external rate/cost budgets;
- generalization tests;
- no Chat dependency;
- industrial safety boundary.

## 35. Fora de escopo/default

- Chat→Copilot migration;
- unrestricted browser/desktop control;
- arbitrary web fetch;
- provider/RPA credentials in prompt/browser state;
- implicit send;
- personal WhatsApp scraping;
- external content auto-published as corporate Knowledge;
- RPA bot as business decision authority;
- RPA clicks/selectors in planner;
- second Workflow engine in Automation Hub;
- event payload directly causing write;
- all events sent to LLM;
- technical executor result treated automatically as business completion;
- global unrestricted L5;
- open-world biometric surveillance;
- free-form machine actuation.

## 36. Reference scenarios

### Research
> “Pesquise a norma mais recente e compare com nosso procedimento.”

### External communication
> “Ache a última conversa com o fornecedor, compare com a OC e prepare uma resposta; só envie depois da governança necessária.”

### Operational Watch
> “Acompanhe pedidos prontos para faturar e prepare a ação quando todos os critérios forem atendidos.”

### Autonomous invoice — future C7 approved scope
> “Quando a readiness formal estiver PASS e a capability estiver autorizada para ACT, fature, confirme a nota emitida e notifique os responsáveis.”

### Production report
> “Avalie automaticamente apontamentos improváveis e peça confirmação quando estiverem fora da plausibilidade definida.”

### Maintenance
> “Se uma máquina ficar parada além do threshold, contextualize o alarme, abra manutenção e notifique/escalone conforme SLA.”

### Meeting
> “Use indicadores e fontes conectadas; gere a ata e candidate actions.”

### Frontline
> “Mostre o procedimento vigente e registre/escalone problemas por governed capabilities.”

## 37. Product Complete

O release completo, conforme escopo declarado, exige standalone independence, Portal/Core integration, intelligence, reads/Graph, Event/Decision foundation, governed business/external/automation writes, Durable Work, Automation Hub semantics, outcome verification, Meeting/Frontline, external privacy/events/learning, capability-scoped autonomy, security/evals/generalization, observability/rollback e CP coverage sem gaps materiais.

Estado real vive no execution ledger.
