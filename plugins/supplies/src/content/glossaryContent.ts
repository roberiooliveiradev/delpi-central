/**
 * Glossário mínimo P0 do Portal Suprimentos (HELP-AND-ONBOARDING).
 * Sem path técnico / operationId.
 */
export type GlossaryEntry = {
  term: string;
  meaning: string;
};

export const GLOSSARY_CONTENT: readonly GlossaryEntry[] = [
  {
    term: "OTD",
    meaning:
      "On-Time Delivery — pontualidade de entrega frente ao compromisso. Indicador analítico (Visão geral / página OTD). Não confundir com a lista operacional Entregas / Atrasos (recebimentos MP no período selecionado).",
  },
  {
    term: "Data de digitação do recebimento",
    meaning:
      "Data em que o recebimento foi digitado/entrado no sistema. Em Entregas / Atrasos, o filtro de período usa essa data — não a data prometida nem a emissão do pedido de compra.",
  },
  {
    term: "ESTSEG",
    meaning:
      "Estoque de segurança — cobertura mínima planejada e déficit. Não é o saldo físico de estoque.",
  },
  {
    term: "Saldo físico",
    meaning:
      "Quantidade atual registrada no estoque do ERP para a combinação produto, unidade e armazém. Não significa saldo disponível.",
  },
  {
    term: "SC",
    meaning: "Solicitação de compras — pedido interno de compra no escopo de centro de custo e filial.",
  },
  {
    term: "Fornecedor",
    meaning:
      "Empresa do pedido de compra. Nas listas aparece com avatar de iniciais. A ficha própria está reservada e ainda não navega.",
  },
  {
    term: "Solicitante",
    meaning:
      "Pessoa que abriu a SC. Nas listas aparece com avatar de iniciais. A ficha própria está reservada e ainda não navega.",
  },
  {
    term: "PC",
    meaning:
      "Pedido de compra — documento com fornecedor após a SC. A ficha mostra itens, entrega prometida, recebimentos e a SC de origem de cada item.",
  },
  {
    term: "CPV",
    meaning: "Custo dos produtos vendidos — indicador de custo no recorte analítico.",
  },
  {
    term: "Giro",
    meaning:
      "Rotatividade do estoque. Pode aparecer em vezes (quantas voltas no período) ou em meses de cobertura — não misture as duas leituras.",
  },
  {
    term: "Filial 01",
    meaning: "Unidade Santa Catarina no escopo TOTVS do Portal.",
  },
  {
    term: "Filial 02",
    meaning: "Unidade Espírito Santo no escopo TOTVS do Portal.",
  },
] as const;
