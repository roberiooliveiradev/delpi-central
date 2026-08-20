export const helpTooltips = {
  home: "Painel inicial do PCP: OTD da filial no mês corrente, volume de atraso e fila de OPs para ação.",
  problemAnalysis:
    "Fila de exceções montada a partir das ordens PCP atrasadas. Crítico: 7 dias ou mais de atraso.",
  machineLoad:
    "Fila de operações alocadas (SH8) congelada por filial e período. O status «em produção» vem ao vivo da HZA. Use Atualizar para regenerar a programação a partir do TOTVS. O rastreio localiza o conjunto (C2_NUM) ou o produto (PA) em todos os CTs.",
  machineLoadLocate:
    "Conjunto = C2_NUM (6 primeiros dígitos da OP completa). Ex.: 10840401003 inclui todas as OPs 108404…. Produto (PA) lista os conjuntos daquele acabado.",
  branch: "Filial TOTVS usada na consulta (Santa Catarina ou Espírito Santo).",
} as const;
