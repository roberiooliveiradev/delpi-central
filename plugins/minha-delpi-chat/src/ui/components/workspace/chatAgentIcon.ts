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

export const DEFAULT_AGENT_ICON: AgentIconName = "bot";

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

export function normalizeAgentIcon(icon: string | null | undefined): AgentIconName {
  const trimmed = String(icon ?? "").trim();

  if (!trimmed) {
    return DEFAULT_AGENT_ICON;
  }

  const normalized = trimmed.toLowerCase();

  if (isAgentIconName(normalized)) {
    return normalized;
  }

  return DEFAULT_AGENT_ICON;
}
