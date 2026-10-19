# 35 — Contratos, Regras, Scripts e Test Matrix — Gate V2

> **EVIDÊNCIA HISTÓRICA, NÃO GATE ATUAL.** Leia o README e o contrato 37. Este documento descreve análises/slices anteriores; `PASS` de seções locais não autoriza runtime.

## Estado

**Parecer transversal vigente (16/10/2026):** [44 — Revalidação A16](./44-a16-revalidacao-final-transversal-2026-10-16.md). C2, P5-A..J e DEC-01..04 permanecem PO_APPROVED; Core T05 source de grupo/função e política de zero áreas obrigatórias (D-FINAL-01/02) impedem fechar A12/A14/A15/A16. Até decisões/evidências: `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`; runtime `TEST_NOT_RUN`. Flags PASS anteriores neste documento são históricas, não substituem o gate vigente.

**Evidência e gate pós-merge vigente:** [38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md) (`A15=INCONCLUSIVE` até contratos/testes verificados).

**TARGET / A15 HISTORICAL_CONSOLIDATION / POSTMERGE_REVALIDATION_INCONCLUSIVE / CONTRACT_BINDINGS_TO_INVENTORY**

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
| A12 | P5 Pacote, Finalização e Envio | C2 / P5-A..J / DEC-01..04 PO_APPROVED; CORE_ELIGIBILITY_AND_BINDINGS_TO_INVENTORY |
| A13 | P6 Administração / Configuração | READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY |

A12 tem decisões de produto aprovadas: C2, D-P5-01..05 refinadas por P5-A..J, DEC-01..04. Rejeição, reatribuição, quorum por área/versão e não reversão estão definidos semanticamente no doc 37; os contratos físicos de elegibilidade, persistência, estados, concorrência, eventos e consumers permanecem TO_INVENTORY.

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
deriveMonthlyClosingCompletion [C2 approved; physical operationId TO_INVENTORY]
```

```text
PACKAGE_FINALIZED
→ PACKAGE_SUBMITTED_FOR_REVIEW
→ REVIEW_PENDING
→ REVIEW_IN_PROGRESS
→ REVIEW_ACCEPTED | CHANGES_REQUESTED | REVIEW_REJECTED
```

Package permanece na Minha DELPI. E-mail é notification only.

**Semântica aprovada:** C2 exige todos pacotes aplicáveis submetidos, um aceite de cada **área obrigatória** na PackageVersion atual, nenhuma clarification aberta nem rejeição terminal confirmada. `REVIEW_REJECTED` por área abre decisão pendente; só coordenador formal DEC-01 pode confirmar terminalmente. Sem confirmação, DEC-02 conserva pendência e permite devolução motivada. P6 congela snapshot de áreas na submissão; DEC-03 não permite reversão de aceite V1.

**Residual TO_INVENTORY (antes de runtime):** Core S2S grupo/função para elegibilidade, binding de coordenador/ownership, snapshots P6, DTO/operationId/eventos/OCC, armazenamento e contract tests; a lista acima representa capacidades **PLANNED**, não rotas existentes.

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
- `validate-p5-submission-review-contract` — **PLANNED:** submissão in-portal, quórum de um aceite por área obrigatória/PackageVersion atual, DEC-01/02 rejeição confirmada ou pendente, versionamento, reatribuição, fail-closed Core e negativos AuthZ
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

## 12. Residual vigente para o freeze transversal

O antigo inventário E04/T04 de envio externo por e-mail é `CLOSED / NOT_REQUIRED_IN_V1`. C2 e as decisões P5-A..J / DEC-01..04 foram aprovadas; não existe nova escolha C1/C2/C3 a solicitar.

```text
PRODUCT_DECISIONS_P5 = PO_APPROVED
CORE_EFFECTIVE_ACCESS_S2S = PROVEN (source controller, no live smoke)
CORE_CORPORATE_GROUP_FUNCTION_ATTRIBUTE = TO_INVENTORY
P5_AREA_ELIGIBILITY_BINDING = TO_INVENTORY
P5_REVIEW_STATE_DTO_EVENTS_AND_OCC = TO_INVENTORY
P6_REQUIRED_AREAS_VERSIONING_BINDING = TO_INVENTORY
A12_POSTMERGE = INCONCLUSIVE
```

Os contratos semânticos aprovados são rastreados no doc 37 e no ledger 23. Revalidar os producer/consumer bindings antes de converter planos de scripts em evidências de execução.

## 13. Freeze readiness após A15

```text
PORTAL_DESIGN_FREEZE          = REVALIDATE_POSTMERGE
FRONTEND_PATTERN_FREEZE       = PASS
SECURITY_MODEL_FREEZE         = REVALIDATE_CORE_T05
TEST_STRATEGY_FREEZE          = REVALIDATE_TEST_MATRIX
PRODUCT_CONTRACT_FREEZE       = PENDING_CORE_T05_AND_PHYSICAL_BINDINGS

DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED      = NO
```

Próximo passo:
- C2 já aprovada; completar binding Core T05, normalização de contratos e prova da matriz de testes;
- reexecutar residual search;
- somente então avaliar `PRODUCT_CONTRACT_FREEZE = PASS` e `DOCUMENTATION_CLOSURE_COMPLETE = PASS`.

**Nota de proveniência:** este relatório conserva a revisão/estratégia histórica; não é fonte independente de `PASS` atual. **Fonte normativa atual de P5:** [37 — contrato consolidado](./37-p5-submissao-e-revisao-no-portal.md); critérios no [ledger 23](./23-ledger-rq-ac-testes.md), plano no [39](./39-roadmap-mestre-implementacao-v1.md), estado de execução no [README](./README.md). O conteúdo anterior de P5 contraditório é `SUPERSEDED`.
