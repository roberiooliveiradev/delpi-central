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

`additionalModules` do produto: `ptBrTranslateModule`, `BpmnPropertiesPanelModule`, `BpmnPropertiesProviderModule`, `propertiesPanelModule` (AdvancedIdProvider + PanelChromePtBr + **BpmnCorePropsProvider** — provider de produto BPMN-core para `calledElement`/`conditionExpression`/`defaultFlow`, command-stack backed — WAVE E) e **`profileGovernanceModule`** (G2A: palette/context-pad/replace/clipboard fail-closed; WAVE F: desligamento de surfaces FUTURE/não-frozen via DI `value:null` + unregister de editor actions — §6a). Engine providers Camunda/Zeebe: **NÃO CARREGADOS** (GOV-15/16/17 + VX-07).

### Vendor palette (create entries)

`create.start-event`, `create.intermediate-event`, `create.end-event`, `create.exclusive-gateway`, `create.task`, `create.subprocess-expanded`, `create.data-object`, `create.data-store`, `create.participant-expanded`, `create.group` + tools (lasso, hand, space, global-connect). **Não existe palette search vendor** (SearchModule = search de diagrama, não de palette).

### Vendor replace menu (PopupEntries — 78 opções)

Tasks: `task`, `user-task`, `service-task`, `send-task`, `receive-task`, `manual-task`, `rule-task`, `script-task`, `call-activity`, `transaction`, `event-subprocess`, `collapsed/expanded-subprocess`, `collapsed/expanded-ad-hoc-subprocess`. Gateways: exclusive, parallel, inclusive, **complex**, event-based. Events: none/message/timer/conditional/signal/error/escalation/compensation/link por posição, incl. non-interrupting. Data: `data-store-reference`, `data-object-reference`. Pools: `expanded-pool`, `collapsed-pool`. **Inclui constructs `RENDER_PRESERVE_ONLY` e `MultiInstanceLoopCharacteristics` — expostos sem governança (DRIFT-BPMN-010 confirmado).**

### Vendor keyboard bindings (`BpmnKeyboardBindings` + diagram-js `KeyboardBindings`)

`Ctrl+A` select-all, **`Ctrl+F` → `find` → searchPad.toggle()**, `L` lasso, `H` hand, `C` global-connect, `E` direct-editing, `R` replace + bindings herdados (undo/redo, delete, copy/paste/duplicate, zoom Ctrl±/0). **`Ctrl+F` está funcionalmente ligado ao search pad vendor** — refina DRIFT-BPMN-009 (overlay existe via vendor; gap é evidência/produto, não ausência de feature). **WAVE F:** `S` (space-tool) **desarmado** — editor action `spaceTool` desregistrada em `editorActions.init`, logo o binding nunca é instalado; `keyboardMoveSelection` (setas movem seleção → DI+dirty) **desligado via DI `value:null`**; `keyboardMove` de navegação (Ctrl+setas = pan de viewport, sem mutação) mantido como conveniência de Pan IN_V1. Classificação completa: §6a.

### Vendor properties panel (`BpmnPropertiesProviderModule`)

Groups/entries presentes no bundle: `CalledElement`, `ConditionProps`, `DefaultFlow`, `EventDefinition`, `MessageProps`, `SignalProps`, `ErrorProps`, `EscalationProps`, `TimerProps`, `LinkProps`, `CompensationProps`, `ProcessRef`, `isExpanded`, name, id, documentation, `isExecutable`, `VersionTag`, `LoopCharacteristics`/`MultiInstance` props. Bundle também contém providers de engine (CandidateUsers etc.) — ~~TO_INVENTORY~~ **WAVE F (§6a): engine providers NÃO carregados; grupos/entries fora da allowlist = fail-closed deny; editable engine surface = 0 (VX-07)**.

## 2. Master capability matrix (por categoria)

Legenda: P=PROVEN · V=VENDOR_ONLY · TI=TO_INVENTORY · M=MISSING · —=NOT_APPLICABLE · "rb"=read-back · "rt"=round-trip

### 2.1 Activities

| Construct | Import | Render | Preserve | Create | Edit | Props | Validate | Save/rb | Export/Reimport | Round-trip | Undo | Layout | Overall | Evidência |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Task (generic) | P | P | P | P | P | P | P | P | P | P | P | P | **PROVEN** | `create.task`/`append.append-task` E2E-40/modeler-journeys; drag→lane/subprocess E2E-40; delete E2E-07; AUTO-08 rename |
| User Task | P | P | P | P | P | PARTIAL | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-02: replace→`bpmn:userTask`→save/rb→reload |
| Service Task | P | V | P | P | P | PARTIAL | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-02: `bpmn:serviceTask` QName |
| Manual Task | P | V | P | P | P | PARTIAL | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-02 |
| Business Rule Task | P | V | P | P | P | PARTIAL | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-02 |
| Script Task | P | V | P | P | P | PARTIAL | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-02 |
| Send Task | P | V | P | P | P | PARTIAL | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-02 |
| Receive Task | P | V | P | P | P | PARTIAL | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-02 |
| Call Activity | P | V | P | P | P | P (calledElement PROVEN — WAVE E, PROP-CORE-01) | P | P | P | P | P | code | **PROVEN (path)** | CE-ACT-03: replace→`bpmn:callActivity`→save/rb→reload |
| SubProcess expanded | P | P | P | P | P | PARTIAL | P | P | P | P | P | P | **PROVEN (path)** | CE-ACT-04: palette `create.subprocess-expanded`→save/rb→reload; HIER-02 |
| SubProcess collapsed | P | P | P | P | P | PARTIAL | P | P | P | P | P | P | **PROVEN (path)** | CE-ACT-04: replace→collapsed; HIER-04 `isExpanded` |
| Ad-hoc SubProcess (preserve-only) | P | V | P | V(exposto!) | V | V | P | P | P | P | — | code | **PROVEN (preserve path)** | FX_PRESERVE_001 + RT-PRES-01 (import→serialize→reimport→compare) backend; replace expõe criação (gap) |
| Transaction (preserve-only) | P | V | P | V(exposto!) | V | V | P | P | P | P | — | code | **PROVEN (preserve path)** | FX_PRESERVE_001 + RT-PRES-01 (import→serialize→reimport→compare) |
| Event SubProcess (preserve-only) | P | V | P | V(exposto!) | V | V | P | P | P | P | — | code | **PROVEN (preserve path)** | FX_PRESERVE_001 + RT-PRES-01 (import→serialize→reimport→compare) |

