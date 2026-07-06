import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import type {
  FlowchartEscopo,
  FlowchartOverlayV1,
  FlowchartV1,
  MergedRevisaoDiagram,
  ProcessoDiagramResponse,
} from "../../types/diagram";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

async function parseEnvelope<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.message || `Erro HTTP ${response.status}`);
  }
  return body.data;
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

export async function fetchProcessoDiagrama(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDiagramResponse> {
  return request(`/processos/${processoId}/diagrama`, getAccessToken);
}

export async function saveProcessoDiagrama(
  processoId: string,
  conteudo: FlowchartV1,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDiagramResponse> {
  return request(`/processos/${processoId}/diagrama`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ conteudo }),
  });
}

export async function fetchInstanciaDiagramEscopo(
  instanciaId: string,
  getAccessToken?: () => string | undefined
): Promise<FlowchartEscopo & { instancia_id: string; empty?: boolean }> {
  return request(`/instancias/${instanciaId}/diagrama-escopo`, getAccessToken);
}

export async function saveInstanciaDiagramEscopo(
  instanciaId: string,
  escopo: FlowchartEscopo,
  getAccessToken?: () => string | undefined
) {
  return request(`/instancias/${instanciaId}/diagrama-escopo`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(escopo),
  });
}

export async function fetchRevisaoDiagramMerged(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<MergedRevisaoDiagram> {
  return request(`/revisoes/${revisaoId}/diagrama`, getAccessToken);
}

export async function fetchRevisaoDiagramOverlay(
  revisaoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ revisao_id: string; conteudo: FlowchartOverlayV1; mermaid?: string | null }>(
    `/revisoes/${revisaoId}/diagrama/overlay`,
    getAccessToken
  );
}

export async function saveRevisaoDiagramOverlay(
  revisaoId: string,
  conteudo: FlowchartOverlayV1,
  getAccessToken?: () => string | undefined
) {
  return request(`/revisoes/${revisaoId}/diagrama/overlay`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ conteudo }),
  });
}

export async function fetchRevisaoDiagramMermaid(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<string> {
  const data = await request<{ mermaid: string }>(
    `/revisoes/${revisaoId}/diagrama/mermaid`,
    getAccessToken
  );
  return data.mermaid;
}
