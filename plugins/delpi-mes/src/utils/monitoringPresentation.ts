import type { MonitoringItem } from "../types/mes";

export type MonitoringTone = "neutral" | "success" | "warning" | "danger";
export type MonitoringPresentation = { label: string; actionLabel: string; tone: MonitoringTone; attentionRank: number; secondary?: string };

export function isPendingReason(item: MonitoringItem): boolean {
  return Boolean(item.downtime && (!item.downtime.confirmed || !item.downtime.reasonCode));
}

export function presentMonitoringState(item: MonitoringItem): MonitoringPresentation {
  if (item.integrityStatus !== "complete") return { label: "Dados incompletos", actionLabel: "Estado indisponível", tone: "warning", attentionRank: 0 };
  if (item.runStatus === "paused") return { label: "Pausa manual", actionLabel: "Pausado", tone: "warning", attentionRank: 3 };
  if (item.runStatus === "running" && item.operationalState === "producing") return { label: "Produzindo", actionLabel: "Produzindo", tone: "success", attentionRank: 4 };
  if (item.runStatus === "running" && item.operationalState === "stopped") return { label: "Parada", actionLabel: "Parado", tone: "danger", attentionRank: isPendingReason(item) ? 1 : 2, secondary: item.stateSource === "system" ? "Detectada automaticamente" : undefined };
  return { label: "Estado indisponível", actionLabel: "Estado indisponível", tone: "neutral", attentionRank: 0 };
}

export function progressPercent(item: MonitoringItem): number | null {
  if (!item.targetPieces || item.targetPieces <= 0) return null;
  return Math.max(0, Math.round((item.piecesTotal / item.targetPieces) * 100));
}

export function runStateSignature(item: MonitoringItem): string {
  return [item.runId, item.runStatus, item.operationalState, item.stateStartedAt, item.downtime?.id, item.downtime?.confirmed].join("|");
}
