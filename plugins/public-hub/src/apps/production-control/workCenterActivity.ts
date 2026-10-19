import type { MesWorkCenterTodayItem } from "./api";

/**
 * Atividade do posto (Etapa 3) — derivados puros e testáveis do payload
 * diário MES. Toda a formatação de horário é fixada em America/Sao_Paulo,
 * independente do fuso do tablet.
 */

const SP_TZ = "America/Sao_Paulo";

const timeFormatter = new Intl.DateTimeFormat("pt-BR", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: SP_TZ,
});

const dayFormatter = new Intl.DateTimeFormat("en-CA", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  timeZone: SP_TZ,
});

/** HH:MM sempre no civil de São Paulo — fuso do tablet nunca decide. */
export function formatTimeHmSp(iso: string | null): string {
  if (!iso) return "—";
  const ms = Date.parse(iso);
  if (!Number.isFinite(ms)) return "—";
  return timeFormatter.format(new Date(ms));
}

/** Chave do dia civil SP (YYYY-MM-DD) — detecta a virada do dia. */
export function spCivilDayKey(at: Date = new Date()): string {
  return dayFormatter.format(at);
}

export type ActivitySegment = {
  item: MesWorkCenterTodayItem;
  /** Posição inicial/final em % da janela [from, to]. */
  leftPct: number;
  widthPct: number;
};

/**
 * Segmentos da faixa visual posicionados pelo tempo real na janela.
 * Intervalos sem evento MES não viram segmento — ficam neutros.
 */
export function timelineSegments(
  items: MesWorkCenterTodayItem[],
  fromIso: string,
  toIso: string,
): ActivitySegment[] {
  const from = Date.parse(fromIso);
  const to = Date.parse(toIso);
  if (!Number.isFinite(from) || !Number.isFinite(to) || to <= from) return [];
  const span = to - from;
  const segments: ActivitySegment[] = [];
  for (const item of items) {
    const start = Date.parse(item.startedAt);
    if (!Number.isFinite(start)) continue;
    const end = item.endedAt != null ? Date.parse(item.endedAt) : to;
    const clipStart = Math.max(start, from);
    const clipEnd = Math.min(end, to);
    if (clipEnd <= clipStart) continue;
    segments.push({
      item,
      leftPct: ((clipStart - from) / span) * 100,
      widthPct: Math.max(0.4, ((clipEnd - clipStart) / span) * 100),
    });
  }
  return segments;
}

/** A parada tem identidade suficiente para classificar pelo contrato real. */
export function classifiableDowntime(
  item: MesWorkCenterTodayItem,
): { runId: string; downtimeId: string } | null {
  const id = item.downtime?.id;
  if (!id || !item.runId) return null;
  return { runId: item.runId, downtimeId: id };
}

/** Motivo pendente: a regra oficial é pendingReason do backend. */
export function isReasonPending(item: MesWorkCenterTodayItem): boolean {
  return item.downtime?.pendingReason === true;
}
