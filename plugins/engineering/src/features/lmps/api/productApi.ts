import { httpGet } from "./httpClient";
import {
  unwrapApiDelpiEnvelope,
  type ApiSuccessResponse,
} from "../types/lmp";
import type { ProductStructureData } from "../types/productStructure";

const ENGINEERING_API_BASE = "/apps/engineering-api/v1";

type StructureEnvelope = {
  status?: string;
  data?: ProductStructureData;
};

/** BOM/estrutura — owner Products via E-PRD-01
 * `GET /v1/products/{code}/structure` (delegação governada do Bearer
 * humano ao contrato oficial de produtos). Estados honestos: quando a
 * fonte/owner nega ou indisponibiliza, o envelope traz `status`. */
export async function getProductStructure(
  code: string,
  signal?: AbortSignal
): Promise<ProductStructureData> {
  const encoded = encodeURIComponent(code.trim());
  const response = await httpGet<ApiSuccessResponse<StructureEnvelope>>(
    `${ENGINEERING_API_BASE}/products/${encoded}/structure?max_depth=6&page_size=200`,
    { signal }
  );

  const envelopeData = unwrapApiDelpiEnvelope(
    response,
    "Erro ao carregar estrutura do produto",
  );
  if (envelopeData.status === "forbidden") {
    throw new Error("Estrutura do produto indisponível para este usuário (owner).");
  }
  if (envelopeData.status && envelopeData.status !== "available") {
    throw new Error("Estrutura do produto indisponível no momento.");
  }
  return (envelopeData.data ?? envelopeData) as ProductStructureData;
}
