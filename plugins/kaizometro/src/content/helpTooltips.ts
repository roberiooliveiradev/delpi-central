import {
  ANNUAL_BUSINESS_DAYS,
  ANNUAL_SAVINGS_EXPLANATION,
  ANNUAL_SAVINGS_FORMULA_LABEL,
} from "./savingsConstants";

export const KAIZEN_HELP_TOOLTIPS = {
  sections: {
    identification: "Dados que identificam o kaizen: título, unidade, setor e categoria da melhoria.",
    process:
      "Contexto do processo: o que era feito antes, qual o problema, o que mudou e o resultado esperado.",
    participants:
      "Quem conduziu e apoiou o kaizen. O primeiro responsável aparece como principal nos relatórios.",
    stage:
      "Estágio operacional (status) e datas da versão vigente. Editar aqui é uma correção da versão atual — não cria uma nova versão.",
    savings:
      `Parâmetros e economia calculada pela API. Economia/ano = ${ANNUAL_SAVINGS_FORMULA_LABEL} ` +
      `(constante Delpi). A validade de contabilização no painel é outro conceito: ` +
      `1 ano corrido desde a implantação — não use 365 no cálculo da projeção anual.`,
    evidences:
      "Registro visual do processo. Anexe fotos do Antes e Depois, PDFs, planilhas e documentos, ou um link externo.",
    revisions:
      "Histórico de versões do kaizen. Cada melhoria, correção ou mudança de status cria uma revisão numerada com vigência.",
    improvements:
      "Cada versão é uma iteração completa do kaizen, com seus próprios dados, economia, evidências e validade de 1 ano. Só uma versão fica implantada por vez; ao implantar uma nova, a anterior é substituída e para de contabilizar.",
    changelog:
      "Registro de alterações do kaizen como um todo, para auditoria: linha do tempo de eventos e trilha de governança imutável.",
    audit:
      "Trilha de governança imutável (append-only): criação, mudanças de status e exclusão, com autor e data.",
  },
  fields: {
    title: "Nome curto e objetivo da melhoria (ex.: 'Suporte para tablet no carrinho').",
    branch: "Unidade onde o kaizen foi implantado.",
    sector: "Área ou setor responsável pela melhoria.",
    category: "Classificação da melhoria (segurança, qualidade, produtividade, ergonomia…). Selecione uma ou mais categorias ou crie novas digitando no campo.",
    investment: "Valor investido para implantar a melhoria (materiais, mão de obra, dispositivos).",
    dateDiscontinued:
      "Data em que a melhoria deixou de operar, quando aplicável. Interrompe a contabilização dos ganhos.",
    dateIdeaReceived:
      "Data em que a ideia de melhoria foi recebida ou registrada, antes da implantação.",
    dateCommitteeApproved:
      "Data em que o comitê aprovou o kaizen. Obrigatória para o status Aprovado. Define o mês do indicador de quantidade (se vazia em registros legados, usa a data de implantação).",
    notes: "Notas livres, observações e detalhes que não se encaixam nos demais campos.",
    changeReason:
      "Descreva o porquê da correção. O texto fica registrado na trilha de auditoria da versão.",
    processDescription: "Como o processo funcionava antes da melhoria.",
    problemDescription: "Problema, desperdício ou risco que motivou o kaizen.",
    improvementDescription: "O que foi alterado no processo.",
    expectedResult: "Ganho esperado com a melhoria (qualitativo ou quantitativo).",
    status:
      "Estágio da versão vigente: recebido, aprovado (comitê), implantado, descontinuado ou cancelado. Aprovado conta na quantidade sem ganhos; Implantado conta quantidade e ganhos. Alterar aqui corrige a versão atual, sem criar uma nova.",
    dateImplemented:
      "Data em que a melhoria entrou em operação. Obrigatória para o status Implantado. Define a vigência da versão implantada, a validade de 1 ano corrido da economia e os ganhos financeiros.",
    savingsType:
      "Como a economia é medida: tempo (segundos/ocorrências), material, financeira fixa, qualitativa ou mista.",
    realizedDailySavings:
      "Economia diária realizada (medida). Se não informada, usa a estimativa calculada pelos parâmetros. A projeção anual usa este valor × " +
      `${ANNUAL_BUSINESS_DAYS} dias úteis — não × 365.`,
    savingsValidity:
      "Validade (ano corrido): o kaizen contabiliza ganhos no painel por 1 ano a partir da implantação (até a data mostrada). " +
      `Isso é diferente da projeção economia/ano, que multiplica a diária por ${ANNUAL_BUSINESS_DAYS} dias úteis.`,
    estimatedDaily:
      "Economia diária estimada pela API a partir dos parâmetros. Base da projeção anual " +
      `(× ${ANNUAL_BUSINESS_DAYS} dias úteis).`,
    estimatedAnnual:
      `Projeção anual estimada: ${ANNUAL_SAVINGS_FORMULA_LABEL} (constante Delpi de dias úteis). ` +
      `Por quê dias úteis: a operação tipicamente não gera o mesmo ganho em todos os dias do calendário. ` +
      `Não confundir com a validade (1 ano corrido desde a implantação).`,
    realizedAnnual:
      `Projeção anual realizada: realizada/dia × ${ANNUAL_BUSINESS_DAYS} dias úteis (constante Delpi). ` +
      `Sem medição informada, espelha a estimada. Validade de contabilização no painel permanece 1 ano corrido.`,
    effectiveness: "Relação entre a economia realizada e a estimada (quão perto do previsto o ganho ficou).",
  },
  savingsParams: {
    seconds_per_occurrence: "Tempo (em segundos) economizado a cada vez que o processo acontece.",
    occurrences_per_day: "Quantas vezes por dia (útil de operação) o processo/ganho acontece.",
    hourly_cost: "Custo por hora usado para converter o tempo economizado em dinheiro.",
    quantity_saved_per_day: "Quantidade de material economizada por dia (peças, kg, litros…).",
    unit_material_cost: "Custo unitário do material economizado, na mesma unidade da quantidade.",
    fixed_daily_savings:
      `Valor fixo economizado por dia útil. A API projeta o ano com × ${ANNUAL_BUSINESS_DAYS} dias úteis.`,
  },
  formNotes: {
    annualProjection: ANNUAL_SAVINGS_EXPLANATION,
  },
  evidence: {
    upload: "Arraste um ou vários arquivos, ou clique para escolher na pasta. Depois defina a etapa de cada um e envie.",
    stage: "Antes / Depois documentam a transformação; Geral para anexos que não são comparativos.",
    link: "Use para referenciar um arquivo ou página externa em vez de anexar o binário.",
    edit:
      "Altere a descrição, a etapa (Antes/Depois/Geral) ou troque o arquivo/foto mantendo o mesmo registro. A edição fica na própria página — a descrição pode ser longa.",
    description:
      "Texto livre que explica a evidência. Aparece no card e na ficha; use quantas linhas precisar.",
  },
  improvements: {
    launch:
      "Cria uma cópia da versão ativa como rascunho (Recebido) e a seleciona. Edite as seções ali mesmo e, ao final, clique em “Salvar e tornar ativa”. A versão ativa segue contabilizando até lá.",
    periodGain:
      "Soma diária × dias úteis equivalentes no intervalo (dias corridos × 253/365), " +
      "dentro da validade de 1 ano corrido de cada versão — o mesmo critério da economia/ano. " +
      "Na ficha, o intervalo pode incluir dias futuros até o fim da validade (projeção). " +
      "No dashboard, competência futura não projeta ganho ainda não realizado. Rascunhos não contam.",
    currentSavings:
      "Economia contabilizada hoje: a versão implantada vigente, dentro da sua validade de 1 ano corrido. " +
      `O valor “/ ano” exibido usa a projeção ${ANNUAL_SAVINGS_FORMULA_LABEL}.`,
    implement:
      "Torna esta versão a vigente usando a data implantação informada no estágio. A versão implantada anterior passa a Substituída e para de contabilizar.",
    editDraft:
      "Ajusta o rascunho antes de implantar. Só versões Recebido (rascunho) podem ser editadas por aqui.",
  },
  actions: {
    exportPdf:
      "Gera uma ficha A4 de uma página com identificação, datas, economia, narrativa (processo/problema/melhoria/resultado) e equipe da versão selecionada. Abre o diálogo de impressão do navegador — use “Salvar como PDF”. Não inclui fotos de evidência, changelog nem histórico completo de versões.",
  },
} as const;
