import type { ChatStreamActivityEntry } from "../../data/api/chatTypes";

export function upsertStreamingActivityEntry(
  current: ChatStreamActivityEntry[],
  entry: ChatStreamActivityEntry,
): ChatStreamActivityEntry[] {
  const index = current.findIndex((item) => item.id === entry.id);

  if (index >= 0) {
    const next = [...current];
    next[index] = entry;
    return next;
  }

  return [...current, entry];
}

export function resolveStreamingHeadline(
  status: string | null,
  entries: ChatStreamActivityEntry[],
): string {
  const active = [...entries].reverse().find((entry) => entry.state === "active");

  if (active?.message?.trim()) {
    return active.message.trim();
  }

  if (status?.trim()) {
    return status.trim();
  }

  return "Processando sua solicitação...";
}
