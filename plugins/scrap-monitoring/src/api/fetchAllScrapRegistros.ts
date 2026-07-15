import { fetchScrapRegistros } from "./refugosApi";
import type { ScrapQueryFilters, ScrapRegistroItem } from "../types/scrap";

const EXPORT_PAGE_SIZE = 100;

export async function fetchAllScrapRegistros(
  filters: ScrapQueryFilters,
  signal?: AbortSignal,
): Promise<ScrapRegistroItem[]> {
  const first = await fetchScrapRegistros(filters, 1, EXPORT_PAGE_SIZE, { signal });
  const all = [...first.items];

  for (let page = 2; page <= first.totalPages; page += 1) {
    const batch = await fetchScrapRegistros(filters, page, EXPORT_PAGE_SIZE, {
      signal,
    });
    all.push(...batch.items);
  }

  return all;
}
