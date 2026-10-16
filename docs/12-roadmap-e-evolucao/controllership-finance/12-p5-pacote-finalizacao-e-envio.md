# 12 — P5 — Pacote, Finalização e Envio

**TARGET / A12 POST-MERGE REVALIDATION / C2 AND P5-A..J + DEC-01..04 PO_APPROVED / PHYSICAL_BINDINGS_TO_INVENTORY**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

VISUAL_SPEC_DEFINED          = PASS
PACKAGE_CONTRACT_DEFINED     = PASS
SUBMISSION_CONTRACT_DEFINED  = PASS
REVIEW_CONTRACT_DEFINED      = PASS
MONTHLY_COMPLETION_RULE      = C2_PO_APPROVED / BY_REQUIRED_AREA_AND_CURRENT_VERSION
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
5. quais pacotes já foram submetidos para análise e qual o estado de review;
6. quais esclarecimentos permanecem abertos;
7. qual histórico de versões, submissões, reviews e esclarecimentos existe.

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
- A conclusão mensal segue a regra C2 aprovada (todas as áreas obrigatórias da versão vigente aceitam, sem esclarecimentos abertos); depende do binding técnico sobre o outcome da revisão; leitura de notificação/e-mail nunca é critério de negócio.
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

A submissão in-portal está fechada, mas o completion gate permanece decisão material:

```text
D-P5-REVIEW-COMPLETION = C2_APPROVED
```

Opções canônicas e recomendação estão em [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md).

Nenhuma implementação deve derivar `MONTHLY_CLOSING_COMPLETED` apenas de submit/notification enquanto essa decisão não for fechada.

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
│                               │ Histórico de versões/submissões/reviews       │
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

Resolver esclarecimento não reabre automaticamente a PackageVersion submetida.

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

