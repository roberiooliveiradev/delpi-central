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
      "Evolução diária das quantidades produzida e perdida no período. Use o filtro de CT para restringir o traçado.",
  },
  tables: {
    byWorkCenter:
      "Totais agregados por centro de trabalho no período. O selo “Inspeção final” marca o CT usado como referência de inspeção.",
    appointments: "Lista paginada dos apontamentos individuais do período.",
    byOp: "Resumo por ordem de produção: contagem de apontamentos, CTs e quantidade produzida.",
  },
} as const;
