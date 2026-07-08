import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type ImpactEffortMatrixMode = "auto" | "manual" | "hibrido";

export type ImpactEffortQuadrant = "quick_win" | "strategic" | "fill_in" | "rethink";

export type ImpactEffortConfidence = "alta" | "media" | "baixa" | "indisponivel";

export type MatrizImpactoMetricas = {
  economia_liquida_anual: number;
  horas_economizadas_anual: number;
  roi_medio: number | null;
  payback_meses: number | null;
  investimento_total_anual: number;
  custo_recursos_anual?: number;
};

export type MatrizImpactoPonto = {
  revisao_id: string;
  versao_revisao: string;
  cenario_tipo: string;
  label: string;
  revisao_ativa: boolean;
  impacto: number;
  esforco: number;
  quadrante: ImpactEffortQuadrant;
  confianca: ImpactEffortConfidence;
  modo: ImpactEffortMatrixMode;
  incluir_na_matriz: boolean;
  metricas: MatrizImpactoMetricas;
};

export type MatrizImpactoVizinho = {
  revisao_id: string;
  impacto: number;
  esforco: number;
  quadrante: ImpactEffortQuadrant;
};

export type MatrizImpactoInputsPersistidos = {
  format?: string;
  format_version?: number;
  modo?: ImpactEffortMatrixMode;
  inputs_manuais?: MatrizImpactoInputsManuais;
  overrides?: MatrizImpactoOverrides;
  atualizado_em?: string;
  atualizado_por?: string;
};

export type MatrizImpactoInputsManuais = {
  impacto_qualitativo?: number;
  esforco_qualitativo?: number;
  alinhamento_estrategico?: number;
  dependencias_externas?: number;
  mudanca_comportamental?: number;
  pessoas_afetadas?: number;
  esforco_implantacao_semanas?: number;
  esforco_horas_equipe?: number;
  observacao?: string;
};

export type MatrizImpactoOverrides = {
  impacto?: number | null;
  esforco?: number | null;
};

export type RevisaoMatrizImpactoResponse = {
  revisao_id: string;
  instancia_id: string;
  competencia: string;
  horizonte_meses: number;
  threshold: number;
  ponto: MatrizImpactoPonto;
  vizinhos: MatrizImpactoVizinho[];
  inputs_persistidos: MatrizImpactoInputsPersistidos | null;
};

export type MatrizImpactoSaveBody = {
  modo: ImpactEffortMatrixMode;
  inputs_manuais?: MatrizImpactoInputsManuais;
  overrides?: MatrizImpactoOverrides;
};

export type MatrizImpactoQuery = {
  competencia?: string;
  horizonte_meses?: number;
};

async function parseEnvelope<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.message || `Erro HTTP ${response.status}`);
  }
  return body.data;
}

function buildQuery(params?: MatrizImpactoQuery): string {
  if (!params) return "";
  const qs = new URLSearchParams();
  if (params.competencia) qs.set("competencia", params.competencia);
  if (params.horizonte_meses != null) qs.set("horizonte_meses", String(params.horizonte_meses));
  const encoded = qs.toString();
  return encoded ? `?${encoded}` : "";
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

export async function fetchRevisaoMatrizImpactoEsforco(
  revisaoId: string,
  getAccessToken?: () => string | undefined,
  params?: MatrizImpactoQuery
): Promise<RevisaoMatrizImpactoResponse> {
  return request(
    `/revisoes/${revisaoId}/matriz-impacto-esforco${buildQuery(params)}`,
    getAccessToken
  );
}

export async function saveRevisaoMatrizImpactoEsforco(
  revisaoId: string,
  body: MatrizImpactoSaveBody,
  getAccessToken?: () => string | undefined,
  params?: MatrizImpactoQuery
): Promise<RevisaoMatrizImpactoResponse> {
  return request(
    `/revisoes/${revisaoId}/matriz-impacto-esforco${buildQuery(params)}`,
    getAccessToken,
    {
      method: "PUT",
      body: JSON.stringify(body),
    }
  );
}
