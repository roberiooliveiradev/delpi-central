export const QUALITY_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores de qualidade: PPM interno/externo, kaizens, auditorias 5S e não conformidades.",
    refresh: "Recarrega PPM, kaizens e auditorias com os filtros atuais.",
  },
  filters: {
    dateStart: "Início do período para PPM, kaizens e auditorias 5S.",
    dateEnd: "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Filial TOTVS. Vazio = todas; múltiplas filiais restringem o recorte dos indicadores.",
  },
  kpis: {
    ppmInternal:
      "Parts Per Million interno: devoluções internas por milhão de unidades produzidas no período.",
    ppmExternal:
      "PPM externo: devoluções de clientes por milhão de unidades faturadas.",
    kaizenOpen: "Quantidade de kaizens abertos ou em andamento no recorte.",
    kaizenClosed: "Kaizens concluídos no período filtrado.",
    kaizenTotal: "Total de kaizens registrados no período conforme filtros aplicados.",
    kaizenSavings: "Soma da economia reportada pelos kaizens no período.",
    audit5sScore: "Nota média das auditorias 5S realizadas no período.",
    audit5sCount: "Quantidade de auditorias 5S registradas no recorte.",
    nonconformities: "Total de não conformidades abertas ou registradas no período.",
    ppmDetail: "PPM calculado com base em unidades devolvidas e produzidas/faturadas.",
    ppmReturned: "Quantidade total de unidades devolvidas no período.",
  },
  charts: {
    ppmEvolution: "Evolução temporal do PPM conforme granularidade selecionada.",
    kaizenByStatus: "Distribuição de kaizens por status no período.",
    audit5sEvolution: "Evolução das notas de auditoria 5S ao longo do tempo.",
  },
} as const;
