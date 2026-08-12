export const HELP_TOOLTIPS = {
  pageSubtitle:
    "Remessas recebidas de clientes para beneficiamento e os retornos vinculados pela identidade SB6.",
  filters: {
    branch: "Filial TOTVS autorizada no seu perfil (SC = 01, ES = 02).",
    product: "Código do produto (SB1/SB6). Use junto com a filial para evitar varrer a base.",
    customerReference:
      "Ref. Cliente do cadastro SB1 (B1_REFEREN) — código do produto no cliente, não o SA1.",
    partner: "Código do cliente (SA1) e loja, quando precisar restringir o parceiro.",
    receipt: "Número da NF de recebimento (entrada da remessa).",
    returnNf: "Número da NF de retorno. Filtra remessas que possuam esse retorno.",
    period: "Período de emissão da remessa (não do retorno).",
    status: "Situação da remessa: concluída, parcial ou sem retorno.",
    onlyBalance: "Lista apenas remessas com saldo ainda pendente de devolução.",
    testProducts: "Inclui códigos fictícios configurados na API (padrão 99999999).",
  },
  kpis: {
    total: "Quantidade de remessas únicas no recorte (não soma linhas de retorno).",
    open: "Remessas com saldo pendente (POSSUI_SALDO = S).",
    partial: "Remessas com pelo menos um retorno, mas ainda com saldo.",
    noReturn: "Remessas sem nenhum retorno vinculado.",
    pending: "Soma do saldo atual das remessas abertas. Não some o saldo nas linhas de retorno.",
  },
  table: {
    shipment: "Identidade B6_IDENT da remessa. Relaciona todos os retornos válidos.",
    balance:
      "Saldo atual da remessa (B6_SALDO). Nas linhas de retorno o valor se repete — não some.",
  },
  export:
    "Exporta todas as linhas de retorno do recorte (não só a página). O saldo da remessa se repete em cada linha.",
  detailPdf:
    "Gera o PDF certificado DELPI desta remessa (logo, recebimento e devoluções). Use Imprimir → Salvar como PDF.",
};
