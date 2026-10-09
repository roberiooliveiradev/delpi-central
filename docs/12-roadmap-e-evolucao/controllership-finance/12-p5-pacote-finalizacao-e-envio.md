# 12 — P5 — Pacote, Finalização e Envio

**TARGET / PAGE_DOCUMENTATION_GATE_V2 PARTIAL / PORTAL_SUBMISSION_MODEL_PASS / MONTHLY_COMPLETION_DECISION_REQUIRED**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

VISUAL_SPEC_DEFINED          = PASS
PACKAGE_CONTRACT_DEFINED     = PASS
SUBMISSION_CONTRACT_DEFINED  = PASS
REVIEW_CONTRACT_DEFINED      = PASS
MONTHLY_COMPLETION_RULE      = DECISION_REQUIRED
AUTHZ_DEFINED                = PASS
PLUGIN_UI_REUSE_DEFINED      = PASS
STATES_DEFINED               = PASS
TEST_MATRIX_DEFINED          = PASS
```

> Este documento fecha P5 no nível de package/finalization/submissão in-portal/revisão, experiência, AuthZ, plugin-ui, Help e aceite visual. Não autoriza runtime. A premissa de delivery externo do documento 36 foi invalidada; o contrato vigente é o documento 37.

## Objetivo da página

Versionar o pacote do fechamento, permitir finalização controlada, acompanhar pacotes por destinatário, tratar esclarecimentos e preservar histórico sem confundir:

```text
READY_TO_FINALIZE
!= PACKAGE_FINALIZED
!= PACKAGE_SUBMITTED_FOR_REVIEW
!= REVIEW_ACCEPTED
!= MONTHLY_CLOSING_COMPLETED
```

A página deve responder, em ordem:

1. qual competência/contexto está sendo operado;
2. quais destinatários possuem pacote aplicável;
3. quais blockers impedem finalização;
4. qual versão está em trabalho/finalizada;
5. quais pacotes já foram enviados por capability comprovada;
6. quais esclarecimentos permanecem abertos;
7. qual histórico de versão/entrega existe.

## Invariantes

```text
FINALIZE != SEND
PACKAGE_FINALIZED != PACKAGE_SUBMITTED_FOR_REVIEW
PACKAGE_SUBMITTED_FOR_REVIEW = IMMUTABLE
RECIPIENT_PACKAGE_A != RECIPIENT_PACKAGE_B
SUBMISSION != NOTIFICATION
NO_OPEN_CLARIFICATION is required for monthly completion
UI_VISIBILITY != AUTHORIZATION
```

- Finalizar cria snapshot/versão; não envia.
- Um destinatário avança independentemente dos demais.
- Versão submetida para análise é histórica e não é alterada in-place.
- Correção após submissão cria complemento/nova versão ligada à anterior.
- Não existe botão de force completion.
- A conclusão mensal depende da decisão pendente sobre o outcome da revisão; leitura de notificação/e-mail nunca é critério de negócio.
- O package permanece na Minha DELPI; e-mail é apenas notification channel.
- A UI apresenta `Enviar para análise` somente quando o package está finalizado e os reviewers/resource scopes aplicáveis estão resolvidos.


## Responsabilidade, owners e non-goals

| Capability/dado | Owner |
|---|---|
| recipient package / version / finalization | P5 / `controllership-finance-api` |
| blockers/readiness inputs | P2/P3/P4 owners, compostos por P5 |
| esclarecimentos do pacote | P5 |
| histórico/versionamento do pacote | P5 |
| effective permissions | Core |
| user-facing notifications | Core Notifications / Minha DELPI capability |
| submissão para análise / reviewer state | P5 / `controllership-finance-api` |
| notifications in-app/e-mail | Core Notifications / Minha DELPI |
| chrome visual | `@delpi/plugin-ui` |

Não pertence a P5:
- sacramentar estoque;
- reabrir P3 após `STOCK_CLOSED`;
- transformar e-mail/notificação em estado de negócio;
- transportar o package como attachment de e-mail na V1;
- criar permission por destinatário/reviewer;
- alterar versão submetida in-place;
- force completion.

Decisão E02 aplicada:
- `STOCK_CLOSED` é terminal no lifecycle P3 do Portal V1;
- uma correção posterior do owner não reabre P3;
- P5 preserva histórico e usa complemento/nova versão quando seu próprio lifecycle exigir correção pós-envio.


## Lifecycle do pacote

### Preparação e finalização

```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED_V1
```

Finalizar exige que os requisitos aplicáveis permitam avanço.

### Reabertura antes do envio

```text
FINALIZED_V1
→ REOPEN_WITH_REASON
→ WORKING_COPY
→ FINALIZED_V2
```

A versão anterior permanece histórica.

### Envio para análise — submissão in-portal

```text
PACKAGE_FINALIZED
→ SUBMIT_FOR_REVIEW
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ REVIEW_PENDING
```

A ação "Enviar para análise":
- não envia attachment por e-mail;
- disponibiliza a versão finalizada aos reviewers autorizados dentro da Minha DELPI;
- registra actor/timestamp/version/reviewer scope;
- emite evento de notification;
- mantém a PackageVersion read-only.

### Esclarecimentos

Por destinatário:

```text
PACKAGE_SUBMITTED_FOR_REVIEW
→ WAITING_FOR_CLARIFICATION
→ CLARIFICATION_RESOLVED
```

### Correção após submissão

```text
PACKAGE_SUBMITTED_FOR_REVIEW_V1
→ COMPLEMENT_OR_NEW_VERSION
→ LINK_TO_V1
→ NEW_SUBMISSION_FOR_REVIEW
```

Motivo obrigatório; V1 permanece imutável.

### Conclusão mensal

```text
ALL_APPLICABLE_RECIPIENT_PACKAGES_SENT
AND
NO_OPEN_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

