export const II_HELP = {
  partySearch:
    "Busque pelo código, nome ou CNPJ no cadastro TOTVS. Se o destinatário não existir, providencie o cadastro antes de solicitar.",
  partyMissing:
    "Destinatário não cadastrado. Providencie o cadastro de cliente ou fornecedor no Protheus antes de enviar a solicitação.",
  openSalesOrders:
    "Pedidos de venda em aberto deste cliente na filial da solicitação. Marque as linhas a faturar; a quantidade não pode passar do saldo.",
  openSalesOrdersEmpty:
    "Nenhum pedido de venda em aberto nesta filial. Informe os itens manualmente.",
  carrierSearch:
    "Busque pelo código, nome reduzido, razão social ou CNPJ no cadastro TOTVS (SA4). O nome de uso é o reduzido (A4_NREDUZ). Transportadora é opcional.",
  carrierMissing:
    "Nenhuma transportadora encontrada. Confira o cadastro SA4 no Protheus ou deixe em branco se não houver.",
  observation: "Informações complementares para o Faturamento, se houver.",
  checklistFooter:
    "A conferência reflete o que já foi preenchido nas etapas anteriores. Em caso de dúvida, confirme com o Faturamento antes de enviar.",
};

export const II_SHEET = {
  party: "Destinatário da nota",
  invoice: "Cabeçalho da nota",
  freight: "Transporte",
  extras: "Complemento",
  items: "Itens para lançar",
  situation: "Situação",
  history: "Histórico",
  actions: "Atendimento",
  hints: {
    partyCode: "Informe este código no destinatário da nota.",
    partyStore: "Informe a loja junto com o código do destinatário.",
    taxId: "CNPJ ou CPF do cadastro, para conferência.",
    invoiceType: "Tipo da nota de saída.",
    salesOrder: "Pedido de venda a faturar, quando a origem for PV.",
    freightMode: "Modalidade de frete da nota (CIF ou FOB).",
    carrier: "Código da transportadora, se houver.",
    weight: "Peso bruto informado na solicitação.",
    volumes: "Quantidade de volumes.",
    stockWriteOff: "Se Sim, dê baixa no almoxarifado 01.",
  },
} as const;

export const WIZARD_STEPS = [
  { id: "recipient", label: "Destinatário" },
  { id: "invoiceType", label: "Tipo de NF" },
  { id: "items", label: "Itens" },
  { id: "freight", label: "Transporte" },
  { id: "extras", label: "Adicionais" },
  { id: "review", label: "Conferência" },
] as const;

export function wizardStepIndex(id: (typeof WIZARD_STEPS)[number]["id"]): number {
  return WIZARD_STEPS.findIndex((step) => step.id === id);
}

export const CHECKLIST_ITEMS = [
  { key: "recipient", label: "Destinatário identificado ou cadastrado." },
  { key: "item_codes", label: "Código dos itens informado." },
  { key: "quantity_price", label: "Quantidade e valor unitário conferidos." },
  { key: "stock_write_off", label: "Baixa de estoque definida." },
  { key: "invoice_type", label: "Tipo de nota fiscal selecionado." },
  { key: "freight_mode", label: "Modalidade de transporte informada." },
  { key: "weight_volumes", label: "Peso e volumes informados." },
] as const;
