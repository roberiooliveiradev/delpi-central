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
  hint?: string;
};

/** Modelos com campos editáveis `{{campo}}` — mesmo padrão da home do chat. */
export const AGENT_ICEBREAKER_TEMPLATES: AgentIcebreakerTemplate[] = [
  { label: "Consultar produto", template: "me fale do produto {{productCode}}" },
  { label: "Ver estoque", template: "qual o estoque do produto {{productCode}}?" },
  { label: "Pesquisar na web", template: "pesquise na web sobre {{searchQuery}}" },
  {
    label: "Capacidades",
    template: "o que você pode fazer?",
    hint: "Ferramentas, dados e limites do agente",
  },
  { label: "Corrigir texto", template: "corrija o texto abaixo:\n\n{{textContent}}" },
];

export type IcebreakerVisualKind =
  | "product"
  | "stock"
  | "web"
  | "capabilities"
  | "text"
  | "generic";

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

export type IcebreakerCardPresentation = {
  title: string;
  subtitle?: string;
  example?: string;
};

/** Rótulo curto + exemplo para cards da home do agente. */
export function resolveIcebreakerCardPresentation(
  template: string,
): IcebreakerCardPresentation {
  const normalized = template.trim();
  const known = AGENT_ICEBREAKER_TEMPLATES.find(
    (item) => item.template === normalized,
  );
  const display = formatShortcutTemplateForDisplay(normalized);
  const exampleMatch = display.match(/\s+Ex\.:\s+(.+)$/i);
  const example = exampleMatch?.[1]?.trim();

  if (known) {
    return {
      title: known.label,
      subtitle: example ?? known.hint,
      example,
    };
  }

  if (exampleMatch) {
    return {
      title: display.replace(/\s+Ex\.:\s+.+$/i, "").trim(),
      subtitle: exampleMatch[1].trim(),
      example: exampleMatch[1].trim(),
    };
  }

  return { title: display };
}

/** Variante visual do card (ícone e cor de destaque). */
export function resolveIcebreakerVisualKind(template: string): IcebreakerVisualKind {
  const normalized = template.trim();
  const known = AGENT_ICEBREAKER_TEMPLATES.find((item) => item.template === normalized);

  if (known) {
    if (known.template.includes("{{productCode}}") && /estoque/i.test(known.template)) {
      return "stock";
    }

    if (known.template.includes("{{productCode}}")) {
      return "product";
    }

    if (known.template.includes("{{searchQuery}}")) {
      return "web";
    }

    if (known.template.includes("{{textContent}}")) {
      return "text";
    }

    if (/o que você pode fazer/i.test(known.template)) {
      return "capabilities";
    }
  }

  if (normalized.includes("{{productCode}}") && /estoque/i.test(normalized)) {
    return "stock";
  }

  if (normalized.includes("{{productCode}}")) {
    return "product";
  }

  if (normalized.includes("{{searchQuery}}")) {
    return "web";
  }

  if (normalized.includes("{{textContent}}")) {
    return "text";
  }

  return "generic";
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
