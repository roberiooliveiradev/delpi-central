import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  FetchAuditoriaApontamentosParams,
  FetchHistoricoDetalheParams,
  FetchHistoricoParams,
  InspecoesProcessoAuditoriaApontamentosResponse,
  InspecoesProcessoHistoricoDetalheResponse,
  InspecoesProcessoHistoricoResponse,
  InspecoesProcessoPorEnsaiadorItem,
  InspecoesProcessoPorProdutoItem,
  InspecoesProcessoResumo,
} from "../types/api";
import { httpGet } from "./httpClient";

export const INSPECOES_PROCESSO_API_BASE = "/apps/api-delpi/inspecoes-processo";

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  return search.toString();
}

export async function getResumo(
  branch: string,
  signal?: AbortSignal,
): Promise<InspecoesProcessoResumo> {
  const response = await httpGet<ApiSuccessResponse<InspecoesProcessoResumo>>(
    `${INSPECOES_PROCESSO_API_BASE}/resumo?${buildQuery({ branch })}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Não foi possível carregar o resumo.");
}

export async function getPorProduto(
  branch: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<InspecoesProcessoPorProdutoItem[]> {
  const response = await httpGet<
    ApiSuccessResponse<InspecoesProcessoPorProdutoItem[]>
  >(
    `${INSPECOES_PROCESSO_API_BASE}/por-produto?${buildQuery({ branch, limit })}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar o ranking por produto.",
  );
}

export async function getPorEnsaiador(
  branch: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<InspecoesProcessoPorEnsaiadorItem[]> {
  const response = await httpGet<
    ApiSuccessResponse<InspecoesProcessoPorEnsaiadorItem[]>
  >(
    `${INSPECOES_PROCESSO_API_BASE}/por-ensaiador?${buildQuery({ branch, limit })}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar o ranking por ensaiador.",
  );
}

export async function getHistorico(
  params: FetchHistoricoParams,
): Promise<InspecoesProcessoHistoricoResponse> {
  const { signal, ...query } = params;
  const response = await httpGet<
    ApiSuccessResponse<InspecoesProcessoHistoricoResponse>
  >(`${INSPECOES_PROCESSO_API_BASE}/historico?${buildQuery(query)}`, { signal });
  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar o histórico.",
  );
}

export async function getHistoricoDetalhe(
  params: FetchHistoricoDetalheParams,
): Promise<InspecoesProcessoHistoricoDetalheResponse> {
  const { signal, ...query } = params;
  const response = await httpGet<
    ApiSuccessResponse<InspecoesProcessoHistoricoDetalheResponse>
  >(
    `${INSPECOES_PROCESSO_API_BASE}/historico/detalhe?${buildQuery(query)}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar o detalhe da ordem de produção.",
  );
}

export async function getAuditoriaApontamentos(
  params: FetchAuditoriaApontamentosParams,
): Promise<InspecoesProcessoAuditoriaApontamentosResponse> {
  const { signal, ...query } = params;
  const response = await httpGet<
    ApiSuccessResponse<InspecoesProcessoAuditoriaApontamentosResponse>
  >(
    `${INSPECOES_PROCESSO_API_BASE}/auditoria-apontamentos?${buildQuery(query)}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar a auditoria de apontamentos.",
  );
}
