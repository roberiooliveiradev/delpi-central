import { maintenanceFetch } from "./maintenanceApiBase";
import { appendListQuery, MAX_LIST_PAGE_SIZE, type ListQueryFilters, type ListQueryParams } from "../../utils/listQuery";

export type FerramentaItem = {
  id: number;
  codigo: string;
  descricao: string;
  grupo?: string;
};

export type FerramentasPage = {
  items: FerramentaItem[];
  total: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
};

export type MaintenanceSubmodule = {
  id: string;
  label: string;
  description: string;
  icon: string;
  entry_path: string;
  can_manage?: boolean;
  filiais?: string[] | null;
};

export type MaintenanceOptions = {
  filiais: Array<{ id: string; label: string }>;
  submodules: MaintenanceSubmodule[];
  modulos: MaintenanceSubmodule[];
  default_filial?: string | null;
  access_scope?: {
    mode: string;
    allowed_filiais: string[];
    manage_filiais?: string[];
    scoped_manage: boolean;
  };
  can_manage_filiais?: boolean;
};

export type PagedItems<T> = {
  items: T[];
  total: number;
};

export type PreventivaResumo = {
  critico: number;
  atencao: number;
  ok: number;
  sem_status: number;
  total: number;
};

export function fetchMaintenanceOptions(
  getAccessToken?: () => string | undefined,
  filial?: string,
) {
  const search = filial ? `?filial=${encodeURIComponent(filial)}` : "";
  return maintenanceFetch<MaintenanceOptions>(`/options${search}`, { getAccessToken });
}

export function fetchFerramentas(
  params: {
    filial: string;
    codigo?: string;
    descricao?: string;
  } & ListQueryParams,
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams();
  search.set("filial", params.filial);
  appendListQuery(
    search,
    {
      page: params.page,
      pageSize: params.pageSize,
      sortKey: params.sortKey,
      sortDirection: params.sortDirection,
    },
    {
      codigo: params.codigo,
      descricao: params.descricao,
    },
  );

  return maintenanceFetch<FerramentasPage>(`/mini-aplicadores/ferramentas?${search.toString()}`, {
    getAccessToken,
  });
}

export function fetchFerramenta(
  codigo: string,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<FerramentaItem>(
    `/mini-aplicadores/ferramentas/${encodeURIComponent(codigo)}?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
}

export type ComponenteItem = {
  id: number;
  nivel: number;
  codigo: string;
  descricao: string;
  unidade: string;
  estoque_local_01: number;
  estoque_local_99: number;
};

export type UltimaReposicaoItem = {
  reposicao_id: string;
  filial: string;
  codigo_ferramenta: string;
  codigo_peca: string;
  descricao_ferramenta?: string;
  descricao_peca?: string;
  data_reposicao: string;
  golpes: number;
};

export function fetchComponentes(
  codigoFerramenta: string,
  filial: string,
  query: ListQueryParams = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({ filial });
  appendListQuery(search, query);
  return maintenanceFetch<PagedItems<ComponenteItem>>(
    `/mini-aplicadores/ferramentas/${encodeURIComponent(codigoFerramenta)}/componentes?${search.toString()}`,
    { getAccessToken },
  );
}

export function fetchUltimasReposicoes(
  filial: string,
  query: ListQueryParams = {},
  filters: ListQueryFilters = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({ filial });
  appendListQuery(search, query, filters);
  return maintenanceFetch<PagedItems<UltimaReposicaoItem>>(
    `/preventiva/ultimas-reposicoes?${search.toString()}`,
    { getAccessToken },
  );
}

export type PreventivaAlerta = {
  filial: string;
  codigo_ferramenta: string;
  codigo_peca: string;
  descricao_ferramenta?: string;
  descricao_peca?: string;
  data_ultima_reposicao: string;
  media_golpes: number;
  golpes_atuais: number;
  percentual_uso: number;
  status: string;
};

export type PreventivaHistoricoItem = {
  reposicao_id: string;
  data_reposicao: string;
  golpes: number;
};

export function fetchPreventivaResumo(
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<PreventivaResumo>(
    `/preventiva/resumo?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
}

export function fetchPreventivaAlertas(
  filial: string,
  query: ListQueryParams = {},
  filters: ListQueryFilters = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({ filial });
  appendListQuery(search, query, filters);
  return maintenanceFetch<PagedItems<PreventivaAlerta>>(
    `/preventiva/alertas?${search.toString()}`,
    { getAccessToken },
  );
}

export function fetchPreventivaHistorico(
  params: { filial: string; codigo_ferramenta: string; codigo_peca: string },
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams(params);
  return maintenanceFetch<PagedItems<PreventivaHistoricoItem>>(
    `/preventiva/historico?${search.toString()}`,
    { getAccessToken },
  );
}

export type RevisaoProgramadaItem = {
  revisao_id: string;
  filial: string;
  codigo_ferramenta: string;
  intervalo_meses: number;
  data_ultima_revisao?: string | null;
  observacao?: string | null;
  data_criacao?: string;
  data_alteracao?: string;
};

export type RevisaoProgramadaAlerta = {
  revisao_id: string;
  filial: string;
  codigo_ferramenta: string;
  descricao_ferramenta?: string;
  intervalo_meses: number;
  observacao?: string | null;
  data_ultima_revisao?: string | null;
  data_referencia?: string | null;
  data_proxima_revisao?: string | null;
  dias_desde_revisao?: number | null;
  dias_restantes?: number | null;
  status: string;
};

export type RevisaoProgramadaResumo = PreventivaResumo;

export function fetchRevisoesProgramadas(
  filial: string,
  query: ListQueryParams = {},
  filters: ListQueryFilters = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({ filial });
  appendListQuery(search, query, filters);
  return maintenanceFetch<PagedItems<RevisaoProgramadaItem>>(
    `/revisoes-programadas?${search.toString()}`,
    { getAccessToken },
  );
}

export function createRevisaoProgramada(
  body: {
    filial: string;
    codigo_ferramenta: string;
    intervalo_meses: number;
    observacao?: string;
    data_ultima_revisao?: string;
  },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<RevisaoProgramadaItem>("/revisoes-programadas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    getAccessToken,
  });
}

