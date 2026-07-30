export type BpmnPaletteCategoryId =
  | "events_start"
  | "events_intermediate"
  | "events_end"
  | "gateways"
  | "tasks"
  | "activities"
  | "artifacts"
  | "boundary";

export type BpmnShapeFamily =
  | "event_start"
  | "event_end"
  | "event_intermediate_catch"
  | "event_intermediate_throw"
  | "gateway"
  | "task"
  | "activity_subprocess"
  | "activity_call"
  | "activity_ad_hoc"
  | "activity_transaction"
  | "activity_event_subprocess"
  | "artifact_document"
  | "artifact_data_store"
  | "artifact_data_object"
  | "artifact_comment"
  | "artifact_group"
  | "boundary";

export type BpmnMarker =
  | "none"
  | "message"
  | "timer"
  | "signal"
  | "conditional"
  | "error"
  | "escalation"
  | "compensation"
  | "cancel"
  | "link"
  | "multiple"
  | "parallel"
  | "terminate"
  | "exclusive"
  | "parallel_gateway"
  | "inclusive"
  | "complex"
  | "event_based"
  | "user"
  | "service"
  | "manual"
  | "script"
  | "business_rule"
  | "send"
  | "receive"
  | "call"
  | "ad_hoc"
  | "transaction"
  | "event_sub";

export type FlowchartNodeType = keyof typeof BPMN_NODE_DEFINITIONS;

export type BpmnNodeDefinition = {
  label: string;
  category: BpmnPaletteCategoryId;
  shape: BpmnShapeFamily;
  marker: BpmnMarker;
  bpmnTag: string;
  bpmnEventDefinition?: string;
  participatesInFlow: boolean;
  hint: string;
  manualTask?: boolean;
};

export const BPMN_PALETTE_CATEGORIES: Array<{ id: BpmnPaletteCategoryId; label: string }> = [
  { id: "events_start", label: "Eventos — início" },
  { id: "events_intermediate", label: "Eventos — intermediários" },
  { id: "events_end", label: "Eventos — fim" },
  { id: "gateways", label: "Desvios" },
  { id: "tasks", label: "Tarefas" },
  { id: "activities", label: "Atividades" },
  { id: "artifacts", label: "Artefatos" },
  { id: "boundary", label: "Eventos de borda" },
];

