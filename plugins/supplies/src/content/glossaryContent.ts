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
      "On-Time Delivery — pontualidade de entrega frente ao compromisso. Não confundir com a lista de atrasos do dia.",
  },
  {
    term: "ESTSEG",
    meaning:
      "Estoque de segurança — cobertura mínima planejada e déficit. Não é o saldo físico de estoque.",
  },
  {
    term: "SC",
    meaning: "Solicitação de compras — pedido interno de compra no escopo de centro de custo e filial.",
  },
  {
    term: "PC",
    meaning: "Pedido de compra — documento com fornecedor após a SC.",
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
