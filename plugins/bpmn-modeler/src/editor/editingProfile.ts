/**
 * BPMN Editing Profile — autoridade central de capabilities de edição da V1.
 *
 * Fonte normativa: docs/12-roadmap-e-evolucao/bpmn-modeler/V1-SCOPE-FREEZE.md §6–8
 * Inventário de superfície: V1-CAPABILITY-EVIDENCE-INVENTORY.md (G1).
 *
 * Separação arquitetural preservada:
 *   IMPORT/RENDER/PRESERVE broad  !=  CREATE/EDIT governed
 * Constructs `RENDER_PRESERVE_ONLY` continuam importáveis, renderizáveis e
 * preservados — apenas não aparecem como opção de criação/replace/propriedade.
 *
 * REGRA FAIL-CLOSED: qualquer id não classificado explicitamente aqui NÃO é
 * exposto para create/replace. Vendor upgrade que adicione opções novas cai
 * em deny por default — o profile nunca amplia o produto silenciosamente.
 *
 * Os ids correspondem às chaves do catálogo vendor (PopupEntries/actionName/
 * context-pad/palette/properties groups) conforme bpmn-js@18.30.1.
 */

// ---------------------------------------------------------------------------
// Replace menu — entry ids (PopupEntries), position-aware pelo próprio id
// ('timer-start' vs 'timer-boundary' vs 'timer-intermediate-catch').
// ---------------------------------------------------------------------------

const ALLOWED_REPLACE_ENTRY_IDS: ReadonlySet<string> = new Set([
  // activities (§6.1)
  "task",
  "user-task",
  "service-task",
  "send-task",
  "receive-task",
  "manual-task",
  "rule-task",
  "script-task",
  "call-activity",
  "collapsed-subprocess",
  "expanded-subprocess",
  // gateways (§6.3)
  "exclusive-gateway",
  "parallel-gateway",
  "inclusive-gateway",
  "event-based-gateway",
  // data (§6.6)
  "data-object-reference",
  "data-store-reference",
  // pools/participants (§6.5) — expanded e collapsed (black-box)
  "expanded-pool",
  "collapsed-pool",
  // none events — posição top-level/catch/throw/end somente;
  // "none-boundary-event" é DENY: boundary CREATE_EDIT exige definição
  // (Message/Timer/Error/Signal/Escalation) — boundary sem definição não é
  // criável nem replace target (import permanece preserve).
  "none-start-event",
  "none-intermediate-throwing",
  "none-end-event",
  // start event definitions (§6.2): None/Message/Timer/Signal
  "message-start",
  "timer-start",
  "signal-start",
  // intermediate catch: Message/Timer/Signal/Link
  "message-intermediate-catch",
  "timer-intermediate-catch",
  "signal-intermediate-catch",
  "link-intermediate-catch",
  // intermediate throw: None/Message/Signal/Escalation/Link
  "message-intermediate-throw",
  "signal-intermediate-throw",
  "escalation-intermediate-throw",
  "link-intermediate-throw",
  // boundary (interrupting + non-interrupting): Message/Timer/Error/Signal/Escalation
  "message-boundary",
  "timer-boundary",
  "error-boundary",
  "signal-boundary",
  "escalation-boundary",
  "non-interrupting-message-boundary",
  "non-interrupting-timer-boundary",
  "non-interrupting-signal-boundary",
  "non-interrupting-escalation-boundary",
  // end: None/Message/Error/Signal/Escalation/Terminate
  "message-end",
  "error-end",
  "signal-end",
  "escalation-end",
  "terminate-end",
]);

/**
 * DENIED por decisão de profile (documentado; fail-closed cobre também
 * qualquer id futuro não listado):
 *   RENDER_PRESERVE_ONLY activities: transaction, event-subprocess,
 *     collapsed-ad-hoc-subprocess, expanded-ad-hoc-subprocess
 *   RENDER_PRESERVE_ONLY gateway: complex-gateway
 *   preserve-only start defs: conditional-start, error-start,
 *     escalation-start, compensation-start, non-interrupting-*-start
 *     (event-subprocess start é preserve-only por posição)
 *   preserve-only catch defs: conditional-intermediate-catch
 *     (multiple/parallel-multiple não existem como entries vendor)
 *   preserve-only throw defs: compensation-intermediate-throw
 *   preserve-only boundary defs: conditional-boundary, cancel-boundary,
 *     compensation-boundary, non-interrupting-conditional-boundary
 *   preserve-only end defs: cancel-end, compensation-end
 */

// sequence-flow morphs: default/conditional flow são IN_V1 (§8.1)
const ALLOWED_SEQUENCE_FLOW_ACTIONS: ReadonlySet<string> = new Set([
  "replace-with-sequence-flow",
  "replace-with-default-flow",
  "replace-with-conditional-flow",
]);

// Replace popup header toggles (property morphs, não construct entries)
const ALLOWED_REPLACE_HEADER_IDS: ReadonlySet<string> = new Set([
  "toggle-non-interrupting", // boundary/start interrupting flag — property edit IN_V1
  "toggle-is-collection", // DataObject.isCollection — propriedade normativa
]);

/**
 * DENIED headers: toggle-parallel-mi, toggle-sequential-mi
 *   (MultiInstanceLoopCharacteristics — fora do profile V1),
 * toggle-loop (StandardLoopCharacteristics — não classificado → fail-closed),
 * toggle-participant-multiplicity (ParticipantMultiplicity — idem).
 */

// ---------------------------------------------------------------------------
// Palette — chaves getPaletteEntries() do vendor
// ---------------------------------------------------------------------------

