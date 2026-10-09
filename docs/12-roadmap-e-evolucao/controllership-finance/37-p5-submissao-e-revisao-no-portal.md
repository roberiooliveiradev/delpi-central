# 37 — P5 — Submissão e Revisão do Pacote na Minha DELPI

## Estado

**TARGET / PRODUCT_CLARIFICATION_APPLIED / REVIEW_COMPLETION_DECISION_REQUIRED**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

PACKAGE_TRANSPORT_BY_EMAIL = NO
PACKAGE_STAYS_IN_MINHA_DELPI = YES
REVIEWERS_HAVE_MINHA_DELPI_LOGIN = YES
NOTIFICATION_IN_APP = YES
NOTIFICATION_BY_EMAIL = PLATFORM_CAPABILITY
EMAIL_ATTACHMENT_DELIVERY = NO
```

Este documento substitui a premissa de delivery externo investigada em 36.

## 1. Decisão de produto

O ato de P5 chamado na UX de **Enviar para análise** significa:

```text
PACKAGE_FINALIZED
→ SUBMIT / MAKE AVAILABLE INSIDE MINHA DELPI
→ ASSIGN/EXPOSE TO AUTHORIZED REVIEWERS
→ NOTIFY REVIEWERS
→ REVIEWERS OPEN MINHA DELPI
→ REVIEW PACKAGE/DOCUMENTS
```

O package não é anexado ao e-mail e não sai do Portal como parte do fluxo V1.

## 2. Separação de conceitos

```text
FINALIZE
!= SUBMIT_FOR_REVIEW
!= NOTIFY
!= REVIEW
!= MONTHLY_CLOSING_COMPLETED
```

### Finalizar

Cria uma `PackageVersion` imutável/snapshot.

### Enviar para análise

É a ação de negócio que sacramenta a versão como submetida aos reviewers daquele recipient package.

Nome técnico TARGET recomendado:

```text
PACKAGE_SUBMITTED_FOR_REVIEW
```

Nome UX PT-BR:

```text
Enviar para análise
Enviado para análise
Aguardando análise
```

### Notificar

Depois da submissão, P5 emite evento para a capability Core Notifications.

A plataforma pode entregar:
- notificação persistida na Minha DELPI;
- e-mail de notificação conforme configuração/preferência/capability vigente.

O e-mail:
- avisa que existe pacote para análise;
- aponta para a Minha DELPI;
- não carrega o package como attachment;
- não é evidence de review;
- falha de e-mail não desfaz a submissão do package.

```text
NOTIFICATION_FAILURE != PACKAGE_SUBMISSION_FAILURE
EMAIL_SENT != PACKAGE_SUBMITTED_FOR_REVIEW
```

### Revisar

Reviewer autenticado acessa P5 na Minha DELPI e analisa somente recipient packages para os quais possui acesso/resource scope.

## 3. Reviewer externo

"Externo da Controladoria" não significa usuário anônimo ou acesso público.

O reviewer:
- possui identidade no Core/Minha DELPI;
- possui acesso ao app;
- usa login normal da plataforma;
- possui `controllership-finance.access`;
- recebe resource scope/assignment para os recipient packages aplicáveis;
- não precisa de `controllership-finance.manage` para revisar;
- não recebe permission code próprio de reviewer.

AuthZ:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND reviewer_assignment/resource_scope
AND package_business_rule
```

`MANAGE` não substitui `ACCESS`.

Reviewer assignment não concede permission global; apenas participa da avaliação de recursos explicitamente associados.

## 4. Ownership

| Conceito | Owner |
|---|---|
| PackageVersion | P5 / controllership-finance-api |
| recipient package | P5 |
| submissão para análise | P5 |
| reviewer assignment | P5, referenciando identidades Core |
| identity/app access/effective permissions | Core |
| review state/outcome | P5 |
| clarification | P5 |
| notifications | Core Notifications / Minha DELPI |
| e-mail de notification | capability de plataforma Core |
| package content | permanece no Portal/P5 e owners de evidence |
| transport de attachment por e-mail | fora do V1 |

## 5. Arquitetura TARGET

```text
Controladoria user
→ P5 finalizePackage
→ PackageVersion immutable

Controladoria user
→ P5 submitPackageForReview
→ recipient package becomes visible/actionable to assigned reviewers
→ P5 emits notification event
→ Core Notifications
   → Minha DELPI inbox
   → optional/best-effort e-mail according platform rules

Reviewer
→ login Minha DELPI
→ controllership-finance.access
→ resource scope/assignment
→ P5 recipient package review
```

