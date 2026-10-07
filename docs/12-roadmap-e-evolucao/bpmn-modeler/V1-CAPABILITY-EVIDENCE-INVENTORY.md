# BPMN Modeler V1 — Capability Evidence Inventory (G1)

> **Gate:** G1 — V1 Capability Evidence Inventory
> **Baseline:** `cbaa3d2eee71fe326760df6496b049e6c65ebccd` (main, 2026-10-07)
> **Status:** INVENTORY — read-only audit; nenhum código alterado, nenhum gap corrigido.
> **Fontes vigentes:** `CURRENT-STATE.md` (implementação) + `V1-SCOPE-FREEZE.md` §6–8 (target profile). Não confundir os dois.

## 0. Regras de classificação

- `PROVEN` — evidência de produto identificável (E2E > integration > unit > code). "Vendor suporta" **não** prova produto.
- `PARTIAL` — parte do caminho provada (ex.: import/render/validate ok, create vendor-only).
- `VENDOR_ONLY` — módulo vendor ativo/carregado, sem evidência de UX, governança ou teste do produto.
- `MISSING` — comprovado que a capability requerida não existe (nem vendor).
- `TO_INVENTORY` — evidência insuficiente para concluir.
- Coluna `NOT_APPLICABLE` quando a dimensão não se aplica ao construct.

## 1. Vendor surface auditada

`Modeler` carrega 36 módulos (bundle auditado `node_modules/bpmn-js@18.30.1/lib/Modeler.js`): Palette, ContextPad, Create, Connect, Move, Resize, Snapping, **GridSnapping**, **CopyPaste**, **Search (searchPad + BpmnSearchProvider)**, LabelEditing (direct editing), **AlignElements**, **DistributeElements**, EditorActions, Keyboard (+`BpmnKeyboardBindings`), KeyboardMove(Selection), InteractionEvents, ReplacePreview, Outline, Bendpoints, MoveCanvas, ZoomScroll, LassoTool/SpaceTool/HandTool/GlobalConnect (via interaction modules), AutoPlace, AutoResize, AutoScroll, ModelingFeedback, KeepSelectionVisible.

`additionalModules` do produto: `ptBrTranslateModule`, `BpmnPropertiesPanelModule`, `BpmnPropertiesProviderModule`, `propertiesPanelModule` (AdvancedIdProvider + PanelChromePtBr). **Sem provider custom de palette, context pad ou replace** — toda a superfície vendor está exposta.

### Vendor palette (create entries)

`create.start-event`, `create.intermediate-event`, `create.end-event`, `create.exclusive-gateway`, `create.task`, `create.subprocess-expanded`, `create.data-object`, `create.data-store`, `create.participant-expanded`, `create.group` + tools (lasso, hand, space, global-connect). **Não existe palette search vendor** (SearchModule = search de diagrama, não de palette).

### Vendor replace menu (PopupEntries — 78 opções)

Tasks: `task`, `user-task`, `service-task`, `send-task`, `receive-task`, `manual-task`, `rule-task`, `script-task`, `call-activity`, `transaction`, `event-subprocess`, `collapsed/expanded-subprocess`, `collapsed/expanded-ad-hoc-subprocess`. Gateways: exclusive, parallel, inclusive, **complex**, event-based. Events: none/message/timer/conditional/signal/error/escalation/compensation/link por posição, incl. non-interrupting. Data: `data-store-reference`, `data-object-reference`. Pools: `expanded-pool`, `collapsed-pool`. **Inclui constructs `RENDER_PRESERVE_ONLY` e `MultiInstanceLoopCharacteristics` — expostos sem governança (DRIFT-BPMN-010 confirmado).**

### Vendor keyboard bindings (`BpmnKeyboardBindings` + diagram-js `KeyboardBindings`)

`Ctrl+A` select-all, **`Ctrl+F` → `find` → searchPad.toggle()**, `S` space-tool, `L` lasso, `H` hand, `C` global-connect, `E` direct-editing, `R` replace + bindings herdados (undo/redo, delete, copy/paste via DOM events, zoom). **`Ctrl+F` está funcionalmente ligado ao search pad vendor** — refina DRIFT-BPMN-009 (overlay existe via vendor; gap é evidência/produto, não ausência de feature).

