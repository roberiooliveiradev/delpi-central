import { httpGet } from "./httpClient";
import type { BranchCode } from "../constants/routes";
import type { MonitoringResponse, WorkCenterTimelineResponse } from "../types/mes";

export function getMonitoring(branch: "01" | "02", signal?: AbortSignal) {
  return httpGet<MonitoringResponse>(`/monitoring?branch=${branch}`, { signal });
}

export function getWorkCenterTimeline(branch: BranchCode, workCenter: string, from: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ branch, from });
  return httpGet<WorkCenterTimelineResponse>(`/work-centers/${encodeURIComponent(workCenter)}/timeline?${params.toString()}`, { signal });
}
