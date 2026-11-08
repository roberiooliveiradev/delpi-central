import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  InspecoesEntradaPendentesFornecedorResponse,
  InspecoesEntradaPendentesResponse,
  InspecoesEntradaRejeitadasProdutoResponse,
  InspecoesEntradaResumo,
} from "../types/inspecoesEntradaDashboard";
import type {
  FetchHistoricoParams,
  InspecoesEntradaHistoricoData,
} from "../types/inspecoesEntradaHistorico";
import type {
  FetchHistoricoDetalheParams,
  InspecoesEntradaHistoricoDetalhe,
} from "../types/inspecoesEntradaHistoricoDetalhe";
import { httpGet } from "./httpClient";

export const INSPECOES_ENTRADA_API_BASE = "/apps/api-delpi/inspecoes-entrada";

function buildBranchQuery(branch: string, extra?: Record<string, string | number>): string {
  const search = new URLSearchParams();
  search.set("branch", branch);
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      search.set(key, String(value));
    }
  }
  return search.toString();
}

export async function fetchInspecoesEntradaResumo(
  branch: string,
  signal?: AbortSignal,
): Promise<InspecoesEntradaResumo> {
  const response = await httpGet<ApiSuccessResponse<InspecoesEntradaResumo>>(
    `${INSPECOES_ENTRADA_API_BASE}/resumo?${buildBranchQuery(branch)}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar o resumo de inspeções.",
  );
}

export async function fetchInspecoesEntradaPendentes(
  branch: string,
  page: number,
  pageSize: number,
  signal?: AbortSignal,
): Promise<InspecoesEntradaPendentesResponse> {
  const response = await httpGet<ApiSuccessResponse<InspecoesEntradaPendentesResponse>>(
    `${INSPECOES_ENTRADA_API_BASE}/pendentes?${buildBranchQuery(branch, {
      page,
      page_size: pageSize,
    })}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar as inspeções pendentes.",
  );
}

export async function fetchInspecoesEntradaPendentesFornecedor(
  branch: string,
  signal?: AbortSignal,
): Promise<InspecoesEntradaPendentesFornecedorResponse> {
  const response = await httpGet<ApiSuccessResponse<InspecoesEntradaPendentesFornecedorResponse>>(
    `${INSPECOES_ENTRADA_API_BASE}/pendentes-fornecedor?${buildBranchQuery(branch)}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar pendências por fornecedor.",
  );
}

export async function fetchInspecoesEntradaRejeitadasProduto(
  branch: string,
  limit = 50,
  signal?: AbortSignal,
): Promise<InspecoesEntradaRejeitadasProdutoResponse> {
  const response = await httpGet<ApiSuccessResponse<InspecoesEntradaRejeitadasProdutoResponse>>(
    `${INSPECOES_ENTRADA_API_BASE}/rejeitadas-produto?${buildBranchQuery(branch, { limit })}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar as rejeições por produto.",
  );
}

function buildHistoricoQuery(params: FetchHistoricoParams): string {
  const search = new URLSearchParams();
  search.set("branch", params.branch);
  search.set("page", String(params.page));
  search.set("page_size", String(params.page_size));

  const optionalKeys = [
    "result",
    "supplier",
    "product_code",
    "inspector",
    "invoice_number",
    "lot",
  ] as const;

  for (const key of optionalKeys) {
    const value = params[key];
    if (value && value.trim()) {
      search.set(key, value.trim());
    }
  }

  if (params.start_date?.trim()) search.set("start_date", params.start_date.trim());
  if (params.end_date?.trim()) search.set("end_date", params.end_date.trim());

  return search.toString();
}

export async function fetchInspecoesEntradaHistorico(
  params: FetchHistoricoParams,
  signal?: AbortSignal,
): Promise<InspecoesEntradaHistoricoData> {
  const query = buildHistoricoQuery(params);
  const response = await httpGet<ApiSuccessResponse<InspecoesEntradaHistoricoData>>(
    `${INSPECOES_ENTRADA_API_BASE}/historico?${query}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar o histórico de inspeções.",
  );
}

export async function fetchInspecoesEntradaHistoricoDetalhe(
  params: FetchHistoricoDetalheParams,
  signal?: AbortSignal,
): Promise<InspecoesEntradaHistoricoDetalhe> {
  const search = new URLSearchParams();
  search.set("branch", params.branch);
  search.set("inspection_id", params.inspection_id);

  const response = await httpGet<ApiSuccessResponse<InspecoesEntradaHistoricoDetalhe>>(
    `${INSPECOES_ENTRADA_API_BASE}/historico/detalhe?${search.toString()}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar o detalhe da inspeção.",
  );
}

/** Lista NCs do Protheus QI2 exclusivamente do tipo Fornecedor (QI2_TIPO=3).
 * Escopo e permissões por filial são validados no servidor. */
export async function fetchInspecoesEntradaNcsFornecedores(
  filters: import("../types/fornecedoresNc").FornecedoresNcFilters,
  signal?: AbortSignal,
): Promise<import("../types/fornecedoresNc").FornecedoresNcResponse> {
  const query = new URLSearchParams({
    branch: filters.branch,
    page: String(filters.page),
    page_size: String(filters.page_size),
  });
  for (const key of ["start_date", "end_date", "status", "item_code", "description"] as const) {
    const value = filters[key]?.trim();
    if (value) query.set(key, value);
  }

  const response = await httpGet<ApiSuccessResponse<
    import("../types/fornecedoresNc").FornecedoresNcResponse
  >>(
    `${INSPECOES_ENTRADA_API_BASE}/ncs-fornecedores?${query}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Não foi possível carregar as NCs de fornecedores.",
  );
}