### Vendor properties panel (`BpmnPropertiesProviderModule`)

Groups/entries presentes no bundle: `CalledElement`, `ConditionProps`, `DefaultFlow`, `EventDefinition`, `MessageProps`, `SignalProps`, `ErrorProps`, `EscalationProps`, `TimerProps`, `LinkProps`, `CompensationProps`, `ProcessRef`, `isExpanded`, name, id, documentation, `isExecutable`, `VersionTag`, `LoopCharacteristics`/`MultiInstance` props. Bundle também contém providers de engine (CandidateUsers etc.) — **TO_INVENTORY** se carregados em runtime com o provider genérico.

## 2. Master capability matrix (por categoria)

Legenda: P=PROVEN · V=VENDOR_ONLY · TI=TO_INVENTORY · M=MISSING · —=NOT_APPLICABLE · "rb"=read-back · "rt"=round-trip

### 2.1 Activities

| Construct | Import | Render | Preserve | Create | Edit | Props | Validate | Save/rb | Export/Reimport | Round-trip | Undo | Layout | Overall | Evidência |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Task (generic) | P | P | P | P | P | P | P | P | P | P | P | P | **PROVEN** | `create.task`/`append.append-task` E2E-40/modeler-journeys; drag→lane/subprocess E2E-40; delete E2E-07; AUTO-08 rename |
| User Task | P | P | P | V | V | V | P | P | TI | PARTIAL | V | code | **PARTIAL** | `bpmn:userTask` só em fixture i18n (sidebar-i18n); replace menu vendor |
| Service Task | P | V | P | V | V | V | P | P | TI | PARTIAL | V | code | **PARTIAL** | diProposal.ts lista tipo; replace vendor |
| Manual Task | P | V | P | V | V | V | P | P | TI | PARTIAL | V | code | **PARTIAL** | idem |
| Business Rule Task | P | V | P | V | V | V | P | P | TI | PARTIAL | V | code | **PARTIAL** | translate.test.ts (i18n label) |
| Script Task | P | V | P | V | V | V | P | P | TI | PARTIAL | V | code | **PARTIAL** | diProposal |
| Send Task | P | V | P | V | V | V | P | P | TI | PARTIAL | V | code | **PARTIAL** | diProposal |
| Receive Task | P | V | P | V | V | V | P | P | TI | PARTIAL | V | code | **PARTIAL** | diProposal |
| Call Activity | P | V | P | V | V | V(calledElement) | P | P | TI | PARTIAL | V | code | **PARTIAL** | layoutProfile `callActivity`; vendor CalledElement |
| SubProcess expanded | P | P | P | V | V | V | P | P | TI | PARTIAL | P | P | **PARTIAL** | HIER-02 preview, containment unit+E2E; palette `create.subprocess-expanded` vendor |
| SubProcess collapsed | P | P | P | V | V | V | P | P | TI | PARTIAL | P | P | **PARTIAL** | HIER-04 `isExpanded` preservado; unit diProposal |
| Ad-hoc SubProcess (preserve-only) | P | V | P | V(exposto!) | V | V | P | P | TI | PARTIAL | — | code | **PARTIAL** | FX_PRESERVE_001 backend; replace expõe criação (gap) |
| Transaction (preserve-only) | P | V | P | V(exposto!) | V | V | P | P | TI | PARTIAL | — | code | **PARTIAL** | FX_PRESERVE_001 |
| Event SubProcess (preserve-only) | P | V | P | V(exposto!) | V | V | P | P | TI | PARTIAL | — | code | **PARTIAL** | FX_PRESERVE_001 |

### 2.2 Events (posição × definition)

