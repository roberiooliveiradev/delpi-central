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
  // grupos produto (BpmnCorePropsProvider, Wave E) — BPMN core normativo
  "callActivity",
  "flow",
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
  // BPMN core entries do produto (BpmnCorePropsProvider, Wave E):
  // calledElement (bpmn:CallActivity), conditionExpression/default
  // (bpmn:SequenceFlow — contexts Activity/Exclusive/InclusiveGateway)
  "calledElement",
  "conditionExpression",
  "defaultFlow",
]);

// ---------------------------------------------------------------------------
// Clipboard (copy/cut/paste/duplicate) — G3
// ---------------------------------------------------------------------------

/**
 * Projeção type-level do profile §6 para o path de criação via clipboard.
 * As allowlists acima governam entry ids das surfaces vendor; paste/duplicate
 * criam elementos por outra via (modeling.createElements) — aqui o critério
 * é o BPMN type + markers do businessObject, mesma decisão CREATE_EDIT.
 * Fail-closed: tipo/marker não classificado → DENY.
 *
 * `RENDER_PRESERVE_ONLY` pode ser importado/selecionado/visualizado —
 * nunca duplicado (PRESERVE_ONLY != CREATE).
 */

const CREATABLE_BPMN_TYPES: ReadonlySet<string> = new Set([
  // activities (§6.1) — SubProcess cobre expanded+collapsed; markers
  // preserve-only (triggeredByEvent/isForCompensation/loopCharacteristics)
  // são negados abaixo
  "bpmn:Task",
  "bpmn:UserTask",
  "bpmn:ServiceTask",
  "bpmn:SendTask",
  "bpmn:ReceiveTask",
  "bpmn:ManualTask",
  "bpmn:BusinessRuleTask",
  "bpmn:ScriptTask",
  "bpmn:CallActivity",
  "bpmn:SubProcess",
  // gateways (§6.3) — ComplexGateway é preserve-only (ausente = deny)
  "bpmn:ExclusiveGateway",
  "bpmn:ParallelGateway",
  "bpmn:InclusiveGateway",
  "bpmn:EventBasedGateway",
  // events — eventDefinitions avaliadas por posição na matriz abaixo
  "bpmn:StartEvent",
  "bpmn:IntermediateCatchEvent",
  "bpmn:IntermediateThrowEvent",
  "bpmn:BoundaryEvent",
  "bpmn:EndEvent",
  // data (§6.6)
  "bpmn:DataObjectReference",
  "bpmn:DataStoreReference",
  // artifacts
  "bpmn:Group",
  "bpmn:TextAnnotation",
  // collaboration
  "bpmn:Participant",
  "bpmn:Lane",
  // connections
  "bpmn:SequenceFlow",
  "bpmn:MessageFlow",
  "bpmn:Association",
  "bpmn:DataInputAssociation",
  "bpmn:DataOutputAssociation",
]);

/** EventDefinitions permitidas por posição (espelha §6.2 — mesma autoridade). */
const EVENT_DEFS_BY_POSITION: Record<string, ReadonlySet<string>> = {
  // start: None/Message/Timer/Signal, interrupting only
  "bpmn:StartEvent": new Set([
    "bpmn:MessageEventDefinition",
    "bpmn:TimerEventDefinition",
    "bpmn:SignalEventDefinition",
  ]),
  // intermediate catch: None/Message/Timer/Signal/Link
  "bpmn:IntermediateCatchEvent": new Set([
    "bpmn:MessageEventDefinition",
    "bpmn:TimerEventDefinition",
    "bpmn:SignalEventDefinition",
    "bpmn:LinkEventDefinition",
  ]),
  // intermediate throw: None/Message/Signal/Escalation/Link
  "bpmn:IntermediateThrowEvent": new Set([
    "bpmn:MessageEventDefinition",
    "bpmn:SignalEventDefinition",
    "bpmn:EscalationEventDefinition",
    "bpmn:LinkEventDefinition",
  ]),
  // boundary: Message/Timer/Error/Signal/Escalation (interrupting + não)
  "bpmn:BoundaryEvent": new Set([
    "bpmn:MessageEventDefinition",
    "bpmn:TimerEventDefinition",
    "bpmn:ErrorEventDefinition",
    "bpmn:SignalEventDefinition",
    "bpmn:EscalationEventDefinition",
  ]),
  // end: None/Message/Error/Signal/Escalation/Terminate
  "bpmn:EndEvent": new Set([
    "bpmn:MessageEventDefinition",
    "bpmn:ErrorEventDefinition",
    "bpmn:SignalEventDefinition",
    "bpmn:EscalationEventDefinition",
    "bpmn:TerminateEventDefinition",
  ]),
};

