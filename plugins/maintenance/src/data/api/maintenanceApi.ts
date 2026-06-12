import { maintenanceFetch } from "./maintenanceApiBase";
import { appendListQuery, type ListQueryFilters, type ListQueryParams } from "../../utils/listQuery";

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

export type MotivoItem = { motivo_id: number; descricao: string };

export type StatusItem = {
  status_id: number;
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
  motivo_id: number;
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
    codigo_peca?: string;
  } & ListQueryParams,
  getAccessToken?: () => string | undefined,
) {
  const search = new URLSearchParams({
    filial: params.filial,
    codigo_ferramenta: params.codigo_ferramenta,
  });
  if (params.codigo_peca) search.set("codigo_peca", params.codigo_peca);
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

export function createReposicao(
  body: {
    filial: string;
    codigo_ferramenta: string;
    codigo_peca: string;
    data_reposicao: string;
    data_ultima_reposicao?: string;
    golpes: number;
    motivo_id: number;
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
    motivo_id: number;
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
) {
  return maintenanceFetch<MotivoItem>("/motivos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filial, descricao }),
    getAccessToken,
  });
}

export function updateMotivo(
  motivoId: number,
  filial: string,
  descricao: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<MotivoItem>(`/motivos/${motivoId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filial, descricao }),
    getAccessToken,
  });
}

export function deleteMotivo(
  motivoId: number,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<null>(`/motivos/${motivoId}?filial=${encodeURIComponent(filial)}`, {
    method: "DELETE",
    getAccessToken,
  });
}

export function updateStatusPeca(
  statusId: number,
  filial: string,
  body: { descricao?: string; operador?: string; percentual?: number },
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<StatusItem>(
    `/status-peca/${statusId}?filial=${encodeURIComponent(filial)}`,
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
  statusId: number,
  filial: string,
  getAccessToken?: () => string | undefined,
) {
  return maintenanceFetch<null>(`/status-peca/${statusId}?filial=${encodeURIComponent(filial)}`, {
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
