/**
 * Catálogo centralizado de ajuda técnica do Studio (pt-BR).
 *
 * Ownership: o conteúdo de domínio (termos de engenharia, proveniência,
 * limitações dos métodos) vive aqui — nunca inline nos componentes nem
 * no Plugin UI. Os mecanismos visuais (balão, rótulo com ajuda, hint de
 * coluna) são genéricos do kit `@delpi/plugin-ui`.
 */

/** Entrada curta de ajuda contextual (balões, hints de coluna, rótulos). */
export type StudioHelpEntry = Readonly<{
  /** Identificador estável — usado por testes e pelo rastreio de cobertura. */
  id: string;
  title: string;
  /** Texto exibido no balão/hint — curto e objetivo. */
  summary: string;
}>;

/** Conteúdo extenso do painel "Como usar este método". */
export type StudioMethodGuide = Readonly<{
  id: string;
  title: string;
  objective: string;
  steps: readonly string[];
  interpretation: readonly string[];
  limitations: readonly string[];
}>;

const h = (id: string, title: string, summary: string): StudioHelpEntry => ({ id, title, summary });

/* ---------- Proveniência e origem do estudo ---------- */

export const SOURCE_HELP = {
  observed: h("source.observed", "OBSERVED",
    "Dados lidos do roteiro oficial do produto (contrato oficial API-DELPI). São uma consulta — nunca uma cópia editável do roteiro."),
  provided: h("source.provided", "PROVIDED",
    "Valor informado manualmente neste estudo. Pertence ao rascunho local e não representa dado oficial."),
  calculated: h("source.calculated", "CALCULATED",
    "Valor derivado de um cálculo declarado. A legenda indica se foi calculado pelo domínio autorizado (análise oficial) ou localmente pelo rascunho."),
  simulation: h("source.simulation", "SIMULATION",
    "Distribuição hipotética deste cenário de estudo. Serve para comparar alternativas — não é aprovação nem alteração do processo oficial."),
  unknown: h("source.unknown", "UNKNOWN",
    "Dado ausente ou desconhecido. O Studio nunca assume ausência como zero: a carga exibida pode ser parcial."),
  draftLocal: h("source.draftLocal", "DRAFT_LOCAL",
    "Rascunho local do estudo. As alterações ficam apenas neste contexto — o roteiro oficial no ERP permanece intacto."),
} as const;

export const STUDY_HELP = {
  product: h("study.product", "Produto DELPI",
    "Código do produto cadastrado na base oficial. A busca traz o roteiro vigente para a filial e o estágio selecionados."),
  manualStudy: h("study.manual", "Estudo manual",
    "Estudo criado do zero, sem vínculo com produto oficial. Todas as operações e tempos são PROVIDED — diagnóstico local, sem análise oficial."),
  routing: h("study.routing", "Roteiro oficial",
    "Sequência de operações cadastrada no ERP para o produto, filial e estágio. Exibida como OBSERVED — somente leitura."),
  branch: h("study.branch", "Filial",
    "Unidade fabril que possui o roteiro. O mesmo produto pode ter roteiros diferentes por filial."),
  stage: h("study.stage", "Estágio produtivo",
    "Etapa do roteiro selecionada para o estudo (ex.: montagem). A análise oficial só cobre o estágio que a resposta oficial retornou."),
  scenario: h("study.scenario", "Cenário",
    "Versão alternativa da atribuição de operações a postos. Compare cenários para avaliar distribuições diferentes — cada um é uma SIMULATION independente."),
  draftSave: h("study.draftSave", "Salvamento do rascunho",
    "Status informado pelo portal sobre a persistência local do rascunho. Não significa publicação no ERP."),
} as const;

/* ---------- Condições de produção ---------- */

