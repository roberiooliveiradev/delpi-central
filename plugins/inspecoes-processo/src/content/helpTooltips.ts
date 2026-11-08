export const IP_HELP = {
  period: {
    startDate: "Data inicial das medições de ensaio (QPR). A consulta usa a data da medição.",
    endDate: "Data final das medições de ensaio (QPR), inclusive.",
  },
  auditoria: {
    period: "Selecione a data inicial e final da produção (inclusive), no máximo 31 dias. Os dados são agrupados por filial, data, turno, operador, OP e operação.",
    shift:
      "O turno considera o horário de início do apontamento, conforme Eficiência Fabril. Indicadores e tabela respeitam período e turno; o status filtra só a tabela.",
    export: "Exporta todos os registros que correspondem ao período, turno e status selecionados, inclusive outras páginas. Até 10 mil linhas por arquivo.",
    missing: "Sem inspeção cadastrada: OP/operação sem exigência de inspeção na revisão vigente da OP. Não é pendência atribuída ao operador.",
  },
};
