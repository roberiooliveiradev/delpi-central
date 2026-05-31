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
  { label: "Corrigir texto", query: "corrija: segue em anexo os documento solicitado" },
  { label: "E-mail formal", query: "escreva um e-mail formal cobrando retorno do fornecedor sobre prazo" },
  { label: "Quem é você?", query: "quem é você?" },
  { label: "Como usar o chat?", query: "como usar o chat?" },
  { label: "Pesquisa na web", query: "como faço pesquisa na web?" },
  { label: "Lousa", query: "como uso a lousa?" },
];

export const CHAT_TEXT_HOME_STARTERS: ChatHomeStarter[] = [
  { label: "Corrigir texto", query: "corrija: segue em anexo os documento solicitado" },
  { label: "Tom mais formal", query: "deixe mais formal: preciso que você envie isso ainda hoje" },
  { label: "Traduzir", query: "traduza para inglês: precisamos confirmar o prazo de entrega" },
  { label: "Resumir", query: "resuma em tópicos o texto abaixo" },
  { label: "E-mail", query: "escreva um e-mail cobrando retorno do fornecedor sobre prazo" },
];

export const DEFAULT_AGENT_ICEBREAKERS: string[] = [
  "O que você consegue consultar?",
  "Visão 360° do produto 10080001",
  "Estoque do produto 10080001",
  "Quem fornece o produto 10080001?",
  "Onde esse componente é usado?",
  "Vendas dos últimos 30 dias",
];