Sem ação independente para “forçar conclusão”.

## Arquitetura de informação

```text
PagePath
→ PageHero / competência
→ blockers / readiness de pacote
→ pacotes por destinatário
→ detalhe do pacote selecionado
   → resumo/status
   → itens/versão
   → finalização/reabertura quando autorizadas
   → review status / reviewer assignment
   → esclarecimentos
   → histórico de versões/submissões/reviews
→ Help contextual
```

A unidade principal é o **recipient package** dentro da competência.

A página não deve representar o estado mensal inteiro como um único percentual.

## Jornada principal — package/finalization

```text
Abrir P5
→ carregar competência e recipient packages
→ selecionar destinatário
→ revisar blockers e itens
→ atingir READY_TO_FINALIZE
→ usuário autorizado finaliza
→ backend valida business rules
→ snapshot/version criado
→ PACKAGE_FINALIZED
→ histórico atualizado
```

Se houver reabertura antes do envio:

```text
PACKAGE_FINALIZED
→ reabrir com motivo
→ working copy
→ corrigir
→ finalizar nova versão
```

## Jornada de envio para análise

```text
PACKAGE_FINALIZED
→ usuário autorizado escolhe "Enviar para análise"
→ backend revalida ACCESS + resource_scope + business_rule
→ resolve reviewers Core identities/resource scope
→ grava submission audit
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ REVIEW_PENDING
→ emite Core Notification
→ reviewer acessa Minha DELPI pelo deep link autorizado
```

A falha do e-mail de notification não reverte a submission. O package não é anexado ao e-mail.

## Wireframe — desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ PagePath                                                                     │
│ Pacote, Finalização e Envio                                                  │
│ Competência / contexto / Help                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ Blockers / readiness                                                         │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ PACOTES POR DESTINATÁRIO      │ DETALHE DO PACOTE                            │
│                               │                                              │
│ [status] Contábil             │ Contábil                                     │
│ versão • estado               │ Estado • versão • finalizado em/por           │
│                               │                                              │
│ [status] Fiscal               │ Itens / resumo                               │
│ versão • estado               │                                              │
│                               │ Ações: finalizar/reabrir quando autorizadas   │
│ ...                           │                                              │
│                               │ Review status / reviewers     │
│                               │                                              │
│                               │ Esclarecimentos                               │
│                               │                                              │
│                               │ Histórico de versões/entregas                 │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

Desktop usa master-detail com `ResizableColumns`.

A lista de recipient packages pode usar `DataTableSection` quando houver densidade suficiente; cards são válidos para baixa cardinalidade.

## Wireframe — mobile

