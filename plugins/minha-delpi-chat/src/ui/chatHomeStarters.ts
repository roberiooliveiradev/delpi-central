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
    query: "corrija o texto abaixo:\n\n{{textContent}}",
  },
  {
    label: "Tom mais formal",
    query: "deixe mais formal o texto abaixo:\n\n{{textContent}}",
  },
  {
    label: "Traduzir",
    query: "traduza para inglês o texto abaixo:\n\n{{textContent}}",
  },
  {
    label: "Resumir",
    query: "resuma em tópicos o texto abaixo:\n\n{{textContent}}",
  },
  {
    label: "E-mail",
    query: "escreva um e-mail formal para {{emailRecipient}} sobre {{emailSubject}}",
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
