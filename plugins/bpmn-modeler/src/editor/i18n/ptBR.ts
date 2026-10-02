/**
 * PT-BR — única fonte de tradução do chrome BPMN apresentacional.
 *
 * Owner de toda string user-facing gerada pelo vendor (bpmn-js +
 * bpmn-js-properties-panel): labels da palette, context pad, popup de
 * replace, cabeçalho de elemento, grupos, campos, descrições e estados
 * do properties panel. Tudo passa pelo serviço injetável `translate`
 * do diagram-js (ver translate.ts) — nenhuma string é patcheada via DOM.
 *
 * Somente PRESENTATION: valores persistidos, ids, tipos moddle e keys
 * internas nunca passam por aqui.
 */

/** Nomes de tipos BPMN com prefixo de definição de evento
 *  (ex.: "Message Start Event" → prefixo "Message" + base "Start Event"). */
const EVENT_DEFINITION_PREFIX: Record<string, string> = {
  Message: "de mensagem",
  Signal: "de sinal",
  Error: "de erro",
  Escalation: "de escalonamento",
  Timer: "temporizado",
  Conditional: "condicional",
  Link: "de ligação",
  Compensate: "de compensação",
  Compensation: "de compensação",
  Cancel: "de cancelamento",
  Terminate: "de terminação",
};

const BASE_TYPE_NAMES: Record<string, string> = {
  Process: "Processo",
  Participant: "Participante",
  Collaboration: "Colaboração",
  Lane: "Raia",
  Group: "Grupo",
  "Text Annotation": "Anotação de texto",

  "Start Event": "Evento inicial",
  "Intermediate Catch Event": "Evento intermediário",
  "Intermediate Throw Event": "Evento intermediário de lançamento",
  "End Event": "Evento final",
  "Boundary Event": "Evento de borda",

  Task: "Tarefa",
  "User Task": "Tarefa de usuário",
  "Manual Task": "Tarefa manual",
  "Service Task": "Tarefa de serviço",
  "Script Task": "Tarefa de script",
  "Business Rule Task": "Tarefa de regra de negócio",
  "Send Task": "Tarefa de envio",
  "Receive Task": "Tarefa de recebimento",

  "Sub Process": "Subprocesso",
  "Expanded Sub Process": "Subprocesso expandido",
  "Collapsed Sub Process": "Subprocesso recolhido",
  "Event Sub Process": "Subprocesso de evento",
  "Ad Hoc Sub Process": "Subprocesso ad hoc",
  Transaction: "Transação",
  "Call Activity": "Atividade de chamada",

  "Exclusive Gateway": "Gateway exclusivo",
  "Parallel Gateway": "Gateway paralelo",
  "Inclusive Gateway": "Gateway inclusivo",
  "Complex Gateway": "Gateway complexo",
  "Event Based Gateway": "Gateway baseado em eventos",

  "Sequence Flow": "Fluxo de sequência",
  "Default Flow": "Fluxo padrão",
  "Conditional Flow": "Fluxo condicional",
  "Message Flow": "Fluxo de mensagem",
  Association: "Associação",
  "Data Input Association": "Associação de entrada de dados",
  "Data Output Association": "Associação de saída de dados",

  "Data Object": "Objeto de dados",
  "Data Object Reference": "Referência a objeto de dados",
  "Data Store": "Armazenamento de dados",
  "Data Store Reference": "Referência a armazenamento de dados",

  "Expanded Pool/Participant": "Pool/participante expandido",
  "Empty Pool/Participant": "Pool/participante vazio",
};

/** Strings literais usadas pelo vendor (palette, context pad, popup,
 *  properties panel, overlays). Fonte: translate() calls do bundle
 *  instalado — chaves são os templates EN exatos. */
