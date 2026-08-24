// portal/src/data/userUsageTypes.ts

import type { AdminStatisticsRankItem } from "./adminApi";

export type UserUsagePeriodDays = 7 | 30 | 90;

export type UserUsageSeriesPoint = {
  date: string;
  opens?: number;
  totalSeconds?: number;
};

export type UserUsageStatistics = {
  generatedAt: string;
  periodDays: number;
  user: {
    id: string;
    name: string;
    email: string;
    active: boolean;
    lastLoginAt?: string | null;
  };
  consent: {
    granted: boolean;
  };
  summary: {
    totalOpens: number;
    appsUsed: number;
    totalDurationSeconds: number;
    portalDurationSeconds: number;
    appDurationSeconds: number;
    avgSessionSeconds: number;
    lastAppUsageAt?: string | null;
  };
  activity: {
    opensSeries: UserUsageSeriesPoint[];
    durationSeries: UserUsageSeriesPoint[];
  };
  rankings: {
    topAppsByOpens: AdminStatisticsRankItem[];
    topAppsByDuration: AdminStatisticsRankItem[];
    topRoutes: AdminStatisticsRankItem[];
  };
  coverage: {
    trackingEnabled: boolean;
    sessionsRecorded: number;
    eventsInPeriod: number;
  };
};