PackageVersion submetida e versões históricas permanecem read-only.

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
- não submete para review;
- não dispara notification;
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
MONTHLY_COMPLETION_RULE     = C2_PO_APPROVED / QUORUM_BY_REQUIRED_AREA
IMPLEMENTATION_AUTHORIZED   = NO
```

Resultado:

```text
A12 P5 PACOTE, FINALIZAÇÃO E ENVIO
= PORTAL_SUBMISSION_MODEL_DEFINED
+ REVIEW_MODEL_DEFINED
+ C2_AND_REQUIRED_AREA_QUORUM_PO_APPROVED
= TARGET_SEMANTICS_DEFINED / PHYSICAL_BINDINGS_TO_INVENTORY
!= IMPLEMENTED
```


## Decisões PO P5-F a P5-J — consolidação contratual vigente (16/10/2026)

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este adendo é superveniente aos registros de perguntas abertas P5-F..J e prevalece quando notas históricas anteriores conflitarem. C2, D-P5-02..05 e P5-A..E permanecem válidas nos termos abaixo. A antiga unanimidade de *pessoas* em D-P5-01 foi substituída pela unanimidade das *áreas obrigatórias* em P5-A.

| ID | Resultado aprovado | Invariante |
|---|---|---|
| **P5-F = A** | Substituição de responsável mantém válido o aceite já realizado para a mesma área e PackageVersion; a autoria permanece a do executor original. Substituto assume somente ações futuras. | REASSIGNMENT != INVALIDATE_PRIOR_ACCEPTANCE |
| **P5-G = A** | Aceite P5 não é reversível/alterável pela UI V1. DEC-03 exclui qualquer processo de reversão/retificação do aceite P5 **dentro do Portal V1**, inclusive endpoint ou override; incidentes são tratados fora do fluxo. | NO_P5_ACCEPTANCE_REVERSAL_IN_V1 |
| **P5-H = A** | P6 configura por tipo de pacote as áreas/especialidades obrigatórias em versão governada; P5 congela a configuração aplicável na submissão. Core fornece identidade, effective permissions e atributos de grupo/função conforme contrato a inventariar. | REVIEW_AREA_SET_SNAPSHOTTED_ON_SUBMISSION |
| **P5-I = B** | Reviewer elegível registra rejeição do pacote em nome da área; uma **autoridade operacional formalmente definida**, distinta da simples permission MANAGE, confirma com justificativa e auditoria a rejeição terminal da competência. | AREA_PACKAGE_REJECTION != TERMINAL_COMPETENCE_REJECTION |
| **P5-J = A** | Após confirmação da rejeição terminal, a competência fica rejeitada e todas as projeções/tarefas de revisão ainda acionáveis deixam de sê-lo; histórico, decisões e autoria permanecem consultáveis conforme AuthZ. | REJECTED_COMPETENCE != MONTHLY_CLOSING_COMPLETED |

### Compatibilidade com regras anteriores

- **C2:** competência concluída somente se TODOS os pacotes aplicáveis foram submetidos, TODAS as áreas obrigatórias aceitaram a PackageVersion vigente e NÃO há esclarecimento aberto. Competência rejeitada nunca satisfaz `MONTHLY_CLOSING_COMPLETED`.
- **P5-A / D-P5-01:** quorum de um aceite por área obrigatória, executado por qualquer usuário elegível; não por indivíduo. Dois elegíveis na mesma área não criam dois aceites necessários.
- **P5-B / D-P5-03 / P5-G:** ninguém sobrescreve aceites; nem o autor pode revertê-los pela UI V1. A referência antiga a “autor pode alterar” é **superseded para aceite P5 na V1**. Reatribuição formal não autoriza mutação de decisões anteriores.
- **P5-C / D-P5-04:** ACCESS efetivo + grupo/função corporativa elegível + escopo do recurso + regra da ação; avaliação server-side fail-closed; reviewer assignment nunca se torna novo permission code.
- **D-P5-02 / P5-E:** esclarecer sem alterar conteúdo preserva versão; qualquer alteração de conteúdo cria nova PackageVersion e **exige novos aceites de todas as áreas obrigatórias**; histórico de versões anteriores preservado.
- **D-P5-05 / P5-D / P5-I:** `CHANGES_REQUESTED` não é `REVIEW_REJECTED`; rejeição da área/pacote não encerra competência automaticamente; só confirmação por autoridade operacional a leva ao estado terminal rejeitado.
- **P5-F / P5-H:** reatribuir elegível não altera aceite já registrado, nem o snapshot de áreas obrigatórias da submissão; edição futura do catálogo P6 não altera snapshots abertos.
- **P5-J:** `TaskProjection != TaskEntity`; P5 continua owner do lifecycle; revisão terminal rejeitada remove acionabilidade, sem hard delete nem apagamento de evidências.

### Trilha de auditoria obrigatória

Preservar identidade Core do ator, data/hora, ação, contexto competência/recipient package, versão, área obrigatória, elegibilidade/scope verificados, motivo/justificativa quando exigidos, estado anterior/posterior, autor original do aceite, referência a reatribuições, confirmação formal da rejeição e correlação da projeção/notificação. Histórico é append-only no nível semântico; **schema físico não definido**.

### Pendências reais — sem aprovação presumida

1. **PO_APPROVED DEC-01/02:** a pessoa formalmente designada para coordenar o fechamento da competência confirma rejeição terminal apenas com ACCESS efetivo, vínculo operacional, scope e business rule; se não confirmar, registra motivo e mantém decisão pendente, com possível devolução auditada para esclarecimento/correção. **TO_INVENTORY:** fonte operacional da designação/substituição e binding técnico, sem usar MANAGE como atalho.
2. **PO_APPROVED DEC-03:** retificação/reversão de aceite P5 não existe **nem por UI nem por endpoint na V1**. Incidentes são registrados fora do fluxo do Portal; não criar mecanismo excepcional, override ou alteração de banco para essa capability.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **PO_APPROVED P5-H/DEC-04; PHYSICAL_BINDING_TO_INVENTORY:** P6 versiona áreas obrigatórias por tipo de pacote e MANAGE+administrative scope publica prospectivamente com motivo e auditoria; P5 congela snapshot por submissão. Falta inventariar schema/DTO/OCC, source de função/grupo, vigência e tratamento de configuração ausente, sem criar tabelas/migrations antecipadas.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.


## Decisões finais do PO — DEC-01 a DEC-04 (16/10/2026)

**TARGET / PO_APPROVED / NOT_IMPLEMENTED.** Vigência: este contrato substitui referências históricas a `DECISION_REQUIRED` sobre autoridade de rejeição, negativa de confirmação, exceção de reversão na V1 e publicador P6. Não equivale a evidence de testes ou freeze.

| ID | Decisão aprovada | Contrato normativo |
|---|---|---|
| DEC-01 | Responsável formal da Controladoria | A pessoa designada para coordenar o fechamento da competência pode confirmar rejeição terminal **somente** com `controllership-finance.access` efetivo, vínculo operacional, escopo do recurso e business rule verificados server-side. `manage` isolado não concede essa autoridade. A designação/substituição deve ser auditada; owner da identidade/permissão é Core; owner do vínculo operacional é o contexto P5. |
| DEC-02 | Rejeição pendente se não confirmada | Rejeição pela área/pacote cria proposta de rejeição da competência; até decisão formal ela não está `MONTHLY_CLOSING_COMPLETED` nem terminalmente rejeitada. Autoridade registra decisão/motivo; pode devolver análise para esclarecimento ou correção nas transições autorizadas. Não apagar evento original. |
| DEC-03 | Sem correção excepcional de aceite P5 na V1 | Aceite P5 é irreversível pela UI e não existe endpoint de reversão/retificação na V1. Incidentes são registrados e encaminhados a processo **fora do fluxo do Portal**, sem presumir ação técnica, override, database edit ou reversão automática. P2 validação de evidência mantém contrato próprio. |
| DEC-04 | P6 publica configuração com MANAGE | Usuário com `controllership-finance.manage` efetivo **e** escopo administrativo publica nova configuração versionada de áreas obrigatórias por tipo de pacote, com justificativa, auditoria e vigência prospectiva. Competências e submissões existentes mantêm snapshots; MANAGE não implica ACCESS operacional. |

### Consistência transversal

C2 continua exigindo todos os pacotes aplicáveis submetidos, **um aceite válido de cada área obrigatória** sobre a versão atual, e nenhuma clarification aberta. Uma competência terminalmente rejeitada é desfecho diferente de conclusão, dependente de confirmação DEC-01. P5-A..J permanecem vigentes: aceites auditados por ator; reatribuição não troca autoria ou invalida aceite vigente; nova versão reinicia aceites obrigatórios; envio é submissão interna; rejeição terminal desativa TaskProjections acionáveis e preserva histórico. `CHANGES_REQUESTED` não é `REVIEW_REJECTED`.

### AC mínimos (PLANNED / TEST_NOT_RUN)

- DEC-01: reviewer de área não consegue encerrar competência; coordenador com ACCESS + vínculo + scope consegue confirmar; MANAGE sem vínculo/ACCESS falha; ausência de Core/elegibilidade falha fechada.
- DEC-02: rejeição de área sem confirmação mantém estado pendente; negativa motivada permanece auditável e permite devolução somente por transição contratada; nenhuma conclusão automática.
- DEC-03: nenhum endpoint ou ação UI V1 altera aceite P5; eventos originais imutáveis e incidentes externos não falsificam C2.
- DEC-04: MANAGE + escopo publica com motivação e versionamento; ACCESS sem MANAGE não publica; submissão anterior não muda; nova submissão adota versão conforme vigência autorizada.

### Pendências técnicas distintas de escolhas PO

**TO_INVENTORY:** contrato Core T05 de effective permissions e atributos corporativos; source do coordenador/vínculo/eligibilidade; owner/contrato físico de persistência e eventos; formato de estados/DTOs, versionamento P6 e CAS/concorrência; UX, notifications, help e projections. **CONTRACT_PENDING:** mapear transições específicas e outcomes da negativa no ledger e testes; identificar .cursor e padrões HEAD aplicáveis. Não declarar `PASS` sem inspeção de código/producers/consumers/testes e reconciliação da branch com main.

`DECISION_REQUIRED_PRODUCT_P5=NONE_IDENTIFIED_AFTER_DEC01_DEC04` (sujeito a inventário material posterior); `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`; `TEST_NOT_RUN`.
