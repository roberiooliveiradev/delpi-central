/** Textos de ajuda do plugin — não importar de `@delpi/plugin-ui`. */
export const PA_HELP_TOOLTIPS = {
  filters: {
    dateStart:
      "Início do período. KPIs, série e tabelas consideram apontamentos com data neste intervalo.",
    dateEnd:
      "Fim do período. Deve ser igual ou posterior à data inicial.",
    workCenter:
      "Restringe o painel a um centro de trabalho (CT). CTs de inspeção final aparecem identificados na lista.",
    op: "Filtra pela ordem de produção (OP). Deixe vazio para todas as OPs do período.",
    product: "Filtra pelo código do produto. Deixe vazio para todos os produtos.",
  },
  kpis: {
    appointments:
      "Total de apontamentos de produção (SH6, tipo P) no período e filtros selecionados.",
    qtyProduced:
      "Soma da quantidade produzida apontada (H6_QTDPROD), já convertida para peças/UN pela API quando a UM do produto é MI.",
    qtyLost:
      "Soma da quantidade perdida no apontamento (H6_QTDPERD) — peças registradas como perda na operação/CT, convertidas para UN pela API. Não é o módulo de refugos de matéria-prima.",
    opCount:
      "Quantidade de ordens de produção (OP) distintas com pelo menos um apontamento no período.",
    workCenterCount:
      "Quantidade de centros de trabalho (CT) distintos com apontamento no período.",
  },
  charts: {
    series:
      "Evolução diária das quantidades produzida e perdida (já convertidas para peças/UN pela API). Use o filtro de CT para restringir o traçado.",
  },
  columns: {
    workCenter:
      "Centro de trabalho (CT) do apontamento, obtido via recurso SH1 → cadastro SHB.",
    workCenterName: "Nome do centro de trabalho no cadastro SHB.",
    appointmentCount: "Quantidade de apontamentos de produção no agrupamento.",
    qtyProduced:
      "Quantidade produzida (H6_QTDPROD), em peças/UN após conversão pela API.",
    qtyLost:
      "Quantidade perdida no apontamento (H6_QTDPERD), em peças/UN. É a perda registrada junto com o apontamento da OP — não o ranking de refugos de MP.",
    opCount: "Quantidade de OPs distintas no agrupamento.",
    appointmentDate: "Data do apontamento no Protheus (H6_DTAPONT).",
    productionOrder: "Número da ordem de produção (H6_OP).",
    product: "Código do produto apontado, com tipo (B1_TIPO) quando disponível.",
    workCenterCount: "Quantidade de CTs distintos com apontamento nesta OP.",
    period:
      "Primeira e última data de apontamento da OP no período filtrado.",
  },
  tables: {
    viewModes:
      "Alterne entre resumo por centro de trabalho, lista de apontamentos e agregação por OP na mesma tabela.",
    byWorkCenter:
      "Totais agregados por centro de trabalho no período. Clique na linha para abrir o detalhe do CT. O selo “Inspeção final” marca o CT usado como referência de inspeção.",
    appointments:
      "Lista paginada dos apontamentos individuais. Clique na linha para abrir o detalhe da OP.",
    byOp:
      "Resumo por ordem de produção. Clique na linha para abrir o detalhe da OP com apontamentos, KPIs e exportação.",
    ctDetailAppointments:
      "Apontamentos deste centro de trabalho no período. Clique na linha para abrir o detalhe da OP.",
  },
} as const;
