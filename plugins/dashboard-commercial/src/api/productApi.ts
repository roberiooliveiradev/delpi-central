import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { ProductStructureData } from "../types/productStructure";

const PRODUCT_API_BASE = "/apps/api-delpi/products";

export async function getProductStructure(
  code: string,
  signal?: AbortSignal
): Promise<ProductStructureData> {
  const encoded = encodeURIComponent(code.trim());
  const response = await httpGet<ApiSuccessResponse<ProductStructureData>>(
    `${PRODUCT_API_BASE}/${encoded}/structure?max_depth=6&page_size=200`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar estrutura do produto");
}
