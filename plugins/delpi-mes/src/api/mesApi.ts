import { httpGet } from "./httpClient";
import type { BranchCode } from "../constants/routes";
import type { MonitoringResponse, RunPerformanceResponse, WorkCenterTimelineResponse } from "../types/mes";

export function getMonitoring(branch: "01" | "02", signal?: AbortSignal) {
  return httpGet<MonitoringResponse>(`/monitoring?branch=${branch}`, { signal });
}

export function getRunPerformance(runId: string, signal?: AbortSignal) {
  return httpGet<RunPerformanceResponse>('/runs/' + encodeURIComponent(runId) + '/performance', { signal });
}

export function getWorkCenterTimeline(branch: BranchCode, workCenter: string, range: { from: string; to?: string }, signal?: AbortSignal) {
  const params = new URLSearchParams({ branch, from: range.from });
  if (range.to) params.set("to", range.to);
  return httpGet<WorkCenterTimelineResponse>(`/work-centers/${encodeURIComponent(workCenter)}/timeline?${params.toString()}`, { signal });
}