```text
PagePath
→ PageHero compacto
→ blockers/readiness
→ lista de recipient packages
→ selecionar pacote
→ detalhe full-width
   → BackLink
   → status/versão
   → itens
   → ações autorizadas
   → review status / reviewers
   → esclarecimentos
   → histórico
```

No mobile:

- não manter split comprimido;
- destinatários aparecem como cards;
- retorno preserva competência e seleção/filtros;
- finalizar/reabrir fica próximo ao contexto correspondente;
- `Enviar para análise` aparece somente após FINALIZED e reviewers resolvidos;
- histórico não perde legibilidade por largura.

## Recipient package

Cada pacote deve expor, quando disponível:

- destinatário;
- estado;
- versão corrente;
- blockers;
- `finalizedAt` / ator quando aplicável;
- `submittedAt` / review state / submittedAt quando aplicável;
- esclarecimentos abertos;
- relação com versões anteriores/complementos.

Não derivar:
- envio concluído a partir de finalização;
- conclusão mensal a partir de um único destinatário;
- notification/e-mail success tratado como business completion;
- ack obrigatório se contract não exigir.

## Finalização

A ação `Finalizar`:

- existe somente em `READY_TO_FINALIZE`;
- cria versão/snapshot;
- não envia;
- registra ator/timestamp;
- preserva inputs/version usados;
- é revalidada no backend.

Após sucesso:

```text
PACKAGE_FINALIZED
```

A UI deve usar linguagem inequívoca: “Finalizar pacote”, nunca “Concluir fechamento” ou “Enviar”.

## Reabertura antes do envio

Quando autorizada:

- exige motivo;
- versão finalizada anterior permanece read-only;
- cria working copy ou equivalente contratual;
- nova finalização cria nova versão;
- histórico mostra relação entre versões.

A UI não edita silenciosamente uma versão finalizada.

## Submissão para análise e notifications

Contrato vigente:

```text
PACKAGE_TRANSPORT_BY_EMAIL = NO
PACKAGE_STAYS_IN_MINHA_DELPI = YES
EXTERNAL_REVIEWER_LOGIN_REQUIRED = YES
EMAIL_AS_NOTIFICATION_ONLY = YES
```

Reviewers externos da Controladoria são usuários autenticados da Minha DELPI.

AuthZ mínima:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND reviewer_assignment/resource_scope
AND package_business_rule
```

Após submit:
- package fica acessível somente aos reviewers autorizados;
- P5 emite notification event;
- Core Notifications registra in-app notification;
- a plataforma pode também enviar e-mail conforme configuração/preferência;
- o e-mail contém aviso/link para a Minha DELPI, não o package.

```text
NOTIFICATION_FAILURE != PACKAGE_SUBMISSION_FAILURE
EMAIL_SENT != PACKAGE_SUBMITTED_FOR_REVIEW
```

Authority:
- [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md).

## Esclarecimentos

Após `PACKAGE_SUBMITTED_FOR_REVIEW`, o reviewer pode iniciar análise e, quando necessário, abrir esclarecimento.

A UI deve exibir:

- destinatário;
- status;
- questão/assunto quando contract fornecer;
- ator/timestamp;
- resolution state;
- histórico.

Resolver esclarecimento não reabre automaticamente pacote enviado.

Se uma correção de conteúdo for necessária, aplicar o fluxo de complemento/nova versão.

## Histórico

Eventos mínimos:

- `PACKAGE_VERSION_CREATED`
- `PACKAGE_FINALIZED`
- `PACKAGE_REOPENED`
- `PACKAGE_SUBMITTED_FOR_REVIEW`
- `PACKAGE_REVIEW_STARTED`
- `PACKAGE_REVIEW_CHANGES_REQUESTED`
- `PACKAGE_REVIEW_ACCEPTED`
- `CLARIFICATION_OPENED`
- `CLARIFICATION_RESOLVED`
- `PACKAGE_COMPLEMENT_CREATED`
- `MONTHLY_CLOSING_COMPLETED`

Usar timeline auditável.

Pacote enviado e versões antigas permanecem read-only.

## Contratos TARGET — MFE → BFF → owners

```text
plugins/controllership-finance
→ controllership-finance-api
   → P2/P3/P4 read contracts
   → Core effective permissions
   → Core Notifications para comunicação user-facing
   → Core identities/effective permissions para reviewers
