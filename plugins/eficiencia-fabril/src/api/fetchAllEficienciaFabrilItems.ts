import { EFICIENCIA_FABRIL_MAX_PAGE_SIZE } from "../constants/businessRules";
import type {
  EficienciaFabrilFilterParams,
  EficienciaFabrilItem,
} from "../types/eficienciaFabril";
import { getEficienciaFabrilDashboard } from "./eficienciaFabrilApi";

export type EficienciaFabrilListFilterParams = Omit<
  EficienciaFabrilFilterParams,
  "page" | "page_size"
>;

export async function fetchAllEficienciaFabrilItems(
  params: EficienciaFabrilListFilterParams,
  signal?: AbortSignal
): Promise<EficienciaFabrilItem[]> {
  const items: EficienciaFabrilItem[] = [];
  let page = 1;
  let totalPages = 1;

  do {
    const data = await getEficienciaFabrilDashboard(
      {
        ...params,
        page,
        page_size: EFICIENCIA_FABRIL_MAX_PAGE_SIZE,
      },
      signal
    );
    items.push(...data.items);
    totalPages = data.pagination.total_pages;
    page += 1;
  } while (page <= totalPages);

  return items;
}
