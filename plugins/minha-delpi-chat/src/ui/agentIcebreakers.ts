import { DEFAULT_AGENT_ICEBREAKERS } from "./chatHomeStarters";
import {
  formatShortcutTemplateForDisplay,
  hasShortcutPlaceholders,
  type ShortcutFieldId,
} from "./chatShortcutPrompt";

/** Limites de quebra-gelos na home do agente e no builder. */
export const AGENT_ICEBREAKER_MAX_COUNT = 6;
export const AGENT_ICEBREAKER_MAX_CHARS = 72;

export type AgentIcebreakerTemplate = {
  label: string;
  template: string;
};

/** Modelos com campos editáveis `{{campo}}` — mesmo padrão da home do chat. */
export const AGENT_ICEBREAKER_TEMPLATES: AgentIcebreakerTemplate[] = [
  { label: "Consultar produto", template: "me fale do produto {{productCode}}" },
  { label: "Ver estoque", template: "qual o estoque do produto {{productCode}}?" },
  { label: "Pesquisar na web", template: "pesquise na web sobre {{searchQuery}}" },
  { label: "Capacidades", template: "o que você pode fazer?" },
  { label: "Corrigir texto", template: "corrija o texto abaixo:\n\n{{textContent}}" },
];

/** Campos inseríveis no editor (token → rótulo curto). */
export const AGENT_ICEBREAKER_PLACEHOLDER_FIELDS: Array<{
  id: ShortcutFieldId;
  label: string;
}> = [
  { id: "productCode", label: "Código do produto" },
  { id: "searchQuery", label: "Termo de pesquisa" },
  { id: "textContent", label: "Texto livre" },
  { id: "period", label: "Período" },
  { id: "emailRecipient", label: "Destinatário" },
  { id: "emailSubject", label: "Assunto" },
];

export function buildIcebreakerPlaceholderToken(fieldId: string): string {
  return `{{${fieldId}}}`;
}

export function normalizeAgentIcebreakers(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, AGENT_ICEBREAKER_MAX_COUNT);
}

/** Valor efetivo na home: configurados ou padrão corporativo. */
export function resolveAgentIcebreakersForDisplay(metadata: unknown): string[] {
  const configured = normalizeAgentIcebreakers(
    metadata && typeof metadata === "object" && !Array.isArray(metadata)
      ? (metadata as Record<string, unknown>).icebreakers
      : undefined,
  );

  return configured.length > 0 ? configured : [...DEFAULT_AGENT_ICEBREAKERS];
}

/** Estado inicial do builder — espelha o que o usuário vê na home quando vazio. */
export function resolveAgentIcebreakersForEditor(metadata: unknown): string[] {
  const configured = normalizeAgentIcebreakers(
    metadata && typeof metadata === "object" && !Array.isArray(metadata)
      ? (metadata as Record<string, unknown>).icebreakers
      : undefined,
  );

  if (configured.length > 0) {
    return configured;
  }

  return [...DEFAULT_AGENT_ICEBREAKERS];
}

export function agentIcebreakersUseDefaults(metadata: unknown): boolean {
  return normalizeAgentIcebreakers(
    metadata && typeof metadata === "object" && !Array.isArray(metadata)
      ? (metadata as Record<string, unknown>).icebreakers
      : undefined,
  ).length === 0;
}

export { formatShortcutTemplateForDisplay, hasShortcutPlaceholders };

export function clampIcebreakerDraft(value: string): string {
  return value.slice(0, AGENT_ICEBREAKER_MAX_CHARS);
}

/** Texto exibido no card (pode truncar; o clique envia o template com `{{campo}}`). */
export function formatIcebreakerForDisplay(
  text: string,
  maxChars: number = AGENT_ICEBREAKER_MAX_CHARS,
): string {
  const trimmed = formatShortcutTemplateForDisplay(text);

  if (trimmed.length <= maxChars) {
    return trimmed;
  }

  return `${trimmed.slice(0, Math.max(0, maxChars - 1)).trimEnd()}…`;
}

/** Classe de densidade do grid conforme a quantidade de sugestões. */
export function getIcebreakerGridDensityClass(count: number): string {
  if (count <= 3) {
    return "mdc-chat-agent-home__icebreakers--few";
  }

  if (count === 4) {
    return "mdc-chat-agent-home__icebreakers--quad";
  }

  return "mdc-chat-agent-home__icebreakers--many";
}