export const PRODUCTION_HELP = {
  shiftMode: h("production.shiftMode", "Modo de turno",
    "Horários: informe início e fim (o turno pode cruzar a meia-noite). Minutos: informe a duração total diretamente."),
  shiftStart: h("production.shiftStart", "Início do turno",
    "Horário de início da jornada produtiva."),
  shiftEnd: h("production.shiftEnd", "Fim do turno",
    "Horário de término. Se anterior ao início, o turno é tratado como noturno (cruza a meia-noite)."),
  shiftMinutes: h("production.shiftMinutes", "Duração do turno",
    "Total de minutos da jornada, antes de descontar as pausas."),
  pause: h("production.pause", "Pausa",
    "Intervalo não produtivo dentro do turno (refeição, café). Pausas são descontadas do tempo produtivo. No modo Horários informe início e fim; no modo Minutos informe a duração."),
  productiveTime: h("production.productiveTime", "Tempo produtivo",
    "Tempo do turno descontadas as pausas. É a base do takt: tempo produtivo disponível para produzir a demanda do turno."),
  demand: h("production.demand", "Demanda por turno",
    "Quantidade de peças que o turno precisa entregar. Necessária para calcular o takt de referência."),
  batch: h("production.batch", "Tamanho do lote",
    "Quantidade de peças processadas por lote. Relevante para ratear tempos de setup por peça quando aplicável."),
  takt: h("production.takt", "Takt de referência",
    "Tempo produtivo dividido pela demanda do turno. Ex.: 420 min disponíveis para 500 peças = 50,4 s por peça. Sem turno e demanda válidos, o takt fica indisponível (—)."),
  standardTime: h("production.standardTime", "Tempo padrão",
    "Tempo por peça registrado no roteiro oficial para a operação (OBSERVED). Ausente = UNKNOWN, nunca zero."),
  setup: h("production.setup", "Setup",
    "Tempo de preparação por lote registrado no roteiro oficial (horas/lote). Independe do tempo por peça."),
} as const;

/* ---------- Balanceamento ---------- */

export const BALANCE_HELP = {
  operation: h("balance.operation", "Operação",
    "Passo do processo estudado. Em estudo OBSERVED vem do roteiro oficial; em estudo manual é informada por você."),
  station: h("balance.station", "Posto",
    "Posto de trabalho hipotético criado neste estudo para distribuir operações. Não equivale a um Centro de Trabalho (CT) oficial nem a um operador ou máquina específicos."),
  workCenter: h("balance.workCenter", "Centro de Trabalho (CT)",
    "Recurso organizacional do roteiro oficial onde a operação é executada. O CT não é, necessariamente, um posto físico único — o posto do estudo é uma hipótese de balanceamento."),
  resource: h("balance.resource", "Recurso",
    "Recurso produtivo registrado no roteiro oficial para a operação (máquina, dispositivo ou equipe). Distinto do CT e do posto hipotético do estudo."),
  stationLoad: h("balance.stationLoad", "Carga por posto",
    "Soma dos tempos conhecidos das operações atribuídas ao posto. Operações sem tempo contribuem como UNKNOWN — a carga pode ser parcial."),
  maxLoad: h("balance.maxLoad", "Maior carga",
    "Maior soma de tempos conhecidos entre os postos. Se houver operação sem tempo, o valor é a carga conhecida (parcial)."),
  unassigned: h("balance.unassigned", "Operações sem posto",
    "Operações do estudo ainda não atribuídas a um posto neste cenário. Atribuir não altera o roteiro oficial — é parte da simulação."),
  yamazumi: h("balance.yamazumi", "Yamazumi",
    "Gráfico de barras empilhadas que mostra a carga de cada posto comparada ao takt. Cada bloco é uma operação; blocos acima da linha de takt indicam posto sobrecarregado."),
  taktVsLoad: h("balance.taktVsLoad", "Takt versus carga",
    "Posto dentro do takt consegue atender a demanda no ritmo necessário. Carga acima do takt indica excesso de trabalho naquele posto — redistribua operações entre postos."),
  bottleneck: h("balance.bottleneck", "Gargalo candidato",
    "Operação com maior tempo individual — provável limitante do fluxo. É um indicador, não um diagnóstico confirmado."),
} as const;

/* ---------- Métodos ---------- */

export const METHOD_HELP = {
  rail: h("method.rail", "Métodos",
    "Lista os métodos disponíveis e os planejados. Expandir/recolher só muda a apresentação — o estudo é preservado."),
  m1: h("method.m1", "M1 — Capacidade e takt",
    "Abre a análise de capacidade: takt de referência, carga por posto e, quando o host autoriza, a análise oficial calculada pelo domínio."),
  m2: h("method.m2", "M2 — FFD / LCR",
    "Método de balanceamento por precedências. Planejado — ainda não disponível nesta versão."),
  m3: h("method.m3", "M3 — Peso posicional",
    "Método de balanceamento por peso posicional (RPW). Planejado — ainda não disponível nesta versão."),
  m4: h("method.m4", "M4 — Kilbridge–Wester",
    "Método clássico de balanceamento por precedências. Planejado — ainda não disponível nesta versão."),
  m5: h("method.m5", "M5 — Yamazumi",
    "Abre o Yamazumi — gráfico interativo de distribuição de cargas por posto, com linha de takt e atribuição por arraste ou teclado."),
  m6: h("method.m6", "M6 — Recursos",
    "Dimensionamento de recursos produtivos. Planejado — ainda não disponível nesta versão."),
  planned: h("method.planned", "Método planejado",
    "Este método está no roadmap do produto, mas ainda não foi entregue. Nenhum cálculo ou contrato existe para ele nesta versão."),
} as const;

