# SUPERSEDED — premissa de delivery externo invalidada

**EXECUTION_DRIFT / SUPERSEDED_BY_PRODUCT_CLARIFICATION**

Decisão/clarificação do Product Owner em 09/10/2026:

- o package **não é entregue por e-mail**;
- o package permanece na Minha DELPI;
- revisores externos da Controladoria possuem login/acesso na Minha DELPI;
- o ato de "Enviar" em P5 significa submeter/disponibilizar a versão finalizada para análise dentro do Portal;
- Core Notifications notifica os usuários na Minha DELPI e pode também enviar e-mail conforme a capability/preferência da plataforma;
- e-mail é **notificação com link para a Minha DELPI**, não transport do package.

Consequência:

```text
EXTERNAL_PACKAGE_DELIVERY_PREMISE = INVALIDATED
GRAPH_ATTACHMENT_DELIVERY = NOT_A_P5_REQUIREMENT
MESSAGE_TRACE = NOT_A_P5_COMPLETION_REQUIREMENT
```

O inventário técnico abaixo permanece válido apenas como evidência das capabilities existentes da plataforma. Ele **não** define o TARGET do P5.

Authority substituta:
- [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md).

---

# 36 — E04/T04 — Package Delivery Capability Decision Packet — histórico superseded

## Estado

**TARGET / INVENTORY COMPLETE / DECISION_REQUIRED / NO CHANGE APPLIED**

    DOCUMENTED != IMPLEMENTED
    IMPLEMENTATION_AUTHORIZED = NO
    E04 = DECISION_REQUIRED
    T04 = INVENTORY_COMPLETE_FOR_DECISION
    PRODUCT_CONTRACT_FREEZE = BLOCKED_BY_DECISION

Este documento fecha o inventário técnico E04/T04 e isola a decisão material restante do envio real de P5. Nenhuma opção abaixo está aprovada.

## Baseline

- data: 09/10/2026;
- main HEAD revalidado: `5e4ae559a5e9e22626a323fde5fd9d12a66e713d`;
- branch documental no início: `5d2aa7cff574d381becbf8e88abd3e6d5e0c9fe2`;
- git status local: `INCONCLUSIVE` neste ambiente;
- runtime `controllership-finance`: NOT_IMPLEMENTED.

## 1. AS-IS

TÉO comprova:

    consolidar relatórios, extratos e documentos por destinatário
    → encaminhar o pacote de fechamento aos destinatários
    → receber questionamentos
    → fornecer complementos
    → concluir o ciclo

A decomposição registra `kp08_t01` (consolidar por destinatário) e `kp08_t02` (encaminhar pacote). O canal técnico não é provado.

    BUSINESS_NEED_TO_DELIVER_PACKAGE = PROVEN
    CURRENT_CHANNEL = UNKNOWN

Não foi provado como canal AS-IS: e-mail, Teams, SharePoint, pasta, download manual ou outro transport.

## 2. Core Notifications

Já provado: `POST /integrations/notifications`, S2S por service token, rate limit, recipient filtering, `sourceApp`, action target e inbox/history/preferences.

    CORE_NOTIFICATION_CAPABILITY = PROVEN
    PACKAGE_DELIVERY_CAPABILITY = NOT_PROVEN

Core Notifications comunica eventos; não possui contract de artifact/package delivery com proof lifecycle.

    NOTIFICATION_DISPATCHED != PACKAGE_SENT

## 3. Delpi Reports / api-delpi

Core metadata registra `reports` como solução de cadastro, agendamento e envio de relatórios por e-mail. O runtime prova:

    ReportDefinition
    → registered ReportProvider
    → provider.collect()
    → provider.render_email()
    → Microsoft Graph sendMail
    → per-recipient delivery rows

Reports possui recipients, file attachments, batches, retry transitório, runs, deliveries e artifact HTML.

Mas `ReportProviderPort` exige `collect(params)` e `render_email(dataset)` dentro do contexto Reports, e o disparo manual `POST /reports/definitions/{definition_id}/run` exige `REPORTS_WRITE_PERMISSIONS`.

Não há contrato S2S genérico provado para `send arbitrary package/artifact → durable delivery proof`.

    DELPI_REPORTS_EMAIL_TRANSPORT = PROVEN
    DELPI_REPORTS_GENERIC_PACKAGE_DELIVERY = NOT_PROVEN

Adicionar provider P5 no api-delpi sem mudar explicitamente o boundary faria Reports conhecer semântica de `PackageVersion`, contrariando ownership.

## 4. Microsoft Graph sendMail

O adapter atual suporta N recipients, HTML, file attachments, retry e `saveToSentItems=true`. Sucesso de transport é HTTP 202.

Documentação oficial Microsoft: 202 significa request accepted; não significa processamento concluído nem entrega concluída.

    GRAPH_202 != PACKAGE_SENT

## 5. Message Trace — padrão runtime existente

CIPA e Transformômetro possuem `MicrosoftGraphMessageTraceClient` + reconciliation service.

Estados já modelados nesses contexts:

    sendStatus: pending | accepted | failed | skipped*
    deliveryStatus: trace_pending | delivered | bounced | unknown

O trace trata delivered, failed, filteredAsSpam, quarantined e unknown.

    SEND_ACCEPTED != DELIVERED

Não existe serviço transversal compartilhado provado para mail trace.

## 6. Alternativas

