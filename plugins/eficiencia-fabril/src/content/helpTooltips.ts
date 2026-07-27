export const EF_HELP_TOOLTIPS = {
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
      "Turno do apontamento conforme horário de início (1º, 2º ou 3º turno).",
    efficiencyBands:
      "Filtra por faixa de eficiência: na faixa (≥ 50%), eficiência baixa (< 50%) ou fora da faixa (0–199%).",
  },
  kpis: {
    efficiency:
      "Média ponderada da eficiência (%) dos apontamentos válidos no período e filtros aplicados.",
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
      "Meta de produção por hora do roteiro/OP (sem setup): QTD_TOTAL_OP ÷ HY_TEMPOM (fallback G2_TEMPAD/1000). Mesma unidade da quantidade apontada — para confrontar com a eficiência.",
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
