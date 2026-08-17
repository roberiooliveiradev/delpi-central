import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";
import type {
  FlowchartEscopo,
  FlowchartOverlayV1,
  FlowchartV1,
  MergedRevisaoDiagram,
  ComposedProcessoDiagram,
  ProcessoDiagramResponse,
} from "../../types/diagram";


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

export async function fetchProcessoDiagrama(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDiagramResponse> {
  return request(`/processes/${processoId}/diagram`, getAccessToken);
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
  return request(`/processes/${processoId}/diagram/composed${suffix}`, getAccessToken);
}

export async function saveProcessoDiagrama(
  processoId: string,
  conteudo: FlowchartV1,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDiagramResponse> {
  return request(`/processes/${processoId}/diagram`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ conteudo }),
  });
}

export async function validateProcessoDiagrama(
  processoId: string,
  conteudo: FlowchartV1,
  getAccessToken?: () => string | undefined
): Promise<DiagramValidationReport> {
  return request(`/processes/${processoId}/diagram/validacao`, getAccessToken, {
    method: "POST",
    body: JSON.stringify({ conteudo }),
  });
}

export async function fetchProcessoDiagramBpmnXml(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<string> {
  const data = await request<{ xml: string }>(
    `/processes/${processoId}/diagram/bpmn.xml`,
    getAccessToken
  );
  return data.xml;
}

export async function importProcessoDiagramBpmnXml(
  processoId: string,
  xml: string,
  getAccessToken?: () => string | undefined
): Promise<ProcessoDiagramResponse> {
  return request(`/processes/${processoId}/diagram/bpmn.xml`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ xml }),
  });
}

export async function fetchInstanciaDiagramEscopo(
  instanciaId: string,
  getAccessToken?: () => string | undefined
): Promise<FlowchartEscopo & { instancia_id: string; empty?: boolean }> {
  return request(`/instances/${instanciaId}/scope-diagram`, getAccessToken);
}

export async function saveInstanciaDiagramEscopo(
  instanciaId: string,
  escopo: FlowchartEscopo,
  getAccessToken?: () => string | undefined
) {
  return request(`/instances/${instanciaId}/scope-diagram`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(escopo),
  });
}

export async function fetchRevisaoDiagramMerged(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<MergedRevisaoDiagram> {
  return request(`/revisions/${revisaoId}/diagram`, getAccessToken);
}

export async function fetchRevisaoDiagramOverlay(
  revisaoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ revisao_id: string; conteudo: FlowchartOverlayV1; mermaid?: string | null }>(
    `/revisions/${revisaoId}/diagram/overlay`,
    getAccessToken
  );
}

export async function saveRevisaoDiagramOverlay(
  revisaoId: string,
  conteudo: FlowchartOverlayV1,
  getAccessToken?: () => string | undefined
) {
  return request(`/revisions/${revisaoId}/diagram/overlay`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ conteudo }),
  });
}

export async function fetchRevisaoDiagramMermaid(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<string> {
  const data = await request<{ mermaid: string }>(
    `/revisions/${revisaoId}/diagram/mermaid`,
    getAccessToken
  );
  return data.mermaid;
}
