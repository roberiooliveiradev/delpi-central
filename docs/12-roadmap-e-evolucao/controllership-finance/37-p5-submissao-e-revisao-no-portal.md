# 37 — P5 — Submissão e Revisão do Pacote na Minha DELPI

## Estado

**Estado transversal atual:** [README](./README.md). Evidência anterior (histórica) no [38](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md).

**TARGET / PRODUCT DECISIONS APPROVED (C2, P5-A..J, DEC-01..04) / A12 TECHNICAL_CONTRACT_INVENTORY_PENDING**

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
AND Core_eligible_corporate_group_or_function
AND required_area_of_current_PackageVersion
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
→ [ REVIEW_ACCEPTED | CHANGES_REQUESTED | REVIEW_REJECTED ]
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
- criar nova PackageVersion com histórico e novos aceites obrigatórios de todas as áreas;
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

**TARGET P5-A/C/H:** P5 produz TaskProjection de obrigação de revisão por **área obrigatória** da PackageVersion vigente, apresentada self-only a cada usuário Core elegível e autorizado. Não existe TaskEntity individual paralela.

Após `PACKAGE_SUBMITTED_FOR_REVIEW`:

```text
required_area_pending_for_current_PackageVersion
AND authenticated_user_eligible_via_Core_group_or_function
AND effective_permission(controllership-finance.access)
AND resource_scope_and_business_rule
AND review actionable
→ TaskProjection self-only em Minhas tarefas
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
- conclusão mensal C2 depende de aceites humanos reais da versão vigente, quorum por área e esclarecimentos resolvidos; ausência de revisores não impede envio, mas mantém revisão pendente.

## 14. Critérios de aceite detalhados — IDs canônicos no ledger 23

### AC-P5-SUBMIT — RQ-P5-05

Aceite:
- package precisa estar FINALIZED;
- submit torna a versão disponível aos reviewers autorizados;
- não existe attachment delivery por e-mail;
- actor/timestamp/version/reviewer scope são auditados.

### AC-P5-REVIEWER-AUTH — RQ-P5-06 / RQ-P5-AREA-04

Aceite:
- reviewer possui login Minha DELPI;
- exige `controllership-finance.access`;
- package fora do scope retorna 403/404 conforme contract;
- MANAGE não é necessário para review.

### AC-P5-NOTIFICATIONS — RQ-P5-07

Aceite:
- submit gera notification event;
- in-app notification aponta por deep link autorizado;
- e-mail pode ser enviado pela capability Core conforme configuração;
- falha de e-mail não reverte package submission.

### AC-P5-TASK-PROJECTION — RQ-P5-08

Aceite:
- actionable review pode aparecer em Minhas tarefas;
- self-only;
- action abre owner P5;
- nenhuma task entity paralela.

### AC-P5-REVIEW-HISTORY — RQ-P5-09

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

## 16. Contrato canônico de decisão — C2, P5-A..J e DEC-01..04

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este é o **único registro normativo das decisões de revisão P5** neste pacote. C1/C3 e unanimidade de pessoas são alternativas históricas, não vigentes. O [ledger 23](./23-ledger-rq-ac-testes.md) é owner dos RQ/AC; o [17](./17-backlog-de-confirmacoes-e-inventarios.md) é owner dos inventários pendentes.

```text
ALL_APPLICABLE_PACKAGES_SUBMITTED_FOR_REVIEW
AND FOR_EACH_APPLICABLE_PACKAGE:
    EXISTS_VALID_HUMAN_REVIEW_ACCEPTANCE_ON_CURRENT_PACKAGE_VERSION
    AND EVERY_REQUIRED_AREA_ACCEPTED_CURRENT_PACKAGE_VERSION
