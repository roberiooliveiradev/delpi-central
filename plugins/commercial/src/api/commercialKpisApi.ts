import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { apiDelpiUrl, httpGet } from "./httpClient";

const COMMERCIAL_PATH = "/commercial";

/** Shape alinhado ao Dashboard Comercial / api-delpi. */
export type RolTargetKpi = {
  rol?: number | null;
  target?: number | null;
  rol_target_pct?: number | null;
};

export type ClosingRateKpi = {
  qtd_proposals?: number | null;
  qtd_won?: number | null;
  sales_conversion_rate_pct?: number | null;
};

export type SalesOrderOtdKpi = {
  sales_order_otd_pct?: number | null;
  total_lines?: number | null;
  on_time_lines?: number | null;
  late_lines?: number | null;
};

function monthRangeIso(date = new Date()): { start_date: string; end_date: string } {
  const y = date.getFullYear();
  const m = date.getMonth();
  const start = new Date(y, m, 1);
  const end = new Date(y, m + 1, 0);
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  return { start_date: fmt(start), end_date: fmt(end) };
}

async function fetchCommercialKpi<T>(path: string, signal?: AbortSignal): Promise<T> {
  const range = monthRangeIso();
  const params = new URLSearchParams(range);
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${apiDelpiUrl(`${COMMERCIAL_PATH}${path}`)}?${params.toString()}`,
    { signal },
  );
  return unwrapEnvelope(response, `Erro ao carregar ${path}`);
}

export function getHeadOfficeRolTargetPct(signal?: AbortSignal) {
  return fetchCommercialKpi<RolTargetKpi>("/head_office_rol_target_pct", signal);
}

export function getClosingRate(signal?: AbortSignal) {
  return fetchCommercialKpi<ClosingRateKpi>("/closing-rate", signal);
}

export function getSalesOrderOtd(signal?: AbortSignal) {
  return fetchCommercialKpi<SalesOrderOtdKpi>("/sales-order-otd", signal);
}

export function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

export function pickRolPct(data: RolTargetKpi | null): number | null {
  return data?.rol_target_pct ?? null;
}

export function pickClosingPct(data: ClosingRateKpi | null): number | null {
  return data?.sales_conversion_rate_pct ?? null;
}

export function pickOtdPct(data: SalesOrderOtdKpi | null): number | null {
  return data?.sales_order_otd_pct ?? null;
}