| Posição | Definition | Target | Create | Edit | Props | Import/Render/Preserve | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|---|
| Start | None | CE | P | P | P | P | P | **PROVEN** | fixtures+E2E-31 seleção+layout |
| Start | Message/Timer/Signal | CE | V | V | V | P(XSD) | TI | **PARTIAL** | replace entries vendor |
| Start | Conditional/Multiple/Parallel | preserve | — | — | — | TI | TI | **TO_INVENTORY** | sem fixture |
| EventSubProcess Start | Error/Escalation/etc | preserve | — | — | — | TI | TI | **TO_INVENTORY** | — |
| Catch | Message/Timer/Signal | CE | V | V | V | P(XSD) | TI | **PARTIAL** | replace vendor |
| Catch | Link | CE | V | V | V | P | PARTIAL | **PARTIAL** | FX_LINK_001 backend + fixture E2E modeler-journeys |
| Catch | Conditional/Multiple/Parallel | preserve | — | — | — | TI | TI | **TO_INVENTORY** | — |
| Boundary (int/non-int) | Error | CE | V | V | V | P | PARTIAL | **PARTIAL** | FX_BND_001 backend; diProposal code |
| Boundary | Message/Timer/Signal/Escalation | CE | V | V | V | P(XSD) | TI | **PARTIAL** | replace vendor (message/timer/escalation/signal/error boundary entries) |
| Boundary | Conditional/Cancel/Compensation/Multiple | preserve | — | — | — | TI | TI | **TO_INVENTORY** | replace expõe criação (gap) |
| Throw | None | CE | V | V | V | P | TI | **PARTIAL** | vendor generic |
| Throw | Message/Signal/Escalation/Link | CE | V | V | V | P(XSD) | TI | **PARTIAL** | replace vendor |
| Throw | Compensation/Multiple | preserve | — | — | — | TI | TI | **TO_INVENTORY** | — |
| End | None | CE | P | P | P | P | P | **PROVEN** | fixtures FX_VALID_001 + render E2E |
| End | Message/Error/Signal/Escalation/Terminate | CE | V | V | V | P(XSD) | TI | **PARTIAL** | replace vendor |
| End | Compensation/Cancel/Multiple | preserve | — | — | — | TI | TI | **TO_INVENTORY** | — |

### 2.3 Gateways

| Gateway | Import/Render/Preserve | Create | Edit | Props | Validate | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|---|
| Exclusive | P | PARTIAL | P | P(default/cond vendor) | P | P | P | **PROVEN** | usado em >6 specs E2E; FX_GW_002 default+condition; replace popup E2E |
| Parallel | P | V | V | V | P | code | TI | **PARTIAL** | diProposal list; replace vendor |
| Inclusive | P | V | V | V | P | code | TI | **PARTIAL** | diProposal list |
| Event-Based | P | V | V | V | P | code | PARTIAL | **PARTIAL** | FX_GW_001 semantic rule backend |
| Complex (preserve) | P(backend)+V(render) | V(exposto!) | — | — | P | code | PARTIAL | **PARTIAL** | FX_PRESERVE_001 |

### 2.4 Connecting objects

| Construct | Create | Edit/Reconnect | Props | Validate | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|
| Sequence Flow | P | P(reconnect V) | P(cond/default V-ui) | P | P | P | **PROVEN** | append E2E; FX_GW_002; RTM-04 invalid connect; STRUCT-010..012 |
| Message Flow | V | V | V | P | P | PARTIAL | **PARTIAL** | FX_VALID_002 backend; layout-hierarchy E2E render |
| Association | V | V | V | P(STRUCT-017) | code | TI | **PARTIAL** | diProposal/elkGraph code |
| Data Association | V | V | V | P(STRUCT-018) | code | TI | **PARTIAL** | diProposal code |

### 2.5 Collaboration

| Construct | Create | Edit | Resize | Props | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|
| Participant/Pool | V | P | V | P(processRef IDG-05) | P | PARTIAL | **PARTIAL** | palette `create.participant-expanded` vendor; RTM drop rules E2E; FX_VALID_002 |
| Lane | V | P | V | V | P | PARTIAL | **PARTIAL** | layout-hierarchy E2E; diProposal unit (flowNodeRef containment) |
| Multiple pools | — | — | — | — | P | PARTIAL | **PARTIAL** | FX_VALID_002 |
| Multiple lanes | — | — | — | — | P | PARTIAL | **PARTIAL** | layout-hierarchy E2E |
| Nested lanes | — | — | — | — | P | PARTIAL | **PARTIAL** | FX_VALID_002 childLaneSet + diProposal unit |
| Message flow entre pools | V | — | — | — | P | PARTIAL | **PARTIAL** | FX_VALID_002; layout E2E |
| Black-box pool | V | V | — | — | code | PARTIAL | **PARTIAL** | FX_VALID_002 Pool_B sem processRef reconhecido; `collapsed-pool` replace vendor |

