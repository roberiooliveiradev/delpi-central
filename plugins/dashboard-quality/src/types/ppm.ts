import type { PaginationParams } from "./pagination";

export type PpmType = "internal" | "external";

export type DateRangeParams = {
  branch?: string;
  date_start?: string;
  date_end?: string;
};

export type PpmSummary = {
  type: PpmType;
  branch: string | null;
  date_start: string | null;
  date_end: string | null;
  total_devolvido_un: number;
  total_produzido_milheiro: number;
  total_produzido_un: number;
  ppm: number;
};

export type PpmItem = {
  branch: string;
  registered_date: string | null;
  code: string;
  revision: string;
  item_code: string | null;
  description: string | null;
  returned_quantity_original: string | null;
  returned_quantity_un: number;
};

export type ListPpmParams = DateRangeParams & PaginationParams;
