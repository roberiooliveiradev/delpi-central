import { httpDownload, httpGet, httpPost, httpPut } from "./httpClient";
import type { BranchCode } from "../constants/routes";
import type {
  DowntimeAnalyticsQuery,
  DowntimeAnalyticsResponse,
  DowntimeClassificationResult,
  DowntimeFilterOptionsResponse,
  DowntimeHistoryResponse,
  DowntimeTreatmentResponse,
  DowntimesQuery,
  DowntimesResponse,
  MonitoringResponse,
  RunPerformanceResponse,
  WorkCenterTimelineResponse,
} from "../types/mes";

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
  if (query.status) params.set("status", query.status);
  if (query.sort) params.set("sort", query.sort);
  if (query.downtimeId) params.set("downtimeId", query.downtimeId);
  return httpGet<DowntimesResponse>("/downtimes?" + params.toString(), { signal });
}

export function getDowntimeAnalytics(query: DowntimeAnalyticsQuery, signal?: AbortSignal) {
  const params = new URLSearchParams({ branch: query.branch, from: query.from });
  if (query.to) params.set("to", query.to);
  if (query.workCenter) params.set("workCenter", query.workCenter);
  if (query.reasonCode) params.set("reasonCode", query.reasonCode);
  if (query.source) params.set("source", query.source);
  if (query.classification) params.set("classification", query.classification);
  if (query.status) params.set("status", query.status);
  return httpGet<DowntimeAnalyticsResponse>("/downtimes/analytics?" + params.toString(), { signal });
}

function downtimeFilterParams(query: DowntimeAnalyticsQuery): URLSearchParams {
  const params = new URLSearchParams({ branch: query.branch });
  if (query.to) params.set("to", query.to);
  if (query.workCenter) params.set("workCenter", query.workCenter);
  if (query.reasonCode) params.set("reasonCode", query.reasonCode);
  if (query.source) params.set("source", query.source);
  if (query.classification) params.set("classification", query.classification);
  if (query.status) params.set("status", query.status);
  return params;
}

export function exportDowntimes(query: DowntimeAnalyticsQuery, format: "csv" | "xlsx", signal?: AbortSignal) {
  const params = downtimeFilterParams(query);
  params.set("format", format);
  params.set("from", query.from);
  return httpDownload("/downtimes/export?" + params.toString(), { signal });
}

export function exportDowntimePendencies(query: DowntimeAnalyticsQuery, format: "csv" | "xlsx", signal?: AbortSignal) {
  const params = downtimeFilterParams(query);
  params.set("format", format);
  params.set("from", query.from);
  return httpDownload("/downtimes/reports/pendencies?" + params.toString(), { signal });
}

export function exportDowntimeExecutiveReport(query: DowntimeAnalyticsQuery, signal?: AbortSignal) {
  const params = downtimeFilterParams(query);
  params.set("from", query.from);
  return httpDownload("/downtimes/reports/executive?" + params.toString(), { signal });
}

export function getDowntimeFilterOptions(branch: BranchCode, signal?: AbortSignal) {
  return httpGet<DowntimeFilterOptionsResponse>("/downtimes/filter-options?branch=" + branch, { signal });
}

/* ---- Gestão gerencial da parada (Etapa 3) ---- */

export function classifyDowntime(
  downtimeId: string,
  body: { branch: string; reasonCode: string; note: string | null; expectedUpdatedAt: string },
) {
  return httpPost<DowntimeClassificationResult>(
    "/downtimes/" + encodeURIComponent(downtimeId) + "/classification",
    body,
  );
}

export function getDowntimeTreatment(downtimeId: string, branch: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ branch });
  return httpGet<DowntimeTreatmentResponse>(
    "/downtimes/" + encodeURIComponent(downtimeId) + "/treatment?" + params.toString(),
    { signal },
  );
}

export function upsertDowntimeTreatment(
  downtimeId: string,
  body: {
    branch: string;
    analysis: string;
    causeKind: string;
    causeNote: string | null;
    actionNeeded: boolean;
    justification: string;
    expectedUpdatedAt: string | null;
  },
) {
  return httpPut<{ treatment: import("../types/mes").DowntimeTreatment }>(
    "/downtimes/" + encodeURIComponent(downtimeId) + "/treatment",
    body,
  );
}

export function referDowntimeTreatment(
  downtimeId: string,
  body: { branch: string; issueCode: string; note: string | null; idempotencyKey?: string | null },
) {
  return httpPost<{ treatment: import("../types/mes").DowntimeTreatment }>(
    "/downtimes/" + encodeURIComponent(downtimeId) + "/treatment/referrals",
    body,
  );
}

export function concludeDowntimeTreatment(
  downtimeId: string,
  body: { branch: string; reason: string },
) {
  return httpPost<{ treatment: import("../types/mes").DowntimeTreatment }>(
    "/downtimes/" + encodeURIComponent(downtimeId) + "/treatment/conclusion",
    body,
  );
}

export function getDowntimeHistory(downtimeId: string, branch: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ branch });
  return httpGet<DowntimeHistoryResponse>(
    "/downtimes/" + encodeURIComponent(downtimeId) + "/history?" + params.toString(),
    { signal },
  );
}
