import type { DashboardGoalFields } from "../utils/goalDisplay";

export type KaizenSummaryParams = {
  title?: string;
  status?: string;
  branch?: string;
  date_start?: string;
  date_end?: string;
};

export type Kaizen = {
  id: string;
  title: string;
  date_implemented: string | null;
  status: string | null;
  accountable: string | null;
  sector: string | null;
  investment: number | null;
  daily_savings: number | null;
  branch: string | null;
};

export type KaizenSummary = DashboardGoalFields & {
  date_start: string | null;
  date_end: string | null;
  total_kaizens: number;
  total_savings: number;
  list_kaizen: Kaizen[];
};
