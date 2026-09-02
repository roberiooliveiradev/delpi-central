import { fetchFreightDashboard, fetchFreightInconsistencies } from "../api/financialApi";
import { copy } from "../content/copy";
import type {
  FinancialBranch,
  FreightDashboardPayload,
  FreightInconsistenciesPayload,
} from "../types";
import { useAsyncResource } from "./useAsyncResource";

export type FreightFilters = {
  branch: FinancialBranch;
  issueStart: string | null;
  issueEnd: string | null;
  entryStart: string | null;
  entryEnd: string | null;
  supplierCode: string | null;
  invoiceDocument: string | null;
  freightDocument: string | null;
};

/**
 * O BFF exige um dos dois intervalos completos; sem isso a consulta nem sai,
 * para a tela não trocar o filtro do usuário por um erro de validação.
 */
export function hasFreightPeriod(filters: FreightFilters): boolean {
  return Boolean(
    (filters.issueStart && filters.issueEnd) || (filters.entryStart && filters.entryEnd),
  );
}

function filterKey(filters: FreightFilters): string {
  return [
    filters.branch,
    filters.issueStart,
    filters.issueEnd,
    filters.entryStart,
    filters.entryEnd,
    filters.supplierCode,
    filters.invoiceDocument,
    filters.freightDocument,
  ].join("|");
}

export function useFreightDashboard(
  filters: FreightFilters & {
    situation: string | null;
    sortBy: string;
    sortDir: "asc" | "desc";
    page: number;
  },
) {
  const key = [filterKey(filters), filters.situation, filters.sortBy, filters.sortDir, filters.page]
    .join("|");
  const enabled = hasFreightPeriod(filters);

  return useAsyncResource<FreightDashboardPayload | null>(
    (signal) => {
      if (!enabled) return Promise.resolve(null);
      return fetchFreightDashboard({
        branch: filters.branch,
        issueStart: filters.issueStart,
        issueEnd: filters.issueEnd,
        entryStart: filters.entryStart,
        entryEnd: filters.entryEnd,
        supplier: filters.supplierCode,
        invoiceDocument: filters.invoiceDocument,
        freightDocument: filters.freightDocument,
        situation: filters.situation,
        sortBy: filters.sortBy,
        sortDir: filters.sortDir,
        page: filters.page,
        signal,
      });
    },
    [key, enabled],
    copy.freight.loadError,
  );
}

export function useFreightInconsistencies(
  filters: FreightFilters & { page: number; enabled: boolean },
) {
  const key = [filterKey(filters), filters.page, filters.enabled].join("|");
  const enabled = filters.enabled && hasFreightPeriod(filters);

  return useAsyncResource<FreightInconsistenciesPayload | null>(
    (signal) => {
      if (!enabled) return Promise.resolve(null);
      return fetchFreightInconsistencies({
        branch: filters.branch,
        issueStart: filters.issueStart,
        issueEnd: filters.issueEnd,
        entryStart: filters.entryStart,
        entryEnd: filters.entryEnd,
        supplier: filters.supplierCode,
        invoiceDocument: filters.invoiceDocument,
        freightDocument: filters.freightDocument,
        page: filters.page,
        signal,
      });
    },
    [key, enabled],
    copy.freight.inconsistencies.loadError,
  );
}
