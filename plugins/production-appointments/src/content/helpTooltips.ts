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
  charts: {
    series:
      "Evolução diária das quantidades produzida e perdida em milheiro (MI / H6_QTDPROD) no período. Use o filtro de CT para restringir o traçado.",
  },
  tables: {
    viewModes:
      "Alterne entre resumo por centro de trabalho, lista de apontamentos e agregação por OP na mesma tabela.",
    byWorkCenter:
      "Totais agregados por centro de trabalho no período (quantidades em milheiro). O selo “Inspeção final” marca o CT usado como referência de inspeção.",
    appointments:
      "Lista paginada dos apontamentos individuais. Quantidades produzida/perdida estão em milheiro (como na SH6). Clique na linha para abrir o detalhe da OP.",
    byOp:
      "Resumo por ordem de produção (quantidades em milheiro). Clique na linha para abrir o detalhe da OP com apontamentos, KPIs e exportação.",
  },
} as const;
