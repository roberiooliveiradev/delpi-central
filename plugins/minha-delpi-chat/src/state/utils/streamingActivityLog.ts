import type { ChatStreamActivityEntry } from "../../data/api/chatTypes";
import {
  detectStreamActivityFlow,
  streamActivityAnsweringRemainingPercent,
  streamActivityPipelineTotal,
  streamActivityProgressRemainingTemplate,
} from "../../content/streamActivityContent";

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

/** Todas as etapas em ordem cronológica (painel expandido / diagnóstico). */
export function fullActivityLogForDisplay(
  entries: ChatStreamActivityEntry[],
): ChatStreamActivityEntry[] {
  return [...entries].sort((left, right) => (left.at ?? 0) - (right.at ?? 0));
}

/** Uma linha por fase — a mais recente substitui a anterior (prévia compacta). */
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

  const line = resolveCurrentActivityLine(entries);

  if (line?.message?.trim()) {
    return line.message.trim();
  }

  if (status?.trim()) {
    return status.trim();
  }

  return "Processando sua solicitação...";
}

export function statusMessageToActivityEntry(
  message: string,
  options?: { entryId?: string; phase?: string },
): ChatStreamActivityEntry {
  const trimmed = message.trim();

  return {
    id: options?.entryId ?? `status-${trimmed.toLowerCase().replace(/\s+/g, "-").slice(0, 48)}`,
    message: trimmed,
    phase: options?.phase ?? "status",
    state: "active",
    at: Date.now(),
  };
}

/** Converte eventos `status` do SSE em linhas do painel de atividade. */
export function appendStatusToActivityLog(
  current: ChatStreamActivityEntry[],
  message: string,
): ChatStreamActivityEntry[] {
  const trimmed = message.trim();

  if (!trimmed) {
    return current;
  }

  const withDone = current.map((entry) =>
    activityPhaseKey(entry) === "status" && entry.state === "active"
      ? { ...entry, state: "done" as const }
      : entry,
  );

  return upsertStreamingActivityEntry(
    withDone,
    statusMessageToActivityEntry(trimmed),
  );
}

export function resolveActivityStatusMessage(
  entry: ChatStreamActivityEntry,
  fallback: string | null = null,
): string | null {
  if (entry.state !== "active") {
    return fallback;
  }

  const headline = entry.message?.trim();

  if (headline) {
    return headline;
  }

  if (entry.phase === "think") {
    return "Pensando...";
  }

  if (entry.phase === "plan") {
    return "Planejando novos passos...";
  }

  if (entry.phase === "prepare") {
    return "Preparando contexto...";
  }

  if (entry.phase === "rag") {
    return "Consultando base de conhecimento...";
  }

  if (entry.phase === "web_search") {
    return "Pesquisando na internet...";
  }

  return fallback;
}

function resolveExplicitRemainingPercent(
  entries: ChatStreamActivityEntry[],
): number | null {
  const ordered = fullActivityLogForDisplay(entries);

  for (const entry of [...ordered].reverse()) {
    const remaining = entry.progress?.remainingPercent;

    if (typeof remaining === "number" && Number.isFinite(remaining)) {
      return Math.max(0, Math.min(99, Math.round(remaining)));
    }
  }

  return null;
}

function estimateRemainingPercent(entries: ChatStreamActivityEntry[]): number {
  const ordered = fullActivityLogForDisplay(entries);
  const flow = detectStreamActivityFlow(ordered);
  const totalSteps = streamActivityPipelineTotal(flow);
  const completed = ordered.filter(
    (entry) => entry.state === "done" || entry.state === "failed",
  ).length;
  const hasActive = ordered.some((entry) => entry.state === "active");
  const advanced = completed + (hasActive ? 0.65 : 0);
  const completeRatio = Math.min(0.92, advanced / Math.max(totalSteps, 1));

  return Math.max(5, Math.round((1 - completeRatio) * 100));
}

/** Percentual restante estimado enquanto o turno ainda não entrou na prosa final. */
export function resolveStreamingRemainingPercent(
  entries: ChatStreamActivityEntry[],
  options: { isActive: boolean; isAnswering: boolean },
): number | null {
  if (!options.isActive || entries.length === 0) {
    return null;
  }

  if (options.isAnswering) {
    return streamActivityAnsweringRemainingPercent();
  }

  return resolveExplicitRemainingPercent(entries) ?? estimateRemainingPercent(entries);
}

export function formatStreamingRemainingLine(
  entries: ChatStreamActivityEntry[],
  options: { isActive: boolean; isAnswering: boolean },
): string | null {
  const remaining = resolveStreamingRemainingPercent(entries, options);

  if (remaining === null) {
    return null;
  }

  return streamActivityProgressRemainingTemplate(remaining);
}