const ALLOWED_PALETTE_ENTRY_IDS: ReadonlySet<string> = new Set([
  // tools não-semânticas (decisão: manter — inventory G1 §50)
  "lasso-tool",
  "hand-tool",
  "space-tool",
  "global-connect-tool",
  "tool-separator",
  // create entries — todos dentro do profile atual
  "create.start-event",
  "create.intermediate-event",
  "create.end-event",
  "create.exclusive-gateway",
  "create.task",
  "create.subprocess-expanded",
  "create.data-object",
  "create.data-store",
  "create.participant-expanded",
  "create.group",
]);

// ---------------------------------------------------------------------------
// Context pad — chaves getContextPadEntries() do vendor
// ---------------------------------------------------------------------------

const ALLOWED_CONTEXT_PAD_ENTRY_IDS: ReadonlySet<string> = new Set([
  "append.end-event",
  "append.gateway", // ExclusiveGateway — append default
  "append.append-task",
  "append.intermediate-event",
  "append.receive-task",
  "append.message-intermediate-event",
  "append.timer-intermediate-event",
  "append.signal-intermediate-event",
  "append.text-annotation",
  "connect",
  "delete",
  "replace",
  "lane-insert-above",
  "lane-insert-below",
  "lane-divide-two",
  "lane-divide-three",
]);

/**
 * DENIED:
 *   "append.condition-intermediate-event" (EventBasedGateway append criaria
 *     ConditionalEventDefinition — preserve-only);
 *   "append.compensation-activity" (emitido em BoundaryEvent com
 *     CompensateEventDefinition — compensation modeling é preserve-only;
 *     o entry converteria import preserve-only em caminho de criação
 *     semântica nova, bypass do CREATE GOVERNED).
 * Qualquer append futuro desconhecido cai em deny.
 */

// ---------------------------------------------------------------------------
// Properties panel — group/entry ids do BpmnPropertiesProvider vendor
// ---------------------------------------------------------------------------

const ALLOWED_PROPERTIES_GROUP_IDS: ReadonlySet<string> = new Set([
  "general",
  "advanced", // grupo produto (AdvancedIdProvider)
  "documentation",
  "error",
  "link",
  "message",
  "signal",
  "escalation",
  "timer",
]);

/**
 * DENIED groups: "multiInstance" (MultiInstanceLoopCharacteristics — fora do
 * profile), "adHocCompletion" (completionCondition de AdHocSubProcess —
 * construct preserve-only), "compensation" (activityRef/isForCompensation —
 * mecânica de compensação fora do profile).
 */

/**
 * ALLOWED properties entries — inventário real da surface vendor
 * (bpmn-js-properties-panel@5.65.1, provider `bpmn` — os providers Zeebe/
 * CamundaPlatform NÃO são carregados pelo adapter). Fail-closed: entry não
 * listada → DENY.
 *
 * `isExecutable` é atributo BPMN NORMATIVO (BPMN 2.0 `process.isExecutable`),
 * não campo vendor/engine-specific. Decisão de produto (G2A/C4): a UI de
 * edição não expõe o entry porque o Meu Modelador modela BPMN mas não
 * executa/deploya workflows — o blank artifact fixa `isExecutable="false"`
 * e permitir marcá-lo implicaria semântica de execução que o produto não
 * possui. O valor importado é PRESERVADO no round-trip (moddle round-trip
 * do atributo); só a edição via painel é ocultada.
 */
const ALLOWED_PROPERTIES_ENTRY_IDS: ReadonlySet<string> = new Set([
  // general + advanced (AdvancedIdProvider move id/processId p/ "advanced")
  "name",
  "id",
  "processId",
  "processName",
  // documentation
  "documentation",
  "processDocumentation",
  // event definition refs/fields aprovados (grupos error/link/message/
  // signal/escalation/timer)
  "errorRef",
  "errorName",
  "errorCode",
  "linkName",
  "messageRef",
  "messageName",
  "signalRef",
  "signalName",
  "escalationRef",
  "escalationName",
  "escalationCode",
  "timerEventDefinitionType",
  "timerEventDefinitionValue",
]);

// ---------------------------------------------------------------------------
// Predicates (fail-closed)
// ---------------------------------------------------------------------------

const REPLACE_PREFIX = "replace-with-";

/** Popup menu 'bpmn-replace' body entries — create/replace targets. */
export function isReplaceEntryAllowed(actionKey: string): boolean {
  if (ALLOWED_SEQUENCE_FLOW_ACTIONS.has(actionKey)) return true;
  if (!actionKey.startsWith(REPLACE_PREFIX)) return false;
  return ALLOWED_REPLACE_ENTRY_IDS.has(actionKey.slice(REPLACE_PREFIX.length));
}

/** Popup menu 'bpmn-replace' header entries (property toggles). */
export function isReplaceHeaderAllowed(entryKey: string): boolean {
  return ALLOWED_REPLACE_HEADER_IDS.has(entryKey);
}

export function isPaletteEntryAllowed(entryKey: string): boolean {
  return ALLOWED_PALETTE_ENTRY_IDS.has(entryKey);
}

export function isContextPadEntryAllowed(entryKey: string): boolean {
  return ALLOWED_CONTEXT_PAD_ENTRY_IDS.has(entryKey);
}

export function isPropertiesGroupAllowed(groupId: string): boolean {
  return ALLOWED_PROPERTIES_GROUP_IDS.has(groupId);
}

export function isPropertiesEntryAllowed(entryId: string): boolean {
  return ALLOWED_PROPERTIES_ENTRY_IDS.has(entryId);
}