### A — P5/BFF owns delivery orchestration; Graph + Message Trace são adapters

    controllership-finance-api
    → DeliveryPort
    → Microsoft Graph Mail adapter
    → Message Trace adapter

P5 mantém ownership de package/version/recipient/delivery attempt/idempotency/business state.

Impactos positivos: segue bounded context, replica padrão já usado por CIPA/Transformômetro, não move regra P5 para Core/api-delpi, permite auditoria/idempotência no owner.

Custos: adapter Graph, credenciais governadas, persistência de attempts, reconciliation, correlação robusta e integration tests.

### B — evoluir Delpi Reports para capability S2S genérica de artifact delivery

    controllership-finance-api
    → api-delpi/reports generic delivery contract
    → Graph

Positivo: reutiliza transport/attachments/retry/runs.

Risco: amplia Reports de report-provider para corporate delivery; exige novo S2S contract, message trace/proof e decisão de platform ownership; maior blast radius.

### C — criar capability corporativa nova de Delivery

Exemplo conceitual: `document-delivery-api` ou equivalente.

Positivo: ownership transversal explícito e reutilizável.

Risco: novo bounded context, owner, infra, secrets, observability e adoção; custo maior para V1 e demanda multi-produto ainda não provada.

## 7. Alternativas rejeitadas sem decisão explícita

- estender Core Notifications para package delivery por conveniência;
- criar provider P5 dentro de Reports sem mudar boundary;
- MFE chamar Graph/Core/api-delpi diretamente.

## 8. Canal

| Canal | Evidência |
|---|---|
| Microsoft Graph e-mail + attachments | PROVEN |
| Exchange Message Trace | PROVEN em CIPA/Transformômetro |
| Core notification inbox | PROVEN, mas não package delivery |
| Teams package delivery | NOT_PROVEN |
| SharePoint package delivery | NOT_PROVEN |
| corporate generic document-delivery service | NOT_PROVEN |

E-mail via Graph é o único canal com transport + attachment + delivery trace concretamente provados no HEAD. Isso sustenta recomendação, não aprovação.

## 9. Semântica de PACKAGE_SENT

### S1 — Graph accepted

    HTTP 202 → PACKAGE_SENT

Mais simples, mas não prova delivery concluída.

### S2 — Exchange delivered

    HTTP 202
    → sendStatus=ACCEPTED
    → deliveryStatus=TRACE_PENDING
    → Message Trace=DELIVERED
    → PACKAGE_SENT

Separa transport acceptance de delivery e não exige read/ack.

### S3 — accepted + proof reconciled later

    HTTP 202 → PACKAGE_SENT
    Message Trace → DELIVERY_PROOF later

Permite conclusão antes da confirmação e exige regra posterior para bounce.

## 10. Recomendação — NÃO APLICADA

Architecture recommendation: **A — P5/BFF owns delivery orchestration, com Graph + Message Trace como infrastructure adapters.**

Business outcome recommendation: **S2 — `PACKAGE_SENT` somente após Message Trace `DELIVERED`.**

Rationale:
- menor expansão coerente com ownership;
- segue padrão runtime já existente;
- evita transformar Core/api-delpi em owner P5;
- 202 não prova delivery;
- delivered não é read/ack, então preserva a regra V1 de acknowledgement não bloqueante.

## 11. Contrato recomendado se A + S2 forem aprovados

    P5 PackageVersion
    → create DeliveryAttempt
    → enforce idempotency
    → Graph sendMail with attachment(s)
    → 202 = SEND_ACCEPTED only
    → trace reconciliation
    → DELIVERED = delivery proof
    → PackageRecipient = PACKAGE_SENT
    → all applicable recipients sent AND no open clarification
    → MONTHLY_CLOSING_COMPLETED

Falhas recomendadas:
- Graph rejection → FAILED;
- trace pending → não enviado ainda;
- bounce/quarantine → não enviado;
- unknown/trace expired → UNKNOWN, sem optimistic completion;
- retry somente por operação governada/idempotente.

Não definir endpoint/path/schema físico nesta fase.

## 12. Segurança

    authenticated actor
    AND effective_permission(controllership-finance.access)
    AND resource_scope/ownership
    AND package business_rule

Graph token/secret, attachments e trace ficam backend-only. Nenhum secret/token no MFE/logs comuns.

## 13. Test matrix futura

Positive: finalized + authorized → accepted → delivered → PACKAGE_SENT; recipients independentes; attachment válido.

Sibling: A não promove B; bounce B não reverte A; complement V2 não altera proof V1.

Negative: sem ACCESS; fora do scope; package não finalizado; duplicate request; 202 tratado como delivered; bounce/quarantine/unknown tratados como success; source/attachment unavailable; secret leak.

Integration: Graph 202/4xx/429/5xx/timeout + trace delivered/bounced/quarantined/unknown/expired.

## 14. DECISION_REQUIRED

    D-P5-DELIVERY-OWNER
    A = P5/BFF owns orchestration + Graph/Trace adapters
    B = evolve Delpi Reports to generic delivery
    C = create corporate Delivery capability

    D-P5-PACKAGE-SENT-OUTCOME
    S1 = Graph accepted
    S2 = Message Trace delivered
    S3 = accepted + proof reconciled later

Recomendação:

    D-P5-DELIVERY-OWNER = A
    D-P5-PACKAGE-SENT-OUTCOME = S2

    DECISION_REQUIRED
    NO CHANGE APPLIED
    IMPLEMENTATION_AUTHORIZED = NO
