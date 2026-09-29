import type { RunTimelineItem } from "./api";

/**
 * Offset entre o relógio local e o relógio do servidor, estimado a partir do
 * `referenceAt` da timeline. O cockpit nunca confia cegamente no relógio do
 * computador do operador.
 */
export function serverClockOffsetMs(referenceAt: string, localNowMs: number): number {
  const server = Date.parse(referenceAt);
  if (!Number.isFinite(server)) return 0;
  return server - localNowMs;
}

/** Estimativa do "agora" no servidor a partir do relógio local + offset. */
export function serverNowMs(localNowMs: number, offsetMs: number): number {
  return localNowMs + offsetMs;
}

/** Segundos decorridos desde `startedAt` até o instante informado (>= 0). */
export function elapsedSeconds(startedAt: string, nowMs: number): number {
  const start = Date.parse(startedAt);
  if (!Number.isFinite(start)) return 0;
  return Math.max(0, Math.floor((nowMs - start) / 1000));
}

/** Duração "viva" do item: aberto evolui com o relógio do servidor. */
export function liveDurationSeconds(item: RunTimelineItem, nowMs: number): number {
  if (item.endedAt != null) return Math.max(0, item.durationSeconds);
  return elapsedSeconds(item.startedAt, nowMs);
}

/**
 * Resumo "vivo" derivado dos itens + relógio do servidor — o segmento aberto
 * continua somando sem precisar de novo GET.
 */
export function liveSummary(
  items: RunTimelineItem[],
  nowMs: number,
): { producingSeconds: number; stoppedSeconds: number; stopCount: number } {
  let producing = 0;
  let stopped = 0;
  let stops = 0;
  for (const item of items) {
    const secs = liveDurationSeconds(item, nowMs);
    if (item.state === "stopped") {
      stopped += secs;
      stops += 1;
    } else if (item.state === "producing") {
      producing += secs;
    }
  }
  return { producingSeconds: producing, stoppedSeconds: stopped, stopCount: stops };
}

/** HH:MM:SS sem limite de 59 minutos (horas podem exceder 99). */
export function formatDurationHms(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const seconds = safe % 60;
  const pad = (v: number) => String(v).padStart(2, "0");
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
}

/** HH:MM local para o histórico legível. */
export function formatTimeHm(iso: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

const STATE_LABELS: Record<string, string> = {
  producing: "Produzindo",
  stopped: "Parado",
  setup: "Preparação",
  idle: "Livre",
  planned_stop: "Parada planejada",
};

export function stateLabel(state: string): string {
  return STATE_LABELS[state] ?? state;
}