export type ClipboardBusinessObject = {
  $type?: string;
  eventDefinitions?: Array<{ $type?: string }>;
  loopCharacteristics?: { $type?: string } | null;
  isForCompensation?: boolean;
  triggeredByEvent?: boolean;
  isInterrupting?: boolean;
  parallelMultiple?: boolean;
};

export type ClipboardElement = {
  type?: string;
  businessObject?: ClipboardBusinessObject | null;
  // createTree do vendor inclui descendants/attachers no clipboard — se o
  // filtro só avaliar a seleção, preserve-only filho vira bypass via parent
  // (ex.: subprocess contendo EventSubProcess, task com boundary cancel).
  children?: ClipboardElement[] | null;
  attachers?: ClipboardElement[] | null;
};

/**
 * true se o elemento pode ser duplicado/colado sem violar CREATE GOVERNED.
 * Fail-closed: businessObject ausente, tipo não listado ou marker
 * preserve-only → DENY. Labels seguem o owner (`type: "label"`).
 * Descendants e attachers são avaliados recursivamente — um parent
 * CREATE_EDIT que contenha preserve-only nega o conjunto inteiro (o vendor
 * não filtra subárvore; o único comportamento seguro é negar o topo).
 */
export function isClipboardElementAllowed(element: ClipboardElement): boolean {
  // labels não carregam businessObject próprio — acompanham o owner,
  // que já passou pelo filtro quando foi avaliado
  if (element.type === "label") return true;
  const bo = element.businessObject;
  if (!bo?.$type || !CREATABLE_BPMN_TYPES.has(bo.$type)) return false;

  const related = [
    ...(element.children ?? []),
    ...(element.attachers ?? []),
  ];
  if (!related.every(isClipboardElementAllowed)) return false;

  const defs = bo.eventDefinitions ?? [];
  if (bo.$type in EVENT_DEFS_BY_POSITION) {
    const allowed = EVENT_DEFS_BY_POSITION[bo.$type];
    // >1 eventDefinition = evento múltiplo/paralelo → preserve-only
    if (defs.length > 1) return false;
    if (bo.parallelMultiple) return false;
    if (defs.some((d) => !d.$type || !allowed.has(d.$type))) return false;
    // boundary exige definição (none-boundary é DENY no profile)
    if (bo.$type === "bpmn:BoundaryEvent" && defs.length === 0) return false;
    // start não-interrupting é preserve-only
    if (bo.$type === "bpmn:StartEvent" && bo.isInterrupting === false) {
      return false;
    }
    return true;
  }

  // activities/subprocess: markers preserve-only negam
  if (bo.loopCharacteristics) return false; // MI/standard loop
  if (bo.isForCompensation) return false; // compensation activity
  if (bo.$type === "bpmn:SubProcess" && bo.triggeredByEvent) return false; // EventSubProcess

  return true;
}

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

// ---------------------------------------------------------------------------
// Palette search — projeção semântica CREATE_EDIT (G3-PAL-1)
//
// A busca promete ao usuário "o elemento BPMN que você quer criar": label +
// aliases devem resultar no QName correspondente. Constructs tipados sem
// entry direta na palette usam CREATE_THEN_REPLACE — create genérico seguido
// do replace governado já existente (mesmo popup 'bpmn-replace' filtrado por
// isReplaceEntryAllowed, via command stack).
//
// Autoridade: esta tabela é uma PROJEÇÃO, não uma segunda allowlist — cada
// ação é emitida somente se a palette entry E a replace entry passarem pelos
// predicados canônicos acima (fail-closed).
// ---------------------------------------------------------------------------

export type SearchCreateStrategy =
  | "DIRECT_PALETTE_CREATE"
  | "CREATE_THEN_REPLACE";

export interface SearchableCreateAction {
  /** id estável da ação de busca */
  id: string;
  /** label PT-BR exibido no resultado */
  label: string;
  /** termos de busca equivalentes ao label (mesmo significado) */
  aliases: string[];
  strategy: SearchCreateStrategy;
  paletteEntryId: string;
  /** chave completa do popup 'bpmn-replace' (ex.: 'replace-with-user-task') */
  replaceEntryId?: string;
}