export function updateRevisaoProgramada(
  revisaoId: string,
  body: {
    filial: string;
    intervalo_meses?: number;
    observacao?: string;
    data_ultima_revisao?: string | null;
  },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<RevisaoProgramadaItem>(
    `/revisoes-programadas/${encodeURIComponent(revisaoId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      getAccessToken,
    },
  );
}

export function deleteRevisaoProgramada(
  revisaoId: string,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<null>(
    `/revisoes-programadas/${encodeURIComponent(revisaoId)}?filial=${encodeURIComponent(filial)}`,
    {
      method: "DELETE",
      getAccessToken,
    },
  );
}

export function registrarRevisaoProgramada(
  revisaoId: string,
  filial: string,
  dataRevisao?: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<RevisaoProgramadaItem>(
    `/revisoes-programadas/${encodeURIComponent(revisaoId)}/registrar?filial=${encodeURIComponent(filial)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dataRevisao ? { data_revisao: dataRevisao } : {}),
      getAccessToken,
    },
  );
}

export function fetchRevisaoProgramadaResumo(
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<RevisaoProgramadaResumo>(
    `/preventiva/revisoes/resumo?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
}

export function fetchRevisaoProgramadaAlertas(
  filial: string,
  query: ListQueryParams = {},
  filters: ListQueryFilters = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({ filial });
  appendListQuery(search, query, filters);
  return maintenanceFetch<PagedItems<RevisaoProgramadaAlerta>>(
    `/preventiva/revisoes/alertas?${search.toString()}`,
    { getAccessToken },
  );
}

export type RevisaoProgramadaRealizacao = {
  realizacao_id: string;
  revisao_id: string;
  filial: string;
  codigo_ferramenta: string;
  data_revisao: string;
  intervalo_meses: number;
  observacao?: string | null;
  data_registro: string;
};

export function fetchRevisaoProgramadaRealizacoes(
  filial: string,
  codigoFerramenta: string,
  query: ListQueryParams = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({
    filial,
    codigo_ferramenta: codigoFerramenta,
  });
  appendListQuery(search, query);
  return maintenanceFetch<PagedItems<RevisaoProgramadaRealizacao>>(
    `/revisoes-programadas/realizacoes?${search.toString()}`,
    { getAccessToken },
  );
}

export type MotivoItem = {
  motivo_id: string;
  descricao: string;
  excluir_preventiva?: boolean;
};

export type StatusItem = {
  status_id: string;
  descricao: string;
  operador: string;
  percentual: number;
};
export type ReposicaoItem = {
  reposicao_id: string;
  filial: string;
  codigo_ferramenta: string;
  codigo_peca: string;
  data_reposicao: string;
  data_ultima_reposicao?: string | null;
  golpes: number;
  motivo_id: string;
  motivo_descricao?: string;
  observacao?: string | null;
};

export function fetchMotivos(
  filial: string,
  query: ListQueryParams = {},
  filters: ListQueryFilters = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({ filial });
  appendListQuery(search, query, filters);
  return maintenanceFetch<PagedItems<MotivoItem>>(`/motivos?${search.toString()}`, { getAccessToken });
}

export function fetchStatusPeca(
  filial: string,
  query: ListQueryParams = {},
  filters: ListQueryFilters = {},
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({ filial });
  appendListQuery(search, query, filters);
  return maintenanceFetch<PagedItems<StatusItem>>(`/status-peca?${search.toString()}`, {
    getAccessToken,
  });
}

export function fetchReposicoes(
  params: {
    filial: string;
    codigo_ferramenta: string;
    codigo_peca?: string[];
    motivo_id?: string[];
    data_inicial?: string;
    data_final?: string;
  } & ListQueryParams,
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({
    filial: params.filial,
    codigo_ferramenta: params.codigo_ferramenta,
  });
  if (params.codigo_peca?.length) {
    for (const peca of params.codigo_peca) {
      search.append("codigo_peca", peca);
    }
  }
  if (params.motivo_id?.length) {
    for (const motivoId of params.motivo_id) {
      search.append("motivo_id", String(motivoId));
    }
  }
  if (params.data_inicial) search.set("data_inicial", params.data_inicial);
  if (params.data_final) search.set("data_final", params.data_final);
  appendListQuery(search, {
    page: params.page,
    pageSize: params.pageSize,
    sortKey: params.sortKey,
    sortDirection: params.sortDirection,
  });
  return maintenanceFetch<PagedItems<ReposicaoItem>>(`/reposicoes?${search.toString()}`, {
    getAccessToken,
  });
}

export async function fetchAllReposicoes(
  params: {
    filial: string;
    codigo_ferramenta: string;
    codigo_peca?: string[];
    motivo_id?: string[];
    data_inicial?: string;
    data_final?: string;
    sortKey?: string | null;
    sortDirection?: "asc" | "desc";
    maxItems?: number;
  },
  getAccessToken?: () => string | undefined,
): Promise<ReposicaoItem[]> {
  const items: ReposicaoItem[] = [];
  const maxItems = params.maxItems ?? Number.POSITIVE_INFINITY;
  let page = 1;
  let total = Number.POSITIVE_INFINITY;

  while (items.length < total && items.length < maxItems) {
    const data = await fetchReposicoes(
      {
        filial: params.filial,
        codigo_ferramenta: params.codigo_ferramenta,
        codigo_peca: params.codigo_peca,
        motivo_id: params.motivo_id,
        data_inicial: params.data_inicial,
        data_final: params.data_final,
        page,
        pageSize: MAX_LIST_PAGE_SIZE,
        sortKey: params.sortKey,
        sortDirection: params.sortDirection,
      },
      getAccessToken,
    );
    total = data.total ?? 0;
    const pageItems = data.items ?? [];
    if (pageItems.length === 0) break;
    items.push(...pageItems);
    page += 1;
  }

  return items.slice(0, maxItems);
}

export function createReposicao(
  body: {
    filial: string;
    codigo_ferramenta: string;
    codigo_peca: string;
    data_reposicao: string;
    data_ultima_reposicao?: string;
    golpes: number;
    motivo_id: string;
    observacao?: string;
  },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<ReposicaoItem>("/reposicoes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    getAccessToken,
  });
}

export function updateReposicao(
  reposicaoId: string,
  body: {
    filial: string;
    codigo_ferramenta: string;
    codigo_peca: string;
    data_reposicao: string;
    data_ultima_reposicao?: string;
    golpes: number;
    motivo_id: string;
    observacao?: string;
  },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<ReposicaoItem>(`/reposicoes/${encodeURIComponent(reposicaoId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    getAccessToken,
  });
}

export function deleteReposicao(reposicaoId: string, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<null>(`/reposicoes/${encodeURIComponent(reposicaoId)}`, {
    method: "DELETE",
    getAccessToken,
  });
}

export function createMotivo(
  filial: string,
  descricao: string,
  getAccessToken?: () => string | undefined,
  excluirPreventiva = false,
) {
  return maintenanceFetch<MotivoItem>("/motivos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filial, descricao, excluir_preventiva: excluirPreventiva }),
    getAccessToken,
  });
}