/* ---------- Ações ---------- */

export const ACTION_HELP = {
  searchRouting: h("action.searchRouting", "Buscar roteiro",
    "Consulta o roteiro oficial do produto informado. A consulta é feita pelo portal — o Studio apenas apresenta o resultado."),
  createStudy: h("action.createStudy", "Criar estudo",
    "Inicia um rascunho manual vazio com um cenário inicial."),
  methodGuide: h("action.methodGuide", "Como usar este método",
    "Explica o objetivo, os passos e as limitações do método aberto na bancada."),
  newScenario: h("action.newScenario", "Novo cenário",
    "Cria outro cenário de estudo para comparar uma distribuição alternativa (até 4 cenários)."),
  conditions: h("action.conditions", "Condições de produção",
    "Abre o painel para configurar turno, pausas, demanda e lote — dados que definem o takt de referência."),
  moreActions: h("action.moreActions", "Mais ações",
    "Abre as ações secundárias do estudo: trocar origem, exportar e limpar."),
  switchOrigin: h("action.switchOrigin", "Trocar origem",
    "Encerra a sessão atual e volta à escolha de origem. O rascunho local salvo deste contexto permanece disponível — pede confirmação."),
  exportCsv: h("action.exportCsv", "Exportar CSV",
    "Gera o arquivo CSV do estudo pelo portal. Exporta o rascunho — não altera dados oficiais."),
  exportXlsx: h("action.exportXlsx", "Exportar Excel",
    "Gera a planilha do estudo pelo portal. Exporta o rascunho — não altera dados oficiais."),
  exportPdf: h("action.exportPdf", "Exportar PDF",
    "Gera o documento PDF do estudo pelo portal. Exporta o rascunho — não altera dados oficiais."),
  clearStudy: h("action.clearStudy", "Limpar estudo",
    "Remove o rascunho local exibido. O roteiro oficial não é alterado."),
  addStation: h("action.addStation", "Adicionar posto",
    "Cria um posto hipotético neste cenário para organizar as operações."),
  addOperation: h("action.addOperation", "Adicionar operação",
    "Inclui uma operação no estudo local. Em estudo OBSERVED ela nasce como PROVIDED (ajuste local), não como operação oficial."),
  removeOperation: h("action.removeOperation", "Remover operação",
    "Remove a operação do rascunho local e suas atribuições em todos os cenários."),
  assignStation: h("action.assignStation", "Atribuir posto",
    "Define o posto da operação neste cenário — por este seletor, pela tabela ou arrastando o bloco no Yamazumi."),
  runAnalysis: h("action.runAnalysis", "Executar análise oficial",
    "Solicita ao portal o cálculo autorizado de capacidade e takt sobre o roteiro OBSERVED. O Studio nunca calcula o resultado oficial."),
  officialDetails: h("action.officialDetails", "Detalhes oficiais",
    "Mostra os metadados observados do roteiro (operação, CT, recurso, tempo padrão, setup). Consulta — não edição."),
} as const;

/* ---------- Estados e validações ---------- */

export const STATE_HELP = {
  noStations: h("state.noStations", "Nenhum posto configurado",
    "Crie um posto e atribua operações para visualizar as cargas comparadas ao takt."),
  noTakt: h("state.noTakt", "Takt indisponível",
    "Configure o turno produtivo e a demanda por turno para calcular o takt de referência."),
  unknownTime: h("state.unknownTime", "Tempo desconhecido",
    "Esta operação não possui tempo informado — a carga apresentada pode ser parcial. Informe o tempo somente se possuir uma referência válida."),
  manualNoOfficial: h("state.manualNoOfficial", "Sem análise oficial",
    "Estudo manual sem vínculo com roteiro oficial — os valores são diagnóstico local do rascunho (SIMULATION / DRAFT_LOCAL), não dimensionamento oficial."),
  stageNotCovered: h("state.stageNotCovered", "Estágio fora do escopo",
    "O resultado oficial retornado não inclui o estágio selecionado. Confira o estágio do estudo ou consulte a Engenharia."),
  missingOfficialTime: h("state.missingOfficialTime", "Operações sem tempo oficial",
    "Operações do roteiro sem tempo padrão registrado — contadas como UNKNOWN, nunca como zero."),
} as const;