### 2.6 Data / Artifacts

| Construct | Create | Edit | Props | Validate | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|
| Data Object / Reference | PARTIAL | V | V | P(FX_REF_003/005) | P | PARTIAL | **PARTIAL** | `create.data-object` E2E-attempt (RTM-03 rejection = palette+governança ativa) |
| Data Store Reference | V | V | V | P | P | PARTIAL | **PARTIAL** | layout-hierarchy/geometry E2E; diProposal.test |
| Data Input/Output (preserve) | — | — | — | TI | code | TI | **TO_INVENTORY** | — |
| Text Annotation | V | V | V | P | code | TI | **PARTIAL** | layoutProfile/diProposal code |
| Group | V | P | P(visual) | P | P | P | **PROVEN(preserve/layout)** | layout-group E2E GROUP-01..07 (vazio, overlap parcial, aninhado, bounds DI); diProposal unit |

## 3. Properties matrix

| Property | Target | Product impl | Test | Status |
|---|---|---|---|---|
| name | IN_V1 | vendor + direct edit + panel | AUTO-08 (rename→autosave), E2E-40 | **PROVEN** |
| BPMN id (edit) | entregue (G0) | AdvancedIdProvider + vendor stack | IDG-01..05 E2E | **PROVEN** |
| processId/processRef | IN_V1 | vendor entry realocado | IDG-05 E2E | **PROVEN** |
| documentation | IN_V1 | vendor entry | — | **VENDOR_ONLY** |
| conditionExpression | IN_V1 | vendor ConditionProps | FX_GW_002 valida XML, sem UI test | **VENDOR_ONLY** |
| default flow | IN_V1 | vendor DefaultFlow | idem | **VENDOR_ONLY** |
| event definition swap/fields | IN_V1 | vendor EventDefinition + Message/Timer/Signal/Error/Escalation/Link/Compensation props | — | **VENDOR_ONLY** |
| lane name | IN_V1 | vendor (direct edit) | — | **VENDOR_ONLY** |
| task type | IN_V1 | replace menu vendor | popup abre (E2E-40), ação não exercitada | **VENDOR_ONLY** |
| subprocess expanded/collapsed | IN_V1 | vendor replace + `isExpanded` | HIER-04 preserva estado | **PARTIAL** |
| calledElement | IN_V1 | vendor CalledElement | — | **VENDOR_ONLY** |
| engine binding fields | OUT_OF_V1 | provider genérico Bpmn (sem camunda); bundle tem MultiInstance/VersionTag/isExecutable | — | **TO_INVENTORY** (exposição exata em runtime) |

## 4. Productivity matrix

