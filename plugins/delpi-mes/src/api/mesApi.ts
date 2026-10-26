import { httpGet } from "./httpClient";
import type { BranchCode } from "../constants/routes";
import type { DowntimeFilterOptionsResponse, DowntimesQuery, DowntimesResponse, MonitoringResponse, RunPerformanceResponse, WorkCenterTimelineResponse } from "../types/mes";

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

export function getDowntimes(query: DowntimesQuery, signal?: AbortSignal) {
  const params = new URLSearchParams({ branch: query.branch });
  params.set("page", String(query.page));
  params.set("pageSize", String(query.pageSize));
  if (query.workCenter) params.set("workCenter", query.workCenter);
  if (query.from) params.set("from", query.from);
  if (query.to) params.set("to", query.to);
  if (query.reasonCode) params.set("reasonCode", query.reasonCode);
  if (query.source) params.set("source", query.source);
  if (query.classification) params.set("classification", query.classification);
  if (query.sort) params.set("sort", query.sort);
  if (query.downtimeId) params.set("downtimeId", query.downtimeId);
  return httpGet<DowntimesResponse>("/downtimes?" + params.toString(), { signal });
}

export function getDowntimeFilterOptions(branch: BranchCode, signal?: AbortSignal) {
  return httpGet<DowntimeFilterOptionsResponse>("/downtimes/filter-options?branch=" + branch, { signal });
}