AND NO_OPEN_CLARIFICATION
AND NO_TERMINAL_COMPETENCE_REJECTION
=> MONTHLY_CLOSING_COMPLETED
```

**D-FINAL-02 — PO aprovado em 19/10/2026:** **somente pessoas aprovam**. Sem revisor elegível ou com conjunto vazio de áreas, **não** inventar trava antecipada de finalização, submissão ou publicação. O pacote segue para revisão e **fica pendente** até que exista aceite humano real válido. Conjunto vazio **nunca** satisfaz C2 automaticamente. Cada área obrigatória existente exige um aceite da versão vigente; cada pacote aplicável exige ao menos um aceite humano real. `CHANGES_REQUESTED` difere de `REVIEW_REJECTED`.

| ID | Decisão vigente |
|---|---|
| C2 / P5-A | Um aceite auditado por **área obrigatória** da PackageVersion atual, não por cada pessoa elegível; todos os pacotes aplicáveis submetidos, sem esclarecimentos abertos nem rejeição terminal |
| P5-B / P5-G | Ninguém edita, retifica ou reverte aceite P5 por UI **ou API** na V1; reatribuição não dá poder de sobrescrever decisão passada |
| P5-C | Revisor precisa de `controllership-finance.access` **efetivo Core**, elegibilidade por grupo/função corporativa, área da versão, scope/ownership e regra de negócio; BFF autoriza fail-closed |
| P5-D | Rejeição **terminal da competência** é desfecho distinto de `MONTHLY_CLOSING_COMPLETED`; não é efeito automático de rejeição da área |
| P5-E | Nova PackageVersion exige novos aceites de todas as áreas obrigatórias; não herda aceites da versão anterior |
| P5-F | Substituição de revisor preserva aceite válido, autoria original e histórico; substituto age apenas futuramente |
| P5-H | P6 versiona áreas obrigatórias por tipo de pacote; P5 congela snapshot na submissão; edições P6 futuras não alteram competências já submetidas |
| P5-I | Revisor pode rejeitar pacote/área; somente autoridade formal da competência pode confirmar rejeição **terminal** com justificativa auditada |
| P5-J | Rejeição terminal torna TaskProjections P5 não acionáveis, sem remover histórico |
| DEC-01 | Coordenador formal do fechamento confirma rejeição terminal **somente** com ACCESS efetivo + vínculo operacional + resource scope + regra; MANAGE isolado não autoriza |
| DEC-02 | Sem confirmação, competência fica **pendente**, com motivo auditado e possível retorno autorizado para esclarecimento/correção |
| DEC-03 | Incidentes de aceite são tratados **fora** do Portal V1; nenhum endpoint, override ou reversão de aceite P5 |
| DEC-04 | Configuração P6 é publicada prospectivamente com MANAGE efetivo **AND** escopo administrativo, justificativa, versionamento e auditoria |

**Authority/boundary:** Core API gerencia identidade, usuários, grupos, concessão e revogação de permissões; Portal CF **não gerencia RBAC**. Somente os permission codes `controllership-finance.access` e `controllership-finance.manage`. O P5 avalia vínculos operacionais, escopo, área e regra de negócio; jamais confiar só em JWT ou frontend. `MANAGE != ACCESS`.

**Auditoria obrigatória:** ator Core, instante, ação, competência, destinatário, PackageVersion, área, effective access/scope avaliado, resultado, motivo quando aplicável, reatribuições e autoria original; registros imutáveis semanticamente. Nomes físicos dos estados, DTO/eventos, storage e OCC são `TO_INVENTORY`.

## 17. Gate e dependências de implementação

- **PROVEN no código da plataforma:** Core effective-access S2S, diretório, notifications e plugin-ui exports; verificar contratos/versionamento no HEAD ao implementar.
- **TO_INVENTORY:** fonte Core de elegibilidade grupo/função corporativa por área (T05), designação formal de coordenador, P6 versioned snapshot, states/DTOs/events, OCC/idempotência, consumers e segurança do recurso. **Não** inventar contrato Core nem persistência sem owner/gate.
- **PLANNED / TEST_NOT_RUN:** casos positivos/sibling/negativos, concorrência, ausência de pessoas, zero áreas, reviewer posterior, revisão terminal, Ajuda e smoke. Ver [41](./41-estrategia-validacao-e-gates-implementacao-v1.md).
- **Sem runtime nesta revisão.** `A12=INCONCLUSIVE`; `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`. Validação transversal e autorização explícita precedem qualquer implementação.