O MFE continua consumindo somente `controllership-finance-api`.

## 6. Surface de reviewer

V1 não cria novo Portal nem nova top-level page.

P5 possui dois modos de uso sobre o mesmo bounded context:

### Controladoria / preparação

- lista recipient packages;
- finaliza versão;
- submete para análise;
- responde esclarecimentos;
- cria complemento/nova versão quando necessário;
- acompanha review state.

### Reviewer / análise

- vê apenas packages dentro do seu resource scope;
- abre PackageVersion read-only;
- consulta documentos/evidências liberados;
- registra início/progresso de análise quando o contract exigir;
- solicita esclarecimento/correção;
- registra outcome de revisão quando permitido;
- não altera PackageVersion;
- não administra template/config;
- não reabre P3.

Deep link de notification/task aponta diretamente ao recipient package autorizado.

## 7. Lifecycle TARGET conhecido

```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED
→ PACKAGE_SUBMITTED_FOR_REVIEW
```

Depois da submissão, o review lifecycle precisa suportar pelo menos:

```text
REVIEW_PENDING
→ REVIEW_IN_PROGRESS
→ [ REVIEW_ACCEPTED | CHANGES_REQUESTED ]
```

Com esclarecimento:

```text
CHANGES_REQUESTED
→ WAITING_FOR_CLARIFICATION
→ CLARIFICATION_RESOLVED
→ REVIEW_IN_PROGRESS
```

Se a correção mudar conteúdo material:
- package submetido anterior permanece histórico;
- criar complemento/nova versão conforme P5;
- reviewer recebe nova submissão/version adequada;
- não sobrescrever versão já analisada.

Os nomes técnicos finais desses review states devem ser normalizados no ledger/contract, mas a semântica acima está congelada.

## 8. Notifications

Evento mínimo após submit:

```text
PACKAGE_SUBMITTED_FOR_REVIEW
→ notify assigned reviewers
```

Notification TARGET:
- sourceApp = controllership-finance;
- recipient(s) = reviewer Core identities resolved/authorized;
- required permission filter = `controllership-finance.access`;
- action target = deep link interno para o recipient package;
- category/template = inventory físico futuro;
- e-mail segue preferência/capability da plataforma.

A notificação pode dizer, por exemplo:

```text
"Há um pacote de fechamento da competência 09/2026 aguardando sua análise."
[Abrir na Minha DELPI]
```

Sem attachment do package.

## 9. Minhas tarefas

A clarificação de produto prova P5 como producer de TaskProjection quando houver responsabilidade individual de reviewer.

Após `PACKAGE_SUBMITTED_FOR_REVIEW`:

```text
reviewer assignment
AND review actionable
→ project to Minhas tarefas
```

TaskProjection:
- é self-only;
- aponta ao recipient package P5;
- desaparece quando a ação não é mais requerida;
- não cria task entity paralela.

## 10. Segurança e privacidade

Reviewer externo:
- nunca recebe URL pública;
- nunca acessa package por token embutido em e-mail;
- não usa e-mail como authorization proof;
- não recebe dados de outro recipient package;
- não recebe `manage` por ser reviewer;
- não acessa Admin/P6 sem `manage`;
- não acessa PackageVersion fora do resource scope.

Notificação por e-mail:
- não carrega conteúdo sensível além do mínimo necessário;
- leva o usuário autenticado à Minha DELPI;
- após login, BFF reautoriza package/resource.

## 11. UX

### Controladoria

Ação:

```text
Enviar para análise
```

Confirmação deve explicar:
- versão será congelada como submetida;
- reviewers receberão acesso/atividade correspondente;
- serão notificados pela Minha DELPI e, quando habilitado, por e-mail;
- package não será anexado/enviado por e-mail.

### Reviewer

Header do package:
- competência;
- destinatário/contexto;
- versão;
- submetido em/por;
- review state;
- freshness/provenance dos documentos quando aplicável.

Ações:
- iniciar/continuar análise;
- solicitar esclarecimento;
- registrar outcome de revisão quando autorizado.

## 12. Estados de experiência

Além do baseline:

```text
LOADING
SUCCESS
EMPTY
PARTIAL
UNAVAILABLE
ERROR
403
404
```

P5 deve representar:

