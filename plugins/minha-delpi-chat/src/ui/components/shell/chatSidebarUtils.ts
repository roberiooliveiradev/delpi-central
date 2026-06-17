import type { ChatSession } from "../../../data/api/chatTypes";

export type SessionGroup = {
  label: string;
  sessions: ChatSession[];
};

export function getSessionDate(session: ChatSession): Date | null {
  const value = session.updated_at || session.created_at;

  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date;
}

export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function getSessionGroupLabel(session: ChatSession): string {
  const date = getSessionDate(session);

  if (!date) {
    return "Sem data";
  }

  const today = startOfDay(new Date());
  const target = startOfDay(date);
  const diffMs = today.getTime() - target.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffDays === 0) {
    return "Hoje";
  }

  if (diffDays === 1) {
    return "Ontem";
  }

  if (diffDays <= 7) {
    return "Últimos 7 dias";
  }

  if (diffDays <= 30) {
    return "Últimos 30 dias";
  }

  return "Anteriores";
}

export function groupSessions(sessions: ChatSession[]): SessionGroup[] {
  const order = [
    "Hoje",
    "Ontem",
    "Últimos 7 dias",
    "Últimos 30 dias",
    "Anteriores",
    "Sem data",
  ];
  const groups = new Map<string, ChatSession[]>();

  for (const session of sessions) {
    const label = getSessionGroupLabel(session);
    groups.set(label, [...(groups.get(label) ?? []), session]);
  }

  return order
    .map((label) => ({
      label,
      sessions: groups.get(label) ?? [],
    }))
    .filter((group) => group.sessions.length > 0);
}

export function formatSessionDate(value?: string): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
