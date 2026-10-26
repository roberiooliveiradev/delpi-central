import type { BranchCode } from "../constants/routes";

export type MonitoringSummary = { activeRuns: number; producing: number; stopped: number; paused: number; unclassifiedDowntimes: number; monitoredCenters?: number; sensorizedCenters?: number };
export type MonitoringDowntime = { id: string; startedAt: string | null; source: string | null; reasonCode: string | null; reasonLabel: string | null; category: string | null; confirmed: boolean; note: string | null };
export type MesPerformance = { idealCycleSeconds: number | null; producedPieces: number; producingSeconds: number; idealProductionSeconds?: number | null; performancePercent: number | null; actualAverageCycleSeconds: number | null; actualThroughputPerHour: number | null; expectedThroughputPerHour: number | null; dataQuality: string; standardTimeSource?: string | null; standardTimeDataQuality?: string | null };
export type MonitoringItem = { branch: string; workCenter: string; runId: string | null; runStatus: string | null; operationalState: string | null; stateStartedAt: string | null; stateSource: string | null; integrityStatus: string | null; productionOrder: string | null; operationCode: string | null; operatorCode: string | null; operatorName: string | null; piecesTotal: number | null; targetPieces: number | null; lastCountActivityAt: string | null; downtime: MonitoringDowntime | null; performance?: MesPerformance | null; autonomousMonitoring?: boolean | null; sensorized?: boolean | null };
export type MonitoringResponse = { branch: string; referenceAt: string; summary: MonitoringSummary; items: MonitoringItem[] };
export type WorkCenterTimelineDowntime = Pick<MonitoringDowntime, "id" | "source" | "reasonCode" | "reasonLabel" | "category" | "confirmed" | "note">;
export type WorkCenterTimelineItem = { stateEventId: string; runId: string | null; productionOrder: string | null; operationCode: string | null; state: string; startedAt: string; endedAt: string | null; source: string | null; downtime: WorkCenterTimelineDowntime | null };
export type WorkCenterTimelineResponse = { branch: string; workCenter: string; from: string; to: string; referenceAt: string; items: WorkCenterTimelineItem[] };
export type RunPerformanceResponse = { runId: string; branch: string; workCenter: string; status: string; referenceAt: string; performance: MesPerformance };

export type DowntimeSort = "recent" | "oldest";
export type DowntimeClassification = "pending" | "confirmed";
export type DowntimeItem = {
  id: string;
  runId: string | null;
  workCenter: string;
  productionOrder: string | null;
  operationCode: string | null;
  startedAt: string | null;
  endedAt: string | null;
  source: string | null;
  reasonCode: string | null;
  reasonLabel: string | null;
  category: string | null;
  confirmed: boolean;
  note: string | null;
};
export type DowntimesResponse = {
  branch: string;
  referenceAt: string;
  page: number;
  pageSize: number;
  total: number;
  items: DowntimeItem[];
};
export type DowntimeReasonOption = { code: string; label: string; category: string; active: boolean };
export type DowntimeSourceOption = { code: string };
export type DowntimeFilterOptionsResponse = { reasons: DowntimeReasonOption[]; sources: DowntimeSourceOption[] };
export type DowntimesQuery = {
  branch: BranchCode;
  workCenter?: string;
  from?: string;
  to?: string;
  reasonCode?: string;
  source?: string;
  classification?: DowntimeClassification;
  sort?: DowntimeSort;
  downtimeId?: string;
  page: number;
  pageSize: number;
};

export type DowntimeAnalyticsSummary = {
  totalStoppedSeconds: number;
  attributedSeconds: number;
  occurrencesCount: number;
  averageOccurrenceSeconds: number;
  pendingCount: number;
  openCount: number;
};
export type DowntimeAnalyticsReasonGroup = {
  key: string;
  reasonCode: string | null;
  label: string;
  seconds: number;
  occurrencesCount: number;
  pendingCount: number;
  percentOfAttributed: number;
  cumulativePercent: number;
};
export type DowntimeAnalyticsWorkCenter = {
  workCenter: string;
  seconds: number;
  occurrencesCount: number;
  averageSeconds: number;
  percentOfTotal: number;
};
export type DowntimeAnalyticsDay = {
  date: string;
  weekday: number;
  seconds: number;
  occurrencesCount: number;
};
export type DowntimeAnalyticsHourCell = {
  weekday: number;
  weekdayLabel: string;
  hour: number;
  seconds: number;
  occurrencesCount: number;
};
export type DowntimeAnalyticsQuality = {
  overlapDetected: boolean;
  overlapSeconds: number;
  partial: boolean;
  factsCapped: boolean;
};
export type DowntimeAnalyticsResponse = {
  branch: string;
  from: string;
  to: string;
  referenceAt: string;
  timezone: string;
  appliedFilters: {
    workCenter: string | null;
    reasonCode: string | null;
    source: string | null;
    classification: string | null;
  };
  summary: DowntimeAnalyticsSummary;
  byReason: DowntimeAnalyticsReasonGroup[];
  byWorkCenter: DowntimeAnalyticsWorkCenter[];
  byDay: DowntimeAnalyticsDay[];
  byWeekdayHour: DowntimeAnalyticsHourCell[];
  quality: DowntimeAnalyticsQuality;
};
export type DowntimeAnalyticsQuery = {
  branch: BranchCode;
  from: string;
  to?: string;
  workCenter?: string;
  reasonCode?: string;
  source?: string;
  classification?: DowntimeClassification;
};
