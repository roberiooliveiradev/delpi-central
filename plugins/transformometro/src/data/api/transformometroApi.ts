import {
  TRANSFORMOMETRO_API_BASE,
  buildAuthHeaders,
} from "./transformometroApiBase";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

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

  const body = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.message || `Erro HTTP ${response.status}`);
  }
  return body.data;
}

export type Processo = {
  processo_id: string;
  codigo_processo: string;
  nome_processo: string;
  filial_id: string;
  setor_id: string;
  status_processo: string;
  descricao_processo?: string | null;
  gestor_responsavel?: string | null;
  objetivo_processo?: string | null;
};

export type Revisao = {
  revisao_id: string;
  processo_id: string;
  versao_revisao: string;
  cenario_tipo: string;
  data_inicio_vigencia: string;
  revisao_ativa: boolean;
  data_implantacao?: string | null;
  data_fim_vigencia?: string | null;
};

export type OptionsData = {
  filiais: { id: string; label: string }[];
  setores: string[];
  status_processo: string[];
  cenario_tipo: string[];
  recorrencias: string[];
  criterio_rateio: string[];
  status_recurso: string[];
  tipo_investimento: string[];
  categorias: string[];
};

export function fetchOptions(getAccessToken?: () => string | undefined) {
  return request<OptionsData>("/options", getAccessToken);
}

export function fetchProcessos(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<{ total: number; items: Processo[] }>(
    `/processos${qs}`,
    getAccessToken
  );
}

export function fetchProcesso(
  processoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<Processo>(`/processos/${processoId}`, getAccessToken);
}

export function createProcesso(
  payload: Partial<Processo>,
  getAccessToken?: () => string | undefined
) {
  return request<Processo>("/processos", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchRevisoes(
  processoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ total: number; items: Revisao[] }>(
    `/processos/${processoId}/revisoes`,
    getAccessToken
  );
}

export function createRevisao(
  payload: Partial<Revisao>,
  getAccessToken?: () => string | undefined
) {
  return request<Revisao>("/revisoes", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
