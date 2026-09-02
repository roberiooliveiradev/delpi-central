export const EF_HELP_TOOLTIPS = {
  tabs: {
    efficiency:
      "Indicadores de eficiência operacional e resultado MOD dos apontamentos produtivos no período.",
    unproductiveHours:
      "Paradas de produção apontadas pelos operadores (horas improdutivas PCP) — todos os motivos, não só retrabalho.",
  },
  filters: {
    dateStart:
      "Início do período. KPIs e gráficos usam apontamentos com data de produção a partir desta data.",
    dateEnd:
      "Fim do período. Deve ser igual ou posterior à data início.",
    operator:
      "Filtra por nome do operador. Permite selecionar vários; vazio = todos os operadores do período.",
    op: "Filtra por ordem de produção (OP). Permite múltipla seleção.",
    finishedProduct:
      "Filtra pelo código do produto acabado (PA) da OP mãe. Permite múltipla seleção entre os PAs do período carregado.",
    operation:
      "Filtra pela operação apontada. Só fica disponível após selecionar um ou mais PAs — as opções vêm só desses produtos.",
    workCenter:
      "Filtra por centro de trabalho (CT). Permite múltipla seleção entre os CTs presentes nos dados carregados.",
    shift:
      "Turno do apontamento (API: turno/turno_label por horário de início — 1º, 2º ou 3º).",
    efficiencyBands:
      "Filtra por faixa de eficiência: na faixa (≥ 50%), eficiência baixa (< 50%) ou fora da faixa (0–199%).",
  },
  unproductiveHours: {
    filters: {
      stopReason:
        "Código do motivo de parada (MOTIVO na view TOTVS), por exemplo RT (retrabalho), OT ou MT. Vazio = todos.",
      operatorCode: "Código do operador que apontou a parada. Vazio = todos.",
      resource: "Código do recurso (máquina/posto) da parada. Vazio = todos.",
      costCenter: "Centro de custo associado ao apontamento de parada. Vazio = todos.",
    },
    kpis: {
      totalHours: "Soma das horas improdutivas (paradas) no período e filtros.",
      totalCost: "Soma do valor da parada (R$) no período. O subtítulo mostra o % de horas sem custo.",
      appointments: "Quantidade de apontamentos de parada retornados pela API.",
      topResource: "Recurso com maior volume de horas improdutivas no período.",
      topOperator: "Operador com maior volume de horas improdutivas no período.",
    },
    charts: {
      byStopReason: "Ranking dos motivos de parada por total de horas no período.",
      byOperator: "Ranking dos operadores por total de horas improdutivas.",
      byResource: "Ranking dos recursos por total de horas improdutivas.",
    },
    table: {
      section:
        "Lista paginada das paradas apontadas. Exporta Excel/PDF de todo o resultado filtrado (todas as páginas).",
    },
  },
  kpis: {
    efficiency:
      "Média simples da eficiência (%) dos centros de trabalho (média de cada CT, depois média desses valores). Não é a média dos apontamentos.",
    appointments:
      "Total de apontamentos na tabela após filtros. Inclui contagem de fora da faixa e eficiência baixa no texto auxiliar.",
    modResult:
      "Soma do resultado de mão de obra direta (MOD) no período — lucro ou prejuízo agregado dos apontamentos.",
    hoursGainedLost:
      "Saldo de horas entre tempo previsto e real. Positivo indica economia de tempo; negativo indica perda.",
  },
  charts: {
    efficiencyByDay:
      "Média diária da eficiência (%). Linha de referência em 100% para comparar com o padrão.",
    modByDay:
      "Lucro e prejuízo MOD empilhados por dia de produção no período filtrado.",
    topOperators:
      "Dez operadores com maior eficiência média no período. Passe o mouse para ver o nome completo.",
    efficiencyByCt:
      "Média da eficiência (%) por centro de trabalho. Cores indicam desempenho relativo.",
    modByCt: "Soma do resultado MOD por centro de trabalho no período.",
    hoursByCt:
      "Comparativo de horas previstas e reais nos doze centros com maior tempo real apontado.",
  },
  table: {
    section:
      "Apontamentos do período após filtros. Clique na linha para abrir detalhe com roteiro, estrutura e tempos.",
    dataProducao: "Data de produção registrada no apontamento.",
    horaInicio: "Horário de início do apontamento.",
    horaFinal: "Horário de término do apontamento.",
    qtdApontada: "Quantidade produzida no apontamento.",
    metaPorHora:
      "Meta de produção por hora do snapshot da OP (SHY.HY_TEMPAD, sem setup): 1 ÷ HY_TEMPAD. Ritmo unitário congelado na OP — não muda com apontamentos parciais (HY_TEMPOM/HY_QUANT). Se SHY não tiver TEMPAD, usa HY_QUANT÷HY_TEMPOM; por fim o cadastro SG2. Mesma unidade da quantidade apontada.",
    filial: "Filial TOTVS do registro.",
    op: "Ordem de produção vinculada ao apontamento.",
    produtoAcabado:
      "Código do produto acabado (PA) da OP mãe — LEFT(OP, 6) + 01001 → SC2.C2_PRODUTO.",
    descricaoProduto: "Descrição do produto fabricado no apontamento (pode ser PI).",
    descricaoOperacao:
      "Descrição da operação apontada no roteiro (SG2.G2_DESCRI), mesma base dos tempos previstos.",
    centroTrabalho: "Centro de trabalho (CT) do apontamento.",
    operador: "Nome ou login do operador.",
    eficienciaPercentual:
      "Eficiência calculada para o apontamento. Valores inválidos ou baixos aparecem destacados em Status.",
    resultadoMod: "Resultado financeiro de MOD (lucro/prejuízo) do apontamento.",
    status:
      "OK = na faixa; Eficiência baixa = válido e < 50%; Verificar = fora da faixa 0–199%.",
  },
} as const;
