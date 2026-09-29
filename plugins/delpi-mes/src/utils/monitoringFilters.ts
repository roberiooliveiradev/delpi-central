import type { MonitoringItem } from "../types/mes";
import { isPendingReason, presentMonitoringState } from "./monitoringPresentation";

export type StatusFilter = "all" | "producing" | "stopped" | "paused" | "pending" | "incomplete";
export type SortMode = "attention" | "workCenter" | "duration" | "productionOrder";
export type MonitoringFilters = { search: string; status: StatusFilter; reason: string; sort: SortMode };

export function filterMonitoringItems(items: MonitoringItem[], filters: MonitoringFilters, nowMs: number): MonitoringItem[] {
  const term = filters.search.trim().toLocaleLowerCase("pt-BR");
  const matchesStatus = (item: MonitoringItem) => {
    if (filters.status === "all") return true;
    if (filters.status === "producing") return item.runStatus === "running" && item.operationalState === "producing";
    if (filters.status === "stopped") return item.operationalState === "stopped";
    if (filters.status === "paused") return item.runStatus === "paused";
    if (filters.status === "pending") return isPendingReason(item);
    return item.integrityStatus !== "complete";
  };
  const result = items.filter((item) => {
    const searchable = [item.workCenter, item.productionOrder, item.operationCode, item.operatorName, item.downtime?.reasonLabel].filter(Boolean).join(" ").toLocaleLowerCase("pt-BR");
    return (!term || searchable.includes(term)) && matchesStatus(item) && (!filters.reason || item.downtime?.reasonLabel === filters.reason);
  });
  const started = (item: MonitoringItem) => Date.parse(item.stateStartedAt || "") || nowMs;
  return result.sort((a, b) => {
    if (filters.sort === "workCenter") return a.workCenter.localeCompare(b.workCenter);
    if (filters.sort === "duration") return started(a) - started(b);
    if (filters.sort === "productionOrder") return (a.productionOrder || "").localeCompare(b.productionOrder || "");
    return presentMonitoringState(a).attentionRank - presentMonitoringState(b).attentionRank || a.workCenter.localeCompare(b.workCenter);
  });
}
