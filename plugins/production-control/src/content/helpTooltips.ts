export const helpTooltips = {
  home: "Painel inicial do PCP: OTD da filial no mês, pedidos a faturar até hoje (estoque/faturado), volume de PAs e fila de OPs atrasadas.",
  productionVolume:
    "Agregação da quantidade produzida de PAs (última operação do roteiro SG2 — entrada em estoque). No modo Dia: mês corrente com média só em dias úteis. No modo Mês × ano ant.: jan→hoje em buckets mensais comparado ao mesmo período do ano anterior.",
  problemAnalysis:
    "Grade de detectores de exceção da fábrica. Cada cartão roda uma regra sobre os dados do TOTVS; abra o cartão para ver os registros que precisam de ação.",
  incompleteOrderSets:
    "Compara a estrutura do produto raiz (SG1, vigente na emissão da OP mãe) com as OPs criadas no mesmo conjunto. Falta = intermediário da estrutura sem OP. Sobra = OP de produto fora da estrutura. Matéria-prima não entra.",
  machineLoad:
    "Fila de operações alocadas (SH8) congelada por filial e período. O status «em produção» vem ao vivo da HZA. Use Atualizar para regenerar a programação a partir do TOTVS. O rastreio localiza o conjunto (C2_NUM) ou o produto (PA) em todos os CTs.",
  machineLoadLocate:
    "Conjunto = C2_NUM (6 primeiros dígitos da OP completa). Ex.: 10840401003 inclui todas as OPs 108404…. Produto (PA) lista os conjuntos daquele acabado.",
  branch: "Filial TOTVS usada na consulta (Santa Catarina ou Espírito Santo).",
  materials:
    "Três recortes de matéria-prima: excesso de SC1 (documento inteiro já coberto depois do ESTSEG), solicitações insuficientes (cobertura + SC1 não chega no estoque de segurança) e consulta de ruptura no conjunto do PA (extrato saldo + pedidos − empenhos). Não elimina no TOTVS.",
  deliveryMap:
    "OPs mãe de PA com saldo em aberto, agrupadas pela data prevista de entrega. O primeiro bloco reúne hoje e atrasadas. Observações vêm do TOTVS (C2_OBS). MP-OK e Feedback são marcações manuais do PCP. A barra de progresso carrega primeiro hoje+atrasadas e, em seguida, OPs com entrega em até 5 dias; demais datas ficam sem barra. Linha riscada só quando o conjunto atinge 100%. A lista congela até clicar em Atualizar.",
} as const;
