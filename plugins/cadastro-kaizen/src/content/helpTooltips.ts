export const KAIZEN_HELP_TOOLTIPS = {
  sections: {
    identification: "Dados que identificam o kaizen: título, filial, setor e categoria da melhoria.",
    process:
      "Contexto do processo: o que era feito antes, qual o problema, o que mudou e o resultado esperado.",
    participants:
      "Quem conduziu e apoiou o kaizen. O primeiro responsável aparece como principal nos relatórios.",
    stage:
      "Estágio operacional (status) e datas de implantação/descontinuação. A mudança de status gera uma revisão.",
    savings:
      "Parâmetros e economia calculada pela API. A economia estimada é comparada com a realizada (efetividade).",
    evidences:
      "Registro visual do processo. Anexe fotos do Antes e Depois, PDFs, planilhas e documentos, ou um link externo.",
    revisions:
      "Histórico de versões do kaizen. Cada melhoria, correção ou mudança de status cria uma revisão numerada com vigência.",
    improvements:
      "Cada melhoria é uma versão do processo com sua própria economia, evidências e validade de 1 ano. Lançar uma nova melhoria num kaizen implantado renova o aniversário e recomeça a contagem de ganhos.",
    changelog:
      "Registro de alterações do kaizen como um todo, para auditoria: linha do tempo de eventos e trilha de governança imutável.",
    audit:
      "Trilha de governança imutável (append-only): criação, mudanças de status e exclusão, com autor e data.",
  },
  fields: {
    title: "Nome curto e objetivo da melhoria (ex.: 'Suporte para tablet no carrinho').",
    branch: "Filial onde o kaizen foi implantado.",
    sector: "Área ou setor responsável pela melhoria.",
    category: "Classificação da melhoria (segurança, qualidade, produtividade, ergonomia…).",
    processDescription: "Como o processo funcionava antes da melhoria.",
    problemDescription: "Problema, desperdício ou risco que motivou o kaizen.",
    improvementDescription: "O que foi alterado no processo.",
    expectedResult: "Ganho esperado com a melhoria (qualitativo ou quantitativo).",
    status:
      "Estágio do kaizen: em andamento, implantado, descontinuado ou cancelado. Mudar o status registra uma revisão.",
    dateImplemented:
      "Data em que a melhoria entrou em operação. A partir dela conta a validade de 1 ano da economia.",
    savingsType:
      "Como a economia é medida: tempo (segundos/ocorrências), material, financeira fixa, qualitativa ou mista.",
    realizedDailySavings:
      "Economia diária efetivamente medida após a implantação. Usada para calcular a efetividade vs. a estimativa.",
    savingsValidity:
      "O kaizen contabiliza ganhos financeiros por 1 ano a partir da implantação; depois disso deixa de somar no run-rate.",
  },
  evidence: {
    upload: "Arraste um ou vários arquivos, ou clique para escolher na pasta. Depois defina a etapa de cada um e envie.",
    stage: "Antes / Depois documentam a transformação; Geral para anexos que não são comparativos.",
    link: "Use para referenciar um arquivo ou página externa em vez de anexar o binário.",
  },
  improvements: {
    launch:
      "Registra uma nova versão do processo com economia e datas próprias. A partir da data informada conta uma nova validade de 1 ano para os ganhos.",
    periodGain:
      "Soma dos ganhos de todas as melhorias vigentes no intervalo, respeitando a validade de 1 ano de cada uma.",
    currentSavings:
      "Economia que está sendo contabilizada hoje: a melhoria vigente dentro da sua validade de 1 ano.",
  },
} as const;
