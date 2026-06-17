import type { ChatMessage } from "../../../data/api/chatTypes";

export type ChatTimelineItem =
  | { type: "day"; key: string; label: string }
  | { type: "message"; key: string; message: ChatMessage };

function startOfDay(value: Date): Date {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date;
}

function getDayKey(iso: string | undefined): string {
  const date = iso ? new Date(iso) : new Date();

  if (Number.isNaN(date.getTime())) {
    return startOfDay(new Date()).toISOString().slice(0, 10);
  }

  return startOfDay(date).toISOString().slice(0, 10);
}

export function formatTimelineDayLabel(iso: string | undefined): string {
  const date = iso ? new Date(iso) : new Date();

  if (Number.isNaN(date.getTime())) {
    return "Hoje";
  }

  const today = startOfDay(new Date());
  const messageDay = startOfDay(date);
  const diffDays = Math.round(
    (today.getTime() - messageDay.getTime()) / (24 * 60 * 60 * 1000),
  );

  if (diffDays === 0) {
    return "Hoje";
  }

  if (diffDays === 1) {
    return "Ontem";
  }

  if (diffDays > 1 && diffDays < 7) {
    return date.toLocaleDateString("pt-BR", { weekday: "long" });
  }

  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: messageDay.getFullYear() !== today.getFullYear() ? "numeric" : undefined,
  });
}

export function formatMessageTime(iso: string | undefined): string {
  const date = iso ? new Date(iso) : new Date();

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function buildChatTimelineItems(messages: ChatMessage[]): ChatTimelineItem[] {
  const items: ChatTimelineItem[] = [];
  let lastDayKey: string | null = null;

  for (const message of messages) {
    const dayKey = getDayKey(message.created_at);

    if (dayKey !== lastDayKey) {
      items.push({
        type: "day",
        key: `day-${dayKey}`,
        label: formatTimelineDayLabel(message.created_at),
      });
      lastDayKey = dayKey;
    }

    items.push({
      type: "message",
      key: message.id,
      message,
    });
  }

  return items;
}