const PT_BR: Record<string, string> = {
  /* --- properties panel: chrome --- */
  "Select an element to edit its properties.":
    "Selecione um elemento para editar suas propriedades.",
  "Multiple elements are selected. Select a single element to edit its properties.":
    "Vários elementos estão selecionados. Selecione um único elemento para editar suas propriedades.",
  "<none>": "<nenhum>",
  "<empty>": "<vazio>",
  "Create new ...": "Criar novo…",
  "Start typing ": "Comece a digitar ",

  /* --- properties panel: grupos --- */
  General: "Geral",
  Documentation: "Documentação",
  Compensation: "Compensação",
  Error: "Erro",
  Link: "Ligação",
  Message: "Mensagem",
  Signal: "Sinal",
  Escalation: "Escalonamento",
  Timer: "Temporizador",
  "Multi-instance": "Multi-instância",
  Completion: "Conclusão",

  /* --- properties panel: campos --- */
  Name: "Nome",
  ID: "ID BPMN",
  "This maps to the process definition key.":
    "Identificador técnico do elemento no arquivo BPMN. Deve ser único no diagrama. Alterações podem afetar referências externas ou integrações.",
  "Process name": "Nome do processo",
  "Process ID": "ID BPMN do processo",
  "Participant Name": "Nome do participante",
  "Participant ID": "ID BPMN do participante",
  Executable: "Executável",
  "Version tag": "Tag de versão",
  "Version Tag": "Tag de versão",
  "Time to live": "Tempo de vida",
  Condition: "Condição",
  "Condition expression": "Expressão de condição",
  "Condition Expression": "Expressão de condição",
  "Element documentation": "Documentação do elemento",
  "Process documentation": "Documentação do processo",
  "Global error reference": "Referência global de erro",
  "Global escalation reference": "Referência global de escalonamento",
  "Global message reference": "Referência global de mensagem",
  "Global signal reference": "Referência global de sinal",
  "Code": "Código",
  Type: "Tipo",
  Value: "Valor",
  Date: "Data",
  Duration: "Duração",
  Cycle: "Ciclo",
  "Loop cardinality": "Cardinalidade do loop",
  Collection: "Coleção",
  "Element variable": "Variável do elemento",
  "Completion condition": "Condição de conclusão",
  "Cancel remaining instances": "Cancelar instâncias restantes",
  "Wait for completion": "Aguardar conclusão",
  "Active elements collection": "Coleção de elementos ativos",
  "Output collection": "Coleção de saída",
  "Output element": "Elemento de saída",
  "Parallel multi-instance": "Multi-instância paralela",
  "Sequential multi-instance": "Multi-instância sequencial",
  Loop: "Repetição",
  "Default value": "Valor padrão",
  "Activity reference": "Referência da atividade",
  Format: "Formato",

  /* --- properties panel: opções de select/radio --- */
  Before: "Antes",
  After: "Depois",
  Exclusive: "Exclusivo",
  On: "Ligado",
  Off: "Desligado",

  /* --- properties panel: validação inline e descrições --- */
  "ID must not be empty.": "O ID não pode ficar vazio.",
  "ID must be unique.": "O ID deve ser único.",
  "ID must not contain spaces.": "O ID não pode conter espaços.",
  "ID must not contain prefix.": "O ID não pode conter o prefixo.",
  "ID must be a valid QName.": "O ID deve ser um QName válido.",
  "A specific point in time defined as ISO 8601 combined date and time representation.":
    "Um ponto específico no tempo, no formato ISO 8601 de data e hora.",
  "UTC time": "Horário UTC",
  "UTC plus 2 hours zone offset": "UTC mais 2 horas de fuso",
  "Documentation: Timer events": "Documentação: eventos temporizados",
  "Timer documentation": "Documentação do temporizador",
  "How to configure a timer": "Como configurar um temporizador",
  "A cycle defined as ISO 8601 repeating intervals format.":
    "Um ciclo no formato ISO 8601 de intervalos repetidos.",
  "A time duration defined as ISO 8601 durations format.":
    "Uma duração no formato ISO 8601.",
  "every 10 seconds, up to 5 times": "a cada 10 segundos, até 5 vezes",
  "every day, infinitely": "todos os dias, indefinidamente",
  "15 seconds": "15 segundos",
  "1 hour and 30 minutes": "1 hora e 30 minutos",
  "14 days": "14 dias",
  "Specify more than one variable change event as a comma separated list. Variable change events are:":
    "Informe mais de um evento de alteração de variável como lista separada por vírgulas. Os eventos são:",
  "Documentation: Variable events": "Documentação: eventos de variável",

  /* --- palette --- */
  "Activate hand tool": "Ativar ferramenta de mão",
  "Activate lasso tool": "Ativar ferramenta de laço",
  "Activate create/remove space tool": "Ativar ferramenta de adicionar/remover espaço",
  "Activate global connect tool": "Ativar ferramenta de conexão global",
  "Create start event": "Criar evento inicial",
  "Create intermediate/boundary event": "Criar evento intermediário/de borda",
  "Create end event": "Criar evento final",
  "Create gateway": "Criar gateway",
  "Create task": "Criar tarefa",
  "Create data object reference": "Criar referência a objeto de dados",
  "Create data store reference": "Criar referência a armazenamento de dados",
  "Create expanded sub-process": "Criar subprocesso expandido",
  "Create pool/participant": "Criar pool/participante",
  "Create group": "Criar grupo",

  /* --- context pad --- */
  "Append task": "Adicionar tarefa",
  "Append append-task": "Adicionar tarefa",
  "Append gateway": "Adicionar gateway",
  "Append end event": "Adicionar evento final",
  "Append intermediate/boundary event": "Adicionar evento intermediário/de borda",
  "Append receive task": "Adicionar tarefa de recebimento",
  "Append message intermediate catch event": "Adicionar evento intermediário de mensagem",
  "Append timer intermediate catch event": "Adicionar evento intermediário temporizado",
  "Append conditional intermediate catch event": "Adicionar evento intermediário condicional",
  "Append signal intermediate catch event": "Adicionar evento intermediário de sinal",
  "Append compensation activity": "Adicionar atividade de compensação",
  "Add text annotation": "Adicionar anotação de texto",
  "Add lane above": "Adicionar raia acima",
  "Add lane below": "Adicionar raia abaixo",
  "Divide into two lanes": "Dividir em duas raias",
  "Divide into three lanes": "Dividir em três raias",
  "Participant multiplicity": "Multiplicidade do participante",
  "Toggle non-interrupting": "Alternar não interruptivo",
  "Connect to other element": "Conectar a outro elemento",
  "Connect using association": "Conectar usando associação",
  "Connect using data input association": "Conectar usando associação de entrada de dados",
  "Change element": "Trocar elemento",
  Delete: "Excluir",
  "Align elements": "Alinhar elementos",
  "Align elements ": "Alinhar elementos",
  "Distribute elements horizontally": "Distribuir elementos horizontalmente",
  "Distribute elements vertically": "Distribuir elementos verticalmente",
  "Search in diagram": "Buscar no diagrama",
  "Open {element}": "Abrir {element}",

  /* --- runtime feedback (ModelingFeedback — tooltips de erro em
     drag/drop/move rejeitados; passam por translate() no vendor) --- */
  "flow elements must be children of pools/participants":
    "Elementos de fluxo devem pertencer a um pool/participante",
  "Data object must be placed within a pool/participant.":
    "Objeto de dados deve ser posicionado dentro de um pool/participante",

  /* --- grupo avançado do product provider (propertiesPanelModule) --- */
  "Advanced settings": "Configurações avançadas",
  "Technical settings stored in the BPMN file. Changes may affect external references and integrations.":
    "Configurações técnicas gravadas no arquivo BPMN. Alterações podem afetar referências externas ou integrações.",
};