```

Operações semânticas já fechadas:

| Operação | Estado |
|---|---|
| listRecipientPackages | DEFINED |
| getRecipientPackage | DEFINED |
| finalizePackage | DEFINED |
| reopenFinalizedPackageBeforeSend | DEFINED |
| createComplementOrNewVersion | DEFINED |
| listClarifications | DEFINED |
| resolveClarification | DEFINED |
| getPackageHistory | DEFINED |
| deriveMonthlyClosingCompletion | DEFINED |
| notifyUserAboutPackageEvent | DEFINED at capability level via Core Notifications |
| submitPackageForReview | DEFINED — in-portal submission; doc 37 |
| getReviewerPackage / startReview / requestChanges / acceptReview | DEFINED at semantic level; exact DTOs/routes TO_INVENTORY |

### Finalization contract

`finalizePackage`:
- exige READY_TO_FINALIZE;
- cria snapshot/version imutável;
- registra actor/timestamp;
- não chama delivery;
- não produz PACKAGE_SUBMITTED_FOR_REVIEW.

### Submission/review contract

```text
PACKAGE_FINALIZED
→ submitPackageForReview
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ REVIEW_PENDING
```

Regras:
- package permanece armazenado/consultado na Minha DELPI;
- reviewer é Core identity com app access;
- reviewer assignment/resource scope limita o acesso;
- submit não depende de transport externo;
- Core notification/e-mail são side effects de comunicação;
- falha de notification não altera o business state.

A semântica de monthly completion permanece pendente no documento 37.

### AuthZ

Toda leitura/ação exige:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND resource_scope / ownership
AND business_rule
```

A operação de submit/review revalida actor + package state + reviewer assignment/resource scope + business rule no backend.

## Reuso obrigatório de `@delpi/plugin-ui`

Import preferencial:

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  ResizableColumns,
  DataTableSection,
  DataRecordCard,
  DetailFieldGrid,
  ReadOnlyField,
  ProgressTracker,
  StatusBadge,
  AlertQueue,
  Timeline,
  StateBanner,
  StateBox,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  ActionButton,
  BackLink,
  HelpTooltip,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Uso esperado:

| Necessidade | Reuso |
|---|---|
| path/contexto | `createDashboardPagePath` + `createDashboardPageHero` |
| readiness/blockers | `AlertQueue` / `StateBanner` |
| lifecycle visual | `ProgressTracker` quando ajuda a explicar state progression |
| master-detail | `ResizableColumns` |
| recipient list desktop | `DataTableSection` |
| recipient list mobile | `DataRecordCard` |
| status | `StatusBadge` |
| resumo do pacote | `DetailFieldGrid` / `ReadOnlyField` |
| seções | `SectionCard` |
| histórico | `Timeline` |
| confirmação | `ModalShell` + `ConfirmModalPanel` |
| feedback | `FloatingNoticeStack` |
| loading/empty | `LoadingState` / `EmptyState` |
| retorno mobile | `BackLink` |
| ajuda curta | `HelpTooltip` |

**DO NOT RECREATE:** master-detail, recipient table/cards, state chrome, lifecycle chrome, detail fields, timeline, modal/confirm, notices ou HelpTooltip.

Não criar componente de delivery externo. A UX deve reutilizar primitives existentes para submit/review/status/history. Se a implementação provar gap real de reviewer workflow no kit, avaliar contribuição ao `plugin-ui`.

## Estados de experiência

### LOADING

- primeira leitura usa loading do kit;
- não assumir zero recipient packages;
- não mostrar conclusão falsa.

### REFRESHING

- preservar conteúdo anterior quando seguro;
- indicar refresh;
- falha de refresh não apaga version/history previamente válida quando contract permitir.

### SUCCESS

- lista e detalhe refletem estado atual;
- cada recipient package mantém estado independente.

### EMPTY

Usar somente se o contrato provar ausência de pacotes aplicáveis.

`EMPTY != SOURCE_UNAVAILABLE`.

### PARTIAL

Quando uma source/recipient falhar:

- preservar siblings válidos;
- exibir coverage/source failure;
- não elevar competência para completa;
- não converter pacote desconhecido em “não aplicável”.

### UNAVAILABLE / UNAVAILABLE_SOURCE

- não transformar source indisponível em blocker resolvido;
- não produzir READY_TO_FINALIZE por ausência de dados;
- retry somente quando contract suportar.

