# 35 — Contratos, Regras, Scripts e Test Matrix — Gate V2

## Estado

**TARGET / A15 CONSOLIDATION PASS_WITH_DECISION_REQUIRED_E04_T04**

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
| A12 | P5 Pacote, Finalização e Envio | PACKAGE_FINALIZATION_READY / SEND_PENDING_E04_T04 |
| A13 | P6 Administração / Configuração | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |

A12 é o único residual material que impede o `PRODUCT_CONTRACT_FREEZE = PASS`; o inventário está concluído e a pendência agora é uma decisão explícita documentada em `36-e04-t04-package-delivery-decision-packet.md`.

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

Fechado:

```text
list/getRecipientPackages
finalizePackage
reopenFinalizedPackageBeforeSend
createComplementOrNewVersion
list/resolveClarifications
getPackageHistory
deriveMonthlyClosingCompletion
notifyUserAboutPackageEvent
```

Pendente:

```text
sendPackage
→ owner/channel/proof/idempotency/retry
= DECISION_REQUIRED_E04_T04
```

Não congelar endpoint físico de envio antes disso.

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
PACKAGE_FINALIZED != PACKAGE_SENT
NOTIFICATION_DISPATCHED != PACKAGE_SENT
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
- `validate-p5-delivery-contract` — must remain blocked until E04/T04
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

```text
E04 / T04
= INVENTORY_COMPLETE_FOR_DECISION
= DECISION_REQUIRED
```

Authority:
- [36-e04-t04-package-delivery-decision-packet.md](./36-e04-t04-package-delivery-decision-packet.md).

Proven:
- Graph e-mail + attachments;
- retry de transport;
- Message Trace delivered/bounced/unknown em contexts reais;
- Core Notifications separado de package delivery.

Decisão ainda necessária:
- owner/orchestration do delivery;
- semântica de `PACKAGE_SENT`.

Recomendação documentada, não aplicada:
- P5/BFF owns orchestration;
- Graph + Message Trace adapters;
- `PACKAGE_SENT` após `DELIVERED`.

## 13. Freeze readiness após A15

```text
PORTAL_DESIGN_FREEZE          = PASS
FRONTEND_PATTERN_FREEZE       = PASS
SECURITY_MODEL_FREEZE         = PASS
TEST_STRATEGY_FREEZE          = PASS
PRODUCT_CONTRACT_FREEZE       = DECISION_REQUIRED_E04_T04

DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED      = NO
```

Próximo passo:
- fechar E04/T04 por evidence/owner;
- reexecutar residual search;
- somente então declarar `DOCUMENTATION_CLOSURE_COMPLETE = PASS`.
