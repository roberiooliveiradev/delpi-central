import type { LmpsFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath } from "../utils/filterUrl";

export const LMPS_BASE_PATH = "/apps/dashboard-lmps";

export const LMPS_ROUTES = {
  home: LMPS_BASE_PATH,
} as const;

export function buildLmpDetailPath(
  saleNumber: string,
  filters?: LmpsFilterUrlState
): string {
  const encoded = encodeURIComponent(String(saleNumber).trim());
  return appendFiltersToPath(`${LMPS_BASE_PATH}/ov/${encoded}`, filters);
}
