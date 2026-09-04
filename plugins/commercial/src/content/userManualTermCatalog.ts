/**
 * Catálogo de termos já usados no Portal e nos helps (`CM_HELP` / métricas).
 * Fonte da seção Ajuda → Catálogo de termos. Espelhar o Manual markdown.
 */
import { BILLING_NATURE_CONTENT } from "./billingNature";
import { CM_HELP, OPEN_ORDER_DELIVERY_DATE_HELP } from "./helpTooltips";
import { OVERVIEW_METRIC_BY_ID } from "./overviewMetricsCatalog";

export type UserManualTermEntry = {
  term: string;
  meaning: string;
  applies: string;
};

export type UserManualTermGroup = {
  id: string;
  title: string;
  entries: readonly UserManualTermEntry[];
};

const OO = CM_HELP.openOrders;
const CUST = CM_HELP.customers;
const OV = CM_HELP.overview;
const SHELL = CM_HELP.shell;

export const USER_MANUAL_TERM_CATALOG: readonly UserManualTermGroup[] = [
  {
    id: "screens",
    title: "Telas e recortes",
    entries: [
      {
        term: "Escopo",
        meaning: SHELL.scope,
        applies: "Chip no topo de todas as telas",
      },
      {
        term: "Início",
        meaning: SHELL.navHome,
        applies: "Menu superior · launcher",
      },
      {
        term: "Visão geral",
        meaning: SHELL.navOverview,
        applies: "Menu superior",
      },
      {
        term: "Meus pedidos",
        meaning: SHELL.navOrders,
        applies: "Menu superior · bancada operacional",
      },
      {
        term: "Minha Carteira",
        meaning: SHELL.navCustomers,
        applies: "Menu superior · lista de clientes",
      },
      {
        term: "Conta",
        meaning: CM_HELP.customerDetail.header,
        applies: "Minha Carteira → clique no cliente",
      },
      {
        term: "Minhas tarefas",
        meaning: SHELL.navMyTasks,
        applies: "Menu superior",
      },
      {
        term: "Sala de interação",
        meaning: SHELL.navInteractionRooms,
        applies: "Menu superior · painel na ficha",
      },
      {
        term: "Administração",
        meaning: SHELL.navAdmin,
        applies: "Menu superior (quem administra)",
      },
      {
        term: "Ajuda",
        meaning: SHELL.navHelp,
        applies: "Menu superior · Início → Manual do usuário",
      },
      {
        term: "SC / ES",
        meaning: OO.filterBranch,
        applies: "Filtros de Meus pedidos e Visão geral",
      },
      {
        term: "Filtro de clientes",
        meaning: CM_HELP.analytics.filterCustomer,
        applies: "Visão geral · OTD · Oportunidades",
      },
      {
        term: "Membership",
        meaning: "Você está vinculado a uma carteira. Sem vínculo, a lista pode vir consolidada.",
        applies: "Escopo · Minha Carteira · Administração",
      },
    ],
  },
  {
    id: "documents",
    title: "Pedido, oportunidade e proposta",
    entries: [
      {
        term: "Pedido",
        meaning: "Linha de pedido de venda em aberto — operação e fábrica.",
        applies: "Meus pedidos · Conta → Pedidos",
      },
      {
        term: "Oportunidade (OV)",
        meaning: CM_HELP.analytics.opportunitiesPage,
        applies: "Início → Oportunidades (Visão colaborador/oportunidade) · Conta → Oportunidades",
      },
      {
        term: "Visão (Oportunidades)",
        meaning: CM_HELP.analytics.opportunitiesView,
        applies: "Início → Oportunidades — hero",
      },
      {
        term: "Proposta (documento)",
        meaning: "Documento ADY + PDF para o cliente. Não é a lista de OV nem o pedido.",
        applies: "Início → Propostas",
      },
      {
        term: "Carteira",
        meaning: "Conjunto de clientes + membros (vendedores) no Delpi.",
        applies: "Escopo · Minha Carteira · Administração",
      },
      {
        term: "Compartilhado",
        meaning: "O cliente está em mais de uma carteira ativa.",
        applies: "Badge na Minha Carteira e na Conta",
      },
    ],
  },
  {
    id: "dates",
    title: "Datas e Incoterm",
    entries: [
      {
        term: "Incoterm",
        meaning:
          "Condição comercial (EXW, FOB, CIF) que define se o cliente busca ou se a Delpi entrega — e o que a Data de entrega representa.",
        applies: "Help da coluna Data de entrega · proposta (frete)",
      },
      {
        term: "EXW",
        meaning: "Ex Works: o cliente busca na origem. Data de entrega = data na expedição.",
        applies: "Data de entrega · frete da proposta",
      },
      {
        term: "FOB",
        meaning:
          "Free On Board: frete por conta do comprador. Data de entrega = data na expedição.",
        applies: "Data de entrega · frete da proposta",
      },
      {
        term: "CIF",
        meaning:
          "Cost, Insurance and Freight: a Delpi entrega. Data de entrega = saída da empresa.",
        applies: "Data de entrega · frete da proposta",
      },
      {
        term: "Data de entrega",
        meaning: OPEN_ORDER_DELIVERY_DATE_HELP,
        applies: "Meus pedidos · ficha da linha · timeline da OP · Conta",
      },
      {
        term: "Data de despacho",
        meaning: OO.columns.data_despacho,
        applies: "Meus pedidos · ficha da linha",
      },
      {
        term: "Previsão entrega (OP)",
        meaning: OO.columns.previsao_entrega_op,
        applies: "Meus pedidos · ficha da linha",
      },
      {
        term: "Próxima entrega",
        meaning: CUST.columns.proximaEntrega,
        applies: "Minha Carteira · Conta · pedidos da conta",
      },
      {
        term: "Postergado",
        meaning: OO.filterPostponed,
        applies: "Chip / atalho em Meus pedidos",
      },
      {
        term: "Atraso (dias)",
        meaning: OO.columns.atraso_dias,
        applies: "Meus pedidos · chip Atraso · Início",
      },
    ],
  },
  {
    id: "stock",
    title: "Estoque, status e Kanban",
    entries: [
      {
        term: "FIFO",
        meaning: OO.columns.no_estoque,
        applies: "Meus pedidos · Pode faturar · ficha da linha",
      },
      {
        term: "Estoque alocado",
        meaning: OO.columns.no_estoque,
        applies: "Coluna em Meus pedidos · indicadores da ficha",
      },
      {
        term: "Cobertura",
        meaning: OO.columns.cobertura,
        applies: "Meus pedidos · ficha da linha",
      },
      {
        term: "Saldo",
        meaning: OO.columns.saldo,
        applies: "Meus pedidos · Conta",
      },
      {
        term: "Valor aberto",
        meaning: OO.columns.valor_aberto,
        applies: "Meus pedidos · Minha Carteira · Visão geral (carteira em aberto)",
      },
      {
        term: "Status estoque",
        meaning: OO.columns.status,
        applies: "Coluna Status em Meus pedidos",
      },
      {
        term: "Pode faturar",
        meaning: OO.kpiCanInvoice,
        applies: "Chip · badge da nav · Kanban · status da linha",
      },
      {
        term: "Estoque parcial",
        meaning: OO.kpiPartialStock,
        applies: "Filtro de estoque · status da linha",
      },
      {
        term: "Sem estoque",
        meaning: "Linha sem estoque alocado suficiente para o saldo em aberto.",
        applies: "Filtro de estoque · status da linha",
      },
      {
        term: "Próximos",
        meaning: OO.kanbanUpcoming,
        applies: "Board Kanban de Meus pedidos",
      },
      {
        term: "Em andamento",
        meaning: OO.kanbanInProgress,
        applies: "Board Kanban de Meus pedidos",
      },
      {
        term: "Pronto para faturar",
        meaning: OO.kanbanReadyToInvoice,
        applies: "Board Kanban · notificação (quem tem permissão)",
      },
      {
        term: "OP",
        meaning: "Ordem de produção usada na previsão da linha (alocação FIFO).",
        applies: "Ficha da linha · ficha da OP",
      },
    ],
  },
  {
    id: "kpis",
    title: "Indicadores e faturamento",
    entries: [
      {
        term: OVERVIEW_METRIC_BY_ID.rol.label,
        meaning: OVERVIEW_METRIC_BY_ID.rol.tooltip,
        applies: "Visão geral · Gestão no Início",
      },
      {
        term: "Meta",
        meaning:
          "Meta dos Indicadores Estratégicos, proporcional aos dias do intervalo. No consolidado (unidade Todas), a meta exibida é a agregação SC+ES pelo SI — não inventada no Portal. Mês incompleto não usa a meta cheia.",
        applies: "Visão geral (ROL vs meta)",
      },
      {
        term: OVERVIEW_METRIC_BY_ID.open_portfolio.label,
        meaning: OVERVIEW_METRIC_BY_ID.open_portfolio.tooltip,
        applies: "Visão geral — snapshot agora, ignora o período dos outros KPIs",
      },
      {
        term: "Faturamento",
        meaning: OV.glossaryOpenVsBilled,
        applies: "Visão geral · Minha Carteira (série, Fat. 12 meses, tendência, share, mix e ABC)",
      },
      {
        term: "Família de produto",
        meaning:
          "Grupo Protheus (B1_GRUPO). Nos painéis Faturamento e ABC da Minha Carteira filtra o mix e o ABC; o toggle Produto|Família agrega a tabela de mix.",
        applies: "Minha Carteira → Faturamento · Minha Carteira → ABC",
      },
      {
        term: "Mercado interno / externo",
        meaning:
          "CFOP com primeiro dígito 5 ou 6 = interno (Brasil); 7 = exportação. Países de destino vêm do cadastro do cliente nas linhas de exportação. Filtro compartilhado entre Faturamento e ABC.",
        applies: "Minha Carteira → Faturamento · Minha Carteira → ABC (filtro Mercado)",
      },
      {
        term: "ABC de clientes",
        meaning:
          "Lista ordenada por participação no faturamento do período (Pareto). Não usa faixas A/B/C e não é o Ranking de crescimento/queda YoY.",
        applies: "Minha Carteira → ABC",
      },
      {
        term: BILLING_NATURE_CONTENT.gross.shortLabel,
        meaning: CUST.billingNature,
        applies: "Toggle Natureza na Minha Carteira",
      },
      {
        term: BILLING_NATURE_CONTENT.net.shortLabel,
        meaning: OV.billingNatureNet,
        applies: "ROL na Visão geral · Natureza na Minha Carteira",
      },
      {
        term: OVERVIEW_METRIC_BY_ID.portfolio_billing_share.label,
        meaning: OVERVIEW_METRIC_BY_ID.portfolio_billing_share.tooltip,
        applies: "Visão geral · Minha Carteira (com permissão)",
      },
      {
        term: OVERVIEW_METRIC_BY_ID.gap_to_target.label,
        meaning: OVERVIEW_METRIC_BY_ID.gap_to_target.tooltip,
        applies: "Visão geral",
      },
      {
        term: OVERVIEW_METRIC_BY_ID.open_portfolio_horizon.label,
        meaning: OVERVIEW_METRIC_BY_ID.open_portfolio_horizon.tooltip,
        applies: "Visão geral — clique abre Meus pedidos",
      },
      {
        term: OVERVIEW_METRIC_BY_ID.closing_rate.label,
        meaning: OVERVIEW_METRIC_BY_ID.closing_rate.tooltip,
        applies: "Visão geral · funil",
      },
      {
        term: OVERVIEW_METRIC_BY_ID.funnel.label,
        meaning: OVERVIEW_METRIC_BY_ID.funnel.tooltip,
        applies: "Visão geral",
      },
      {
        term: "OTD",
        meaning: CM_HELP.analytics.otdPage,
        applies: "Início → Pontualidade (OTD) · KPI na Visão geral",
      },
      {
        term: "Fat. 12 meses",
        meaning: CUST.columns.billed12m,
        applies: "Minha Carteira · Conta",
      },
    ],
  },
  {
    id: "portfolio",
    title: "Minha Carteira — foco e tendência",
    entries: [
      {
        term: "Foco",
        meaning: CUST.filterFocus,
        applies: "Filtro Foco na Minha Carteira",
      },
      {
        term: "Tendência",
        meaning: CUST.trend,
        applies: "Coluna e filtro Tendência na Minha Carteira",
      },
      {
        term: "Em aberto",
        meaning: CUST.columns.valorTotalAberto,
        applies: "Coluna na Minha Carteira",
      },
      {
        term: "Atrasos",
        meaning: CUST.columns.quantidadePedidosAtrasados,
        applies: "Coluna na Minha Carteira",
      },
      {
        term: "Última venda",
        meaning: CUST.columns.lastPurchaseDate,
        applies: "Minha Carteira · Conta",
      },
      {
        term: "Sem venda 60d",
        meaning: CUST.kpiNoSale60,
        applies: "Foco e KPI da Minha Carteira",
      },
    ],
  },
];

export function flattenUserManualTermCatalog(): readonly UserManualTermEntry[] {
  return USER_MANUAL_TERM_CATALOG.flatMap((group) => group.entries);
}