### 2.2 Events (posição × definition)

| Posição | Definition | Target | Create | Edit | Props | Import/Render/Preserve | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|---|
| Start | None | CE | P | P | P | P | P | **PROVEN** | fixtures+E2E-31 seleção+layout |
| Start | Message/Timer/Signal | CE | P | P | PARTIAL | P(XSD) | P | **PROVEN (path)** | CE-EVT-01: replace defs→EventDefinition XML→save/rb→reload |
| Start | Conditional/Multiple/Parallel | preserve | — | — | — | P | P | **PROVEN (preserve)** | sem fixture |
| EventSubProcess Start | Error/Escalation/etc | preserve | — | — | — | P | P | **PROVEN (preserve)** | — |
| Catch | Message/Timer/Signal | CE | P | P | PARTIAL | P(XSD) | P | **PROVEN (path)** | CE-EVT-02: append catch→replace defs→read-back |
| Catch | Link | CE | P | P | PARTIAL | P | P | **PROVEN (path)** | CE-EVT-02 replace link; FX_LINK_001 backend |
| Catch | Conditional/Multiple/Parallel | preserve | — | — | — | P | P | **PROVEN (preserve)** | — |
| Boundary (int/non-int) | Error | CE | P | P | PARTIAL | P | P | **PROVEN (path)** | CE-EVT-04 attach+replace; FX_BND_001 backend |
| Boundary | Message/Timer/Signal/Escalation | CE | P | P | PARTIAL | P(XSD) | P | **PROVEN (path)** | CE-EVT-04: drop on task (`attachedToRef`) + defs + non-int `cancelActivity="false"` |
| Boundary | Conditional/Cancel/Compensation/Multiple | preserve | — | — | — | P | P | **PROVEN (preserve)** | replace expõe criação (gap) |
| Throw | None | CE | P | P | PARTIAL | P | P | **PROVEN (path)** | CE-EVT-03 append `append.intermediate-event` |
| Throw | Message/Signal/Escalation/Link | CE | P | P | PARTIAL | P(XSD) | P | **PROVEN (path)** | CE-EVT-03 replace defs |
| Throw | Compensation/Multiple | preserve | — | — | — | P | P | **PROVEN (preserve)** | — |
| End | None | CE | P | P | P | P | P | **PROVEN** | fixtures FX_VALID_001 + render E2E |
| End | Message/Error/Signal/Escalation/Terminate | CE | P | P | PARTIAL | P(XSD) | P | **PROVEN (path)** | CE-EVT-05 replace defs→read-back |
| End | Compensation/Cancel/Multiple | preserve | — | — | — | P | P | **PROVEN (preserve)** | — |

### 2.3 Gateways

| Gateway | Import/Render/Preserve | Create | Edit | Props | Validate | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|---|
| Exclusive | P | PARTIAL | P | P (cond/default PROVEN — WAVE E, PROP-FLOW-01..06) | P | P | P | **PROVEN (path)** | CE-GW-01 + >6 specs E2E; FX_GW_002 default+condition (XML backend); replace popup E2E |
| Parallel | P | P | P | — | P | code | P | **PROVEN (path)** | CE-GW-02: replace→connect→`bpmn:parallelGateway`→save/rb |
| Inclusive | P | P | P | P (cond/default PROVEN — WAVE E, PROP-FLOW-01..06) | P | code | P | **PROVEN (path)** | CE-GW-03 |
| Event-Based | P | P | P | — | P | code | P | **PROVEN (path)** | CE-GW-04/05: replace+append catch; conditional append DENY |
| Complex (preserve) | P(backend)+V(render→P E2E RT-PRES-01) | V(exposto!) | — | — | P | code | P | **PROVEN (preserve path)** | FX_PRESERVE_001 + RT-PRES-01 |

### 2.4 Connecting objects

| Construct | Create | Edit/Reconnect | Props | Validate | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|
| Sequence Flow | P | P(reconnect V) | P (cond/default PROVEN — WAVE E, PROP-FLOW-01..06) | P | P | P | **PROVEN (path)** | append E2E; FX_GW_002 (XML backend); RTM-04 invalid connect; STRUCT-010..012 |
| Message Flow | P | — | — | P | P | P | **PROVEN (path)** | CE-COL-03: tA→tB cross-pool→`<bpmn:messageFlow>`; FX_VALID_002 |
| Association | P | — | — | P(STRUCT-017) | code | P | **PROVEN (path)** | CE-ART-03: task→annotation→`<bpmn:association>` |
| Data Association | P | — | — | P(STRUCT-018) | code | P | **PROVEN (path)** | CE-ART-02: output+input associations→QName+reload |

### 2.5 Collaboration

| Construct | Create | Edit | Resize | Props | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|
| Participant/Pool | P | P | — | P(processRef IDG-05) | P | P | **PROVEN (path)** | CE-COL-01: palette expanded→`processRef`+`laneSet`+save/rb |
| Lane | P | P | — | P | P | P | **PROVEN (path)** | CE-COL-02/05: insert above/below+divide+rename+move task (`flowNodeRef`) |
| Multiple pools | P | — | — | — | P | P | **PROVEN (path)** | CE-COL-03: 2 participants |
| Multiple lanes | P | — | — | — | P | P | **PROVEN (path)** | CE-COL-02/05 |
| Nested lanes | P | — | — | — | P | P | **PROVEN (path)** | CE-COL-02: divide→`childLaneSet` real |
| Message flow entre pools | P | — | — | — | P | P | **PROVEN (path)** | CE-COL-03 |
| Black-box pool | P | V | — | — | code | P | **PROVEN (path)** | CE-COL-04: `replace-with-collapsed-pool`→participant sem processRef |

### 2.6 Data / Artifacts

| Construct | Create | Edit | Props | Validate | Layout | Round-trip | Status | Evidência |
|---|---|---|---|---|---|---|---|---|
| Data Object / Reference | P | P | PARTIAL | P(FX_REF_003/005) | P | P | **PROVEN (path)** | CE-ART-01: `create.data-object`→`bpmn:dataObjectReference`→save/rb |
| Data Store Reference | P | P | PARTIAL | P | P | P | **PROVEN (path)** | CE-ART-01: `create.data-store`→`bpmn:dataStoreReference`→save/rb |
| Data Input/Output (preserve) | — | — | — | P | code | P | **PROVEN (preserve)** | RT-PRES-04: ioSpecification DataInput/DataOutput + sets round-trip |
| Text Annotation | P | P | P(texto editado) | P | code | P | **PROVEN (path)** | CE-ART-03: append→rename→`<bpmn:textAnnotation>`+assoc |
| Group | V | P | P(visual) | P | P | P | **PROVEN(preserve/layout)** | layout-group E2E GROUP-01..07 (vazio, overlap parcial, aninhado, bounds DI); diProposal unit |

