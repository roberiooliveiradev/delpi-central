export type ChatHomeStarter = {
  label: string;
  query: string;
};

/** Chips operacionais na home (sem código fixo — preenchimento no clique). */
export const CHAT_OPERATIONAL_HOME_STARTERS: ChatHomeStarter[] = [
  { label: "Consultar produto", query: "me fale do produto {{productCode}}" },
  { label: "Ver estoque", query: "qual o estoque do produto {{productCode}}?" },
  { label: "Buscar fornecedor", query: "quem fornece o produto {{productCode}}?" },
  { label: "Ver vendas", query: "mostre vendas do produto {{productCode}}" },
  { label: "Pesquisar na web", query: "pesquise na web sobre {{searchQuery}}" },
  { label: "O que você pode fazer?", query: "o que você pode fazer?" },
];

export const CHAT_TEXT_HOME_STARTERS: ChatHomeStarter[] = [
  {
    label: "Corrigir texto",
    query: "corrija: segue em anexo os documento solicitado",
  },
  {
    label: "Tom mais formal",
    query: "deixe mais formal: preciso que você envie isso ainda hoje",
  },
  {
    label: "Traduzir",
    query: "traduza para inglês: precisamos confirmar o prazo de entrega",
  },
  { label: "Resumir", query: "resuma em tópicos o texto abaixo" },
  {
    label: "E-mail",
    query: "escreva um e-mail cobrando retorno do fornecedor sobre prazo",
  },
];

/** União legada (home/help). */
export const CHAT_HOME_STARTERS: ChatHomeStarter[] = [
  ...CHAT_OPERATIONAL_HOME_STARTERS,
  ...CHAT_TEXT_HOME_STARTERS,
];

/** Quebra-gelos padrão na home do agente (sem código fixo). */
export const DEFAULT_AGENT_ICEBREAKERS: string[] = [
  "me fale do produto {{productCode}}",
  "qual o estoque do produto {{productCode}}?",
  "pesquise na web sobre {{searchQuery}}",
  "o que você pode fazer?",
];