| Capability | Target | Vendor | Product wiring | UX | Test | Status | Gap owner |
|---|---|---|---|---|---|---|---|
| Copy/Paste/Cut (mesmo modelo) | IN_V1 | CopyPasteModule + DOM keybindings | ativo | vendor | — | **VENDOR_ONLY** | 03/06 |
| Multi-select (Shift/lasso) | IN_V1 | SelectionModule+LassoTool (`L`) | ativo | vendor | — | **VENDOR_ONLY** | 03/06 |
| Select all | IN_V1 | vendor + `Ctrl+A` | context menu "Selecionar tudo" | product | E2E-34 | **PROVEN** | — |
| Bulk move | IN_V1 | MoveModule | ativo | vendor | — | **VENDOR_ONLY** | 03/06 |
| Bulk delete | IN_V1 | modeling | ativo | vendor | — | **VENDOR_ONLY** | 03/06 |
| Ctrl/Cmd+S | IN_V1 | — | product flush | product | AUTO/UNLOAD specs | **PROVEN** | — |
| Undo/Redo (Ctrl+Z/Y) | IN_V1 | commandStack+keys | product | product | theme-stability, E2E-06, AUTO-04/05 | **PROVEN** | — |
| Delete key | IN_V1 | vendor binding | ativo | vendor | delete via menu E2E-07 | **PARTIAL** | 03/06 |
| Zoom/Pan/Fit | IN_V1 | ZoomScroll/MoveCanvas | adapter + floating controls | product | E2E-35/38, CANVAS-REG-04 | **PROVEN** | — |
| Ctrl/Cmd+F search | IN_V1 | **searchPad+`find` bindado** | módulo ativo + tradução PT-BR da label | vendor | — | **PARTIAL** (evidence gap) | 03/06 |
| Search by name/id | IN_V1 | searchPad + adapter `findElements` | API existe | vendor | unit adapter | **PARTIAL** | 03 |
| Palette search | IN_V1 | **não existe vendor** | — | — | — | **MISSING** | 03 (G3) |
| Snap/Grid fixo | IN_V1 | GridSnapping+Snapping ativos | config vendor default | vendor | — | **PARTIAL** | 03 |
| Resize | IN_V1 | ResizeModule | resizers visíveis | product theme | E2E-40 (visual) | **PARTIAL** | 03/06 |
| Direct editing | IN_V1 | LabelEditingModule (`E`, dblclick) | ativo | product theme | E2E-40 | **PROVEN** | — |
| Replace/context pad | IN_V1 | ContextPad+ReplaceMenu | popup temático | product theme | E2E-32/40 (abre/fecha) | **PARTIAL** | 03/06 |
| Mini-map | FUTURE | — | — | — | — | **NOT_APPLICABLE** | — |
| Align/Distribute | FUTURE | **módulos ATIVOS** | expostos sem governance | vendor | — | **VENDOR_ONLY** (exposição fora do profile) | 00/03 |

## 5. Round-trip, validation, layout, multi-diagram

- **Round-trip (artefato):** PROVEN byte-exact — `test_import_model_roundtrip` (import→read-back conteúdo idêntico + checksum), `X-Artifact-SHA256` na API, export E2E-01/02, extensão preservada E2E-10. **Per-construct compare (export→reimport→diff semântico/DI): PARTIAL** — sem suíte por construct.
- **Validation:** PROVEN — catálogo 47/47 implementado (SEC-7, XML-WF-2, REC-4, STRUCT-11, SEM-8, BPMNDI-9, PROD-2, EXT-4) com `test_validation_contract`/`test_validation_engine` sobre corpus FX-* (collab+lanes+black-box+messageFlow, boundary error, link, gateways, condition/default, preserve-only set, DI 7 casos, security 2). Regras semânticas por construct específico: PARTIAL (SEM-001..008 cobrem padrões selecionados).
- **Layout:** PROVEN para task/event/gateway/pool/lane/subProcess(expanded/collapsed)/messageFlow/group/label — 4 specs E2E (LGEO, HIER, GROUP, LABEL) + `diProposal.test.ts` (~30 tests). Exotic constructs (ad-hoc, transaction, boundary, data objects raros): code-supported em `elkGraph`/`diProposal`, sem E2E dedicado → PARTIAL.
- **Múltiplos BPMNDiagram:** PROVEN — E2E-18 (seletor, troca), FX_DI_004 backend (2 planes), adapter diagram switching.
- **Extensions:** PROVEN — E2E-10 (mustUnderstand=false preserva round-trip), E2E-11 (mustUnderstand=true → read-only gate), EXT-001..004 backend.
- **Unknown BPMN válido fora do profile:** PARTIAL — FX_PRESERVE_001 (complex+adHoc+transaction+eventSubProcess) reconhecido/válido; render = vendor best-effort não auditado por construct.

## 6. VENDOR-ONLY capabilities (não promover a produto)

Copy/paste/cut · lasso + shift multi-select · bulk move/delete/copy · align/distribute · space-tool · hand-tool · global-connect · keyboard-move · replace-menu actions (todas as morphs) · context-pad append de tipos específicos · palette create entries não-task (subprocess, pool, data-store, group, gateways via append) · typed task create (9) · event definition swap/fields · boundary/intermediate throw create · complex gateway · ad-hoc/transaction/event-subprocess create **(fora do profile, exposto)** · MultiInstanceLoopCharacteristics **(fora do profile, exposto)** · documentation edit · conditionExpression UI · defaultFlow UI · calledElement · Ctrl+F search pad overlay · shortcuts S/L/H/C/E/R · palette search pad (inexistente vendor) · CandidateUsers/engine providers (**TO_INVENTORY** se carregados).