## 3. Properties matrix

| Property | Target | Product impl | Test | Status |
|---|---|---|---|---|
| name | IN_V1 | vendor + direct edit + panel | AUTO-08 (rename→autosave), E2E-40 | **PROVEN** |
| BPMN id (edit) | entregue (G0) | AdvancedIdProvider + vendor stack | IDG-01..05 E2E | **PROVEN** |
| processId/processRef | IN_V1 | vendor entry realocado | IDG-05 E2E | **PROVEN** |
| documentation | IN_V1 | vendor entry exposta via allowlist | PROP-DOC-01/02 E2E (task+process → save/rb → reload) | **PROVEN** (WAVE E) |
| conditionExpression | IN_V1 | **BpmnCorePropsProvider** (produto) — `bpmn:FormalExpression` via command stack; somente fonte elegível (Activity/XOR/OR), exclusivo com default | PROP-FLOW-01/03 E2E (set/clear→rb→reload) | **PROVEN** (WAVE E) |
| default flow | IN_V1 | **BpmnCorePropsProvider** (produto) — `source.default` IDREF; exclusividade por source, exclusivo com condition | PROP-FLOW-02/04/05 E2E (set/switch/clear/delete sem ref pendurada) | **PROVEN** (WAVE E) |
| event definition swap | IN_V1 | replace menu | CE-EVT-01..05 (defs por posição) | **PROVEN** |
| event definition fields | IN_V1 | timer type/value + message/signal/error/escalation/link ref entries | CE-EVT-06 (timer) + PROP-EVT-01..05 (root definition + ref → rb → reload) | **PROVEN** (WAVE E) |
| lane name | IN_V1 | direct edit | CE-COL-05 (rename + read-back) | **PROVEN** |
| task type | IN_V1 | replace menu vendor | CE-ACT-02 (7 typed tasks com QName) | **PROVEN** |
| subprocess expanded/collapsed | IN_V1 | palette + replace | CE-ACT-04 create path; HIER-04 preserva estado | **PROVEN** |
| calledElement | IN_V1 | **BpmnCorePropsProvider** (produto) — `CallActivity.calledElement`, sem binding/version (engine) | PROP-CORE-01 E2E (edit→undo/redo→rb→reload) | **PROVEN** (WAVE E) |
| engine binding fields | OUT_OF_V1 | provider genérico Bpmn (sem camunda/zeebe); bundle tem MultiInstance/VersionTag/isExecutable | GOV-15/16/17 + VX-07 E2E (engine editable entries = 0; grupos deny ausentes) | **PROVEN — NOT_EXPOSED** (WAVE F, §6a) |

## 4. Productivity matrix

| Capability | Target | Vendor | Product wiring | UX | Test | Status | Gap owner |
|---|---|---|---|---|---|---|---|
| Copy/Paste/Cut (mesmo modelo) | IN_V1 | CopyPasteModule + DOM keybindings | ativo + `copyPaste.canCopyElements` → `isClipboardElementAllowed` | vendor + governance | PROD-CLIP-01..07 | **PROVEN** | — |
| Multi-select (Shift/lasso) | IN_V1 | SelectionModule+LassoTool (`L`) | ativo | vendor | PROD-SEL-01/02 | **PROVEN** | — |
| Select all | IN_V1 | vendor + `Ctrl+A` | context menu "Selecionar tudo" | product | E2E-34 + PROD-SEL-03 | **PROVEN** | — |
| Bulk move | IN_V1 | MoveModule | ativo | vendor | PROD-SEL-04 | **PROVEN** | — |
| Bulk delete | IN_V1 | modeling | ativo | vendor | PROD-SEL-05 | **PROVEN** | — |
| Ctrl/Cmd+S | IN_V1 | — | product flush | product | AUTO/UNLOAD specs + PROD-KEY-01 | **PROVEN** | — |
| Undo/Redo (Ctrl+Z/Y) | IN_V1 | commandStack+keys | product + restoreFocus pós-drag | product | theme-stability, E2E-06, AUTO-04/05, PROD-CLIP-04, PROD-SEL-04/05, PROD-RSZ, PROD-PAL-SEM-07 | **PROVEN** | — |
| Delete/Backspace key | IN_V1 | vendor binding | ativo | vendor | PROD-KEY-03 + E2E-07 | **PROVEN** | — |
| Zoom/Pan/Fit | IN_V1 | ZoomScroll/MoveCanvas | adapter + floating controls | product | E2E-35/38, CANVAS-REG-04 | **PROVEN** | — |
| Ctrl/Cmd+F search | IN_V1 | searchPad + `find` bindado | módulo ativo + tradução PT-BR | vendor | PROD-SRCH-01..04 | **PROVEN** | — |
| Search by name/id | IN_V1 | searchPad + adapter `findElements` | ativo | vendor | PROD-SRCH-01/02 (nome, id, substring, acentos) | **PROVEN** | — |
| Palette search (semântica) | IN_V1 | não existe vendor | `PaletteSearch` → projeção `listSearchableCreateActions()` do editingProfile (DIRECT_PALETTE_CREATE + CREATE_THEN_REPLACE via replaceMenuProvider governado) | product | PROD-PAL-01..05 + PROD-PAL-SEM-01..08 | **PROVEN** | — |
| Snap/Grid fixo | IN_V1 | GridSnapping+Snapping ativos | config vendor default | vendor | PROD-SEL-06 (grid 10 quantização medida) | **PROVEN** | — |
| Resize | IN_V1 | ResizeModule | resizers + restoreFocus | product theme | PROD-RSZ-01..05 (funcional + fixed-size BLOCKED_AS_EXPECTED) | **PROVEN** | — |
| Direct editing | IN_V1 | LabelEditingModule (`E`, dblclick) | ativo | product theme | E2E-40 + PROD-KEY-02 | **PROVEN** | — |
| Replace/context pad | IN_V1 | ContextPad+ReplaceMenu governados | popup temático + governança | product theme | E2E-32/40 + GOV-PAD/RPL + PROD-KEY-04..06 | **PROVEN** | — |
| Mini-map | FUTURE | — | — | — | — | **NOT_APPLICABLE** | — |
| Align/Distribute | FUTURE | módulos carregados, providers desligados (DI `value:null` — WAVE F) | NOT_EXPOSED | vendor | GOV-15/16 + VX-01 | **PROVEN — DISABLE/FUTURE** (§6a) | — |

