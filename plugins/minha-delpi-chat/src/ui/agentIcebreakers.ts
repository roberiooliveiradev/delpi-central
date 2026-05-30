/** Limites de quebra-gelos na home do agente e no builder. */
export const AGENT_ICEBREAKER_MAX_COUNT = 6;
export const AGENT_ICEBREAKER_MAX_CHARS = 72;

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

export function clampIcebreakerDraft(value: string): string {
  return value.slice(0, AGENT_ICEBREAKER_MAX_CHARS);
}

/** Texto exibido no card (pode truncar; o clique envia o texto completo). */
export function formatIcebreakerForDisplay(
  text: string,
  maxChars: number = AGENT_ICEBREAKER_MAX_CHARS,
): string {
  const trimmed = text.trim();

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

  if (count <= 4) {
    return "mdc-chat-agent-home__icebreakers--medium";
  }

  return "mdc-chat-agent-home__icebreakers--many";
}
