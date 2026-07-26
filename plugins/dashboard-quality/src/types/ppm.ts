import type { DashboardGoalFields } from "../utils/goalDisplay";
import type { PaginationParams } from "./pagination";

export type PpmType = "internal" | "external";

export type DateRangeParams = {
  branch?: string;
  start_date?: string;
  end_date?: string;
  product_prefix?: string;
};

export type PpmSummary = DashboardGoalFields & {
  type: PpmType;
  branch: string | null;
  start_date: string | null;
  end_date: string | null;
  total_devolvido_un: number;
  total_produzido_milheiro: number;
  total_produzido_un: number;
  ppm: number;
};

export type PpmItem = {
  branch: string;
  registered_date: string | null;
  code: string;
  code_display: string | null;
  revision: string;
  item_code: string | null;
  description: string | null;
  detailed_description: string | null;
  customer_code: string | null;
  customer_store: string | null;
  customer_name: string | null;
  returned_quantity_original: string | null;
  returned_quantity_un: number;
};

export type ListPpmParams = DateRangeParams & PaginationParams;

export type PpmSeriesPoint = {
  periodo: string;
  sort_key: string;
  start_date: string;
  end_date: string;
  ppm: number;
  total_devolvido_un: number;
  total_produzido_un: number;
};

export type PpmSeriesResponse = {
  type: PpmType;
  granularity: string;
  truncated: boolean;
  points: PpmSeriesPoint[];
};
