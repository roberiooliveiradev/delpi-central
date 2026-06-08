import { normalizeShortcutTemplate } from "./chatShortcutPrompt";

export type ChatHomeStarter = {
  label: string;
  query: string;
};

/** IDs de atalhos da home que exigem agente com actions (espelha API onboarding). */
export const OPERATIONAL_HOME_STARTER_IDS = new Set([
  "product",
  "stock",
  "supplier",
  "structure",
  "sales",
  "purchases",
  "data",
  "kpi",
]);

const OPERATIONAL_HIGHLIGHT_FEATURE_IDS = new Set(["product_lookup"]);

export function isOperationalHomeStarter(context: {
  starterId?: string | null;
  query?: string | null;
  featureId?: string | null;
}): boolean {
  const starterId = String(context.starterId ?? "").trim().toLowerCase();

  if (OPERATIONAL_HOME_STARTER_IDS.has(starterId)) {
    return true;
  }

  const featureId = String(context.featureId ?? "").trim();

  if (featureId && OPERATIONAL_HIGHLIGHT_FEATURE_IDS.has(featureId)) {
    return true;
  }

  const normalized = normalizeShortcutTemplate(String(context.query ?? "").trim()).toLowerCase();

  return normalized.includes("{{productcode}}");
}

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
  {
    label: "Carta formal",
    query: "crie uma carta formal solicitando autorização",
  },
  {
    label: "Ata de reunião",
    query: "transforme estas anotações em ata de reunião:\n\n{{textContent}}",
  },
  {
    label: "ELI5",
    query: "explique {{searchQuery}} como se eu tivesse 5 anos",
  },
  {
    label: "Documentação",
    query: "transforme a explicação abaixo em documentação técnica:\n\n{{textContent}}",
  },
];

/** Quebra-gelos padrão na home do agente (sem código fixo). */
export const DEFAULT_AGENT_ICEBREAKERS: string[] = [
  "me fale do produto {{productCode}}",
  "qual o estoque do produto {{productCode}}?",
  "pesquise na web sobre {{searchQuery}}",
  "o que você pode fazer?",
];
