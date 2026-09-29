import type { LucideIcon } from "lucide-react";
import { Activity, Coffee, Pause, Play, TriangleAlert } from "lucide-react";
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

export function monitoringStatItems(summary: MonitoringSummary): StatCardItem[] {
  return [
    { id: "active", label: "Runs ativos", value: summary.activeRuns, tone: "info", icon: Activity },
    { id: "producing", label: "Produzindo", value: summary.producing, tone: "success", icon: Play },
    { id: "stopped", label: "Estado parado", value: summary.stopped, tone: "warning", icon: Pause, description: "inclui pausas manuais" },
    { id: "paused", label: "Pausas manuais", value: summary.paused, tone: "warning", icon: Coffee },
    { id: "pending", label: "Motivos pendentes", value: summary.unclassifiedDowntimes, tone: "danger", icon: TriangleAlert },
  ];
}
