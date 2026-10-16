# 35 — Contratos, Regras, Scripts e Test Matrix — Gate V2

## Estado

**TARGET / A15 CONSOLIDATION PASS_WITH_BLOCKED_BY_P5_DERIVED_REVIEW_CONTRACT**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO
DOCUMENTATION_CLOSURE_COMPLETE = NO
```

Este documento consolida A15 após a revisão transversal A14.

Authorities detalhadas continuam nos documentos de cada página; este arquivo é o índice de fechamento e não duplica integralmente cada contrato.

## 1. Page readiness

| Etapa | Página | Gate V2 |
|---|---|---|
| A01 | Página do usuário | READY_FOR_IMPLEMENTATION_BRIEF |
| A02 | Início | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A03 | Visão geral | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A04 | Minhas tarefas | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A05 | Sala de interação | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A06 | Administração | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A07 | Ajuda | READY_FOR_IMPLEMENTATION_BRIEF |
| A08 | P1 Cockpit da Competência | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A09 | P2 Checklist e Documentos | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A10 | P3 Estoque e Conciliação | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY / STOP T03 |
| A11 | P4 Classificações e Pendências | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |
| A12 | P5 Pacote, Finalização e Envio | PORTAL_SUBMISSION_MODEL_PASS / P5_DERIVED_REVIEW_CONTRACT_PENDING |
| A13 | P6 Administração / Configuração | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |

A12 permanece com contrato derivado pendente. C2 e D-P5-01 a D-P5-05 foram aprovados pelo Product Owner; ainda faltam as semânticas de rejeição terminal, substituição, quorum versionado e ressubmissão.

## 2. Contrato arquitetural transversal

```text
plugins/controllership-finance
→ /apps/controllership-finance-api
→ owner canônico
```

Owners:
- Core → identidade, apps, effective permissions, RBAC, users, notifications;
- api-delpi → SQL/regras TOTVS/Protheus;
- strategic-indicators-api → metas/indicadores estratégicos;
- controllership-finance-api → estado/regras próprios + composição/adapters;
- plugin-ui → chrome/componentes reutilizáveis.

Proibido:

```text
browser → Core
browser → api-delpi
browser → strategic-indicators-api
browser → DB vizinho
```

## 3. Contratos semânticos por página

Os nomes abaixo são operações semânticas, não endpoint names obrigatórios.

### A01 — Página do usuário

```text
getUserProfile
getUserPhoto
resolveViewerEffectiveAccess
resolveTargetAppMembership
```

Owners:
- Core Directory;
- Core Person Profile;
- Core PermissionResolver.

Writes de identidade não pertencem ao Portal.

### A02 — Início

```text
resolveViewerContext
getActiveCompetenceSummary
getMyTaskPreview
getBlockerSummary
getAttentionEvents
getFavorites/saveFavorites [inventory]
routeCatalog [MFE]
recentViews [MFE local]
```

Home compõe; não cria regra owner.

### A03 — Visão geral

```text
getFinancialKpis
getFinancialOperationalContext
getStrategicPerformance
getIndicatorSeries
getIndicatorDrilldown
resolveViewerAccess
```

A BFF normaliza shape/provenance; não recalcula fórmula/score.

### A04 — Minhas tarefas

```text
getMyTaskProjections
→ source registry
→ owner adapters
→ validated owner deep links
```

```text
TaskProjection != TaskEntity
WORKLIST_SCOPE = MINE_ONLY
```

### A05 — Sala de interação

```text
listRooms
resolveRoomByContext
getRoom
list/post/edit/softDeleteMessage
readState
mentionSuggest
reaction/pin
sharedItems
findInRoom
attachments [inventory]
realtime [inventory]
```

```text
MESSAGE != BUSINESS_DECISION
ROOM_MEMBER != AUTHORIZATION_GRANT
```

### A06/A13 — Administração / P6

```text
getAdministrationSummary
list/get/create/update template draft
startReview
publishTemplate
listCatalogRegistry
list/get/create/update/inactivateCatalogItem
resolveEligiblePeople
listAdministrationAudit
notifyBusinessEvent via Core Notifications adapter
```

Sem user/RBAC write.

### A07 — Ajuda

```text
MFE content registry
→ createDashboardUserManual
→ capability/permission filtered sections
```

Sem BFF/DB/CMS V1.

### A08 — P1

```text
resolveClosingContext
composeStockAxis
composeDocumentsAxis
composePackageAxis
listPriorityPendencies
listClosingHistory
composeBlockers
```

P1 é read-model/composição.

### A09 — P2

```text
list/get checklist items
attachEvidence
validateEvidence
reverseRejection
mark/revertNotApplicable
create/update/cancelExceptionalItem
request/reviewStructuralCorrection
promoteToMaster
listItemHistory
resolveEligiblePeople
```

### A10 — P3

```text
getStockClosingState
confirmCutoff
revalidateStockInputs
getReconciliation
getReconciliationDrilldown
getStockClosingHistory
```

```text
STOCK_CLOSED = terminal no P3 Portal V1
```

Portal não executa sacramentação ERP.

### A11 — P4

```text
list/getPendencies
claim/reassign
startAnalysis
waitExternal
resolve
dismiss
getClassificationSuggestion
confirmClassification
listPendencyHistory
```

IA sugere; humano confirma.

### A12 — P5

```text
list/getRecipientPackages
finalizePackage
reopenFinalizedPackageBeforeSubmit
submitPackageForReview
getReviewerPackage
startReview
requestChanges
acceptReview
createComplementOrNewVersion
list/resolveClarifications
getPackageHistory
notifyUserAboutPackageEvent
deriveMonthlyClosingCompletion [decision pending]
```

```text
PACKAGE_FINALIZED
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ REVIEW_PENDING
→ REVIEW_IN_PROGRESS
→ REVIEW_ACCEPTED | CHANGES_REQUESTED
```

Package permanece na Minha DELPI. E-mail é notification only.

Residual:
- `D-P5-REVIEW-COMPLETION`.

## 4. AuthZ contract

```text
JWT
→ identity/context

