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

  let body: ApiEnvelope<T> & { detail?: unknown };
  try {
    body = (await response.json()) as ApiEnvelope<T> & { detail?: unknown };
  } catch {
    throw new Error(
      response.ok
        ? "Resposta inválida da API."
        : `Erro HTTP ${response.status} — verifique se transformometro-api está no ar e as migrations V002 foram aplicadas.`
    );
  }

  if (!response.ok || !body.success) {
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail
              .map((item: { msg?: string; loc?: unknown[] }) => {
                const loc = Array.isArray(item.loc) ? item.loc.join(".") : "";
                return loc ? `${loc}: ${item.msg ?? ""}` : (item.msg ?? "");
              })
              .filter(Boolean)
              .join("; ")
          : "";
    throw new Error(body.message || detail || `Erro HTTP ${response.status}`);
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

export function updateRevisao(
  revisaoId: string,
  payload: Partial<Revisao> & {
    processo_id: string;
    versao_revisao: string;
    cenario_tipo: string;
    data_inicio_vigencia: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<Revisao>(`/revisoes/${revisaoId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function activateRevisao(
  revisaoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<Revisao>(`/revisoes/${revisaoId}/ativar`, getAccessToken, {
    method: "POST",
  });
}

export type Medicao = {
  medicao_id?: string;
  revisao_id: string;
  volume_mensal: number;
  tempo_medio_execucao_min: number;
  tempo_retrabalho_min: number;
  percentual_retrabalho: number;
  percentual_erro: number;
  quantidade_erros_mes: number;
  custo_hora_mao_obra: number;
  custo_unitario_erro: number;
  custo_unitario_retrabalho: number;
  custo_outros_desperdicios: number;
  base_referencia_mes?: string | null;
  observacoes?: string | null;
};

export type Investimento = {
  investimento_id: string;
  revisao_id: string;
  tipo_investimento: string;
  descricao_item: string;
  quantidade: number;
  valor_unitario: number;
  valor_total: number;
  recorrencia: string;
  categoria_investimento?: string | null;
  data_investimento?: string | null;
  meses_vigencia?: number | null;
};

export type RecursoCompartilhado = {
  recurso_compartilhado_id: string;
  codigo_recurso: string;
  nome_recurso: string;
  tipo_custo: string;
  recorrencia: string;
  valor_total_recorrente: number;
  criterio_rateio: string;
  status_recurso: string;
  categoria_recurso?: string | null;
  fornecedor?: string | null;
  data_inicio_vigencia?: string | null;
  data_fim_vigencia?: string | null;
};

export type VinculoRecurso = {
  vinculo_id: string;
  revisao_id: string;
  recurso_compartilhado_id: string;
  nome_recurso?: string;
  codigo_recurso?: string;
  ativo: boolean;
  data_inicio_uso?: string | null;
  data_fim_uso?: string | null;
};

export function fetchMedicao(
  revisaoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<Medicao | null>(`/revisoes/${revisaoId}/medicoes`, getAccessToken);
}

export function upsertMedicao(
  payload: Medicao,
  getAccessToken?: () => string | undefined
) {
  return request<Medicao>("/medicoes", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchInvestimentos(
  revisaoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ total: number; items: Investimento[] }>(
    `/revisoes/${revisaoId}/investimentos`,
    getAccessToken
  );
}

export function createInvestimento(
  payload: Partial<Investimento> & { revisao_id: string; descricao_item: string; tipo_investimento: string },
  getAccessToken?: () => string | undefined
) {
  return request<Investimento>("/investimentos", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteInvestimento(
  investimentoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<null>(`/investimentos/${investimentoId}`, getAccessToken, {
    method: "DELETE",
  });
}

export function fetchRecursos(getAccessToken?: () => string | undefined) {
  return request<{ total: number; items: RecursoCompartilhado[] }>(
    "/recursos-compartilhados",
    getAccessToken
  );
}

export function createRecurso(
  payload: Partial<RecursoCompartilhado> & {
    nome_recurso: string;
    tipo_custo: string;
    recorrencia: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<RecursoCompartilhado>("/recursos-compartilhados", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchVinculos(
  revisaoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ total: number; items: VinculoRecurso[] }>(
    `/revisoes/${revisaoId}/recursos-compartilhados`,
    getAccessToken
  );
}

export function createVinculo(
  payload: {
    revisao_id: string;
    recurso_compartilhado_id: string;
    ativo?: boolean;
    data_inicio_uso?: string;
    data_fim_uso?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<VinculoRecurso>("/revisao-recursos-compartilhados", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteVinculo(
  vinculoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<null>(`/revisao-recursos-compartilhados/${vinculoId}`, getAccessToken, {
    method: "DELETE",
  });
}

export type DashboardResumo = {
  solucoes_implementadas: number;
  economia_liquida_total: number;
  economia_bruta_total: number;
  horas_economizadas_total?: number;
  investimento_unico_total?: number;
  custo_recorrente_total?: number;
  roi_medio: number | null;
  linhas_materializadas?: number;
};

export type DashboardEvolucaoItem = {
  competencia: string;
  economia_bruta: number;
  investimento_unico_mes?: number;
  custo_recorrente_mes: number;
  economia_liquida_mes: number;
};

export type DashboardProcessoItem = {
  processo_id: string;
  codigo_processo: string;
  nome_processo: string;
  economia_diaria: number | null;
  economia_liquida_mes?: number;
  economia_bruta?: number;
};

export function recalcularDashboard(getAccessToken?: () => string | undefined) {
  return request<{ rows_upserted: number; elapsed_ms: number }>(
    "/dashboard/recalcular",
    getAccessToken,
    { method: "POST" }
  );
}

export function fetchDashboardResumo(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<DashboardResumo>(`/dashboard/resumo${qs}`, getAccessToken);
}

export function fetchDashboardEvolucao(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<{ total: number; items: DashboardEvolucaoItem[] }>(
    `/dashboard/evolucao${qs}`,
    getAccessToken
  );
}

export function fetchDashboardProcessos(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<{ total: number; items: DashboardProcessoItem[] }>(
    `/dashboard/processos${qs}`,
    getAccessToken
  );
}