## 5. Round-trip, validation, layout, multi-diagram

- **Round-trip (artefato):** PROVEN byte-exact — `test_import_model_roundtrip` (import→read-back conteúdo idêntico + checksum), `X-Artifact-SHA256` na API, export E2E-01/02, extensão preservada E2E-10. **Per-construct compare: PROVEN (G4)** — suíte `e2e/specs/roundtrip-*.spec.ts` (16 testes E2E, workers=2) + `src/editor/roundtrip-adapter.test.ts` (14 testes unit-level) + `src/editor/extensionPreservation.test.ts` (7 testes): import real→read-back byte-exact→validate→open editor→`exportXml()` capturado via "Validar"→compare estrutural QName/ns-aware (`e2e/rt-compare.ts`)→reimport→read-back→idempotência. Corpus: `e2e/fixtures/roundtrip/` (13 fixtures, XSD-validadas). Normalizações permitidas no comparador: decl XML, prefixo, whitespace, ordem de attrs, omissão de XSD-default, `exporter*` provenance, `incoming`/`outgoing` derivados consistentes. Transforms vendor classificados e allow-listados por caso: drilldown plane de subprocess colapsado (EXTRA BPMNDiagram), `isMarkerVisible="true"` em gateway DI, DI gerado no path no-DI, BPMNLabel no shape renomeado. **EXTENSION_LOSS ALLOWLIST: 0** — ver §5 Extensions (G4-EXT-1 resolvido: repair + fail-closed gate).
- **Validation:** PROVEN — catálogo 47/47 implementado (SEC-7, XML-WF-2, REC-4, STRUCT-11, SEM-8, BPMNDI-9, PROD-2, EXT-4) com `test_validation_contract`/`test_validation_engine` sobre corpus FX-* (collab+lanes+black-box+messageFlow, boundary error, link, gateways, condition/default, preserve-only set, DI 7 casos, security 2). Regras semânticas por construct específico: PARTIAL (SEM-001..008 cobrem padrões selecionados).
- **Layout:** PROVEN para task/event/gateway/pool/lane/subProcess(expanded/collapsed)/messageFlow/group/label — 4 specs E2E (LGEO, HIER, GROUP, LABEL) + `diProposal.test.ts` (~30 tests). Exotic constructs (ad-hoc, transaction, boundary, data objects raros): code-supported em `elkGraph`/`diProposal`, sem E2E dedicado → PARTIAL.
- **Múltiplos BPMNDiagram:** PROVEN — E2E-18 (seletor, troca), FX_DI_004 backend (2 planes), adapter diagram switching, RT-DI-01 (secondary diagram não descartado no round-trip).
- **Extensions:** PROVEN — E2E-10 (mustUnderstand=false), E2E-11 (mustUnderstand=true → read-only gate), EXT-001..004 backend, RT-EXT-01..04 (G4: round-trip sem perda + fail-closed read-only + safe-edit isolation). **G4-EXT-1 CLOSED:** `bpmn:extension/@definition` (QName isReference dropado no parse) reparado por `extensionPreservation.ts` no adapter boundary — referência léxica `{id}` reemite o attr; attr namespaced same-URI em `extensionElements` (irremediável no serializer `moddle-xml` — `isLocalNs` stripa prefixo) é detectado por `hasUnpreservableExtensionContent` → `UNSUPPORTED_EXTENSION_SERIALIZATION` → read-only + save blocked, artefato byte-exact. Attrs cross-ns, elementos/nested/texto de extensão: preservados. Nada normalizado no comparador.
- **No-DI path:** PROVEN — RT-DI-02: fixture sem BPMN-DI → `hasBpmnDi` → elkjs → `injectDiIntoXml` transitório → render + export gera DI (transform esperado, classificado); adapter cru sem page = `EDITOR_CAPABILITY_FAILURE` ("no diagram to display") — evidência unit-level.
- **Unknown BPMN válido fora do profile:** PROVEN (G4) — corpus preserve-only RT-PRES-01..04: complex gateway, transaction (cancel), ad-hoc, eventSubProcess (`triggeredByEvent`), compensation activity/event, MI parallel+sequential, standard loop, conditional/multiple/parallel-multiple/compensate/cancel event defs em todas as posições, DataInput/DataOutput via ioSpecification — import→render→serialize→reimport→compare + safe-edit em elemento alheio preserva todo o restante (RT-PRES-02).

## 6. VENDOR-ONLY capabilities (não promover a produto)

~~Pós-G2A/G3, o vendor-only residual ativo sem governança de produto é apenas: align/distribute · space-tool · hand-tool · global-connect · keyboard-move (WAVE F — decisão de exposição pendente) · CandidateUsers/engine providers (TO_INVENTORY se carregados)~~ → **WAVE F CLOSED** — decisão de exposição fechada em §6a. ~~conditionExpression UI · defaultFlow UI · calledElement~~ → **CLOSED (WAVE E)** — implementados pelo provider de produto `BpmnCorePropsProvider` (BPMN core only, command stack, allowlist do editingProfile); evidência PROP-CORE-01 + PROP-FLOW-01..06.

### 6a. WAVE F — Vendor exposure decision matrix (CLOSED)

`PACKAGE PRESENT != MODULE LOADED != CAPABILITY ACTIVE != UI/KEYBOARD EXPOSED != PRODUCT SUPPORTED`. Mecanismo de governança: providers desligados via DI `value:null` (o construtor que auto-registra na surface nunca roda) + `editorActions.unregister` em `editorActions.init` (binding de teclado nunca é instalado — `isRegistered` é checado no register). Nenhum CSS-hide, nenhum DOM patch.

