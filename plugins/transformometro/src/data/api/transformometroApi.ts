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

async function downloadFile(
  path: string,
  filename: string,
  getAccessToken?: () => string | undefined
): Promise<void> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
    headers: buildAuthHeaders(getAccessToken),
  });

  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { message?: string; detail?: string };
      message = body.message || body.detail || message;
    } catch {
      // resposta pode ser binária/texto
    }
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
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
  instancia_id?: string;
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

export type SetorOption = {
  id: string;
  label: string;
  filiais: string[];
  setor_id?: string;
  codigo_setor?: string;
};

export type FilialOption = {
  id: string;
  label: string;
  filial_id?: string;
  codigo_filial?: string;
};

export type AccessScope = {
  mode: "unrestricted" | "scoped";
  allowed_filiais: string[];
  can_view_consolidated: boolean;
  scoped_manage?: boolean;
};

export type DashboardViewMode = "consolidated" | "filial" | "department";

export type Setor = {
  setor_id: string;
  codigo_setor?: string;
  nome_setor: string;
  status_setor: string;
  filiais: string[];
};

export type Filial = {
  filial_id: string;
  codigo_filial?: string;
  nome_filial: string;
  status_filial: string;
};

export type ProcessoInstanciaSetor = {
  setor_id: string;
  codigo_setor?: string;
  nome_setor?: string;
};

export type ProcessoInstancia = {
  instancia_id: string;
  processo_id: string;
  filial_id?: string | null;
  todas_filiais_ativas?: boolean;
  setor_id?: string;
  setor_ids?: string[];
  setores?: ProcessoInstanciaSetor[];
  codigo_filial?: string;
  codigo_setor?: string;
  nome_filial?: string;
  nome_setor?: string;
  rotulo_instancia?: string | null;
  status_instancia?: string;
};

export type OptionsData = {
  filiais: FilialOption[];
  setores: SetorOption[];
  access_scope?: AccessScope;
  status_filial?: string[];
  status_setor: string[];
  status_processo: string[];
  cenario_tipo: string[];
  recorrencias: string[];
  criterio_rateio: string[];
  base_competencia_recurso?: string[];
  status_recurso: string[];
  escopo_recurso?: string[];
  tipo_investimento: string[];
  tipo_custo: string[];
  categorias: string[];
  status_aprovacao_revisao: string[];
};

export function fetchOptions(getAccessToken?: () => string | undefined) {
  return request<OptionsData>("/options", getAccessToken);
}

export function fetchFiliais(
  getAccessToken?: () => string | undefined,
  includeInactive = false
) {
  const qs = includeInactive ? "?include_inactive=true" : "";
  return request<{ total: number; items: Filial[] }>(`/filiais${qs}`, getAccessToken);
}

export function fetchFilial(filialId: string, getAccessToken?: () => string | undefined) {
  return request<Filial>(`/filiais/${filialId}`, getAccessToken);
}

