/**
 * Textos de cobertura / overlapping / gap de carteiras (E6.1 / E6.4 / gap).
 */
export const PORTFOLIO_COVERAGE_CONTENT = {
  filterAll: "Todas",
  filterActive: "Ativas",
  filterInactive: "Inativas",
  filterOverlapping: "Com overlapping",
  filterOverlappingEmpty:
    "Nenhuma carteira ativa com cliente em mais de uma carteira.",
  filterUncovered: "Sem cobertura",
  filterUncoveredEmpty: "Todos os clientes com pedido aberto estão em alguma carteira ativa.",
  filterUncoveredUnavailable:
    "A lista de clientes sem cobertura ainda não está disponível (universo de pedidos em aberto).",
  filterUncoveredPanelTitle: "Clientes sem cobertura",
  filterUncoveredPanelSubtitle:
    "Clientes com pedido em aberto que não estão em nenhuma carteira ativa.",
  filterHint:
    "Filtre por situação, overlapping ou clientes com pedido aberto fora de qualquer carteira.",
  overlappingBadge: "Overlapping",
  overlappingAlsoIn: "Também em",
  sharedBadge: "Compartilhado",
  alsoInPrefix: "Também em",
  linkWarningTitle: "Cliente em outra carteira",
  heroOverlapping: "Overlapping",
  heroUncovered: "Sem cobertura",
  colCustomerCode: "Código/loja",
  colCustomerName: "Cliente",
  colOpenValue: "Valor aberto",
} as const;