/** Sufixos/qualificadores dos labels do popup de replace
 *  (ex.: "Sub-process (collapsed)", "(non-interrupting)",
 *  "(removes content)"). */
const ENTRY_QUALIFIERS: [RegExp, string][] = [
  [/\(non[- ]interrupting\)$/i, " (não interruptivo)"],
  [/\(collapsed\)$/i, " (recolhido)"],
  [/\(expanded\)$/i, " (expandido)"],
  [/\(removes content\)$/i, " (remove o conteúdo)"],
];

/** O popup de replace usa variações lowercase/hifenizadas do nome
 *  ("Sub-process (expanded)", "Message start event (non-interrupting)").
 *  Normaliza para a forma PascalCase espaçada usada pelo properties panel. */
function normalizeEntryLabel(label: string): string {
  return label
    .replace(/sub-process/gi, "sub process")
    .replace(/event-based/gi, "event based")
    .replace(/ad-hoc/gi, "ad hoc")
    .replace(/pool\/participant/gi, "pool/participant")
    .replace(/(^|[\s/])([a-z])/g, (_, sep: string, c: string) => sep + c.toUpperCase());
}

/**
 * Nome amigável PT-BR para o tipo concreto do elemento — mesmas strings
 * que o properties panel produz via getConcreteType + espaçamento
 * (ex.: "Timer Boundary Event", "(Non Interrupting) Start Event"),
 * incluindo os labels do popup de replace ("User task",
 * "Sub-process (collapsed)", "Message start event (non-interrupting)").
 */
export function translateBpmnTypeName(spacedType: string): string {
  let clean = spacedType.trim();
  let suffix = "";
  for (const [pattern, ptSuffix] of ENTRY_QUALIFIERS) {
    if (pattern.test(clean)) {
      suffix = ptSuffix + suffix;
      clean = clean.replace(pattern, "").trim();
    }
  }
  clean = normalizeEntryLabel(clean);

  const exact = BASE_TYPE_NAMES[clean];
  if (exact) return exact + suffix;

  // "Message Start Event" → "Evento inicial de mensagem"
  for (const prefix of Object.keys(EVENT_DEFINITION_PREFIX)) {
    if (clean.startsWith(prefix + " ")) {
      const base = BASE_TYPE_NAMES[clean.slice(prefix.length + 1)];
      if (base) return `${base} ${EVENT_DEFINITION_PREFIX[prefix]}${suffix}`;
    }
  }
  return spacedType;
}

/** Lookup central: tipo composto → mapa literal → template original. */
export function lookupPtBr(template: string): string {
  const typeName = translateBpmnTypeName(template);
  if (typeName !== template) return typeName;
  return PT_BR[template] ?? template;
}