/* ---------- Guias extensos dos métodos ---------- */

export const METHOD_GUIDES: Readonly<Record<"M1" | "M5", StudioMethodGuide>> = {
  M1: {
    id: "guide.m1",
    title: "M1 — Capacidade e takt",
    objective:
      "Verificar se a capacidade do estudo atende a demanda: quanto tempo cada unidade pode levar (takt) e como a carga conhecida se distribui pelos postos.",
    steps: [
      "Abra «Condições de produção» e informe o turno — por horários (com pausas) ou diretamente em minutos.",
      "Informe a demanda por turno (e o lote, quando relevante).",
      "Leia o «Takt de referência» nos indicadores — tempo máximo por unidade para atender a demanda.",
      "Compare a «Carga conhecida» de cada posto com o takt na tabela do método.",
      "Em estudo com roteiro oficial, use «Executar análise oficial» para obter o resultado calculado pelo domínio autorizado.",
    ],
    interpretation: [
      "Takt — tempo produtivo do turno dividido pela demanda. É a referência, não uma meta.",
      "Conteúdo de trabalho — soma dos tempos conhecidos das operações (CALCULATED).",
      "Mínimo teórico de postos — piso estimado a partir do conteúdo de trabalho e do takt.",
      "Gargalo candidato — operação com maior tempo individual; indicador, não diagnóstico.",
      "Diagnóstico local × análise oficial — os valores locais dependem dos dados do rascunho; a análise oficial é calculada pelo domínio autorizado do portal sobre o roteiro OBSERVED.",
    ],
    limitations: [
      "Sem turno e demanda válidos, o takt fica indisponível (—).",
      "Operações sem tempo entram como UNKNOWN — a carga exibida pode ser parcial e nunca é assumida como zero.",
      "Se o resultado oficial não cobrir o estágio selecionado, o aviso correspondente é exibido.",
      "Valores de estudo manual são apenas diagnóstico local — nunca dimensionamento oficial.",
    ],
  },
  M5: {
    id: "guide.m5",
    title: "M5 — Yamazumi",
    objective:
      "Visualizar e ajustar a distribuição das operações entre postos, comparando a carga de cada posto com o takt de referência.",
    steps: [
      "Crie postos com «+ Adicionar posto» — eles são hipotéticos e pertencem ao cenário.",
      "Atribua operações: arraste um bloco de um posto para outro ou solte na área «Sem posto» para desatribuir.",
      "Alternativa por teclado: selecione o posto de cada operação na tabela «Operações».",
      "Ajuste tempos locais na coluna «Tempo (s)» — o gráfico e a tabela são duas visões do mesmo estudo.",
      "Compare cenários com o seletor «Cenário» e «+ Novo cenário».",
    ],
    interpretation: [
      "Cada coluna é um posto; cada bloco colorido é uma operação proporcional ao seu tempo.",
      "A linha horizontal é o takt — blocos acima dela indicam posto sobrecarregado.",
      "A marcação de carga parcial indica operação sem tempo (UNKNOWN) — a barra mostra só o conhecido.",
      "O gráfico e a tabela refletem o mesmo estado: uma alteração em um aparece no outro.",
    ],
    limitations: [
      "O Yamazumi é uma SIMULATION visual — não é um solver e não substitui a validação técnica da Engenharia.",
      "Sem turno e demanda válidos, a linha de takt não é exibida.",
      "As atribuições valem apenas para o cenário ativo e não alteram o roteiro oficial.",
    ],
  },
} as const;

/** Todos os grupos de entradas curtas — facilita teste de integridade do catálogo. */
export const STUDIO_HELP_GROUPS = {
  source: SOURCE_HELP,
  study: STUDY_HELP,
  production: PRODUCTION_HELP,
  balance: BALANCE_HELP,
  method: METHOD_HELP,
  action: ACTION_HELP,
  state: STATE_HELP,
} as const;