| Capability | Vendor package | Module loaded | UI antes | Shortcut | Mutação | Freeze | Decisão WAVE F |
|---|---|---|---|---|---|---|---|
| Align elements | diagram-js `align-elements` + bpmn-js providers | sim | context pad `align-elements` + popup `align-elements` (providers separados do ContextPadProvider principal — bypassavam o pad governado) | — | DI via modeling | FUTURE (§8) | **DISABLE / NOT_EXPOSED** — `alignElementsContextPadProvider`, `alignElementsMenuProvider`, `distributeElementsMenuProvider` = `value:null`; actions `alignElements`/`distributeElements` unregistered (GOV-15/16, VX-01) |
| Distribute elements | bpmn-js `distribute-elements` | sim | popup `align-elements` | — | DI | FUTURE (§8) | **DISABLE / NOT_EXPOSED** — idem |
| Space Tool | diagram-js `space-tool` | sim | palette `space-tool` | `S` | DI (make-space) | não-frozen → FUTURE | **DISABLE / NOT_EXPOSED** — fora da palette allowlist + action `spaceTool` unregistered (GOV-14/15, VX-01/02) |
| Hand Tool | diagram-js `hand-tool` | sim | palette `hand-tool` | `H` | **não** — viewport-only | Pan IN_V1 (§8/§35) | **KEEP — PAN implementation** (VX-04: viewport muda; canonical/DI/dirty intactos) |
| Global Connect | diagram-js `global-connect` | sim | palette `global-connect-tool` | `C` | conexões via `BpmnRules` (mesma autoridade do connect do context pad) | Connect IN_V1 (§8) | **KEEP — convenience alias of Connect** (VX-05: connect permitido persiste + undo; VX-06: rota proibida →start negada) |
| Keyboard Move — seleção | diagram-js `keyboard-move-selection` | sim | — | setas | **DI** via `moveElements` + dirty | fora da matriz §32 | **DISABLE / NOT_EXPOSED** — `keyboardMoveSelection: value:null` (listener nunca instalado; action `moveSelection` não registrada — GOV-15/17, VX-03) |
| Keyboard Move — canvas | diagram-js `navigation/keyboard-move` | sim | — | Ctrl+setas | **não** — viewport scroll | Pan IN_V1 | **KEEP — convenience alias of Pan** (viewport-only; `moveCanvas` ativo — GOV-15) |
| Lasso | diagram-js `lasso-tool` | sim | palette `lasso-tool` | `L` | não — seleção | Multi-select IN_V1 (§33) | **KEEP — IN_V1 implementation** (PROD-SEL-02) |
| Direct editing `E` | diagram-js `label-editing` | sim | dblclick/Enter frozen (§32) | `E` | label via command stack | Direct editing IN_V1 | **KEEP — vendor convenience alias** (PROD-KEY-02) |
| Replace `R` | bpmn-js `replace` | sim | context pad `replace` governado | `R` | abre popup `bpmn-replace` governado | Replace menu IN_V1 (§31) | **KEEP — vendor convenience alias** (PROD-KEY-03/04; entries fail-closed pelo profile) |
| Ctrl+D duplicate | diagram-js `copy-paste` | sim | — | `Ctrl+D` | criação via `copyPaste.duplicate` | Clipboard IN_V1 (§33) | **KEEP — convenience alias of clipboard** — governado por `copyPaste.canCopyElements`; preserve-only não duplica (PROD-CLIP-05) |

Engine providers: `BpmnPropertiesProviderModule` LOADED; Camunda/Zeebe **NOT LOADED** (`additionalModules` auditado). Engine-specific editable entries: **0** (VX-07 — deny-list candidateUsers/candidateGroups/versionTag/binding/version/retry/async/listeners/delegate + grupos `multiInstance`/`compensation`/`adHocCompletion` ausentes). `MultiInstanceLoopCharacteristics` = **BPMN core, PRESERVE_ONLY** — painel nega edição, XML preserva (RT-PRES-01 + VX-07/08); **NÃO é engine field**. `isExecutable` = **BPMN core, imported preserved, edit hidden** (GOV-13 + VX-07/08) — decisão G2A/C4 não reaberta.

Residuais WAVE F: unclassified exposed vendor features **0** · FUTURE exposed **0** · engine editable entries **0** · BPMN-core misclassified as engine **0**. Evidência: `e2e/specs/vendor-exposure.spec.ts` VX-01..08 (8/8, workers=2) + unit GOV-14..17 (`profileGovernance.test.ts`).

Promovidos a produto/governados (não mais vendor-only): copy/paste/cut + duplicate (canCopyElements governado) · multi-select/lasso/bulk ops · replace-menu/context-pad/palette entries (fail-closed pelo editingProfile) · typed task + event def + gateway creates (replace governado) · Ctrl+F searchPad · shortcuts · palette search semântica (projeção do profile). Preserve-only (complex gateway, ad-hoc/transaction/event-subprocess, MultiInstance) permanecem DENY — não são "expostos", são bloqueados pela governança.

## 7. Gaps

### IMPLEMENTATION GAPS (feature requerida ausente)

| GAP | Capability | Evidence | Missing | Owner | Severity | Wave |
|---|---|---|---|---|---|---|
| IG-1 | Palette search (IN_V1) | **CLOSED (G3-PAL-1)** — `PaletteSearch` + projeção `listSearchableCreateActions()` exportada por `editingProfile.ts` (mesma autoridade palette/context-pad/replace/clipboard — zero allowlist paralela). Roteamento semântico: DIRECT_PALETTE_CREATE + CREATE_THEN_REPLACE (replace governado via `replaceMenuProvider` no `create.end`); label/aliases = QName criado ("usuário"→UserTask, "gateway paralelo"→ParallelGateway); fail-closed: replace indisponível reverte o create; Lane/Boundary/preserve-only ausentes da busca global. `/` abre, ArrowUp/Down+Enter+Escape, role=combobox/aria-activedescendant. Evidência PROD-PAL-01..05 + PROD-PAL-SEM-01..08 | implementada | 03 | P2 | **G3 EXECUTED** |
| IG-2 | Profile governance (palette/context-pad/replace/panel) | ~~replace expõe ad-hoc/transaction/eventSubProcess/complex/MultiInstance~~ | provider de restrição | 03+02 | **P1** | G2/G3 → **CLOSED / VERIFIED AFTER CORRECTION PASS** — `editingProfile.ts`+`profileGovernanceModule.ts`+`ProfileGovernedPanelProvider`; fail-closed em todas as surfaces incl. properties entries (allowlist); bypasses corrigidos: `none-boundary-event` (não-criável), `append.compensation-activity` (compensation preserve-only); `isExecutable` classificado BPMN normativo, edição oculta por decisão de produto, valor preservado no round-trip. Evidência `profile-governance.spec.ts` |

### EVIDENCE GAPS (provavelmente funciona, sem prova de produto)