export function createFilial(
  payload: {
    codigo_filial: string;
    nome_filial: string;
    status_filial?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<Filial>("/filiais", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateFilial(
  filialId: string,
  payload: {
    nome_filial: string;
    status_filial?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<Filial>(`/filiais/${filialId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteFilial(filialId: string, getAccessToken?: () => string | undefined) {
  return request<null>(`/filiais/${filialId}`, getAccessToken, { method: "DELETE" });
}

export function fetchSetores(
  getAccessToken?: () => string | undefined,
  filialId?: string
) {
  const qs = filialId ? `?${new URLSearchParams({ filial_id: filialId })}` : "";
  return request<{ total: number; items: Setor[] }>(`/setores${qs}`, getAccessToken);
}

export function createSetor(
  payload: {
    setor_id: string;
    nome_setor: string;
    filiais: string[];
    status_setor?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<Setor>("/setores", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateSetor(
  setorId: string,
  payload: {
    nome_setor: string;
    filiais: string[];
    status_setor?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<Setor>(`/setores/${setorId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteSetor(setorId: string, getAccessToken?: () => string | undefined) {
  return request<null>(`/setores/${setorId}`, getAccessToken, { method: "DELETE" });
}

export function fetchProcessos(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<{ total: number; items: Processo[] }>(`/processos${qs}`, getAccessToken);
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
  return request<null>(`/processos/${processoId}`, getAccessToken, { method: "DELETE" });
}

export function fetchProcessoInstancias(
  processoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ total: number; items: ProcessoInstancia[] }>(
    `/processos/${processoId}/instancias`,
    getAccessToken
  );
}

export function fetchInstancia(
  instanciaId: string,
  getAccessToken?: () => string | undefined
) {
  return request<ProcessoInstancia>(`/instancias/${instanciaId}`, getAccessToken);
}

export function createProcessoInstancia(
  processoId: string,
  payload: {
    filial_id?: string;
    todas_filiais_ativas?: boolean;
    setor_ids: string[];
    rotulo_instancia?: string;
    status_instancia?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<ProcessoInstancia>(`/processos/${processoId}/instancias`, getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateInstancia(
  instanciaId: string,
  payload: {
    setor_ids: string[];
    rotulo_instancia?: string;
    status_instancia?: string;
    filial_id?: string;
    todas_filiais_ativas?: boolean;
  },
  getAccessToken?: () => string | undefined
) {
  return request<ProcessoInstancia>(`/instancias/${instanciaId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteInstancia(instanciaId: string, getAccessToken?: () => string | undefined) {
  return request<null>(`/instancias/${instanciaId}`, getAccessToken, { method: "DELETE" });
}

export type InstanciaDuplicateResult = {
  instancia: ProcessoInstancia;
  processo_id: string;
  origem_instancia_id: string;
  copiados: {
    revisoes: number;
    medicoes: number;
    investimentos: number;
    vinculos: number;
  };
};

export function duplicateInstancia(
  instanciaId: string,
  payload: { filial_id: string; setor_id: string; rotulo_instancia?: string },
  getAccessToken?: () => string | undefined
) {
  return request<InstanciaDuplicateResult>(`/instancias/${instanciaId}/duplicar`, getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type ProcessoDuplicateResult = {
  processo: Processo;
  origem_processo_id: string;
  copiados: {
    revisoes: number;
    medicoes: number;
    investimentos: number;
    vinculos: number;
  };
};

export function duplicateProcesso(
  processoId: string,
  payload?: { nome_processo?: string },
  getAccessToken?: () => string | undefined
) {
  return request<ProcessoDuplicateResult>(`/processos/${processoId}/duplicar`, getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload ?? {}),
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
  payload: Partial<Revisao> & {
    processo_id: string;
    versao_revisao: string;
    cenario_tipo: string;
    data_inicio_vigencia: string;
    instancia_id?: string;
  },
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

export function deleteRevisao(
  revisaoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<null>(`/revisoes/${revisaoId}`, getAccessToken, { method: "DELETE" });
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
  escopo_recurso?: string;
  base_competencia?: string;
  status_recurso: string;
  categoria_recurso?: string | null;
  fornecedor?: string | null;
  data_inicio_vigencia?: string | null;
  data_fim_vigencia?: string | null;
  centro_custo?: string | null;
  observacoes?: string | null;
};

export type RecursoCusto = {
  recurso_custo_id: string;
  recurso_compartilhado_id: string;
  valor_mensal: number;
  data_inicio_vigencia: string;
  data_fim_vigencia?: string | null;
  observacoes?: string | null;
};

type RecursoCustoMutationResponse = {
  custo?: RecursoCusto;
  recurso?: RecursoCompartilhado | null;
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
  base_competencia?: string;
  status_recurso?: string;
  recurso_observacoes?: string | null;
  ativo: boolean;
  data_inicio_uso?: string | null;
  data_fim_uso?: string | null;
  peso_rateio?: number | null;
  observacoes?: string | null;
  processo_id?: string;
  codigo_processo?: string;
  nome_processo?: string;
  filial_id?: string;
  setor_id?: string;
  status_processo?: string;
  familia_processo?: string | null;
  gestor_responsavel?: string | null;
  versao_revisao?: string;
  cenario_tipo?: string;
  revisao_ativa?: boolean;
  revisao_data_inicio_vigencia?: string | null;
  revisao_data_implantacao?: string | null;
  revisao_data_fim_vigencia?: string | null;
};

export function fetchMedicao(revisaoId: string, getAccessToken?: () => string | undefined) {
  return request<Medicao | null>(`/revisoes/${revisaoId}/medicoes`, getAccessToken);
}

export function upsertMedicao(payload: Medicao, getAccessToken?: () => string | undefined) {
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

export function updateInvestimento(
  investimentoId: string,
  payload: Partial<Investimento> & { tipo_investimento: string; descricao_item: string },
  getAccessToken?: () => string | undefined
) {
  return request<Investimento>(`/investimentos/${investimentoId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteInvestimento(
  investimentoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<null>(`/investimentos/${investimentoId}`, getAccessToken, { method: "DELETE" });
}

export function fetchRecursos(getAccessToken?: () => string | undefined) {
  return request<{ total: number; items: RecursoCompartilhado[] }>(
    "/recursos-compartilhados",
    getAccessToken
  );
}

export function fetchRecurso(recursoId: string, getAccessToken?: () => string | undefined) {
  return request<RecursoCompartilhado>(`/recursos-compartilhados/${recursoId}`, getAccessToken);
}

export function createRecurso(
  payload: Partial<RecursoCompartilhado> & { nome_recurso: string; tipo_custo: string; recorrencia: string },
  getAccessToken?: () => string | undefined
) {
  return request<RecursoCompartilhado>("/recursos-compartilhados", getAccessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRecurso(
  recursoId: string,
  payload: Partial<RecursoCompartilhado> & { nome_recurso: string; tipo_custo: string; recorrencia: string },
  getAccessToken?: () => string | undefined
) {
  return request<RecursoCompartilhado>(`/recursos-compartilhados/${recursoId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteRecurso(recursoId: string, getAccessToken?: () => string | undefined) {
  return request<null>(`/recursos-compartilhados/${recursoId}`, getAccessToken, { method: "DELETE" });
}

export function fetchRecursoCustos(
  recursoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ total: number; items: RecursoCusto[] }>(
    `/recursos-compartilhados/${recursoId}/custos`,
    getAccessToken
  );
}

export function reajusteRecursoCusto(
  recursoId: string,
  payload: { valor_mensal: number; vigente_desde: string; observacoes?: string },
  getAccessToken?: () => string | undefined
) {
  return request<RecursoCustoMutationResponse>(
    `/recursos-compartilhados/${recursoId}/custos/reajuste`,
    getAccessToken,
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export function updateRecursoCusto(
  recursoCustoId: string,
  payload: {
    valor_mensal: number;
    data_inicio_vigencia: string;
    data_fim_vigencia?: string | null;
    observacoes?: string;
  },
  getAccessToken?: () => string | undefined
) {
  return request<RecursoCustoMutationResponse>(`/recurso-custos/${recursoCustoId}`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteRecursoCusto(
  recursoCustoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<RecursoCustoMutationResponse>(`/recurso-custos/${recursoCustoId}`, getAccessToken, {
    method: "DELETE",
  });
}

export function fetchVinculos(revisaoId: string, getAccessToken?: () => string | undefined) {
  return request<{ total: number; items: VinculoRecurso[] }>(
    `/revisoes/${revisaoId}/recursos-compartilhados`,
    getAccessToken
  );
}

export function fetchRecursoVinculos(
  recursoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<{ total: number; items: VinculoRecurso[] }>(
    `/recursos-compartilhados/${recursoId}/vinculos`,
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

export function deleteVinculo(vinculoId: string, getAccessToken?: () => string | undefined) {
  return request<null>(`/revisao-recursos-compartilhados/${vinculoId}`, getAccessToken, { method: "DELETE" });
}

export type DashboardResumo = {
  solucoes_implementadas: number;
  economia_liquida_total: number;
  economia_bruta_total: number;
  horas_economizadas_total?: number;
  investimento_unico_total?: number;
  custo_recorrente_total?: number;
  custo_recursos_compartilhados_total?: number;
  investimento_total?: number;
  roi_medio: number | null;
  linhas_materializadas?: number;
};

export type DashboardEvolucaoItem = {
  competencia: string;
  economia_bruta: number;
  investimento_unico_mes?: number;
  custo_recorrente_mes: number;
  investimento_total_mes?: number;
  custo_recursos_compartilhados_mes?: number;
  economia_liquida_mes: number;
  horas_economizadas_mes?: number;
};

export type DashboardProcessoItem = {
  processo_id: string;
  codigo_processo: string;
  nome_processo: string;
  economia_diaria: number | null;
  horas_diaria?: number | null;
  horas_economizadas_mes?: number;
  economia_liquida_mes?: number;
  economia_bruta?: number;
  investimento_unico_mes?: number;
  custo_recorrente_mes?: number;
  custo_recursos_compartilhados_mes?: number;
  investimento_total_mes?: number;
  data_implantacao?: string | null;
  revisao_implantacao_id?: string | null;
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
  return request<DashboardRecalcResult>(`/dashboard/recalcular${qs}`, getAccessToken, { method: "POST" });
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

export type DashboardAlertaItem = {
  processo_id: string;
  codigo_processo: string;
  nome_processo: string;
  filial_id?: string | null;
  setor_id?: string | null;
  familia_processo?: string | null;
  agrupador_ferramenta?: string | null;
  months: number;
  competencia_inicio: string;
  competencia_fim: string;
  economia_liquida_acumulada: number;
};

export type DashboardAlertItem = DashboardAlertaItem;

export function fetchDashboardAlertas(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return request<{ total: number; items: DashboardAlertaItem[] }>(
    `/dashboard/alertas${qs}`,
    getAccessToken
  );
}

export type DashboardFamiliaItem = {
  familia_processo: string;
  processos: number;
  economia_bruta: number;
  economia_liquida_mes: number;
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

export function downloadDashboardCsv(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return downloadFile(`/dashboard/export.csv${qs}`, "dashboard-transformometro.csv", getAccessToken);
}

export function downloadDashboardExcel(
  getAccessToken?: () => string | undefined,
  params?: Record<string, string>
) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return downloadFile(`/dashboard/export.xls${qs}`, "dashboard-transformometro.xls", getAccessToken);
}

export type ProcessoComparativoItem = {
  revisao_id: string;
  versao_revisao?: string | null;
  cenario_tipo?: string | null;
  revisao_ativa?: boolean | null;
  data_inicio_vigencia?: string | null;
  data_fim_vigencia?: string | null;
  ultima_competencia?: string | null;
  meses_com_dados?: number | null;
  totais: {
    economia_bruta: number;
    economia_liquida_mes: number;
    horas_economizadas_mes: number;
    investimento_unico_mes?: number;
    custo_recorrente_mes?: number;
    custo_recursos_compartilhados_mes?: number;
    investimento_total_mes?: number;
  };
};

export type ProcessoComparativoResponse = {
  processo?: {
    processo_id: string;
    codigo_processo?: string | null;
    nome_processo?: string | null;
    familia_processo?: string | null;
    agrupador_ferramenta?: string | null;
  };
  total_revisoes: number;
  items: ProcessoComparativoItem[];
};

export function fetchProcessoComparativo(
  processoId: string,
  getAccessToken?: () => string | undefined
) {
  return request<ProcessoComparativoResponse>(`/processos/${processoId}/comparativo`, getAccessToken);
}

export type JsonBackupBundle = {
  schema_version: string;
  exported_at?: string;
  import_format?: "modern" | "legacy";
  counts?: Record<string, number>;
  filiais?: Record<string, unknown>[];
  setores: Record<string, unknown>[];
  setor_filiais: Record<string, unknown>[];
  processos: Record<string, unknown>[];
  processo_instancias?: Record<string, unknown>[];
  revisoes: Record<string, unknown>[];
  medicoes: Record<string, unknown>[];
  investimentos: Record<string, unknown>[];
  recursos_compartilhados: Record<string, unknown>[];
  recurso_custos: Record<string, unknown>[];
  revisao_recursos_compartilhados: Record<string, unknown>[];
};

export type JsonImportMode = "replace" | "merge";
export type JsonImportFormat = "auto" | "modern" | "legacy";

export type JsonImportEntityStats = {
  total: number;
  insert: number;
  update: number;
  skip: number;
};

export type JsonImportPreview = {
  valid: boolean;
  errors?: string[];
  mode: JsonImportMode;
  requested_format?: JsonImportFormat;
  resolved_format?: "modern" | "legacy";
  detected_format?: "modern" | "legacy";
  legacy_transformed?: boolean;
  entities?: Record<string, JsonImportEntityStats>;
  current_counts?: Record<string, number>;
  import_counts?: Record<string, number>;
  recalc?: DashboardRecalcResult;
};

export function downloadJsonExport(getAccessToken?: () => string | undefined) {
  return downloadFile("/data/export", "transformometro-backup.json", getAccessToken);
}

export function previewJsonImport(
  data: JsonBackupBundle,
  mode: JsonImportMode,
  importFormat: JsonImportFormat = "auto",
  getAccessToken?: () => string | undefined
) {
  return request<JsonImportPreview>("/data/import/preview", getAccessToken, {
    method: "POST",
    body: JSON.stringify({ mode, import_format: importFormat, data }),
  });
}

export function applyJsonImport(
  data: JsonBackupBundle,
  mode: JsonImportMode,
  importFormat: JsonImportFormat = "auto",
  getAccessToken?: () => string | undefined
) {
  return request<JsonImportPreview & { recalc?: DashboardRecalcResult }>(
    "/data/import/apply",
    getAccessToken,
    {
      method: "POST",
      body: JSON.stringify({ mode, import_format: importFormat, data }),
    }
  );
}
