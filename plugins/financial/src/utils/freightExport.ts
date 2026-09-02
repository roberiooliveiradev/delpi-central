import {
  fetchFreightDashboard,
  fetchFreightInconsistencies,
} from "../api/financialApi";
import type {
  FinancialBranch,
  FreightInconsistency,
  FreightInvoice,
} from "../types";

/**
 * Teto do BFF (`freight.json` → `pagination.maxPageSize`). Exportar a consulta
 * inteira usa esse tamanho para minimizar round-trips sem estourar o clamp.
 */
export const FREIGHT_EXPORT_PAGE_SIZE = 200;

export type FreightExportFilters = {
  branch: FinancialBranch;
  issueStart: string | null;
  issueEnd: string | null;
  entryStart: string | null;
  entryEnd: string | null;
  supplierCode: string | null;
  invoiceDocument: string | null;
  freightDocument: string | null;
  situation: string | null;
  sortBy: string;
  sortDir: "asc" | "desc";
};

type PaginatedSlice<T> = {
  items: T[];
  pagination: { hasNext: boolean; totalItems: number };
};

/**
 * Percorre todas as páginas do endpoint até esgotar `hasNext`.
 *
 * Sem isso o Excel só refletiria a página da grade (25 linhas) e o usuário
 * acharia que a consulta tem só aquele recorte.
 */
export async function collectAllFreightPages<T>(
  loadPage: (page: number, pageSize: number) => Promise<PaginatedSlice<T>>,
  pageSize = FREIGHT_EXPORT_PAGE_SIZE,
): Promise<T[]> {
  const collected: T[] = [];
  let page = 1;

  while (true) {
    const response = await loadPage(page, pageSize);
    collected.push(...response.items);

    if (
      collected.length >= response.pagination.totalItems ||
      response.items.length < pageSize ||
      !response.pagination.hasNext
    ) {
      break;
    }
    page += 1;
  }

  return collected;
}

export async function fetchAllFreightInvoices(
  filters: FreightExportFilters,
  signal?: AbortSignal,
): Promise<FreightInvoice[]> {
  return collectAllFreightPages(async (page, pageSize) => {
    const response = await fetchFreightDashboard({
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
      page,
      pageSize,
      signal,
    });
    return { items: response.items, pagination: response.pagination };
  });
}

export async function fetchAllFreightInconsistencies(
  filters: Omit<FreightExportFilters, "situation" | "sortBy" | "sortDir">,
  signal?: AbortSignal,
): Promise<FreightInconsistency[]> {
  return collectAllFreightPages(async (page, pageSize) => {
    const response = await fetchFreightInconsistencies({
      branch: filters.branch,
      issueStart: filters.issueStart,
      issueEnd: filters.issueEnd,
      entryStart: filters.entryStart,
      entryEnd: filters.entryEnd,
      supplier: filters.supplierCode,
      invoiceDocument: filters.invoiceDocument,
      freightDocument: filters.freightDocument,
      page,
      pageSize,
      signal,
    });
    return { items: response.items, pagination: response.pagination };
  });
}