const SEARCHABLE_CREATE_ACTIONS: readonly SearchableCreateAction[] = [
  // ---- activities ---------------------------------------------------------
  {
    id: "task",
    label: "Tarefa",
    aliases: ["task", "atividade", "tarefa"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.task",
  },
  {
    id: "user-task",
    label: "Tarefa de Usuário",
    aliases: ["usuario", "usuário", "user task", "tarefa de usuario"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-user-task",
  },
  {
    id: "service-task",
    label: "Tarefa de Serviço",
    aliases: ["servico", "serviço", "service task", "tarefa de servico"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-service-task",
  },
  {
    id: "manual-task",
    label: "Tarefa Manual",
    aliases: ["manual", "tarefa manual"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-manual-task",
  },
  {
    id: "rule-task",
    label: "Tarefa de Regra de Negócio",
    aliases: ["regra", "regra de negocio", "business rule"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-rule-task",
  },
  {
    id: "script-task",
    label: "Tarefa de Script",
    aliases: ["script", "tarefa de script"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-script-task",
  },
  {
    id: "send-task",
    label: "Tarefa de Envio",
    aliases: ["envio", "send task", "tarefa de envio"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-send-task",
  },
  {
    id: "receive-task",
    label: "Tarefa de Recebimento",
    aliases: ["recebimento", "receive task", "tarefa de recebimento"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-receive-task",
  },
  {
    id: "call-activity",
    label: "Atividade de Chamada",
    aliases: ["chamada", "call activity", "callactivity"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.task",
    replaceEntryId: "replace-with-call-activity",
  },
  {
    id: "subprocess-expanded",
    label: "Subprocesso",
    aliases: ["subprocesso", "sub processo", "sub-processo"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.subprocess-expanded",
  },
  {
    id: "subprocess-collapsed",
    label: "Subprocesso Colapsado",
    aliases: ["subprocesso colapsado", "collapsed subprocess"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.subprocess-expanded",
    replaceEntryId: "replace-with-collapsed-subprocess",
  },
  // ---- gateways -----------------------------------------------------------
  {
    id: "exclusive-gateway",
    label: "Gateway Exclusivo",
    aliases: ["exclusivo", "xor", "decisao", "decisão"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.exclusive-gateway",
  },
  {
    id: "parallel-gateway",
    label: "Gateway Paralelo",
    aliases: ["paralelo", "parallel", "gateway paralelo"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.exclusive-gateway",
    replaceEntryId: "replace-with-parallel-gateway",
  },
  {
    id: "inclusive-gateway",
    label: "Gateway Inclusivo",
    aliases: ["inclusivo", "inclusive", "gateway inclusivo"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.exclusive-gateway",
    replaceEntryId: "replace-with-inclusive-gateway",
  },
  {
    id: "event-based-gateway",
    label: "Gateway Baseado em Eventos",
    aliases: ["baseado em eventos", "event based", "gateway de eventos"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.exclusive-gateway",
    replaceEntryId: "replace-with-event-based-gateway",
  },
  // ---- events: start ------------------------------------------------------
  {
    id: "start-event",
    label: "Evento de Início",
    aliases: ["inicio", "início", "start event", "evento de inicio"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.start-event",
  },
  {
    id: "message-start",
    label: "Evento de Início por Mensagem",
    aliases: ["inicio por mensagem", "message start"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.start-event",
    replaceEntryId: "replace-with-message-start",
  },
  {
    id: "timer-start",
    label: "Evento de Início por Timer",
    aliases: ["inicio por timer", "timer start", "inicio temporizado"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.start-event",
    replaceEntryId: "replace-with-timer-start",
  },
  {
    id: "signal-start",
    label: "Evento de Início por Sinal",
    aliases: ["inicio por sinal", "signal start"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.start-event",
    replaceEntryId: "replace-with-signal-start",
  },
  // ---- events: intermediate (palette cria catch; throw via replace) -------
  {
    id: "intermediate-event",
    label: "Evento Intermediário",
    aliases: ["intermediario", "intermediário", "intermediate event"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.intermediate-event",
  },
  {
    id: "message-intermediate-catch",
    label: "Evento Intermediário de Captura por Mensagem",
    aliases: ["intermediario mensagem", "message catch"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.intermediate-event",
    replaceEntryId: "replace-with-message-intermediate-catch",
  },
  {
    id: "timer-intermediate-catch",
    label: "Evento Intermediário de Captura por Timer",
    aliases: ["intermediario timer", "timer catch", "timer intermediario"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.intermediate-event",
    replaceEntryId: "replace-with-timer-intermediate-catch",
  },
  {
    id: "signal-intermediate-catch",
    label: "Evento Intermediário de Captura por Sinal",
    aliases: ["intermediario sinal", "signal catch"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.intermediate-event",
    replaceEntryId: "replace-with-signal-intermediate-catch",
  },
  {
    id: "message-intermediate-throw",
    label: "Evento Intermediário de Lançamento por Mensagem",
    aliases: ["lancamento mensagem", "lançamento mensagem", "message throw"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.intermediate-event",
    replaceEntryId: "replace-with-message-intermediate-throw",
  },
  {
    id: "signal-intermediate-throw",
    label: "Evento Intermediário de Lançamento por Sinal",
    aliases: ["lancamento sinal", "lançamento sinal", "signal throw"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.intermediate-event",
    replaceEntryId: "replace-with-signal-intermediate-throw",
  },
  {
    id: "escalation-intermediate-throw",
    label: "Evento Intermediário de Lançamento por Escalada",
    aliases: ["lancamento escalada", "lançamento escalada", "escalation throw"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.intermediate-event",
    replaceEntryId: "replace-with-escalation-intermediate-throw",
  },
  // ---- events: end --------------------------------------------------------
  {
    id: "end-event",
    label: "Evento de Fim",
    aliases: ["fim", "end event", "termino", "término", "evento de fim"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.end-event",
  },
  {
    id: "message-end",
    label: "Evento de Fim por Mensagem",
    aliases: ["fim por mensagem", "message end"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.end-event",
    replaceEntryId: "replace-with-message-end",
  },
  {
    id: "error-end",
    label: "Evento de Fim por Erro",
    aliases: ["fim por erro", "error end"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.end-event",
    replaceEntryId: "replace-with-error-end",
  },
  {
    id: "signal-end",
    label: "Evento de Fim por Sinal",
    aliases: ["fim por sinal", "signal end"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.end-event",
    replaceEntryId: "replace-with-signal-end",
  },
  {
    id: "escalation-end",
    label: "Evento de Fim por Escalada",
    aliases: ["fim por escalada", "escalation end"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.end-event",
    replaceEntryId: "replace-with-escalation-end",
  },
  {
    id: "terminate-end",
    label: "Evento de Fim de Término",
    aliases: ["fim de termino", "fim de término", "terminate end"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.end-event",
    replaceEntryId: "replace-with-terminate-end",
  },
  // ---- data / artifacts ---------------------------------------------------
  {
    id: "data-object",
    label: "Objeto de Dados",
    aliases: ["objeto de dados", "data object", "dado"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.data-object",
  },
  {
    id: "data-store",
    label: "Repositório de Dados",
    aliases: ["repositorio", "repositório", "data store"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.data-store",
  },
  {
    id: "group",
    label: "Grupo",
    aliases: ["grupo", "agrupamento"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.group",
  },
  // ---- collaboration ------------------------------------------------------
  {
    id: "participant-expanded",
    label: "Pool / Participante",
    aliases: ["pool", "participante", "participant"],
    strategy: "DIRECT_PALETTE_CREATE",
    paletteEntryId: "create.participant-expanded",
  },
  {
    id: "participant-collapsed",
    label: "Pool (caixa-preta)",
    aliases: ["pool caixa preta", "black box pool", "pool vazio"],
    strategy: "CREATE_THEN_REPLACE",
    paletteEntryId: "create.participant-expanded",
    replaceEntryId: "replace-with-collapsed-pool",
  },
];

/**
 * Constructs contextuais intencionalmente AUSENTES da busca global:
 * - Lane: criada apenas via context-pad do Participant (lane-divide-*) —
 *   mapear "raia/lane" → Participant mentiria a semântica.
 * - BoundaryEvent: exige Activity de attachment — não representável numa
 *   busca global sem contexto de seleção.
 * - TextAnnotation/Association: create apenas via context-pad.
 * - Preserve-only (ComplexGateway, Transaction, AdHoc, MultiInstance,
 *   Compensation...): sem entries CREATE_EDIT → nunca listados.
 */
export function listSearchableCreateActions(): SearchableCreateAction[] {
  return SEARCHABLE_CREATE_ACTIONS.filter(
    (a) =>
      isPaletteEntryAllowed(a.paletteEntryId) &&
      (!a.replaceEntryId || isReplaceEntryAllowed(a.replaceEntryId)),
  ).map((a) => ({ ...a }));
}