### VALIDATION_ERROR

- preservar contexto;
- mostrar motivo da ação inválida;
- nenhuma transição otimista permanece se backend rejeitar.

### ERROR

- erro explícito;
- retry local quando seguro;
- sem vazamento técnico.

### FORBIDDEN — 403

Sem ACCESS ou sem resource ownership/context access:
- não renderizar dados protegidos;
- MANAGE não bypassa ACCESS.

### NOT_FOUND — 404

Pacote/competência inexistente ou inacessível conforme política do contract.

A página não decide enumeração localmente.

## AuthZ

Base:

```text
authenticated identity
AND effective_permission(controllership-finance.access)
AND resource_scope / ownership
AND business_rule
```

Para toda ação:

- backend reautoriza;
- UI não é authority;
- MANAGE não implica ACCESS;
- nenhum permission code por destinatário, finalização, envio ou esclarecimento;
- filial/unidade permanece dimensão de dado/contexto.

## URL / deep link / F5

Preservar semanticamente quando aplicável:

- competência;
- destinatário selecionado;
- versão;
- filtro/status;
- origem/return context seguro.

Nomes físicos de path/query params ficam para router/OpenAPI futuro.

F5 reconstrói contexto sem depender apenas de state frontend.

Nunca aceitar open redirect.

## Light / dark

Mesma árvore conceitual.

- tokens do Portal/`plugin-ui`;
- status não depende apenas de cor;
- `PACKAGE_FINALIZED`, `PACKAGE_SUBMITTED_FOR_REVIEW` e review states têm labels inequívocos;
- nenhum CSS de componente do kit no MFE.

## Acessibilidade

Obrigatório:
- headings semânticos;
- status textual;
- lista/detalhe navegáveis por teclado;
- foco visível;
- modal com focus trap;
- confirmação "Enviar para análise" com texto inequívoco;
- mudança de recipient package preserva lógica de foco;
- review actions e histórico legíveis por leitor de tela;
- notification não substitui estado visível na página.

## Help

Help contextual deve explicar:
- finalizar != enviar para análise;
- enviar para análise = disponibilizar dentro da Minha DELPI;
- reviewer acessa com login e `controllership-finance.access` + resource scope;
- e-mail é apenas notificação e leva ao Portal;
- package não vai anexado por e-mail;
- versionamento;
- recipient packages independentes;
- review/clarification/correction;
- regra de conclusão mensal após decisão pendente.

Fonte canônica:
- [29-ajuda.md](./29-ajuda.md);
- [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md).

## RQ / aceite visual

### RQ-P5-01 — blockers impedem finalização
- READY_TO_FINALIZE só aparece quando rules aplicáveis permitem;
- blocker/source failure permanece visível.

### RQ-P5-02 — finalizar cria versão
- "Finalizar pacote";
- sucesso → `PACKAGE_FINALIZED`;
- não submete e não notifica reviewers ainda.

### RQ-P5-03 — reabertura preserva versão
- motivo obrigatório;
- versão anterior read-only;
- nova working/version distinta.

### RQ-P5-04 — recipient packages independentes
- ação/status de A não altera B.

### RQ-P5-05 — enviar para análise é in-portal
- exige FINALIZED;
- sucesso → `PACKAGE_SUBMITTED_FOR_REVIEW`;
- package permanece na Minha DELPI;
- não existe attachment delivery por e-mail.

### RQ-P5-06 — reviewer authenticated
- reviewer possui login Minha DELPI;
- exige `controllership-finance.access`;
- exige reviewer assignment/resource scope;
- MANAGE não é necessário.

### RQ-P5-07 — notification side effect
- submit gera notification in-app;
- e-mail pode ser enviado pela capability Core;
- falha de e-mail não reverte submission;
- notification contém deep link, não package attachment.

### RQ-P5-08 — review history
- reviewer/action/outcome/version/timestamps auditáveis;
- versão submetida não é editada in-place.

### RQ-P5-09 — clarification/correction
- reviewer pode solicitar esclarecimento/correção;
- nova versão/complemento preserva histórico.

### RQ-P5-10 — Help
- manual explica finalize vs submit vs notify vs review;
- nenhuma instrução de attachment delivery por e-mail.

