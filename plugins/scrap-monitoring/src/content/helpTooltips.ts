/** Textos dos balões de ajuda (HelpTooltip) — domínio scrap-monitoring. */

export const SCRAP_HELP_TOOLTIPS = {
  filters: {
    dateStart:
      "Início do período filtrado. Afeta totais do período, rankings e a tabela de registros.",
    dateEnd:
      "Fim do período filtrado. Também define o dia do KPI «Refugo dia» e o mês calendário do KPI «Refugo no mês».",
    mp: "Filtra por código de matéria-prima (produto apontado na perda SBC).",
    pa: "Filtra pelo produto acabado da ordem de produção vinculada ao refugo.",
    op: "Filtra pela ordem de produção (OP) do apontamento de refugo.",
    motivo: "Filtra pelo motivo cadastrado em CYO (BC_MOTIVO).",
    centroTrabalho:
      "Filtra pelo centro de trabalho / recurso (BC_RECURSO), ex.: CT-23.",
  },
  kpis: {
    valorDia:
      "Soma do valor de refugo (R$) apenas no dia de data final (dataFim), com os demais filtros aplicados.",
    valorMes:
      "Soma do valor de refugo (R$) no mês calendário completo de dataFim (do dia 1º ao último dia do mês). Não depende do intervalo dataInicio–dataFim dentro desse mês.",
    totalPeriodo:
      "Soma do valor de refugo (R$) entre data inicial e data final, com os filtros opcionais aplicados.",
    ocorrencias:
      "Quantidade de linhas de apontamento de refugo (BC_TIPO = R) no período filtrado.",
    quantidade:
      "Soma das quantidades apontadas (BC_QUANT) no período filtrado.",
    semCusto:
      "Registros cujo custo unitário ficou zerado (sem B2_CM1 nem B1_CUSTD), impossibilitando o cálculo em R$.",
  },
  charts: {
    motivo:
      "Distribuição do valor de refugo (R$) por motivo no período filtrado, com percentual sobre o total do ranking.",
    serie:
      "Evolução do valor de refugo (R$) ao longo do período. Até 62 dias agrega por dia; períodos maiores agregam por mês.",
    materiaPrima:
      "Top 10 matérias-primas por valor de refugo (R$) no período filtrado (código + descrição).",
    produtoAcabado:
      "Top 10 produtos acabados (via OP) por valor de refugo (R$) no período filtrado (código + descrição).",
    centroTrabalho:
      "Ranking de centros de trabalho por valor de refugo (R$) no período filtrado.",
    colaborador:
      "Top 10 colaboradores por valor de refugo (R$) no período filtrado.",
  },
  table: {
    section:
      "Listagem paginada dos apontamentos de refugo no período. Clique na linha para abrir o detalhe.",
    data: "Data do apontamento de perda (BC_DATA).",
    op: "Ordem de produção vinculada ao apontamento.",
    pa: "Produto acabado da OP (via SC2).",
    mp: "Código da matéria-prima / produto da perda (BC_PRODUTO).",
    descricao: "Descrição do produto no cadastro SB1.",
    motivo: "Motivo do refugo (descrição CYO ou código BC_MOTIVO).",
    ct: "Centro de trabalho / recurso (BC_RECURSO).",
    colaborador: "Operador associado ao apontamento (SYS_USR).",
    qtd: "Quantidade apontada (BC_QUANT) e unidade de medida.",
    valor: "Valor em R$ (quantidade × custo unitário médio ou custo padrão).",
  },
  pagination: {
    info: "Paginação server-side: tamanho da página e navegação disparam nova consulta na API.",
    pageSize: "Define quantos registros são buscados por página.",
    jump: "Digite o número da página e pressione Enter ou saia do campo.",
    jumpEmpty: "Informe o número da página.",
    jumpInvalid: "Número de página inválido.",
    jumpBelowMin: "A página mínima é 1.",
    previous: "Volta uma página mantendo filtros e tamanho da lista.",
    next: "Avança uma página mantendo filtros e tamanho da lista.",
  },
} as const;