export const BPMN_NODE_DEFINITIONS = {
  start: {
    label: "Início",
    category: "events_start",
    shape: "event_start",
    marker: "none",
    bpmnTag: "startEvent",
    participatesInFlow: true,
    hint: "Evento de início genérico (nenhum gatilho específico).",
  },
  start_message: {
    label: "Início — mensagem",
    category: "events_start",
    shape: "event_start",
    marker: "message",
    bpmnTag: "startEvent",
    bpmnEventDefinition: "messageEventDefinition",
    participatesInFlow: true,
    hint: "Processo inicia ao receber uma mensagem.",
  },
  start_timer: {
    label: "Início — temporizador",
    category: "events_start",
    shape: "event_start",
    marker: "timer",
    bpmnTag: "startEvent",
    bpmnEventDefinition: "timerEventDefinition",
    participatesInFlow: true,
    hint: "Processo inicia em data/horário ou intervalo programado.",
  },
  start_signal: {
    label: "Início — sinal",
    category: "events_start",
    shape: "event_start",
    marker: "signal",
    bpmnTag: "startEvent",
    bpmnEventDefinition: "signalEventDefinition",
    participatesInFlow: true,
    hint: "Processo inicia ao receber um sinal em difusão.",
  },
  start_conditional: {
    label: "Início — condicional",
    category: "events_start",
    shape: "event_start",
    marker: "conditional",
    bpmnTag: "startEvent",
    bpmnEventDefinition: "conditionalEventDefinition",
    participatesInFlow: true,
    hint: "Processo inicia quando uma condição de negócio é satisfeita.",
  },
  start_multiple: {
    label: "Início — múltiplo",
    category: "events_start",
    shape: "event_start",
    marker: "multiple",
    bpmnTag: "startEvent",
    bpmnEventDefinition: "multipleEventDefinition",
    participatesInFlow: true,
    hint: "Início disparado por um entre vários eventos possíveis.",
  },
  start_parallel: {
    label: "Início — paralelo",
    category: "events_start",
    shape: "event_start",
    marker: "parallel",
    bpmnTag: "startEvent",
    bpmnEventDefinition: "parallelMultipleEventDefinition",
    participatesInFlow: true,
    hint: "Início exige que todos os eventos paralelos ocorram.",
  },

  intermediate: {
    label: "Intermediário",
    category: "events_intermediate",
    shape: "event_intermediate_catch",
    marker: "none",
    bpmnTag: "intermediateCatchEvent",
    participatesInFlow: true,
    hint: "Evento intermediário genérico (captura).",
  },
  intermediate_message_catch: {
    label: "Intermediário — mensagem (recepção)",
    category: "events_intermediate",
    shape: "event_intermediate_catch",
    marker: "message",
    bpmnTag: "intermediateCatchEvent",
    bpmnEventDefinition: "messageEventDefinition",
    participatesInFlow: true,
    hint: "Aguarda recebimento de mensagem durante o fluxo.",
  },
  intermediate_timer: {
    label: "Intermediário — temporizador",
    category: "events_intermediate",
    shape: "event_intermediate_catch",
    marker: "timer",
    bpmnTag: "intermediateCatchEvent",
    bpmnEventDefinition: "timerEventDefinition",
    participatesInFlow: true,
    hint: "Aguarda tempo decorrer (delay, prazo, ciclo).",
  },
  intermediate_signal_catch: {
    label: "Intermediário — sinal (recepção)",
    category: "events_intermediate",
    shape: "event_intermediate_catch",
    marker: "signal",
    bpmnTag: "intermediateCatchEvent",
    bpmnEventDefinition: "signalEventDefinition",
    participatesInFlow: true,
    hint: "Aguarda um sinal em difusão durante o fluxo.",
  },
  intermediate_conditional: {
    label: "Intermediário — condicional",
    category: "events_intermediate",
    shape: "event_intermediate_catch",
    marker: "conditional",
    bpmnTag: "intermediateCatchEvent",
    bpmnEventDefinition: "conditionalEventDefinition",
    participatesInFlow: true,
    hint: "Aguarda condição de negócio ser satisfeita.",
  },
  intermediate_link_catch: {
    label: "Intermediário — vínculo (recepção)",
    category: "events_intermediate",
    shape: "event_intermediate_catch",
    marker: "link",
    bpmnTag: "intermediateCatchEvent",
    bpmnEventDefinition: "linkEventDefinition",
    participatesInFlow: true,
    hint: "Ponto de chegada de um vínculo dentro do mesmo processo.",
  },
  intermediate_message_throw: {
    label: "Intermediário — mensagem (envio)",
    category: "events_intermediate",
    shape: "event_intermediate_throw",
    marker: "message",
    bpmnTag: "intermediateThrowEvent",
    bpmnEventDefinition: "messageEventDefinition",
    participatesInFlow: true,
    hint: "Envia mensagem para outro participante ou processo.",
  },
  intermediate_signal_throw: {
    label: "Intermediário — sinal (envio)",
    category: "events_intermediate",
    shape: "event_intermediate_throw",
    marker: "signal",
    bpmnTag: "intermediateThrowEvent",
    bpmnEventDefinition: "signalEventDefinition",
    participatesInFlow: true,
    hint: "Emite sinal em difusão durante o fluxo.",
  },
  intermediate_link_throw: {
    label: "Intermediário — vínculo (envio)",
    category: "events_intermediate",
    shape: "event_intermediate_throw",
    marker: "link",
    bpmnTag: "intermediateThrowEvent",
    bpmnEventDefinition: "linkEventDefinition",
    participatesInFlow: true,
    hint: "Salta para o ponto de vínculo correspondente no diagrama.",
  },
  intermediate_escalation_throw: {
    label: "Intermediário — escalação",
    category: "events_intermediate",
    shape: "event_intermediate_throw",
    marker: "escalation",
    bpmnTag: "intermediateThrowEvent",
    bpmnEventDefinition: "escalationEventDefinition",
    participatesInFlow: true,
    hint: "Dispara escalação para nível superior ou subprocesso.",
  },
  intermediate_compensation_throw: {
    label: "Intermediário — compensação",
    category: "events_intermediate",
    shape: "event_intermediate_throw",
    marker: "compensation",
    bpmnTag: "intermediateThrowEvent",
    bpmnEventDefinition: "compensateEventDefinition",
    participatesInFlow: true,
    hint: "Solicita compensação de atividades já concluídas.",
  },

  end: {
    label: "Fim",
    category: "events_end",
    shape: "event_end",
    marker: "none",
    bpmnTag: "endEvent",
    participatesInFlow: true,
    hint: "Evento de fim genérico — término normal do fluxo.",
  },
  end_message: {
    label: "Fim — mensagem",
    category: "events_end",
    shape: "event_end",
    marker: "message",
    bpmnTag: "endEvent",
    bpmnEventDefinition: "messageEventDefinition",
    participatesInFlow: true,
    hint: "Fim ao enviar mensagem para outro participante.",
  },
  end_error: {
    label: "Fim — erro",
    category: "events_end",
    shape: "event_end",
    marker: "error",
    bpmnTag: "endEvent",
    bpmnEventDefinition: "errorEventDefinition",
    participatesInFlow: true,
    hint: "Fim por erro de negócio ou técnico.",
  },
  end_terminate: {
    label: "Fim — terminate",
    category: "events_end",
    shape: "event_end",
    marker: "terminate",
    bpmnTag: "endEvent",
    bpmnEventDefinition: "terminateEventDefinition",
    participatesInFlow: true,
    hint: "Encerra imediatamente todo o processo (inclui tokens paralelos).",
  },
  end_signal: {
    label: "Fim — sinal",
    category: "events_end",
    shape: "event_end",
    marker: "signal",
    bpmnTag: "endEvent",
    bpmnEventDefinition: "signalEventDefinition",
    participatesInFlow: true,
    hint: "Fim ao emitir sinal em difusão.",
  },
  end_escalation: {
    label: "Fim — escalação",
    category: "events_end",
    shape: "event_end",
    marker: "escalation",
    bpmnTag: "endEvent",
    bpmnEventDefinition: "escalationEventDefinition",
    participatesInFlow: true,
    hint: "Fim por escalação para responsável externo.",
  },
  end_cancel: {
    label: "Fim — cancelamento",
    category: "events_end",
    shape: "event_end",
    marker: "cancel",
    bpmnTag: "endEvent",
    bpmnEventDefinition: "cancelEventDefinition",
    participatesInFlow: true,
    hint: "Fim por cancelamento de transação.",
  },
  end_compensation: {
    label: "Fim — compensação",
    category: "events_end",
    shape: "event_end",
    marker: "compensation",
    bpmnTag: "endEvent",
    bpmnEventDefinition: "compensateEventDefinition",
    participatesInFlow: true,
    hint: "Fim após concluir fluxo de compensação.",
  },

  decision: {
    label: "Decisão (XOR)",
    category: "gateways",
    shape: "gateway",
    marker: "exclusive",
    bpmnTag: "exclusiveGateway",
    participatesInFlow: true,
    hint: "Desvio exclusivo — apenas um caminho de saída é tomado.",
  },
  gateway_parallel: {
    label: "Paralelo (AND)",
    category: "gateways",
    shape: "gateway",
    marker: "parallel_gateway",
    bpmnTag: "parallelGateway",
    participatesInFlow: true,
    hint: "Desvio paralelo — todos os caminhos de saída são ativados.",
  },
  gateway_inclusive: {
    label: "Inclusivo (OR)",
    category: "gateways",
    shape: "gateway",
    marker: "inclusive",
    bpmnTag: "inclusiveGateway",
    participatesInFlow: true,
    hint: "Desvio inclusivo — um ou mais caminhos conforme condição.",
  },
  gateway_complex: {
    label: "Complexo",
    category: "gateways",
    shape: "gateway",
    marker: "complex",
    bpmnTag: "complexGateway",
    participatesInFlow: true,
    hint: "Desvio com regras de sincronização customizadas.",
  },
  gateway_event: {
    label: "Baseado em evento",
    category: "gateways",
    shape: "gateway",
    marker: "event_based",
    bpmnTag: "eventBasedGateway",
    participatesInFlow: true,
    hint: "Escolhe caminho conforme o primeiro evento que ocorrer.",
  },

  process: {
    label: "Atividade",
    category: "tasks",
    shape: "task",
    marker: "none",
    bpmnTag: "task",
    participatesInFlow: true,
    manualTask: true,
    hint: "Tarefa genérica ou manual (retângulo arredondado).",
  },
  task_user: {
    label: "Tarefa — usuário",
    category: "tasks",
    shape: "task",
    marker: "user",
    bpmnTag: "userTask",
    participatesInFlow: true,
    hint: "Tarefa executada por um usuário humano.",
  },
  task_service: {
    label: "Tarefa — serviço",
    category: "tasks",
    shape: "task",
    marker: "service",
    bpmnTag: "serviceTask",
    participatesInFlow: true,
    hint: "Tarefa automatizada via serviço ou sistema.",
  },
  task_manual: {
    label: "Tarefa — manual",
    category: "tasks",
    shape: "task",
    marker: "manual",
    bpmnTag: "manualTask",
    participatesInFlow: true,
    manualTask: true,
    hint: "Trabalho manual sem suporte de sistema.",
  },
  task_script: {
    label: "Tarefa — script",
    category: "tasks",
    shape: "task",
    marker: "script",
    bpmnTag: "scriptTask",
    participatesInFlow: true,
    hint: "Tarefa executada por script embarcado.",
  },
  task_business_rule: {
    label: "Tarefa — regra de negócio",
    category: "tasks",
    shape: "task",
    marker: "business_rule",
    bpmnTag: "businessRuleTask",
    participatesInFlow: true,
    hint: "Decisão automatizada via motor de regras (DMN).",
  },
  task_send: {
    label: "Tarefa — enviar",
    category: "tasks",
    shape: "task",
    marker: "send",
    bpmnTag: "sendTask",
    participatesInFlow: true,
    hint: "Envia mensagem como parte da atividade.",
  },
  task_receive: {
    label: "Tarefa — receber",
    category: "tasks",
    shape: "task",
    marker: "receive",
    bpmnTag: "receiveTask",
    participatesInFlow: true,
    hint: "Aguarda e recebe mensagem como atividade.",
  },

  subprocess: {
    label: "Subprocesso",
    category: "activities",
    shape: "activity_subprocess",
    marker: "none",
    bpmnTag: "subProcess",
    participatesInFlow: true,
    hint: "Subprocesso encapsulado com fluxo interno.",
  },
  call_activity: {
    label: "Chamada de subprocesso",
    category: "activities",
    shape: "activity_call",
    marker: "call",
    bpmnTag: "callActivity",
    participatesInFlow: true,
    hint: "Referência reutilizável a outro diagrama de processo.",
  },
  subprocess_ad_hoc: {
    label: "Subprocesso improvisado",
    category: "activities",
    shape: "activity_ad_hoc",
    marker: "ad_hoc",
    bpmnTag: "adHocSubProcess",
    participatesInFlow: true,
    hint: "Subprocesso não ordenado — atividades executadas conforme necessidade.",
  },
  subprocess_transaction: {
    label: "Subprocesso transação",
    category: "activities",
    shape: "activity_transaction",
    marker: "transaction",
    bpmnTag: "transaction",
    participatesInFlow: true,
    hint: "Subprocesso transacional com compensação/cancelamento.",
  },
  subprocess_event: {
    label: "Subprocesso por evento",
    category: "activities",
    shape: "activity_event_subprocess",
    marker: "event_sub",
    bpmnTag: "subProcess",
    bpmnEventDefinition: "triggeredByEvent",
    participatesInFlow: true,
    hint: "Subprocesso acionado por evento.",
  },

  document: {
    label: "Documento",
    category: "artifacts",
    shape: "artifact_document",
    marker: "none",
    bpmnTag: "textAnnotation",
    participatesInFlow: false,
    hint: "Documento ou artefato produzido/consumido (folha com canto dobrado).",
  },
  data_object: {
    label: "Objeto de dados",
    category: "artifacts",
    shape: "artifact_data_object",
    marker: "none",
    bpmnTag: "dataObjectReference",
    participatesInFlow: false,
    hint: "Dado de entrada/saída referenciado no fluxo (paralelogramo).",
  },
  data: {
    label: "Armazenamento",
    category: "artifacts",
    shape: "artifact_data_store",
    marker: "none",
    bpmnTag: "dataStoreReference",
    participatesInFlow: false,
    hint: "Armazenamento persistente (cilindro BPMN).",
  },
  comment: {
    label: "Nota",
    category: "artifacts",
    shape: "artifact_comment",
    marker: "none",
    bpmnTag: "textAnnotation",
    participatesInFlow: false,
    hint: "Anotação explicativa — não participa da lógica do fluxo.",
  },
  group: {
    label: "Grupo",
    category: "artifacts",
    shape: "artifact_group",
    marker: "none",
    bpmnTag: "group",
    participatesInFlow: false,
    hint: "Agrupamento visual de elementos relacionados.",
  },

  boundary_timer: {
    label: "Borda — temporizador",
    category: "boundary",
    shape: "boundary",
    marker: "timer",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "timerEventDefinition",
    participatesInFlow: true,
    hint: "Interrompe ou desvia atividade após prazo.",
  },
  boundary_message: {
    label: "Borda — mensagem",
    category: "boundary",
    shape: "boundary",
    marker: "message",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "messageEventDefinition",
    participatesInFlow: true,
    hint: "Desvia fluxo ao receber mensagem durante atividade.",
  },
  boundary_error: {
    label: "Borda — erro",
    category: "boundary",
    shape: "boundary",
    marker: "error",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "errorEventDefinition",
    participatesInFlow: true,
    hint: "Captura erro da atividade anexada (interrompente).",
  },
  boundary_signal: {
    label: "Borda — sinal",
    category: "boundary",
    shape: "boundary",
    marker: "signal",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "signalEventDefinition",
    participatesInFlow: true,
    hint: "Desvia fluxo ao receber sinal durante atividade.",
  },
  boundary_escalation: {
    label: "Borda — escalação",
    category: "boundary",
    shape: "boundary",
    marker: "escalation",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "escalationEventDefinition",
    participatesInFlow: true,
    hint: "Escala atividade para responsável externo.",
  },
  boundary_compensation: {
    label: "Borda — compensação",
    category: "boundary",
    shape: "boundary",
    marker: "compensation",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "compensateEventDefinition",
    participatesInFlow: true,
    hint: "Gatilho de compensação na atividade anexada.",
  },
  boundary_cancel: {
    label: "Borda — cancelamento",
    category: "boundary",
    shape: "boundary",
    marker: "cancel",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "cancelEventDefinition",
    participatesInFlow: true,
    hint: "Cancela transação da atividade anexada.",
  },
  boundary_conditional: {
    label: "Borda — condicional",
    category: "boundary",
    shape: "boundary",
    marker: "conditional",
    bpmnTag: "boundaryEvent",
    bpmnEventDefinition: "conditionalEventDefinition",
    participatesInFlow: true,
    hint: "Desvia fluxo quando condição é satisfeita durante atividade.",
  },
} as const satisfies Record<string, BpmnNodeDefinition>;