Core PermissionResolver
→ effective permissions

BFF ALLOW
= capability
AND resource_scope / ownership
AND business_rule
```

Permission codes:

```text
controllership-finance.access
controllership-finance.manage
```

Nenhum outro permission code do produto.

Administração/P6:
- MANAGE é capability administrativa;
- MANAGE não implica ACCESS às superfícies operacionais.

Unidade/filial:
- dimensão de dado/contexto;
- nunca permission code.

## 5. Regras canônicas

Authority:
- [04-regras-de-negocio-consolidadas.md](./04-regras-de-negocio-consolidadas.md).

Invariantes principais:

```text
ATTACHED != VALIDATED
NO_MOVEMENT != NOT_APPLICABLE
PRELIMINARY != FINAL
SOURCE_UNAVAILABLE != ZERO
PENDING_SINCE != SLA
AI_SUGGESTION != HUMAN_DECISION
MESSAGE != BUSINESS_DECISION
BLOCKER != MY_TASK
TASK_PROJECTION != TASK_ENTITY
READY_TO_CLOSE != STOCK_CLOSED
FINALIZE != SEND
PACKAGE_FINALIZED != PACKAGE_SUBMITTED_FOR_REVIEW
NOTIFICATION_DISPATCHED != PACKAGE_SUBMITTED_FOR_REVIEW
DOCUMENTED != IMPLEMENTED
```

Paridade:

```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
TOLERANCIA_MONETARIA = NONE
```

## 6. Estados de experiência

Baseline de todas as páginas:

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

Adicionais quando aplicável:

```text
REFRESHING
VALIDATION_ERROR
CONFLICT
CONNECTION_DEGRADED
STALE_ITEM
```

`UNAVAILABLE_SOURCE` pode qualificar uma source, mas a experiência continua classificada como `UNAVAILABLE`/PARTIAL conforme contract.

## 7. plugin-ui / frontend pattern

Authority:
- [30-plugin-ui-reuse-map.md](./30-plugin-ui-reuse-map.md);
- current `plugins/plugin-ui/src/index.ts`.

A14 confirmou exports para:
- charts;
- collaboration;
- task workspace;
- user manual;
- user profile;
- layout/data/forms/feedback/help/action primitives.

```text
PLUGIN_UI_FIRST = REQUIRED
LOCAL_CLONE = FORBIDDEN
```

Se gap real:
- prove gap;
- preferir contribuição no kit;
- não recriar chrome local.

## 8. Scripts / validators planejados

Nenhum script abaixo deve ser criado na FASE A.

### A01
- `USER-PROFILE-CONTRACT-VALIDATOR`
- `USER-PROFILE-PLUGIN-UI-REUSE-CHECK`
- `USER-PROFILE-STATE-MATRIX`
- `USER-PROFILE-DEEP-LINK-SMOKE`

### A02
- `validate-home-route-catalog`
- `validate-home-favorites`
- `validate-home-deep-links`
- `validate-home-help`

### A03
- `validate-overview-indicator-catalog`
- `validate-overview-route-contracts`
- `validate-overview-filter-url`
- `validate-overview-source-states`
- `validate-overview-help`

### A04
- `validate-task-projection-registry`
- `validate-task-projection-ownership`
- `validate-task-projection-coverage`
- `validate-task-projection-due`
- `validate-task-projection-links`
- `validate-task-help`

### A05
- `validate-interaction-context-registry`
- `validate-interaction-route-contracts`
- `validate-interaction-authz`
- `validate-interaction-message-policy`
- `validate-interaction-attachment-boundary`
- `validate-interaction-help`

### A06/A13
- `validate-admin-catalog-registry`
- `validate-admin-template-lifecycle`
- `validate-admin-snapshot-immutability`
- `validate-admin-effective-dates`
- `validate-admin-authz`
- `validate-admin-identity-boundary`
- `validate-admin-audit`
- `validate-admin-help`
- `validate-p6-notification-adapter`
- `validate-p6-core-people-boundary`

### A07
- `validate-help-route`
- `validate-help-section-registry`
- `validate-help-tool-links`
- `validate-help-capability-gating`
- `validate-help-contextual-links`
- `validate-help-terminology`
- `validate-help-sync`
- `validate-help-plugin-ui`

### A08
- `validate-p1-axis-contracts`
- `validate-p1-blockers`
- `validate-p1-deep-links`
- `validate-p1-authz`
- `validate-p1-help`
- `validate-p1-plugin-ui`

### A09
- `validate-p2-state-machine`
- `validate-p2-snapshot`
- `validate-p2-evidence-history`
- `validate-p2-authz`
- `validate-p2-attachment-boundary`
- `validate-p2-notifications`
- `validate-p2-help`
- `validate-p2-plugin-ui`

### A10
- `validate-p3-monetary-parity`
- `validate-p3-state-machine`
- `validate-p3-source-readiness`
- `validate-p3-owner-boundary`
- `validate-p3-authz`
- `validate-p3-deep-links`
- `validate-p3-help`
- `validate-p3-plugin-ui`

### A11
- `validate-p4-state-machine`
- `validate-p4-human-decision`
- `validate-p4-ownership`
- `validate-p4-source-boundary`
- `validate-p4-authz`
- `validate-p4-deep-links`
- `validate-p4-help`
- `validate-p4-plugin-ui`

### A12
- `validate-p5-package-lifecycle`
- `validate-p5-versioning`
- `validate-p5-completion-rule`
- `validate-p5-notification-boundary`
- `validate-p5-submission-review-contract` — cobre submissão in-portal, unanimidade, versionamento e falhas de AuthZ
- `validate-p5-authz`
- `validate-p5-help`
- `validate-p5-plugin-ui`

Localização/tecnologia dos scripts seguem o padrão vigente do HEAD quando a implementação for autorizada.

## 9. Test matrix padrão

Toda página/slice deve provar quatro famílias.

### Positive

Exemplos:
- happy path autorizado;
- zero real;
- transição válida;
- deep link válido;
- F5;
- owner/source disponível.

### Sibling

Provar isolamento:
- recurso A não altera B;
- source A falhando não apaga B;
- recipient A não avança B;
- usuário A não vê/projeta trabalho de B;
- mudança de filtro não reutiliza stale data de sibling.

### Negative

Obrigatório conforme página:
- sem permission;
- permission errada;
- scope/ownership inválido;
- direct URL;
- state transition inválida;
- source unavailable convertido em zero/empty;
- hard delete/overwrite histórico;
- open redirect;
- UI action sem backend authorization;
- permission proliferation;
- capability futura não implementada.

### Experiência

```text
LOADING
SUCCESS
EMPTY
PARTIAL
UNAVAILABLE
ERROR
403
404
desktop
mobile
light
dark
keyboard/focus
deep-link/F5
Help
```

Adicionar REFRESHING/VALIDATION_ERROR/CONFLICT/etc quando aplicável.

## 10. Testes transversais

Authority:
- [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md).

A15 normalizou RQ-SEC-01..06 e RQ-UX-01..06 para conter:
- aceite;
- teste mínimo;
- dependência;
- estado.

Nenhum RQ pode ser PASS por associação.

## 11. Inventários que não reabrem produto

Quando não houver evidence incompatível:

- E01 — bank/account seed/source;
- E05 — attachment roles seed;
- E06 — rejection reason seed;
- T01 — api-delpi physical bindings;
- T02 — Core notification product adapter;
- T03 — canonical STOCK_CLOSED owner;
- T05 — Core resource scope/effective access bindings;
- H/TSK/R/ADM/HELP inventories físicos definidos nas páginas.

Se a evidence invalidar owner/semântica:
- `EXECUTION_DRIFT`;
- não adaptar silenciosamente.

## 12. Residual que bloqueia o freeze global

A premissa de external package delivery foi superseded.

```text
E04_EXTERNAL_DELIVERY = CLOSED / NOT_REQUIRED_IN_V1
T04_EXTERNAL_DELIVERY_CAPABILITY = CLOSED / NOT_REQUIRED_IN_V1
```

Contrato vigente:

```text
PACKAGE_FINALIZED
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ authenticated reviewer in Minha DELPI
→ review lifecycle
```

Residual:

```text
D-P5-REVIEW-COMPLETION
= DECISION_REQUIRED
```

Opções:
- C1 submission suficiente;
- C2 review accepted obrigatório;
- C3 política configurável.

Authority:
- [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md).

## 13. Freeze readiness após A15

```text
PORTAL_DESIGN_FREEZE          = PASS
FRONTEND_PATTERN_FREEZE       = PASS
SECURITY_MODEL_FREEZE         = PASS
TEST_STRATEGY_FREEZE          = PASS
PRODUCT_CONTRACT_FREEZE       = BLOCKED_BY_P5_DERIVED_REVIEW_CONTRACT

DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED      = NO
```

Próximo passo:
- decidir `D-P5-REVIEW-COMPLETION`;
- reexecutar residual search;
- somente então avaliar `PRODUCT_CONTRACT_FREEZE = PASS` e `DOCUMENTATION_CLOSURE_COMPLETE = PASS`.


## Decisões PO P5-F a P5-J — consolidação contratual vigente (16/10/2026)

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este adendo é superveniente aos registros de perguntas abertas P5-F..J e prevalece quando notas históricas anteriores conflitarem. C2, D-P5-02..05 e P5-A..E permanecem válidas nos termos abaixo. A antiga unanimidade de *pessoas* em D-P5-01 foi substituída pela unanimidade das *áreas obrigatórias* em P5-A.

| ID | Resultado aprovado | Invariante |
|---|---|---|
| **P5-F = A** | Substituição de responsável mantém válido o aceite já realizado para a mesma área e PackageVersion; a autoria permanece a do executor original. Substituto assume somente ações futuras. | REASSIGNMENT != INVALIDATE_PRIOR_ACCEPTANCE |
| **P5-G = A** | Aceite P5 não é reversível/alterável pela UI V1. Eventual erro exige processo excepcional separado, formal, auditado e **não autorizado enquanto seu contrato não for aprovado**. | NO_P5_ACCEPTANCE_REVERSAL_IN_V1 |
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

1. **DECISION_REQUIRED:** quem é a autoridade operacional de confirmação de rejeição terminal; como é designada e substituída, e se a confirmação pode ser negada (e qual estado fica então). Não equiparar automaticamente a `manage`.
2. **DECISION_REQUIRED:** procedimento excepcional de correção de aceite P5 fora da UI V1 (owner, autorização, efeitos na conclusão mensal e revalidação), se for implementado nesta versão; na ausência de decisão, **capability não existe na V1**.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **CONTRACT_PENDING:** mapa versionado tipo de pacote → áreas obrigatórias em P6; regras de publicação/vigência/snapshot, defaults inválidos, configuração ausente e concorrência; não inventar tabelas/migrations.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.

**Matriz P5-F..J (PLANNED / TEST_NOT_RUN):** replacement preserva aceite e autor; tentativa de reversão pela UI falha; novo tipo/template P6 não muda áreas de submissão existente; package rejected não é competência rejeitada até confirmação autorizada; confirmação terminal encerra tasks acionáveis e mantém histórico; Core indisponível bloqueia ações; pacote B não herda efeitos de A; nova versão exige todos os aceites. Incluir desktop/mobile/light-dark/teclado/foco/deep-link/Help.