| GAP | Capability | State | Owner | Severity | Wave |
|---|---|---|---|---|---|
| EG-1 | Copy/cut/paste mesmo modelo | **CLOSED (G3)** — PROD-CLIP-01..07: single/multi/flows, ids novos no paste, refs válidas, undo/redo, autosave/RB/reload; governança `copyPaste.canCopyElements` → `isClipboardElementAllowed` recursivo; bypass preserve-only negado (`[Task, ComplexGateway]→[Task]`) | 06+03 | P2 | **G3 EXECUTED** |
| EG-2 | Multi-select/lasso/bulk ops | **CLOSED (G3)** — PROD-SEL-01..05: Shift+click, lasso (L+drag), Ctrl+A, deselect, bulk move (geom. relativa + DI + undo/redo + RB/reload), bulk delete (flows + refs limpas + undo/redo + RB); snap/grid grid 10 provado (PROD-SEL-06) | 06+03 | P2 | **G3 EXECUTED** |
| EG-3 | Typed tasks + callActivity create/edit | **CLOSED (G2B)** — CE-ACT-02/03: 7 typed tasks + CallActivity via Replace → QName + save/read-back/reload. calledElement = panel gap → EG-14/WAVE E | 03+02 | **P1** | G2 |
| EG-4 | Event definitions CE (create/swap/fields) | **CLOSED (G2B)** — CE-EVT-01..06: start/catch/throw/boundary/end defs + boundary attach + non-interrupting + timer type/value → XML + read-back + reload | 03+02 | **P1** | G2 |
| EG-5 | Parallel/Inclusive/EventBased gateway create | **CLOSED (G2B)** — CE-GW-02..05: replace + connect + QName + EventBased append governance (conditional deny) | 03+02 | **P1** | G2 |
| EG-6 | Pool/lane create/resize/membership | **CLOSED (G2B)** — CE-COL-01/02/05: participant+processRef+laneSet, insert above/below + divide (nested childLaneSet), rename + move task entre lanes | 03+04 | P1 | G2 |
| EG-7 | Message flow create entre pools | **CLOSED (G2B)** — CE-COL-03: 2 pools + MessageFlow tA→tB cross-process → `<bpmn:messageFlow>` read-back | 03 | P2 | G2 |
| EG-8 | Per-construct round-trip compare | **CLOSED (G4)** — 16 testes E2E `roundtrip-*.spec.ts` + 14 adapter-level `roundtrip-adapter.test.ts` + 7 `extensionPreservation.test.ts`: comparador estrutural QName/ns/DI-aware (`e2e/rt-compare.ts`), XSD-default normalization, allow-lists classificadas por transform vendor, extension-loss allowlist 0 (§5) | 02+06 | P1 | G4 |
| EG-9 | Resize funcional | **CLOSED (G3)** — PROD-RSZ-01..05: drag real em `.djs-resizer-*` muda DI (SubProcess expandido, Participant, Lane, Group) + undo/redo + save/RB/reload; task/event/gateway/data-object = `BLOCKED_AS_EXPECTED` por `BpmnRules.canResize`; fix de foco pós-drag (`drag.ended` → `canvas.restoreFocus`) habilita undo/redo via teclado | 03 | P3 | **G3 EXECUTED** |
| EG-10 | Search pad overlay (Ctrl+F funciona?) | **CLOSED (G3)** — PROD-SRCH-01..04: Ctrl+F abre, busca por nome e por id (substring, acentos), Enter seleciona, ArrowDown navega matches, Escape fecha, zero mutação | 03+06 | P2 | **G3 EXECUTED** |
| EG-11 | TextAnnotation/Association/DataAssociation create | **CLOSED (G2B)** — CE-ART-02/03: dataOutput+dataInputAssociation + textAnnotation editada + `<bpmn:association>` read-back/reload | 03 | P2 | G3→G2B |
| EG-12 | Preserve-only render/round-trip por construct | **CLOSED (G4)** — RT-PRES-01..04: render check (`djs-element` por id) + serialize→reimport→compare por construct (activities/events/data preserve-only) + safe-edit isolation | 02+06 | P1 | G4 |
| EG-13 | Shortcuts vendor (Del, R, E, S, L, H, C, zoom) | **CLOSED (G3)** — PROD-KEY-01..06: Ctrl+S flush, E direct editing, R replace menu, Backspace/Delete, context pad actions governadas, replace morph; matriz shortcut→efeito executada (§CURRENT-STATE 14a); foco restaurado pós-drag via `canvas.restoreFocus` | 03+06 | P2 | **G3 EXECUTED** |
| EG-14 | ~~panel fields IN_V1 ausentes: `calledElement`/`conditionExpression`/`defaultFlow`~~ → **CLOSED (WAVE E, BPMN-core)** — `BpmnCorePropsProvider` de produto cobre os 3 (command stack, contexto válido, exclusão mútua cond/default, sem ref pendurada em delete); evidência PROP-CORE-01 + PROP-FLOW-01..06 + PROP-DOC-01/02 + PROP-EVT-01..05 (14 testes E2E, workers=2). NOTA G2A: `isExecutable` **resolvido** — BPMN normativo (não engine-specific); edição intencionalmente não exposta por decisão de produto; preservação de import **PROVEN** (GOV-13). NOTA G2B: `calledElement`/`conditionExpression`/`defaultFlow` reclassificados VENDOR_ONLY→~~IMPLEMENTATION_GAP~~ **PROVEN (WAVE E)**. Residual decomposto: **ENGINE PROPERTY EXPOSURE** (MultiInstance/VersionTag/CandidateUsers/binding-version etc.) = ~~TO_INVENTORY / WAVE F~~ → **CLOSED (WAVE F, §6a)** — providers Camunda/Zeebe não carregados (inventário runtime), engine editable entries = 0 (VX-07); MultiInstance = BPMN core PRESERVE_ONLY (não engine field), `isExecutable` = BPMN core preservado/edit-hidden | 03+02 | P2 | WAVE E/F **EXECUTED** |

### TARGET GAPS (scope congelado não inventariado)