```text
PACKAGE_FINALIZED
PACKAGE_SUBMITTED_FOR_REVIEW
REVIEW_PENDING
REVIEW_IN_PROGRESS
CHANGES_REQUESTED
WAITING_FOR_CLARIFICATION
CLARIFICATION_RESOLVED
REVIEW_ACCEPTED
```

Nenhum desses estados depende de e-mail enviado/lido.

## 13. Help

Help deve explicar:
- finalizar != enviar para análise;
- enviar para análise disponibiliza o package dentro da Minha DELPI;
- reviewer acessa com login;
- e-mail é só notificação;
- package não vai anexado por e-mail;
- reviewer só vê packages autorizados;
- clarification/correction/version history;
- regra de conclusão mensal após a decisão D-P5-REVIEW-COMPLETION.

## 14. RQ / AC adicionais

### RQ-P5-11 — submit in-portal

Aceite:
- package precisa estar FINALIZED;
- submit torna a versão disponível aos reviewers autorizados;
- não existe attachment delivery por e-mail;
- actor/timestamp/version/reviewer scope são auditados.

### RQ-P5-12 — reviewer authenticated

Aceite:
- reviewer possui login Minha DELPI;
- exige `controllership-finance.access`;
- package fora do scope retorna 403/404 conforme contract;
- MANAGE não é necessário para review.

### RQ-P5-13 — notifications

Aceite:
- submit gera notification event;
- in-app notification aponta por deep link autorizado;
- e-mail pode ser enviado pela capability Core conforme configuração;
- falha de e-mail não reverte package submission.

### RQ-P5-14 — reviewer work projection

Aceite:
- actionable review pode aparecer em Minhas tarefas;
- self-only;
- action abre owner P5;
- nenhuma task entity paralela.

### RQ-P5-15 — review history

Aceite:
- reviewer/action/outcome/timestamps auditáveis;
- versão analisada permanece identificável;
- nova versão não apaga review anterior.

## 15. Test matrix

Positive:
- finalizado → submit → reviewer autorizado vê package;
- reviewer recebe notification in-app;
- e-mail notification habilitado pode ser enviado;
- deep link abre package após reautorização;
- reviewer inicia análise;
- clarification roundtrip;
- review outcome auditado.

Sibling:
- reviewer A não vê package de B;
- submit A não submete B;
- e-mail failure não muda submission;
- clarification A não muda sibling;
- nova versão não apaga review anterior.

Negative:
- submit antes de finalização;
- reviewer sem ACCESS;
- reviewer sem assignment/resource scope;
- MANAGE sem ACCESS;
- package anexado por e-mail;
- deep link bypassando AuthZ;
- notification criada para usuário sem app access;
- reviewer editando PackageVersion;
- user externo acessando Admin sem MANAGE.

Experience:
- desktop/mobile;
- light/dark;
- keyboard/focus;
- loading/success/empty/partial/unavailable/error/403/404;
- F5/deep link;
- Help.

## 16. Decisão material ainda aberta

A clarificação fecha o modelo de entrega, mas falta decidir quando o fechamento mensal é considerado concluído.

### C1 — submissão é suficiente

```text
ALL_APPLICABLE_PACKAGES_SUBMITTED_FOR_REVIEW
AND NO_OPEN_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

Reviewer pode continuar avaliação depois.

### C2 — review aceito é obrigatório

```text
ALL_APPLICABLE_REVIEWS_ACCEPTED
AND NO_OPEN_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

A avaliação externa faz parte formal do completion gate.

### C3 — regra configurável por recipient/package type

Alguns recipients exigem review accepted; outros só submission.

Maior flexibilidade, maior complexidade e configuração.

### Recomendação

**C2**, se a validação do pessoal externo é parte necessária do processo de fechamento.

Rationale:
- "enviar para quem vai avaliar" deixa de ser simples handoff técnico;
- o Portal passa a modelar a continuidade real do processo;
- evita marcar fechamento concluído antes do reviewer terminar;
- mantém clarification/correção dentro de um lifecycle auditável.

Se a avaliação externa for apenas pós-fechamento/controle posterior, C1 é o modelo correto.

## 17. Gate

```text
PACKAGE_TRANSPORT_MODEL = PASS / PORTAL_FIRST
NOTIFICATION_MODEL = PASS
EXTERNAL_REVIEWER_ACCESS = PASS
EMAIL_AS_NOTIFICATION_ONLY = PASS
REVIEW_SURFACE = PASS
TASK_PROJECTION = PASS
MONTHLY_COMPLETION_RULE = DECISION_REQUIRED
IMPLEMENTATION_AUTHORIZED = NO
```
