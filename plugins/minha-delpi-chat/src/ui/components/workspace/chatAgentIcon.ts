import { isLucideIconName } from "../../utils/lucideIconResolver";

export const AGENT_ICON_OPTIONS = [
  "bot",
  "sparkles",
  "brain",
  "message-square",
  "search",
  "chart-line",
  "shield",
  "zap",
  "box",
  "users",
] as const;

export type AgentIconName = (typeof AGENT_ICON_OPTIONS)[number];

export const DEFAULT_AGENT_ICON = "bot";

export const AGENT_ICON_LABELS: Record<AgentIconName, string> = {
  bot: "Assistente",
  sparkles: "Criativo",
  "message-square": "Conversa",
  brain: "Análise",
  search: "Pesquisa",
  "chart-line": "Dados",
  shield: "Segurança",
  zap: "Rápido",
  box: "Integração",
  users: "Equipe",
};

export function isAgentIconName(value: string): value is AgentIconName {
  return (AGENT_ICON_OPTIONS as readonly string[]).includes(value);
}

function normalizeIconSlug(icon: string | null | undefined): string {
  return String(icon ?? "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-");
}

export function normalizeAgentIcon(icon: string | null | undefined): string {
  const normalized = normalizeIconSlug(icon);

  if (!normalized) {
    return DEFAULT_AGENT_ICON;
  }

  if (isLucideIconName(normalized)) {
    return normalized;
  }

  return DEFAULT_AGENT_ICON;
}