- TG-1: **CLOSED (G2B)** — todo o profile `CREATE_EDIT` exercitado por specs `e2e/specs/create-edit-{activities,gateways,events,collaboration,artifacts}.spec.ts` (24 testes, save→authoritative read-back→reload→verify QName/DI).
- TG-2: **CLOSED (G4)** — `RENDER_PRESERVE_ONLY` fixtures por construct criados e executados: `pres-activities.bpmn` (complex gw, transaction+cancel, adhoc, eventSubProcess `triggeredByEvent`, compensation, MI parallel/sequential, standard loop), `pres-events.bpmn` (conditional/multiple/parallel-multiple/compensate/cancel em start/catch/throw/end/boundary — canonical XSD forms: múltiplas eventDefinitions + `parallelMultiple="true"`), `pres-data.bpmn` (ioSpecification DataInput/DataOutput + inputSet/outputSet).
- TG-3: **CLOSED (G2B)** — CE-ACT-04 (collapsed SubProcess via replace) + CE-COL-04 (black-box pool via `replace-with-collapsed-pool` → participant sem processRef).

### G3 gaps (já identificados em G0) — verificação

- **Diagram search:** REFINADO (G0) — overlay vendor searchPad existe e está bindado (Ctrl+F) + traduzido PT-BR → **CLOSED (G3)** — evidência PROD-SRCH-01..04. → EG-10 closed.
- **Palette restriction:** ~~CONFIRMADO — nenhum provider de restrição~~ → **CLOSED (G2A)** — palette/context-pad/replace/panel governados pelo profile central (`editingProfile.ts`), fail-closed; preserve-only e MultiInstance não são criáveis nem replace targets. → IG-2 closed.
- **Copy/paste:** ~~CONFIRMADO vendor-only~~ → **CLOSED (G3)** — PROVEN com governança (`canCopyElements` recursivo nega preserve-only); evidência PROD-CLIP-01..07. → EG-1 closed.
- **Multi-select:** ~~CONFIRMADO vendor-only (exceto select-all)~~ → **CLOSED (G3)** — PROVEN: Shift+click, lasso, select-all, deselect, bulk move/delete; evidência PROD-SEL-01..06. → EG-2 closed.
- **Palette search:** ~~CONFIRMADO MISSING~~ → **CLOSED (G3 + G3-PAL-1)** — implementada como projeção semântica CREATE_EDIT do editingProfile (ver IG-1). → IG-1 closed.
- **Snap/grid:** ~~vendor ativo com config default → PARTIAL~~ → **CLOSED / PROVEN (G3)** — quantização no grid 10 medida em bounds/waypoints DI; evidência PROD-SEL-06.

## 8. V1 scope completeness score

- **Activities:** 11 PROVEN (Task + 7 typed + CallActivity + SubProcess expanded/collapsed — CE-ACT-01..04) · 3 preserve PROVEN no path render+preserve+round-trip (RT-PRES-01).
- **Events:** CREATE_EDIT profile PROVEN (start None/Msg/Timer/Signal · catch Msg/Timer/Signal/Link · throw None/Msg/Signal/Esc/Link · boundary Msg/Timer/Error/Signal/Esc + non-interrupting · end None/Msg/Error/Signal/Esc/Terminate — CE-EVT-01..06) · preserve-only defs PROVEN render+round-trip (RT-PRES-03 — TG-2 closed).
- **Gateways:** 5 PROVEN (Exclusive/Parallel/Inclusive/EventBased — CE-GW-01..05 · Complex preserve path — RT-PRES-01).
- **Connecting:** 3 PROVEN (SequenceFlow, MessageFlow, Association) + DataOutput/InputAssociation PROVEN (CE-ART-02).
- **Collaboration:** PROVEN create path — participant expanded+processRef+laneSet, lanes insert/divide/nested/rename/move, black-box pool, 2 pools + MessageFlow (CE-COL-01..05).
- **Data/Artifacts:** PROVEN — DataObject, DataStoreReference, TextAnnotation+texto, Group, Association, DataAssociation (CE-ART-01..04).
- **Properties breadth:** PROVEN (WAVE E) — name, id, processId/processRef, lane name, task type, subprocess expanded/collapsed, annotation text, timer type/value, documentation (task+process), calledElement, conditionExpression (set/clear/contexto válido), defaultFlow (exclusividade/clear/delete sem ref pendurada), messageRef+name, signalRef+name, errorRef+name+code, escalationRef+name+code, linkName — evidência `properties-{core,flows,events}.spec.ts` (14 testes E2E, workers=2) + CE-EVT-06.
- **Productivity:** PROVEN (G3) — clipboard governado, multi-select/lasso/select-all/deselect, bulk move/delete, Ctrl+F searchPad, palette search implementada (IG-1), resize funcional com fixed-size blocked, shortcuts executados, snap/grid grid 10. ~~Restam `TO_INVENTORY` não-semânticos: align/distribute/space/hand/global-connect (WAVE F).~~ → **CLOSED (WAVE F, §6a)** — align/distribute/space-tool desligados; hand/lasso/global-connect classificados e mantidos; keyboard-move-selection desligado; zero superfície vendor sem decisão.
- **Validation:** PROVEN (47/47 regras) · per-construct semantic PARTIAL.
- **Round-trip:** artifact-level PROVEN · per-construct PROVEN (G4 — semântica + BPMN-DI + extensions/unknown por construct; safe-edit isolation; G4-EXT-1 CLOSED — repair + fail-closed gate).
- **Lifecycle/API/Ownership/Autosave/Revisions:** PROVEN (fora do escopo deste inventário — ver CURRENT-STATE).

## 9. Candidate next waves (input para 00 — não é decisão)

