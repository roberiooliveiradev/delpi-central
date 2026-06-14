import { httpGet, httpPut } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  CulturaDelpiContent,
  UpdateCulturaDelpiContentPayload,
} from "../types/culturaDelpi";

export const CULTURA_DELPI_API_BASE = "/apps/api-delpi/cultura-delpi";

export async function getCulturaDelpiContent(
  signal?: AbortSignal,
): Promise<CulturaDelpiContent> {
  const response = await httpGet<ApiSuccessResponse<CulturaDelpiContent>>(
    `${CULTURA_DELPI_API_BASE}/content`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar conteúdo da Cultura DELPI.");
}

export async function updateCulturaDelpiContent(
  payload: UpdateCulturaDelpiContentPayload,
  signal?: AbortSignal,
): Promise<CulturaDelpiContent> {
  const response = await httpPut<ApiSuccessResponse<CulturaDelpiContent>>(
    `${CULTURA_DELPI_API_BASE}/content`,
    payload,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao salvar conteúdo da Cultura DELPI.");
}