## 7. Gaps

### IMPLEMENTATION GAPS (feature requerida ausente)

| GAP | Capability | Evidence | Missing | Owner | Severity | Wave |
|---|---|---|---|---|---|---|
| IG-1 | Palette search (IN_V1) | vendor não implementa | feature inteira | 03 | P2 | G3 |
| IG-2 | Profile governance (palette/context-pad/replace/panel) | ~~replace expõe ad-hoc/transaction/eventSubProcess/complex/MultiInstance~~ | provider de restrição | 03+02 | **P1** | G2/G3 → **CLOSED / VERIFIED AFTER CORRECTION PASS** — `editingProfile.ts`+`profileGovernanceModule.ts`+`ProfileGovernedPanelProvider`; fail-closed em todas as surfaces incl. properties entries (allowlist); bypasses corrigidos: `none-boundary-event` (não-criável), `append.compensation-activity` (compensation preserve-only); `isExecutable` classificado BPMN normativo, edição oculta por decisão de produto, valor preservado no round-trip. Evidência `profile-governance.spec.ts` |

### EVIDENCE GAPS (provavelmente funciona, sem prova de produto)

| GAP | Capability | State | Owner | Severity | Wave |
|---|---|---|---|---|---|
| EG-1 | Copy/cut/paste mesmo modelo | vendor wired, zero test | 06+03 | P2 | G3 |
| EG-2 | Multi-select/lasso/bulk ops | vendor wired, zero test | 06+03 | P2 | G3 |
| EG-3 | Typed tasks + callActivity create/edit/calledElement | replace menu expõe, zero test | 03+02 | **P1** | G2 |
| EG-4 | Event definitions CE (create/swap/fields) | vendor expõe, zero test | 03+02 | **P1** | G2 |
| EG-5 | Parallel/Inclusive/EventBased gateway create | vendor expõe, backend valida | 03+02 | **P1** | G2 |
| EG-6 | Pool/lane create/resize/membership | vendor expõe, layout provado | 03+04 | P1 | G2 |
| EG-7 | Message flow create entre pools | vendor, fixture backend | 03 | P2 | G2 |
| EG-8 | Per-construct round-trip compare | só byte-exact genérico | 02+06 | P1 | G4 |
| EG-9 | Resize funcional | resizers visuais testados | 03 | P3 | G3 |
| EG-10 | Search pad overlay (Ctrl+F funciona?) | vendor wired + traduzido, zero test | 03+06 | P2 | G3 |
| EG-11 | TextAnnotation/Association/DataAssociation create | vendor expõe | 03 | P2 | G3 |
| EG-12 | Preserve-only render/round-trip por construct | backend fixture único | 02+06 | P1 | G4 |
| EG-13 | Shortcuts vendor (Del, R, E, S, L, H, C, zoom) | bindings ativos | 03+06 | P2 | G3 |
| EG-14 | Engine fields no panel (isExecutable/MultiInstance/VersionTag) | bundle tem; exposição runtime TI | 03+02 | P2 | G3 |

### TARGET GAPS (scope congelado não inventariado)

- TG-1: prova CREATE por construct para todo o profile `CREATE_EDIT` (EG-3..7 cobrem).
- TG-2: `RENDER_PRESERVE_ONLY` — fixtures por definition (conditional/multiple/parallel-multiple/cancel/compensation start/catch/throw/end/boundary; DataInput/Output; event-subprocess start events).
- TG-3: subprocesso/pool collapsed-pool create path.

### G3 gaps (já identificados em G0) — verificação