- **WAVE A — Profile Governance:** provider de restrição palette/context-pad/replace/panel para o profile CE; bloquear/excluir preserve-only+engine constructs da criação. (IG-2, EG-14) — P1, owners 03+02. → **EXECUTED (G2A, PASS)** — parte creation/replacement fechada; exposição residual de engine fields no panel = TO_INVENTORY (EG-14 permanece para WAVE E).
- **WAVE B — CREATE_EDIT Evidence Closure:** → **EXECUTED (G2B, PASS)** — 24 testes E2E `create-edit-*.spec.ts` (workers=2, baseline determinístico) provam create→configure→connect→save→authoritative read-back→reload por construct CE. Construct paths = PROVEN; properties breadth = ~~PARTIAL~~ PROVEN (WAVE E). (EG-3..7, EG-11, TG-1, TG-3 fechados).
- **WAVE C — Round-trip & Preserve Evidence:** suíte export→reimport→compare por construct + corpus preserve-only. (EG-8, EG-12, TG-2) — P1, owners 02+06. → **EXECUTED (G4, PASS/CLOSED)** — 16 testes E2E `roundtrip-*.spec.ts` (workers=2, determinístico) + 14 adapter-level `roundtrip-adapter.test.ts` + 7 `extensionPreservation.test.ts`; comparador estrutural `e2e/rt-compare.ts`; corpus `e2e/fixtures/roundtrip/` XSD-validado (13 fixtures); transforms vendor classificados; G4-EXT-1 resolvido sem normalização de perda — `definition` reparado, attr same-ns fail-closed read-only.
- **WAVE D — Productivity:** → **EXECUTED (G3, PASS/CLOSED)** — 41 testes E2E `productivity-{clipboard,selection,search,resize,shortcuts}.spec.ts` (workers=2, determinístico); palette search = projeção semântica CREATE_EDIT do editingProfile (G3-PAL-1: semantic routing, misrouting=0); defeito de foco pós-drag corrigido no adapter (`drag.ended`/`mouseup` → `canvas.restoreFocus`); UNCONTROLLED OUT-OF-PROFILE CREATE PATHS via paste = 0. (EG-1,2,9,10,13, IG-1 fechados).
- **WAVE E — Properties Breadth:** → **EXECUTED (PASS)** — `BpmnCorePropsProvider` de produto (BPMN core only, sem providers Camunda/Zeebe) cobre `calledElement`/`conditionExpression`/`defaultFlow` via command stack com contexto válido e exclusão mútua; 14 testes E2E `properties-{core,flows,events}.spec.ts` (workers=2) provam UI→command→autosave→canonical XML→read-back→reload; event refs (message/signal/error/escalation/link) + documentation fechados; timer regressão verde (CE-EVT-06). Engine fields (MultiInstance/VersionTag/CandidateUsers/binding) = TO_INVENTORY → WAVE F. (EG-14 BPMN-core fechado).
- **WAVE F — Vendor Exposure Decision:** → **EXECUTED (PASS)** — decisão de exposição fechada em §6a: align/distribute DISABLE (FUTURE — providers DI `value:null` + actions unregistered), space-tool DISABLE (palette deny + action unregistered), keyboard-move-selection DISABLE (DI `value:null`), hand/lasso/global-connect KEEP (implementações/aliases de Pan, multi-select e Connect IN_V1), `E`/`R`/Ctrl+D/Ctrl+setas KEEP como convenience aliases governados; engine editable surface = 0; 8/8 E2E `vendor-exposure.spec.ts` + 4 unit GOV-14..17 + regressões G2A/G3/Wave E/G4-smoke verdes (workers=2).
- **G6 — Runtime Provenance & Deployment Acceptance:** → **EXECUTED (PASS)** — LOCAL INTEGRATION RUNTIME (não production acceptance). FINAL ACCEPTED RUNTIME: `bb447872ee12d50435fc64549c51cdb9bfc515eb` — hardening de provenance criado em `9ff9e9e14b`, equivalente rebaseado `511369e2f5` (blobs idênticos), rebuild/redeploy aceito em `bb447872ee`. Cadeia: worktree limpo → `docker compose build` com `BPMN_MODELER_BUILD_SHA` → imagens `infra-bpmn-modeler{,-api}` com OCI label `org.opencontainers.image.revision` → containers recriados → `GET /apps/bpmn-modeler/assets/build-info.json` e `GET /apps/bpmn-modeler-api/health` retornam o SHA servido; remoteEntry servido = arquivo na imagem (sha256 idêntico), chunks referenciados 200; migrations V001–V004 com checksum = fonte; ownership runtime 404 + isolation, create/edit/`If-Match` save/read-back/reload/export, conflict CONFLICT, archive read-only, revision smoke, validação 6-stage; fingerprints Wave E/F/extensões/paleta no runtime deployado (32/32 E2E). Deploy: lint/test/build AUTOMATED (CI), migrations startup AUTOMATED, image build/deploy MANUAL local, CI image push/deploy MISSING — `docker cp` aposentado como release contract (CURRENT-STATE §13d).

- **G5 — Transformômetro ↔ BPMN Modeler (explicit reference):** → **EXECUTED (PASS)** — LOCAL INTEGRATION RUNTIME. Vínculo owned pelo Transformômetro (`transformometro.processo_bpmn_references`, V052): `(bpmn_model_id, bpmn_revision_number)` + audit, granularidade `processo_id`, **zero** XML/DI/checksum/display-name persistido, zero FK cross-schema, zero SQL em `bpmn_modeler.*`, zero proxy genérico, zero service token. Identidade delegada (bearer forward) → foreign model 404 preservado; write fail-closed (Modeler down → 503, sem dangling ref); read degradado (`resolved|unavailable|inaccessible_or_missing`); revisão explícita sem auto-follow-latest (R1 estável após R2 existir; badge read-only); unlink TM-only. API: `GET/PUT/DELETE …/bpmn-reference` + candidates/revisions picker. UI: card "Modelo BPMN" em Mapeamento→Fluxo com deep links product-owned. Audit old/new reference em `audit_logs`. Evidência (G5-ACC-1 closure): 27/27 backend (`test_process_bpmn_reference` + `test_path_alias_middleware`) + 6/6 structural + vitest TM + 138 regressão BPMN + **runtime harness 20/20** (`scripts/g5_bpmn_reference_runtime_acceptance.sh` — `previous` validado via audit DB, contrato real) + **cross-app browser E2E 8/8** (`transformometro-bpmn-reference.spec.ts`, portal+MFEs+APIs+Keycloak reais, zero mock) cobrindo empty→link, view revision read-only, open-in-Modeler sem mutação, no auto-follow, update explícito+audit, model switch+audit, unlink, cross-owner degradado. AuthZ precision: read/write do vínculo dividem `transformometro.access` — separação dedicada NÃO existe (follow-up). Fix de runtime descoberto pelo E2E: skip-prefix `/bpmn-reference` no `path_alias_middleware` (`/revisions`→`/revisoes` quebrava candidates/revisions). Modeler: **zero mudança de contrato**. Contrato: ADR-005 + CURRENT-STATE §13e.

Ordem sugerida: A → B → C → D/E → F. **FINAL PRIORITY OWNER: 00 — Arquitetura & Coordenação.**

## 10. Notas de método

- Evidência hierarquizada: E2E real > integration > unit > code > vendor > doc target.
- Nenhum teste foi executado neste gate (inventário estático); comandos de busca listados na seção residual do relatório.
- `bpmn-js@18.30.1`, `bpmn-js-properties-panel@5.65.1`, `elkjs@0.12.0` — pins auditados.
- Nenhuma capability foi promovida por presença vendor; nenhum target foi rebaixado por ausência de implementação.