### RQ-P5-11 — monthly completion
- **DECISION_REQUIRED**: submission suficiente vs review accepted obrigatório vs regra configurável.

## Testes futuros mínimos

### Positive
- READY_TO_FINALIZE → finalize;
- FINALIZED → submit for review;
- reviewer autorizado vê package;
- notification in-app;
- e-mail notification habilitado;
- deep link autenticado;
- start review;
- clarification roundtrip;
- review outcome auditado.

### Sibling
- submit recipient A não submete B;
- reviewer A não vê B;
- falha de e-mail não altera submission;
- clarification A não altera sibling;
- nova versão não apaga review anterior.

### Negative
- sem ACCESS;
- MANAGE sem ACCESS;
- reviewer sem assignment/resource scope;
- submit antes de FINALIZED;
- reviewer editando PackageVersion;
- package anexado por e-mail;
- deep link bypassando AuthZ;
- notification enviada a usuário sem app access;
- force completion;
- open redirect.

### Experiência
- loading;
- refreshing;
- success;
- empty;
- partial;
- unavailable;
- validation error;
- error;
- 403;
- 404;
- desktop/mobile;
- light/dark;
- keyboard/focus;
- Help.

## Scripts e artefatos auxiliares PLANNED

```text
validate-p5-package-lifecycle
- FINALIZE != SUBMIT_FOR_REVIEW
- submitted version immutable
- recipient siblings independent

validate-p5-review-authz
- ACCESS + reviewer assignment/resource scope
- no reviewer permission code
- MANAGE does not bypass ACCESS

validate-p5-notification-boundary
- submit emits notification event
- e-mail is notification only
- notification failure != submission failure
- no package attachment

validate-p5-review-lifecycle
- pending/in-progress/changes-requested/accepted
- history/version preserved

validate-p5-task-projection
- actionable reviewer work appears self-only
- owner remains P5

validate-p5-completion-rule
- BLOCK until D-P5-REVIEW-COMPLETION is decided

validate-p5-help
- finalize/submit/notify/review terminology synchronized

validate-p5-plugin-ui
- master-detail/lifecycle/timeline/modal reused
- no local clone
```

Não criar durante a FASE A.

## E04/T04 — reclassificação

A premissa "delivery externo do package" foi invalidada pelo Product Owner.

```text
E04_EXTERNAL_DELIVERY = NOT_REQUIRED_IN_V1
T04_EXTERNAL_DELIVERY_CAPABILITY = NOT_REQUIRED_IN_V1
```

O documento 36 permanece como inventário histórico superseded.

Authority TARGET:
- [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md).

Inventários físicos futuros:
- reviewer assignment storage/binding;
- Core identity lookup/effective access;
- notification category/template/action target;
- exact review DTOs/routes;
- TaskProjection adapter;
- deep-link params.

## Gate documental V2

```text
OBJECTIVE_BOUNDARY_DEFINED  = PASS
OWNERS_DEFINED              = PASS
VISUAL_SPEC_DEFINED         = PASS
PACKAGE_CONTRACT_DEFINED    = PASS
SUBMISSION_CONTRACT_DEFINED = PASS
REVIEW_CONTRACT_DEFINED     = PASS
NOTIFICATION_MODEL_DEFINED  = PASS
AUTHZ_DEFINED               = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS
STATES_DEFINED              = PASS
DEEP_LINK_F5_DEFINED        = PASS
RESPONSIVE_DEFINED          = PASS
LIGHT_DARK_DEFINED          = PASS
A11Y_DEFINED                = PASS
HELP_SYNC_DEFINED           = PASS
RQ_AC_DEFINED               = PASS
TEST_MATRIX_DEFINED         = PASS
SCRIPTS_ARTIFACTS_PLANNED   = PASS
MONTHLY_COMPLETION_RULE     = DECISION_REQUIRED
IMPLEMENTATION_AUTHORIZED   = NO
```

Resultado:

```text
A12 P5 PACOTE, FINALIZAÇÃO E ENVIO
= PORTAL_SUBMISSION_MODEL_DEFINED
+ REVIEW_MODEL_DEFINED
+ MONTHLY_COMPLETION_DECISION_REQUIRED
!= FULL_PAGE_READY_FOR_IMPLEMENTATION_BRIEF
!= IMPLEMENTED
```
