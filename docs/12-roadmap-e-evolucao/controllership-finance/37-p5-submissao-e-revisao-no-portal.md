# 37 — P5 — Submissão e Revisão do Pacote na Minha DELPI

## Estado

**Verificação pós-merge de A12 e contratos Core:** [38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md).

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

## 16. Decisão de produto vigente — conclusão mensal C2 e rejeição terminal

**TARGET / PO_APPROVED:** C1 (somente submissão) e C3 (completion configurável) são alternativas históricas não escolhidas. A opção aprovada é **C2**; não há decisão aberta sobre qual critério encerra o fechamento.

```text
ALL_APPLICABLE_PACKAGES_SUBMITTED_FOR_REVIEW
AND FOR_EACH_APPLICABLE_PACKAGE:
    EXISTS_VALID_HUMAN_REVIEW_ACCEPTANCE_ON_CURRENT_PACKAGE_VERSION
    AND EVERY_REQUIRED_AREA_ACCEPTED_CURRENT_PACKAGE_VERSION
AND NO_OPEN_CLARIFICATION
AND NO_TERMINAL_COMPETENCE_REJECTION
→ MONTHLY_CLOSING_COMPLETED
```

**D-FINAL-02 — PO_APPROVED (19/10/2026):** a revisão depende de **aceite humano real**, nunca de aprovação automática. **Não adicionar trava prévia ao Finalizar/Enviar nem impedir publicação P6 por ausência momentânea de pessoas elegíveis.** Se não houver pessoa para revisar ou se a configuração de áreas vier vazia, o pacote permanece em revisão pendente — o conjunto vazio não é aceite e não satisfaz C2. Para qualquer pacote aplicável, o encerramento exige pelo menos um evento efetivo de aceite humano válido na versão vigente, além do aceite de cada área obrigatória do snapshot. Se não houver nenhum aceite, o fluxo não conclui naturalmente; não criar novo permission code, fallback MANAGE ou endpoint de aceite automático.

Cada área obrigatória é configurada por tipo de pacote no P6 e congelada no ato da submissão P5. Um único aceite auditado por usuário elegível satisfaz aquela área para aquela PackageVersion; dois usuários elegíveis não duplicam o quorum. Nova versão exige novamente os aceites de todas as áreas obrigatórias, sem herdar os anteriores. Reatribuição de pessoa preserva aceite histórico e autoria, sem reversão pela UI ou por endpoint da V1.

Rejeição `REVIEW_REJECTED` por reviewer elegível registra outcome da área/pacote, **não** rejeita automaticamente toda a competência. O responsável formal da Controladoria designado para aquela competência, com `controllership-finance.access` efetivo, vínculo operacional, scope e regra de negócio verificados pela BFF, pode confirmar a rejeição terminal mediante justificativa auditável (DEC-01). Sem confirmação, permanece pendente de decisão formal; eventual retorno para esclarecimento/correção exige transição auditada (DEC-02). Confirmada a rejeição, a competência encerra como rejeitada (distinta de `MONTHLY_CLOSING_COMPLETED`) e as projeções/tarefas de revisão deixam de ser acionáveis, preservando histórico (P5-D/J).

**Binding físico TO_INVENTORY:** fonte/grupo/função corporativa para elegibilidade, atribuição formal, endpoint/DTO/eventos, OCC/concorrência e nomes finais dos estados. Não criar permission de reviewer ou área. `controllership-finance.manage` não substitui ACCESS; nenhuma reversão excepcional de aceite é implementada na V1 (DEC-03).

## 17. Gate

```text
PACKAGE_TRANSPORT_MODEL = PASS / PORTAL_FIRST
NOTIFICATION_MODEL = PASS
EXTERNAL_REVIEWER_ACCESS = PASS
EMAIL_AS_NOTIFICATION_ONLY = PASS
REVIEW_SURFACE = PASS
TASK_PROJECTION = PASS
MONTHLY_COMPLETION_RULE = C2_DECIDED / DERIVED_CONTRACT_PENDING
IMPLEMENTATION_AUTHORIZED = NO
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
