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
  familia_processo?: string | null;
  agrupador_ferramenta?: string | null;
};

export type Revisao = {
  revisao_id: string;
  processo_id: string;
  versao_revisao: string;
  cenario_tipo: string;
  data_inicio_vigencia: string;
  revisao_ativa: boolean;
  status_aprovacao?: string;
  motivo_rejeicao?: string | null;
  aprovado_por_email?: string | null;
  data_implantacao?: string | null;
  data_fim_vigencia?: string | null;
  descricao_revisao?: string | null;
  motivo_revisao?: string | null;
  observacoes?: string | null;
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
  tipo_custo: string[];
  categorias: string[];
  status_aprovacao_revisao: string[];
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

export function updateProcesso(
  processoId: string,
  payload: Partial<Processo>,
  getAccessToken?: () => string | undefined
) {
  return request<Processo>(`/processos/${processoId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteProcesso(
  processoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<null>(`/processos/${processoId}`, getAccessToken, {
    method: "DELETE",
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
  centro_custo?: string | null;
  observacoes?: string | null;
};

export type VinculoRecurso = {
  vinculo_id: string;
  revisao_id: string;
  recurso_compartilhado_id: string;
  nome_recurso?: string;
  codigo_recurso?: string;
  categoria_recurso?: string | null;
  fornecedor?: string | null;
  tipo_custo?: string;
  recorrencia?: string;
  valor_total_recorrente?: number;
  recurso_data_inicio_vigencia?: string | null;
  recurso_data_fim_vigencia?: string | null;
  centro_custo?: string | null;
  criterio_rateio?: string;
  status_recurso?: string;
  recurso_observacoes?: string | null;
  ativo: boolean;
  data_inicio_uso?: string | null;
  data_fim_uso?: string | null;
  peso_rateio?: number | null;
  observacoes?: string | null;
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

export function updateRecurso(
  recursoId: string,
  payload: Partial<RecursoCompartilhado> & {
    nome_recurso: string;
    tipo_custo: string;
    recorrencia: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<RecursoCompartilhado>(`/recursos-compartilhados/${recursoId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteRecurso(
  recursoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<null>(`/recursos-compartilhados/${recursoId}`, getAccessToken, {
    method: "DELETE",
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
    peso_rateio?: number;
    observacoes?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<VinculoRecurso>("/revisao-recursos-compartilhados", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateVinculo(
  vinculoId: string,
  payload: {
    ativo?: boolean;
    data_inicio_uso?: string;
    data_fim_uso?: string;
    peso_rateio?: number;
    observacoes?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<VinculoRecurso>(`/revisao-recursos-compartilhados/${vinculoId}`, getAccessToken, {
    method: "PUT",
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

export type DashboardRecalcResult = {
  mode: "full" | "incremental";
  rows_upserted: number;
  rows_deleted?: number;
  elapsed_ms: number;
  revisao_id?: string;
  processo_id?: string;
  competencia_inicio?: string;
  competencia_fim?: string;
};

export function recalcularDashboard(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<DashboardRecalcResult>(
    `/dashboard/recalcular${qs}`,
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

export type ImportPreviewResult = {
  validation: {
    ok: boolean;
    errors: string[];
    sheet_counts: Record<string, number>;
  };
  sheet_summary?: {
    solucoes_implementadas?: number;
    economia_liquida_total?: number;
    economia_bruta_total?: number;
    roi_medio?: number | null;
  } | null;
  db_counts?: Record<string, number>;
  db_summary?: ImportPreviewResult["sheet_summary"];
};

export type ImportApplyResult = {
  imported: Record<string, number>;
  recalc?: { rows_upserted: number; elapsed_ms: number };
  diff: {
    items: { metric: string; sheet: number; database: number; delta: number; match: boolean }[];
    all_match: boolean;
  };
  validation: { sheet_counts: Record<string, number> };
};

export function previewSheetImport(getAccessToken?: () => string | undefined) {
  return request<ImportPreviewResult>("/import/preview", getAccessToken);
}

export function applySheetImport(
  payload: { replace_existing?: boolean; recalc_dashboard?: boolean; csv_dir?: string },
  getAccessToken?: () => string | undefined
) {
  return request<ImportApplyResult>("/import/apply", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
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

export type DashboardFamiliaItem = {
  familia_processo: string;
  processos: number;
  economia_bruta: number;
  economia_liquida_mes: number;
};

export type DashboardAlertItem = {
  processo_id: string;
  codigo_processo?: string;
  nome_processo?: string;
  months: number;
  competencia_inicio?: string;
  competencia_fim?: string;
  economia_liquida_acumulada: number;
  familia_processo?: string | null;
  agrupador_ferramenta?: string | null;
};

export type RevisionCompareItem = {
  revisao_id: string;
  versao_revisao?: string;
  cenario_tipo?: string;
  revisao_ativa?: boolean;
  ultima_competencia?: string | null;
  meses_com_dados?: number;
  totais: {
    economia_bruta: number;
    economia_liquida_mes: number;
    investimento_unico_mes: number;
    custo_recorrente_mes: number;
    horas_economizadas_mes: number;
  };
};

export type RateioDiagnostic = {
  revisao_id: string;
  competencia?: string;
  economia_bruta: number;
  custo_recursos_compartilhados_mes: number;
  economia_liquida_mes: number;
  rateio_excede_ganho: boolean;
  message: string;
};

export function fetchDashboardPorFamilia(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<{ total: number; items: DashboardFamiliaItem[] }>(
    `/dashboard/por-familia${qs}`,
    getAccessToken
  );
}

export function fetchDashboardAlertas(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<{ min_consecutive_months: number; total: number; items: DashboardAlertItem[] }>(
    `/dashboard/alertas${qs}`,
    getAccessToken
  );
}

async function downloadDashboardExport(
  path: string,
  filename: string,
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}/dashboard/${path}${qs}`, {
    headers: buildAuthHeaders(getAccessToken),
  });
  if (!response.ok) {
    throw new Error(`Exportação falhou (HTTP ${response.status})`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function downloadDashboardCsv(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  return downloadDashboardExport("export.csv", "transformometro-dashboard.csv", getAccessToken, params);
}

export function downloadDashboardExcel(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  return downloadDashboardExport("export.xls", "transformometro-dashboard.xls", getAccessToken, params);
}

export function fetchProcessoComparativo(
  processoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{
    processo: Processo;
    total_revisoes: number;
    items: RevisionCompareItem[];
  }>(`/processos/${processoId}/comparativo`, getAccessToken);
}

export function fetchRevisaoDiagnosticoRateio(
  revisaoId: string,
  getAccessToken?: () => string | undefined,
  competencia?: string
) {
  const qs = competencia ? `?competencia=${encodeURIComponent(competencia)}` : "";
  return request<RateioDiagnostic>(`/revisoes/${revisaoId}/diagnostico-rateio${qs}`, getAccessToken);
}
