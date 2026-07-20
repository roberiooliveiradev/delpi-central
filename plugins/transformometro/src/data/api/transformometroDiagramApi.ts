import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import type {
  FlowchartEscopo,
  FlowchartOverlayV1,
  FlowchartV1,
  MergedRevisaoDiagram,
  ComposedProcessoDiagram,
  ProcessoDiagramResponse,
} from "../../types/diagram";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type DiagramValidationIssue = {
  severity: "error" | "warning" | "info";
  code: string;
  message: string;
  node_id?: string;
};

export type DiagramValidationReport = {
  valid: boolean;
  issues: DiagramValidationIssue[];
  simulation: {
    completed_paths: Array<{
      path_ids: string[];
      path_labels: string[];
      steps: number;
      branch?: string;
    }>;
    stuck_paths: Array<{
      path_ids: string[];
      path_labels: string[];
      reason: string;
    }>;
    completed_count: number;
    stuck_count: number;
  };
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

export async function fetchProcessoDiagramaComposed(
  processoId: string,
  getAccessToken?: () => string | undefined,
  params?: { at?: string; instancia_id?: string }
): Promise<ComposedProcessoDiagram> {
  const qs = new URLSearchParams();
  if (params?.at) qs.set("at", params.at);
  if (params?.instancia_id) qs.set("instancia_id", params.instancia_id);
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/processos/${processoId}/diagrama/composed${suffix}`, getAccessToken);
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

export async function validateProcessoDiagrama(
  processoId: string,
  conteudo: FlowchartV1,
  getAccessToken?: () => string | undefined
): Promise<DiagramValidationReport> {
  return request(`/processos/${processoId}/diagrama/validacao`, getAccessToken, {
    method: "POST",
    body: JSON.stringify({ conteudo }),
  });
}

export async function fetchProcessoDiagramBpmnXml(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<string> {
  const data = await request<{ xml: string }>(
    `/processos/${processoId}/diagrama/bpmn.xml`,
    getAccessToken
  );
  return data.xml;
}

export async function importProcessoDiagramBpmnXml(
  processoId: string,
  xml: string,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDiagramResponse> {
  return request(`/processos/${processoId}/diagrama/bpmn.xml`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ xml }),
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