export function updateMotivo(
  motivoId: string,
  filial: string,
  payload: { descricao: string; excluir_preventiva?: boolean },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<MotivoItem>(`/motivos/${encodeURIComponent(motivoId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filial, ...payload }),
    getAccessToken,
  });
}

export function deleteMotivo(
  motivoId: string,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<null>(`/motivos/${encodeURIComponent(motivoId)}?filial=${encodeURIComponent(filial)}`, {
    method: "DELETE",
    getAccessToken,
  });
}

export function updateStatusPeca(
  statusId: string,
  filial: string,
  body: { descricao?: string; operador?: string; percentual?: number },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<StatusItem>(
    `/status-peca/${encodeURIComponent(statusId)}?filial=${encodeURIComponent(filial)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      getAccessToken,
    },
  );
}

export function createStatusPeca(
  body: {
    filial: string;
    descricao: string;
    operador: string;
    percentual: number;
  },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<StatusItem>("/status-peca", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    getAccessToken,
  });
}

export function deleteStatusPeca(
  statusId: string,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<null>(`/status-peca/${encodeURIComponent(statusId)}?filial=${encodeURIComponent(filial)}`, {
    method: "DELETE",
    getAccessToken,
  });
}

export function fetchPecas(
  codigoFerramenta: string,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<PagedItems<FerramentaItem>>(
    `/mini-aplicadores/ferramentas/${encodeURIComponent(codigoFerramenta)}/pecas?filial=${encodeURIComponent(filial)}`,
    { getAccessToken },
  );
}

