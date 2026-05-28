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

export function activityPhaseKey(entry: ChatStreamActivityEntry): string {
  return String(entry.phase || entry.group || "atividade").trim() || "atividade";
}

/** Uma linha por fase — a mais recente substitui a anterior (efeito de log). */
export function compactActivityLogForDisplay(
  entries: ChatStreamActivityEntry[],
): ChatStreamActivityEntry[] {
  const latestByPhase = new Map<string, ChatStreamActivityEntry>();
  const phaseOrder: string[] = [];

  for (const entry of entries) {
    const key = activityPhaseKey(entry);

    if (!latestByPhase.has(key)) {
      phaseOrder.push(key);
    }

    latestByPhase.set(key, entry);
  }

  return phaseOrder
    .map((key) => latestByPhase.get(key))
    .filter((entry): entry is ChatStreamActivityEntry => Boolean(entry));
}

/** Linha principal exibida abaixo dos três pontos (etapa ativa ou última do log). */
export function resolveCurrentActivityLine(
  entries: ChatStreamActivityEntry[],
): ChatStreamActivityEntry | null {
  const active = [...entries].reverse().find((entry) => entry.state === "active");

  if (active) {
    return active;
  }

  const compact = compactActivityLogForDisplay(entries);

  return compact[compact.length - 1] ?? null;
}

export function formatActivityLogLine(entry: ChatStreamActivityEntry): string {
  const message = entry.message?.trim();

  if (message) {
    return message;
  }

  const verb = entry.verb?.trim() || "Processando";
  const target = entry.target?.trim();

  return target ? `${verb} ${target}` : verb;
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