- **Diagram search:** REFINADO — overlay vendor searchPad existe e está bindado (Ctrl+F) + traduzido PT-BR. Gap real = evidência/produto-styling, não ausência. → EG-10.
- **Palette restriction:** ~~CONFIRMADO — nenhum provider de restrição~~ → **CLOSED (G2A)** — palette/context-pad/replace/panel governados pelo profile central (`editingProfile.ts`), fail-closed; preserve-only e MultiInstance não são criáveis nem replace targets. → IG-2 closed.
- **Copy/paste:** CONFIRMADO vendor-only. → EG-1.
- **Multi-select:** CONFIRMADO vendor-only (exceto select-all). → EG-2.
- **Palette search:** CONFIRMADO MISSING (vendor não fornece). → IG-1.
- **Snap/grid:** vendor ativo com config default — não é configuração de produto explícita → PARTIAL.

## 8. V1 scope completeness score

- **Activities:** 1 PROVEN (generic Task) · 10 PARTIAL · 3 PARTIAL-preserve · 0 MISSING · 0 TI no target CE.
- **Events:** ~2 linhas PROVEN (start-none, end-none) · ~6 PARTIAL · ~8 TO_INVENTORY (preserve-only sem fixture).
- **Gateways:** 1 PROVEN (Exclusive) · 3 PARTIAL · 1 PARTIAL-preserve.
- **Connecting:** 1 PROVEN (SequenceFlow) · 3 PARTIAL.
- **Collaboration:** 0 full-PROVEN · 7 PARTIAL (todas com evidência de render/layout/backend, create vendor-only).
- **Data/Artifacts:** 1 PROVEN (Group — preserve/layout) · 4 PARTIAL · 1 TO_INVENTORY (DataIO).
- **Productivity:** 6 PROVEN (select-all, Ctrl+S, undo/redo, zoom/pan/fit, direct edit, canvas) · ~10 PARTIAL · ~12 VENDOR_ONLY · 1 MISSING (palette search).
- **Validation:** PROVEN (47/47 regras) · per-construct semantic PARTIAL.
- **Round-trip:** artifact-level PROVEN · per-construct PARTIAL.
- **Lifecycle/API/Ownership/Autosave/Revisions:** PROVEN (fora do escopo deste inventário — ver CURRENT-STATE).

## 9. Candidate next waves (input para 00 — não é decisão)

- **WAVE A — Profile Governance:** provider de restrição palette/context-pad/replace/panel para o profile CE; bloquear/excluir preserve-only+engine constructs da criação. (IG-2, EG-14) — P1, owners 03+02. → **EXECUTED (G2A, PASS)** — parte creation/replacement fechada; exposição residual de engine fields no panel = TO_INVENTORY (EG-14 permanece para WAVE E).
- **WAVE B — CREATE_EDIT Evidence Closure:** E2E de create/edit/save/read-back por construct CE (typed tasks, gateways P/I/EB, event defs, lanes/pools, messageFlow, artifacts). (EG-3..7, EG-11, TG-1) — P1, owners 03+06.
- **WAVE C — Round-trip & Preserve Evidence:** suíte export→reimport→compare por construct + corpus preserve-only. (EG-8, EG-12, TG-2) — P1, owners 02+06.
- **WAVE D — Productivity:** copy/paste, multi-select/bulk, search pad product QA, palette search impl, shortcuts map, resize funcional. (EG-1,2,9,10,13, IG-1) — P2, owners 03+06.
- **WAVE E — Properties Evidence:** doc/condition/default/event-fields/calledElement UI tests. — P2, owner 03+06.
- **WAVE F — Vendor Exposure Decision:** align/distribute/space/hand/global-connect ativos mas FUTURE — decidir manter/desativar/documentar. — P3, owner 00+03.

Ordem sugerida: A → B → C → D/E → F. **FINAL PRIORITY OWNER: 00 — Arquitetura & Coordenação.**

## 10. Notas de método

- Evidência hierarquizada: E2E real > integration > unit > code > vendor > doc target.
- Nenhum teste foi executado neste gate (inventário estático); comandos de busca listados na seção residual do relatório.
- `bpmn-js@18.30.1`, `bpmn-js-properties-panel@5.65.1`, `elkjs@0.12.0` — pins auditados.
- Nenhuma capability foi promovida por presença vendor; nenhum target foi rebaixado por ausência de implementação.