export type SuggestGolpesResult = {
  total_golpes: number;
  data_ultima_reposicao: string | null;
  data_inicial?: string;
  data_final?: string;
};

export function suggestGolpes(
  params: {
    filial: string;
    codigo_ferramenta: string;
    codigo_peca: string;
    data_inicial?: string;
    data_final?: string;
  },
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({
    filial: params.filial,
    codigo_ferramenta: params.codigo_ferramenta,
    codigo_peca: params.codigo_peca,
  });
  if (params.data_inicial) search.set("data_inicial", params.data_inicial);
  if (params.data_final) search.set("data_final", params.data_final);
  return maintenanceFetch<SuggestGolpesResult>(
    `/mini-aplicadores/sugerir-golpes?${search.toString()}`,
    { getAccessToken },
  );
}

export type FilialItem = {
  filial_id: number;
  codigo_filial: string;
  nome_filial: string;
  status_filial: "ativo" | "inativo";
  data_criacao?: string | null;
  data_alteracao?: string | null;
};

export function fetchFiliaisAdmin(
  query: ListQueryParams = {},
  getAccessToken?: () => string | undefined,
  includeInactive = true,
) {
  const search = new URLSearchParams({ admin: "true" });
  if (includeInactive) search.set("include_inactive", "true");
  appendListQuery(search, query);
  return maintenanceFetch<PagedItems<FilialItem>>(`/filiais?${search.toString()}`, {
    getAccessToken,
  });
}

export function createFilial(
  payload: { codigo_filial: string; nome_filial: string; status_filial?: "ativo" | "inativo" },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<FilialItem>("/filiais", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    getAccessToken,
    body: JSON.stringify({
      status_filial: "ativo",
      ...payload,
    }),
  });
}

export function updateFilial(
  filialRef: string | number,
  payload: { nome_filial: string; status_filial: "ativo" | "inativo" },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<FilialItem>(`/filiais/${filialRef}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    getAccessToken,
    body: JSON.stringify(payload),
  });
}

export function deleteFilial(filialRef: string | number, getAccessToken?: () => string | undefined) {
  return maintenanceFetch<null>(`/filiais/${filialRef}`, {
    method: "DELETE",
    getAccessToken,
  });
}
