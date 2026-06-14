import { httpGet } from "./httpClient";
import type { ApiSuccessResponse } from "../types/api";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  PropostaComercialDetail,
  PropostaComercialListData,
} from "../types/propostasComerciais";

export const PROPOSTAS_COMERCIAIS_API_BASE = "/apps/api-delpi/propostas-comerciais";

export async function listPropostasComerciais(
  limit = 100,
  signal?: AbortSignal,
): Promise<PropostaComercialListData> {
  const query = new URLSearchParams({ limit: String(limit) });
  const response = await httpGet<ApiSuccessResponse<PropostaComercialListData>>(
    `${PROPOSTAS_COMERCIAIS_API_BASE}?${query.toString()}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao listar propostas comerciais.");
}

export async function getPropostaComercial(
  propostaInterna: string,
  signal?: AbortSignal,
): Promise<PropostaComercialDetail> {
  const code = encodeURIComponent(propostaInterna.trim());
  const response = await httpGet<ApiSuccessResponse<PropostaComercialDetail>>(
    `${PROPOSTAS_COMERCIAIS_API_BASE}/${code}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar proposta comercial.");
}
