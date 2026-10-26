import type { MonitoringItem } from "../types/mes";

export type MonitoringTone = "neutral" | "success" | "warning" | "danger";
export type MonitoringPresentation = { label: string; actionLabel: string; tone: MonitoringTone; attentionRank: number; secondary?: string };

export function isPendingReason(item: MonitoringItem): boolean {
  return Boolean(item.downtime && (!item.downtime.confirmed || !item.downtime.reasonCode));
}

export function downtimeReasonDisplay(
  downtime: { reasonCode?: string | null; reasonLabel: string | null; note: string | null } | null | undefined,
): string | null {
  const label = downtime?.reasonLabel?.trim() || null;
  if (!label) return null;
  const note = downtime?.note?.trim() || null;
  const isOther = label.toLowerCase() === "outro" || downtime?.reasonCode?.trim().toLowerCase() === "outro";
  return note && isOther ? `${label} (${note})` : label;
}

export function presentMonitoringState(item: MonitoringItem): MonitoringPresentation {
  // PC-MES-CT-AUTONOMOUS-DOWNTIME: CT sensorizado sem fato MES aberto é
  // "Monitorado" — não é dado incompleto nem produção ativa.
  if (!item.runId && !item.operationalState) {
    if (item.sensorized || item.autonomousMonitoring) return { label: "Monitorado", actionLabel: "Monitorado", tone: "neutral", attentionRank: 5, secondary: "Sem produção ativa" };
    return { label: "Sem apontamento", actionLabel: "Sem apontamento", tone: "neutral", attentionRank: 5 };
  }
  if (item.integrityStatus !== "complete") return { label: "Dados incompletos", actionLabel: "Estado indisponível", tone: "warning", attentionRank: 0 };
  if (item.runStatus === "paused") return { label: "Pausa manual", actionLabel: "Pausado", tone: "warning", attentionRank: 3 };
  // runStatus é NULL nos fatos autônomos — producing/stopped valem com ou sem OP.
  if (item.operationalState === "producing") return { label: "Produzindo", actionLabel: "Produzindo", tone: "success", attentionRank: 4 };
  if (item.operationalState === "stopped") return { label: "Parada", actionLabel: "Parado", tone: "danger", attentionRank: isPendingReason(item) ? 1 : 2, secondary: item.stateSource === "system" || item.stateSource === "autonomous-monitor" ? "Detectada automaticamente" : undefined };
  return { label: "Estado indisponível", actionLabel: "Estado indisponível", tone: "neutral", attentionRank: 0 };
}

export function progressPercent(item: MonitoringItem): number | null {
  if (!item.targetPieces || item.targetPieces <= 0 || item.piecesTotal == null) return null;
  return Math.max(0, Math.round((item.piecesTotal / item.targetPieces) * 100));
}

export function runStateSignature(item: MonitoringItem): string {
  return [item.runId, item.runStatus, item.operationalState, item.stateStartedAt, item.downtime?.id, item.downtime?.confirmed].join("|");
}
