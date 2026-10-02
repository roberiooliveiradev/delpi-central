import type { LucideIcon } from "lucide-react";
import { Activity, Pause, Play, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";
import type { MonitoringSummary } from "../types/mes";

export type StatCardItem = {
  id: string;
  label: string;
  value: ReactNode;
  tone: "info" | "success" | "warning" | "danger";
  icon: LucideIcon;
  description?: string;
};

/**
 * Parada automática e pausa manual já compartilham o estado operacional
 * `stopped`. `paused` é um recorte desse total — somar os dois contaria
 * a mesma máquina duas vezes.
 */
export function monitoringDowntimeCount(summary: MonitoringSummary): number {
  return summary.stopped;
}

export function monitoringStatItems(summary: MonitoringSummary): StatCardItem[] {
  return [
    { id: "active", label: "Apontamentos ativos", value: summary.activeRuns, tone: "info", icon: Activity },
    { id: "producing", label: "Produzindo", value: summary.producing, tone: "success", icon: Play },
    { id: "downtime", label: "Paradas", value: monitoringDowntimeCount(summary), tone: "warning", icon: Pause },
    { id: "pending", label: "Motivos pendentes", value: summary.unclassifiedDowntimes, tone: "danger", icon: TriangleAlert },
  ];
}
