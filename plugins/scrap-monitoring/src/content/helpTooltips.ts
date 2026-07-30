/** Textos dos balões de ajuda (HelpTooltip) — domínio scrap-monitoring. */

export const SCRAP_HELP_TOOLTIPS = {
  filters: {
    dateStart:
      "Início do período filtrado. Afeta totais do período, rankings e a tabela de registros.",
    dateEnd:
      "Fim do período filtrado. Também define o dia do KPI «Refugo dia» e o mês calendário do KPI «Refugo no mês».",
    mp: "Filtra por código de matéria-prima (produto apontado na perda SBC). Produtos de terceiro (B1_TPMAT = Sim) já são excluídos pela API.",
    pa: "Filtra pelo produto acabado da ordem de produção vinculada ao refugo.",
    op: "Filtra pela ordem de produção (OP) do apontamento de refugo.",
    motivo: "Filtra pelo motivo cadastrado em CYO (BC_MOTIVO).",
    centroTrabalho:
      "Filtra pelo centro de trabalho / recurso (BC_RECURSO), ex.: CT-23.",
  },
  kpis: {
    valorDia:
      "Soma do valor de refugo (R$) apenas no dia de data final (dataFim), com os demais filtros aplicados. Não inclui produto de terceiro (B1_TPMAT = 2).",
    valorMes:
      "Soma do valor de refugo (R$) no mês calendário completo de dataFim (do dia 1º ao último dia do mês). Não depende do intervalo dataInicio–dataFim dentro desse mês. Exclui produto de terceiro.",
    totalPeriodo:
      "Soma do valor de refugo (R$) entre data inicial e data final, com os filtros opcionais aplicados. Exclui produto de terceiro (cadastro SB1).",
    ocorrencias:
      "Quantidade de linhas de apontamento de refugo (BC_TIPO = R) no período filtrado, sem produto de terceiro.",
    quantidade:
      "Soma das quantidades apontadas (BC_QUANT) no período filtrado, sem produto de terceiro.",
    semCusto:
      "Registros cujo custo unitário ficou zerado (sem B2_CM1 do almoxarifado 01 nem B1_CUSTD), impossibilitando o cálculo em R$.",
  },
  charts: {
    motivo:
      "Distribuição do valor de refugo (R$) por motivo no período filtrado, com percentual sobre o total do ranking. Sem produto de terceiro.",
    serie:
      "Evolução do valor de refugo (R$) ao longo do período. Até 62 dias agrega por dia; períodos maiores agregam por mês. Sem produto de terceiro.",
    materiaPrima:
      "Top 10 matérias-primas por valor de refugo (R$) no período filtrado (código + descrição). Produtos de terceiro não entram.",
    produtoAcabado:
      "Top 10 produtos acabados (via OP) por valor de refugo (R$) no período filtrado (código + descrição).",
    centroTrabalho:
      "Ranking de centros de trabalho por valor de refugo (R$) no período filtrado.",
    colaborador:
      "Top 10 colaboradores por valor de refugo (R$) no período filtrado.",
  },
  actions: {
    refresh:
      "Recarrega KPIs, gráficos, opções de filtro e a tabela com o período e filtros atuais.",
  },
  detail: {
    identification:
      "Dados de filial, data, OP e códigos de produto associados ao apontamento.",
    cause:
      "Motivo do refugo e contexto operacional (centro de trabalho e colaborador).",
    financial:
      "Quantidade apontada, custo unitário usado no cálculo e valor total em R$.",
    unitCost:
      "Custo unitário do almoxarifado (B2_CM1 no B2_LOCAL=01) ou, se ausente, custo padrão (B1_CUSTD). O local 99 é fábrica e não entra no cálculo.",
    product:
      "Matéria-prima da perda e produto acabado da OP, com descrições do cadastro SB1.",
  },
  table: {
    section:
      "Listagem paginada dos apontamentos de refugo no período (sem produto de terceiro — B1_TPMAT = Sim). Clique na linha para abrir o detalhe.",
    data: "Data do apontamento de perda (BC_DATA).",
    op: "Ordem de produção vinculada ao apontamento.",
    pa: "Produto acabado da OP (via SC2).",
    mp: "Código da matéria-prima / produto da perda (BC_PRODUTO).",
    descricao: "Descrição do produto no cadastro SB1.",
    motivo: "Motivo do refugo no formato SIGLA - significado (código BC_MOTIVO + descrição CYO).",
    ct: "Centro de trabalho / recurso (BC_RECURSO).",
    colaborador: "Operador associado ao apontamento (SYS_USR).",
    qtd: "Quantidade apontada (BC_QUANT) e unidade de medida.",
    valor: "Valor em R$ (quantidade × B2_CM1 do almoxarifado 01, ou B1_CUSTD).",
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
