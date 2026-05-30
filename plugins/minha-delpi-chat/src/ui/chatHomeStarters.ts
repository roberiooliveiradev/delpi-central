export type ChatHomeStarter = {
  label: string;
  query: string;
};

export const CHAT_HOME_STARTERS: ChatHomeStarter[] = [
  { label: "O que você pode fazer?", query: "o que você pode fazer?" },
  { label: "Consultar produto", query: "me fale do produto 10080001" },
  { label: "Ver estoque", query: "qual o estoque do produto 10080001?" },
  { label: "Buscar fornecedor", query: "quem fornece o produto 10080001?" },
  { label: "Ver vendas", query: "mostre vendas do produto 10080001" },
  { label: "Quem é você?", query: "quem é você?" },
];

export const DEFAULT_AGENT_ICEBREAKERS: string[] = [
  "O que você consegue consultar?",
  "Visão 360° do produto 10080001",
  "Estoque do produto 10080001",
  "Quem fornece o produto 10080001?",
  "Onde esse componente é usado?",
  "Vendas dos últimos 30 dias",
];
