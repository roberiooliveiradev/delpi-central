import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";
import { describeHttpError } from "../../utils/apiErrorMessage";
import type {
  DecompositionEscopo,
  DecompositionOverlayV1,
  DecompositionTreeV1,
  InstanciaContextoV1,
  MergedRevisaoDecomposition,
  ComposedProcessoDecomposition,
  ProcessoDecompositionResponse,
} from "../../types/decomposition";


async function parseEnvelope<T>(response: Response): Promise<T> {
  return parseApiEnvelope<T>(response);
}

async function request<T>(
  path: string,
  getAccessToken?: () => string | undefined,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders(getAccessToken),
      ...(init?.headers ?? {}),
    },
  });
  return parseEnvelope<T>(response);
}

export async function fetchProcessoDecomposicao(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDecompositionResponse> {
  return request(`/processes/${processoId}/decomposition`, getAccessToken);
}

export async function fetchProcessoDecomposicaoComposed(
  processoId: string,
  getAccessToken?: () => string | undefined,
  params?: { at?: string; instancia_id?: string }
): Promise<ComposedProcessoDecomposition> {
  const qs = new URLSearchParams();
  if (params?.at) qs.set("at", params.at);
  if (params?.instancia_id) qs.set("instancia_id", params.instancia_id);
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/processes/${processoId}/decomposition/composed${suffix}`, getAccessToken);
}

export async function saveProcessoDecomposicao(
  processoId: string,
  conteudo: DecompositionTreeV1,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDecompositionResponse> {
  return request(`/processes/${processoId}/decomposition`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ conteudo }),
  });
}

export async function downloadProcessoDecomposicaoCsv(
  processoId: string,
  getAccessToken?: () => string | undefined,
  params?: { instancia_id?: string; revisao_id?: string }
): Promise<Blob> {
  const qs = params ? `?${new URLSearchParams(params as Record<string, string>)}` : "";
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/processes/${processoId}/decomposition/export.csv${qs}`,
    { headers: buildAuthHeaders(getAccessToken) }
  );
  if (!response.ok) {
    try {
      await parseApiEnvelope(response);
    } catch (err) {
      throw err instanceof Error ? err : new Error(describeHttpError(response.status));
    }
  }
  return response.blob();
}

export async function suggestDecomposicaoRascunho(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<{ conteudo: DecompositionTreeV1; persisted: boolean }> {
  return request(`/processes/${processoId}/decomposition/suggest-draft`, getAccessToken, {
    method: "POST",
  });
}

export async function validateDecomposicaoVinculosFluxo(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<{ valid: boolean; warnings: Array<Record<string, string>> }> {
  return request(`/processes/${processoId}/decomposition/validate-flow-links`, getAccessToken, {
    method: "POST",
  });
}

export async function fetchInstanciaDecomposicaoEscopo(
  instanciaId: string,
  getAccessToken?: () => string | undefined
): Promise<DecompositionEscopo & { instancia_id: string; empty?: boolean }> {
  return request(`/instances/${instanciaId}/decomposition-escopo`, getAccessToken);
}

export async function saveInstanciaDecomposicaoEscopo(
  instanciaId: string,
  escopo: DecompositionEscopo,
  getAccessToken?: () => string | undefined
) {
  return request(`/instances/${instanciaId}/decomposition-escopo`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(escopo),
  });
}

export async function fetchInstanciaContexto(
  instanciaId: string,
  getAccessToken?: () => string | undefined
): Promise<{ instancia_id: string; conteudo: InstanciaContextoV1; empty?: boolean }> {
  return request(`/instances/${instanciaId}/context`, getAccessToken);
}

export async function saveInstanciaContexto(
  instanciaId: string,
  conteudo: InstanciaContextoV1,
  getAccessToken?: () => string | undefined
) {
  return request(`/instances/${instanciaId}/context`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ conteudo }),
  });
}

export async function fetchRevisaoDecomposicaoMerged(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<MergedRevisaoDecomposition> {
  return request(`/revisions/${revisaoId}/decomposition`, getAccessToken);
}

export async function fetchRevisaoDecomposicaoOverlay(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<{ revisao_id: string; conteudo: DecompositionOverlayV1; empty?: boolean }> {
  return request(`/revisions/${revisaoId}/decomposition/overlay`, getAccessToken);
}

export async function saveRevisaoDecomposicaoOverlay(
  revisaoId: string,
  conteudo: DecompositionOverlayV1,
  getAccessToken?: () => string | undefined
) {
  return request(`/revisions/${revisaoId}/decomposition/overlay`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ conteudo }),
  });
}
