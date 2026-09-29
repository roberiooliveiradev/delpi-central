import { httpGet } from "./httpClient";
import type { MonitoringResponse, RunTimeline } from "../types/mes";

export function getMonitoring(branch: "01" | "02", signal?: AbortSignal) {
  return httpGet<MonitoringResponse>(`/monitoring?branch=${branch}`, { signal });
}

export function getRunTimeline(runId: string, signal?: AbortSignal) {
  return httpGet<RunTimeline>(`/runs/${encodeURIComponent(runId)}/timeline`, { signal });
}
