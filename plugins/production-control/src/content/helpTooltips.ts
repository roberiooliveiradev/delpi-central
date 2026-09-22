export const helpTooltips = {
  home: "Painel inicial do PCP: OTD da filial no mês, pedidos a faturar até hoje (estoque/faturado), volume de PAs e fila de OPs atrasadas.",
  productionVolume:
    "Agregação da quantidade produzida de PAs (última operação do roteiro SG2 — entrada em estoque). No modo Dia: mês corrente com média só em dias úteis. No modo Mês × ano ant.: jan→hoje em buckets mensais comparado ao mesmo período do ano anterior.",
  problemAnalysis:
    "Grade de detectores de exceção da fábrica. Cada cartão roda uma regra sobre os dados do TOTVS; abra o cartão para ver os registros que precisam de ação.",
  incompleteOrderSets:
    "Compara a estrutura do produto raiz (vigente na emissão da OP mãe) com as OPs criadas no mesmo conjunto. Falta = intermediário da estrutura sem OP. Sobra = OP de produto fora da estrutura. Matéria-prima não entra.",
  quantityMismatches:
    "Compara a quantidade de cada intermediário com OP no conjunto à necessidade da estrutura para a quantidade da OP mãe. Abaixo = OP filha menor que o esperado. Acima = OP filha maior. Só entram códigos que já existem no conjunto; falta de OP fica no detector de conjuntos incompletos.",
  uncoveredDemand:
    "Mesma regra da aba Demanda: saldo aberto sem estoque nem OP suficiente (sem cobertura), ou OP prevista só depois da entrega ao cliente. Atrasadas com buraco também aparecem aqui.",
  sharedStructureIntermediates:
    "Intermediários PI/PA da estrutura vigente hoje que aparecem em mais de um PA com apontamento produtivo nos últimos 12 meses. Alteração de engenharia nesse código impacta todos os acabados listados.",
  machineLoad:
    "Fila de operações alocadas (SH8) congelada por filial e período. A fila de todos os CTs é carregada de uma vez, então trocar de aba é imediato. O status «em produção» vem da HZA e se atualiza sozinho a cada 30 s, sem recarregar a fila. «Já apontada» (linha tachada / Limpar fila) só vale quando o saldo da própria operação acabou — apontamento parcial continua na fila. O saldo do cabeçalho da OP só muda na última operação do roteiro. Use Atualizar para regenerar a programação a partir do TOTVS. O rastreio localiza o conjunto (C2_NUM) ou o produto (PA) em todos os CTs.",
  machineLoadLocate:
    "Conjunto = C2_NUM (6 primeiros dígitos da OP completa). Ex.: 10840401003 inclui todas as OPs 108404…. Produto (PA) lista os conjuntos daquele acabado.",
  branch: "Filial TOTVS usada na consulta (Santa Catarina ou Espírito Santo).",
  materials:
    "Três recortes de matéria-prima: excesso de SC1 (documento inteiro já coberto depois do ESTSEG), solicitações insuficientes (cobertura + SC1 não chega no estoque de segurança) e consulta de ruptura no conjunto do PA (extrato saldo + pedidos − empenhos). Não elimina no TOTVS.",
  deliveryMap:
    "OPs mãe de PA com saldo em aberto, agrupadas pela data prevista de entrega. O primeiro bloco reúne hoje e atrasadas. Observações vêm do TOTVS (C2_OBS). MP-OK e Feedback são marcações manuais do PCP. A barra de progresso carrega só nas 3 primeiras tabelas (hoje+atrasadas primeiro); demais datas ficam sem barra. Linha riscada só quando o conjunto atinge 100%. A lista congela até clicar em Atualizar.",
  reports:
    "Relatórios operacionais do Portal PCP. A entrada lista cards do catálogo; ao abrir um card você entra na página do relatório, com voltar ao catálogo. Saldos: na filial 01 só códigos 9…; na 02 códigos 8… e 9…. Ordens de produção: padrão em aberto (sem data real de fim). Para OPs encerradas, filtra também pela data real de fim (C2_DATRF). Colunas: nº da OP, produto, emissão, início, entrega, quantidade, saldo e observações.",
  productModels:
    "Anexe um arquivo .glb ao código do produto da ordem de produção (PI ou PA). No cockpit, o operador vê o 3D na operação daquele produto; o desenho PDF continua sendo o do PA.",
} as const;