export const FLOWCHART_NODE_TYPES = Object.keys(BPMN_NODE_DEFINITIONS) as FlowchartNodeType[];

export const FLOWCHART_NODE_PALETTE = FLOWCHART_NODE_TYPES.map((type) => ({
  type,
  label: BPMN_NODE_DEFINITIONS[type].label,
  category: BPMN_NODE_DEFINITIONS[type].category,
}));

export function getBpmnNodeDefinition(type: string): BpmnNodeDefinition | undefined {
  if (!isKnownFlowchartNodeType(type)) return undefined;
  return BPMN_NODE_DEFINITIONS[type] as BpmnNodeDefinition;
}

export function isManualTaskType(type: string): boolean {
  const def = getBpmnNodeDefinition(type);
  return Boolean(def?.manualTask) || type === "process";
}

export function isKnownFlowchartNodeType(type: string): type is FlowchartNodeType {
  return type in BPMN_NODE_DEFINITIONS;
}

export function normalizeFlowchartNodeType(type: string): FlowchartNodeType {
  return isKnownFlowchartNodeType(type) ? type : "process";
}

const START_TYPES = new Set(
  FLOWCHART_NODE_TYPES.filter((type) => BPMN_NODE_DEFINITIONS[type].shape === "event_start")
);
const END_TYPES = new Set(
  FLOWCHART_NODE_TYPES.filter((type) => BPMN_NODE_DEFINITIONS[type].shape === "event_end")
);
const GATEWAY_TYPES = new Set(
  FLOWCHART_NODE_TYPES.filter((type) => BPMN_NODE_DEFINITIONS[type].shape === "gateway")
);
const NON_FLOW_TYPES = new Set(
  FLOWCHART_NODE_TYPES.filter((type) => !BPMN_NODE_DEFINITIONS[type].participatesInFlow)
);

export function isStartEventType(type: string): boolean {
  return START_TYPES.has(type as FlowchartNodeType);
}

export function isEndEventType(type: string): boolean {
  return END_TYPES.has(type as FlowchartNodeType);
}

export function isGatewayType(type: string): boolean {
  return GATEWAY_TYPES.has(type as FlowchartNodeType);
}

export function isNonFlowNodeType(type: string): boolean {
  return NON_FLOW_TYPES.has(type as FlowchartNodeType);
}

export function paletteByCategory(category: BpmnPaletteCategoryId) {
  return FLOWCHART_NODE_PALETTE.filter((item) => item.category === category);
}
