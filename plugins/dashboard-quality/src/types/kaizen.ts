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
  annual_savings: number | null;
  branch: string | null;
  /** Âncora do indicador de quantidade (aprovação comitê ou implantação). */
  quantity_date?: string | null;
  /** Ganho no período (daily_savings × dias ativos) — vem em list_savings_kaizen. */
  period_savings?: number | null;
};

export type KaizenDetail = Kaizen & {
  seconds_per_occurrence: number | null;
  occurrences_per_day: number | null;
  hourly_cost: number | null;
  hours_saved_per_day: number | null;
};

export type KaizenIdeasGoalBlock = DashboardGoalFields & {
  total_kaizens?: number;
};

export type KaizenSummary = DashboardGoalFields & {
  date_start: string | null;
  date_end: string | null;
  total_kaizens: number;
  total_savings: number;
  list_kaizen: Kaizen[];
  /** Implantados que compõem total_savings (pode diferir de list_kaizen). */
  list_savings_kaizen?: Kaizen[];
  /** Meta de ideias/mês (catálogo SI `quality_kaizen_ideas`). */
  ideas_goal?: KaizenIdeasGoalBlock | null;
};
