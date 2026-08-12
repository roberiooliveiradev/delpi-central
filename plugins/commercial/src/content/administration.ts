/**
 * Textos do hub Administração (Painel · Carteiras · Membros).
 */
export const ADMINISTRATION_CONTENT = {
  breadcrumbRoot: "Administração",
  subnavAriaLabel: "Seções da Administração",
  panel: {
    navLabel: "Painel",
    eyebrow: "Administração",
    title: "Painel",
    description: "Cadastre carteiras, gerencie membros e monitore cobertura.",
    refresh: "Atualizar",
    loading: "Carregando resumo das carteiras.",
    loadError: "Não foi possível carregar o resumo da Administração.",
    actionsTitle: "Ações rápidas",
    openPortfolios: "Abrir Carteiras",
    openMembers: "Membros",
    newPortfolio: "Nova carteira",
    bulkTransfer: "Transferência em massa",
    newPortfolioHint: "Abre a lista de carteiras para cadastrar uma nova.",
    bulkTransferHint: "Abre a lista de carteiras para iniciar a transferência.",
  },
  portfolios: {
    navLabel: "Carteiras",
  },
  members: {
    navLabel: "Membros",
    eyebrow: "Administração",
    title: "Membros",
    description: "Pessoas com acesso às carteiras do Portal.",
    placeholder:
      "O roster de membros por pessoa estará nesta aba. Enquanto isso, gerencie membros no detalhe de cada carteira.",
    openPortfolios: "Ir para Carteiras",
  },
  metrics: {
    total: "Carteiras",
    active: "Ativas",
    inactive: "Inativas",
    customers: "Clientes",
    overlapping: "Overlapping",
    uncovered: "Sem cobertura",
  },
} as const;
