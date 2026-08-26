import { fetchFerramentas, type FerramentaItem } from "../data/api/maintenanceApi";
import { MAX_LIST_PAGE_SIZE } from "./listQuery";

export async function fetchAllFerramentasForPeca(
  filial: string,
  codigoPeca: string,
  getAccessToken?: () => string | undefined,
): Promise<FerramentaItem[]> {
  const all: FerramentaItem[] = [];
  let page = 1;
  let total = 0;

  do {
    const data = await fetchFerramentas(
      {
        filial,
        codigoPeca,
        page,
        pageSize: MAX_LIST_PAGE_SIZE,
        sortKey: "codigo",
        sortDirection: "asc",
      },
      getAccessToken,
    );
    all.push(...(data.items ?? []));
    total = data.total ?? all.length;
    page += 1;
  } while (all.length < total);

  return all;
}
