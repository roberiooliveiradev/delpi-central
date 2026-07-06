import { fetchRetrabalhoDetalhes } from "./retrabalhoApi";
import type { RetrabalhoDetalheItem, RetrabalhoQueryFilters } from "../types/retrabalho";

const EXPORT_PAGE_SIZE = 100;

export async function fetchAllRetrabalhoDetalhes(
  filters: RetrabalhoQueryFilters,
  signal?: AbortSignal,
): Promise<RetrabalhoDetalheItem[]> {
  const first = await fetchRetrabalhoDetalhes(filters, 1, EXPORT_PAGE_SIZE, { signal });
  const all = [...first.items];

  for (let page = 2; page <= first.totalPages; page += 1) {
    const batch = await fetchRetrabalhoDetalhes(filters, page, EXPORT_PAGE_SIZE, { signal });
    all.push(...batch.items);
  }

  return all;
}
